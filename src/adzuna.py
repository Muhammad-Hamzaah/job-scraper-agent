import os
import requests
import logging
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)

ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID")
ADZUNA_APP_KEY = os.getenv("ADZUNA_APP_KEY")

# Adzuna supported country codes
VALID_COUNTRIES = {"us", "gb", "fr", "de", "ca", "in", "au", "br", "nl", "sg", "za", "pl", "it", "es", "mx", "nz"}


def fetch_adzuna_jobs(keyword="", location="", country="us"):
    """Fetches jobs from the Adzuna API, filtered by keyword, location, and country."""
    if not ADZUNA_APP_ID or not ADZUNA_APP_KEY:
        logging.error("Adzuna credentials missing in .env file")
        return []

    country = country.lower().strip()
    if country not in VALID_COUNTRIES:
        logging.error(f"'{country}' is not a supported Adzuna country code. Defaulting to 'us'.")
        country = "us"

    url = f"https://api.adzuna.com/v1/api/jobs/{country}/search/1"
    params = {
        "app_id": ADZUNA_APP_ID,
        "app_key": ADZUNA_APP_KEY,
        "what": keyword,
        "results_per_page": 20,
    }

    if location:
        params["where"] = location

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        jobs = data.get("results", [])
        logging.info(
            f"Found {len(jobs)} jobs from Adzuna for '{keyword}'"
            + (f" in '{location}, {country}'" if location else f" in '{country}'")
        )
        return jobs
    except requests.RequestException as e:
        logging.error(f"Adzuna API request failed: {e}")
        return []


def format_posted_date(raw_date):
    """Converts an Adzuna date string (e.g. '2026-09-20T14:23:00Z') into just the date, or 'Unknown' if missing."""
    if not raw_date:
        return "Unknown"
    return raw_date.split("T")[0]


if __name__ == "__main__":
    keyword = input("What job are you looking for? (e.g. python, marketing): ")
    country = input("Which country code? (e.g. us, gb, fr, de, in): ")
    location = input("Which city? (e.g. Paris, London, or leave blank): ")
    jobs = fetch_adzuna_jobs(keyword, location, country)

    if not jobs:
        print("No jobs found for this keyword/location.")
    else:
        for job in jobs[:5]:
            print("\n---")
            print("Title:", job.get("title"))
            print("Company:", job.get("company", {}).get("display_name"))
            print("Location:", job.get("location", {}).get("display_name"))
            print("Posted at:", format_posted_date(job.get("created")))
            print("Apply:", job.get("redirect_url"))