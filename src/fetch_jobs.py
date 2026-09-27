import requests
import logging

logging.basicConfig(level=logging.INFO)

ARBEITNOW_URL = "https://www.arbeitnow.com/api/job-board-api"


def fetch_jobs(keyword=""):
    """Fetches jobs from the Arbeitnow API, sorted by relevance to the keyword."""
    try:
        response = requests.get(ARBEITNOW_URL, timeout=10)
        response.raise_for_status()
        data = response.json()
        all_jobs = data.get("data", [])

        if not keyword:
            logging.info(f"Fetched {len(all_jobs)} total jobs")
            return all_jobs

        keyword_words = keyword.lower().split()
        scored_jobs = []

        for job in all_jobs:
            searchable_text = " ".join([
                job.get("title", ""),
                " ".join(job.get("tags", [])),
                job.get("description", "")
            ]).lower()

            # 1 point for each keyword word found
            score = sum(1 for word in keyword_words if word in searchable_text)

            if score > 0:
                scored_jobs.append((score, job))

        # Highest-scoring jobs first
        scored_jobs.sort(key=lambda x: x[0], reverse=True)

        # Keep jobs that match at least half the keyword words (or 1, if only 1 word given)
        min_score = max(1, len(keyword_words) // 2)
        filtered_jobs = [job for score, job in scored_jobs if score >= min_score]

        logging.info(f"Found {len(filtered_jobs)} jobs relevant to '{keyword}'")
        return filtered_jobs

    except requests.RequestException as e:
        logging.error(f"API request failed: {e}")
        return []


if __name__ == "__main__":
    keyword = input("What job are you looking for? (e.g. python, marketing): ")
    jobs = fetch_jobs(keyword)

    if not jobs:
        print("No jobs found for this keyword.")
    else:
        for job in jobs[:5]:
            print("\n---")
            print("Title:", job.get("title"))
            print("Company:", job.get("company_name"))
            print("Location:", job.get("location"))
            print("Apply:", job.get("url"))