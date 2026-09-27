import requests
import logging

logging.basicConfig(level=logging.INFO)

ARBEITNOW_URL = "https://www.arbeitnow.com/api/job-board-api"


def fetch_jobs(keyword=""):
    """Fetches jobs from the Arbeitnow API, requiring ALL keyword words to match."""
    try:
        response = requests.get(ARBEITNOW_URL, timeout=10)
        response.raise_for_status()
        data = response.json()
        all_jobs = data.get("data", [])

        if not keyword:
            logging.info(f"Fetched {len(all_jobs)} total jobs")
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

            # Require every keyword word to appear somewhere in the job
            if all(word in full_text for word in keyword_words):
                # Give a higher score if the words appear in the title (more relevant)
                title_score = sum(1 for word in keyword_words if word in title_text)
                matched_jobs.append((title_score, job))

        # Jobs with keyword words in the title rank higher
        matched_jobs.sort(key=lambda x: x[0], reverse=True)
        filtered_jobs = [job for _, job in matched_jobs]

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