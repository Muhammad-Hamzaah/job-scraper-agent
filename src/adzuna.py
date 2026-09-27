import os
import requests
import logging
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)

ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID")
ADZUNA_APP_KEY = os.getenv("ADZUNA_APP_KEY")
ADZUNA_URL = "https://api.adzuna.com/v1/api/jobs/us/search/1"  # "us" = country code, can change (gb, in, etc.)


def fetch_adzuna_jobs(keyword="", country="us"):
    """Fetches jobs from the Adzuna API, filtered by keyword."""
    if not ADZUNA_APP_ID or not ADZUNA_APP_KEY:
        logging.error("Adzuna credentials missing in .env file")
        return []

    url = f"https://api.adzuna.com/v1/api/jobs/{country}/search/1"
    params = {
        "app_id": ADZUNA_APP_ID,
        "app_key": ADZUNA_APP_KEY,
        "what": keyword,
        "results_per_page": 20,
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        jobs = data.get("results", [])
        logging.info(f"Found {len(jobs)} jobs from Adzuna for '{keyword}'")
        return jobs
    except requests.RequestException as e:
        logging.error(f"Adzuna API request failed: {e}")
        return []


if __name__ == "__main__":
    keyword = input("What job are you looking for? (e.g. python, marketing): ")
    jobs = fetch_adzuna_jobs(keyword)

    if not jobs:
        print("No jobs found for this keyword.")
    else:
        for job in jobs[:5]:
            print("\n---")
            print("Title:", job.get("title"))
            print("Company:", job.get("company", {}).get("display_name"))
            print("Location:", job.get("location", {}).get("display_name"))
            print("Apply:", job.get("redirect_url"))