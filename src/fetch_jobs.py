import requests
import logging

logging.basicConfig(level=logging.INFO)

ARBEITNOW_URL = "https://www.arbeitnow.com/api/job-board-api"


def fetch_jobs(keyword=""):
    """Arbeitnow API se jobs fetch karta hai, keyword ke words match karke."""
    try:
        response = requests.get(ARBEITNOW_URL, timeout=10)
        response.raise_for_status()
        data = response.json()
        all_jobs = data.get("data", [])

        if not keyword:
            logging.info(f"{len(all_jobs)} total jobs fetch hue")
            return all_jobs

        keyword_words = keyword.lower().split()
        filtered_jobs = []

        for job in all_jobs:
            searchable_text = " ".join([
                job.get("title", ""),
                " ".join(job.get("tags", [])),
                job.get("description", "")
            ]).lower()

            if any(word in searchable_text for word in keyword_words):
                filtered_jobs.append(job)

        logging.info(f"'{keyword}' se related {len(filtered_jobs)} jobs mili")
        return filtered_jobs

    except requests.RequestException as e:
        logging.error(f"API call fail hui: {e}")
        return []


if __name__ == "__main__":
    keyword = input("Kis job ki talaash hai? (e.g. python, marketing): ")
    jobs = fetch_jobs(keyword)

    if not jobs:
        print("Koi job nahi mili is keyword ke liye.")
    else:
        for job in jobs[:5]:
            print("\n---")
            print("Title:", job.get("title"))
            print("Company:", job.get("company_name"))
            print("Location:", job.get("location"))
            print("Apply:", job.get("url"))