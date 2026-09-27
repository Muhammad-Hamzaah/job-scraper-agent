import requests
import logging

logging.basicConfig(level=logging.INFO)

ARBEITNOW_URL = "https://www.arbeitnow.com/api/job-board-api"


def fetch_jobs(keyword=""):
    """Arbeitnow API se jobs fetch karta hai, keyword ke hisab se filter karke."""
    try:
        response = requests.get(ARBEITNOW_URL, timeout=10)
        response.raise_for_status()
        data = response.json()
        all_jobs = data.get("data", [])

        if keyword:
            keyword = keyword.lower()
            filtered_jobs = [
                job for job in all_jobs
                if keyword in job.get("title", "").lower()
            ]
            logging.info(f"'{keyword}' se related {len(filtered_jobs)} jobs mili")
            return filtered_jobs

        logging.info(f"{len(all_jobs)} total jobs fetch hue")
        return all_jobs

    except requests.RequestException as e:
        logging.error(f"API call fail hui: {e}")
        return []


if __name__ == "__main__":
    keyword = input("Kis job ki talaash hai? (e.g. python, marketing): ")
    jobs = fetch_jobs(keyword)

    if not jobs:
        print("Koi job nahi mili is keyword ke liye.")
    else:
        for job in jobs[:5]:  # sirf pehli 5 dikhayenge abhi
            print("\n---")
            print("Title:", job.get("title"))
            print("Company:", job.get("company_name"))
            print("Location:", job.get("location"))
            print("Apply:", job.get("url"))