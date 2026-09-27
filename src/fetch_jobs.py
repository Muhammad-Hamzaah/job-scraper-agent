import requests
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)

ARBEITNOW_URL = "https://www.arbeitnow.com/api/job-board-api"


def fetch_jobs(keyword="", location=""):
    """Fetches jobs from the Arbeitnow API, filtered by keyword and (optionally) location."""
    try:
        response = requests.get(ARBEITNOW_URL, timeout=10)
        response.raise_for_status()
        data = response.json()
        all_jobs = data.get("data", [])

        # Step 1: filter by location first (if provided)
        if location:
            location_lower = location.lower()
            all_jobs = [
                job for job in all_jobs
                if location_lower in job.get("location", "").lower()
                or (location_lower == "remote" and job.get("remote") is True)
            ]

        if not keyword:
            logging.info(f"Fetched {len(all_jobs)} jobs after location filter")
            return all_jobs

        keyword_words = keyword.lower().split()
        matched_jobs = []

        for job in all_jobs:
            title_text = job.get("title", "").lower()
            full_text = " ".join([
                title_text,
                " ".join(job.get("tags", [])),
                job.get("description", "")
            ]).lower()

            if all(word in full_text for word in keyword_words):
                title_score = sum(1 for word in keyword_words if word in title_text)
                matched_jobs.append((title_score, job))

        matched_jobs.sort(key=lambda x: x[0], reverse=True)
        filtered_jobs = [job for _, job in matched_jobs]

        logging.info(f"Found {len(filtered_jobs)} jobs relevant to '{keyword}'" + (f" in '{location}'" if location else ""))
        return filtered_jobs

    except requests.RequestException as e:
        logging.error(f"API request failed: {e}")
        return []


def format_posted_date(timestamp):
    """Converts an Arbeitnow timestamp into a readable date, or 'Unknown' if missing."""
    if not timestamp:
        return "Unknown"
    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d")


if __name__ == "__main__":
    keyword = input("What job are you looking for? (e.g. python, marketing): ")
    location = input("Which location? (e.g. remote, Berlin, or leave blank): ")
    jobs = fetch_jobs(keyword, location)

    if not jobs:
        print("No jobs found for this keyword/location.")
    else:
        for job in jobs[:5]:
            print("\n---")
            print("Title:", job.get("title"))
            print("Company:", job.get("company_name"))
            print("Location:", job.get("location"))
            print("Posted at:", format_posted_date(job.get("created_at")))
            print("Apply:", job.get("url"))