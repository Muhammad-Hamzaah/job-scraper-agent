"""FastAPI backend for the JobScout web app.

Run from the src/ folder:
    uvicorn api:app --reload
"""

import asyncio
import hashlib
import html
import logging
import re
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles

from adzuna import VALID_COUNTRIES, fetch_adzuna_jobs
from database import init_db, insert_jobs
from fetch_jobs import fetch_jobs
from main import normalize_adzuna_job, normalize_arbeitnow_job

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Folder at project root: job-scraper-agent/frontend
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

# Readable labels for the country dropdown (codes come from Adzuna).
COUNTRY_NAMES = {
    "us": "United States",
    "gb": "United Kingdom",
    "fr": "France",
    "de": "Germany",
    "ca": "Canada",
    "in": "India",
    "au": "Australia",
    "br": "Brazil",
    "nl": "Netherlands",
    "sg": "Singapore",
    "za": "South Africa",
    "pl": "Poland",
    "it": "Italy",
    "es": "Spain",
    "mx": "Mexico",
    "nz": "New Zealand",
}

MAX_TEXT_LEN = 100
SNIPPET_LEN = 220

app = FastAPI(title="JobScout API", version="0.1.0")


def html_to_plain_text(raw: str | None) -> str:
    """Turn third-party HTML (or plain text) into safe plain text."""
    if not raw:
        return ""

    text = raw
    # List items become markdown-style bullets.
    text = re.sub(r"<li[^>]*>", "- ", text, flags=re.IGNORECASE)
    text = re.sub(r"</li>", "\n", text, flags=re.IGNORECASE)
    # Block tags and line breaks become newlines.
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</?p[^>]*>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</?h2[^>]*>", "\n", text, flags=re.IGNORECASE)
    # Drop every remaining tag (never send HTML to the frontend as markup).
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text)
    # Collapse runs of blank lines, keep single paragraph breaks.
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def job_id_from_url(url: str) -> str:
    """Stable 12-character id from the job URL (SHA-1 prefix)."""
    return hashlib.sha1((url or "").encode("utf-8")).hexdigest()[:12]


def to_api_job(job: dict) -> dict:
    """Map the shared scraper dict to the JSON shape the frontend will use."""
    description = html_to_plain_text(job.get("description"))
    snippet = description[:SNIPPET_LEN]
    if len(description) > SNIPPET_LEN:
        snippet = snippet.rstrip() + "..."

    url = job.get("url") or ""
    return {
        "id": job_id_from_url(url),
        "title": job.get("title") or "",
        "company": job.get("company_name") or "",
        "location": job.get("location") or "",
        "job_types": job.get("job_types") or [],
        "snippet": snippet,
        "description": description,
        "url": url,
        "source": job.get("source") or "",
        "posted_at": job.get("posted_at") or "Unknown",
    }


def resolve_search_params(keyword: str, country: str, city: str) -> dict:
    """Same remote/country/city split as described for CLI run()."""
    if country == "remote":
        return {
            "arbeitnow_keyword": keyword,
            "arbeitnow_location": "remote",
            "adzuna_keyword": f"{keyword} remote",
            "adzuna_location": city,
            "adzuna_country": "us",
        }
    return {
        "arbeitnow_keyword": keyword,
        "arbeitnow_location": city,
        "adzuna_keyword": keyword,
        "adzuna_location": city,
        "adzuna_country": country,
    }


async def fetch_normalized_arbeitnow(keyword: str, location: str) -> list[dict]:
    """Run the blocking Arbeitnow client in a thread; never raise to the caller."""
    try:
        raw = await asyncio.to_thread(fetch_jobs, keyword, location)
        return [normalize_arbeitnow_job(j) for j in raw]
    except Exception:
        logger.exception("Arbeitnow fetch failed")
        return []


async def fetch_normalized_adzuna(keyword: str, location: str, country: str) -> list[dict]:
    """Run the blocking Adzuna client in a thread; never raise to the caller."""
    try:
        raw = await asyncio.to_thread(fetch_adzuna_jobs, keyword, location, country)
        return [normalize_adzuna_job(j) for j in raw]
    except Exception:
        logger.exception("Adzuna fetch failed")
        return []


def dedupe_by_url(jobs: list[dict]) -> list[dict]:
    """Keep the first job for each apply URL."""
    seen: set[str] = set()
    unique: list[dict] = []
    for job in jobs:
        url = job.get("url") or ""
        if not url or url in seen:
            continue
        seen.add(url)
        unique.append(job)
    return unique


def save_jobs_safely(jobs: list[dict]) -> None:
    """Persist results; a DB error must not fail the search response."""
    try:
        init_db()
        insert_jobs(jobs)
    except Exception:
        logger.exception("Could not save jobs to the database")


# --- API routes (registered before the static mount) ---


@app.get("/api/health")
def health():
    """Liveness check for the web app and later for deployment probes."""
    return {"status": "ok"}


@app.get("/api/countries")
def countries():
    """Country dropdown: Adzuna codes plus a Remote option."""
    items = [
        {"code": code, "name": COUNTRY_NAMES.get(code, code.upper())}
        for code in sorted(VALID_COUNTRIES)
    ]
    items.append({"code": "remote", "name": "Remote"})
    return {"countries": items}


@app.get("/api/search")
async def search(
    keyword: str = Query(..., min_length=1, max_length=MAX_TEXT_LEN),
    country: str = Query("us", max_length=20),
    city: str = Query("", max_length=MAX_TEXT_LEN),
):
    """Search Arbeitnow and Adzuna in parallel and return a combined list."""
    keyword = keyword.strip()
    country = country.strip().lower()
    city = city.strip()

    if not keyword or len(keyword) > MAX_TEXT_LEN:
        raise HTTPException(status_code=400, detail="keyword must be 1 to 100 characters.")
    if city and len(city) > MAX_TEXT_LEN:
        raise HTTPException(status_code=400, detail="city must be at most 100 characters.")
    if country != "remote" and country not in VALID_COUNTRIES:
        raise HTTPException(
            status_code=400,
            detail="country must be 'remote' or a supported Adzuna country code.",
        )

    params = resolve_search_params(keyword, country, city)
    logger.info(
        "Search keyword=%r country=%s city=%r",
        keyword,
        country,
        city,
    )

    arbeitnow_jobs, adzuna_jobs = await asyncio.gather(
        fetch_normalized_arbeitnow(
            params["arbeitnow_keyword"],
            params["arbeitnow_location"],
        ),
        fetch_normalized_adzuna(
            params["adzuna_keyword"],
            params["adzuna_location"],
            params["adzuna_country"],
        ),
    )

    combined = dedupe_by_url(arbeitnow_jobs + adzuna_jobs)
    save_jobs_safely(combined)

    api_jobs = [to_api_job(job) for job in combined]
    return {"count": len(api_jobs), "jobs": api_jobs}


# Serve frontend/ at / (html=True so / returns index.html).
# Must stay last so /api/* and /docs are not swallowed by StaticFiles.
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
