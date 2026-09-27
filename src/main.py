from datetime import datetime

from fetch_jobs import fetch_jobs
from adzuna import fetch_adzuna_jobs, VALID_COUNTRIES
from database import init_db, insert_jobs


def normalize_arbeitnow_job(job):
    """Converts an Arbeitnow job into the common format used across all sources."""
    timestamp = job.get("created_at")
    posted_date = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d") if timestamp else "Unknown"

    return {
        "title": job.get("title"),
        "company_name": job.get("company_name"),
        "location": job.get("location"),
        "job_types": job.get("job_types", []),
        "description": job.get("description"),
        "url": job.get("url"),
        "source": "Arbeitnow",
        "posted_at": posted_date,
    }


def normalize_adzuna_job(job):
    """Converts an Adzuna job into the common format used across all sources."""
    raw_date = job.get("created")
    posted_date = raw_date.split("T")[0] if raw_date else "Unknown"

    return {
        "title": job.get("title"),
        "company_name": job.get("company", {}).get("display_name"),
        "location": job.get("location", {}).get("display_name"),
        "job_types": [job.get("contract_time", "")] if job.get("contract_time") else [],
        "description": job.get("description"),
        "url": job.get("redirect_url"),
        "source": "Adzuna",
        "posted_at": posted_date,
    }


def run(keyword, country, city):
    print(f"\nSearching for '{keyword}' across all sources...\n")

    arbeitnow_location = city or country  # Arbeitnow only understands plain text, no country codes
    arbeitnow_jobs = [normalize_arbeitnow_job(j) for j in fetch_jobs(keyword, arbeitnow_location)]
    adzuna_jobs = [normalize_adzuna_job(j) for j in fetch_adzuna_jobs(keyword, city, country)]

    all_jobs = arbeitnow_jobs + adzuna_jobs
    print(f"Total combined results: {len(all_jobs)}\n")

    for job in all_jobs[:10]:
        print("---")
        print("Title:", job["title"])
        print("Company:", job["company_name"])
        print("Location:", job["location"])
        print("Source:", job["source"])
        print("Posted at:", job["posted_at"])
        print("Apply:", job["url"])
        print()

    init_db()
    insert_jobs(all_jobs)


if __name__ == "__main__":
    keyword = input("What job are you looking for? (e.g. python, marketing): ")
    country = input(f"Which country code? ({', '.join(sorted(VALID_COUNTRIES))}, or 'remote'): ")
    city = input("Which city? (optional, leave blank): ")

    run(keyword, country, city)