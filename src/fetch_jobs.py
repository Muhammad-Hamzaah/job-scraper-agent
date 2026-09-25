import requests
import logging

logging.basicConfig(level=logging.INFO)

ARBEITNOW_URL = "https://www.arbeitnow.com/api/job-board-api"


def fetch_jobs():
    """Arbeitnow API se jobs ki list fetch karta hai."""
    try:
        response = requests.get(ARBEITNOW_URL, timeout=10)
        response.raise_for_status()  # agar error aayi to yahan rukega
        data = response.json()
        jobs = data.get("data", [])
        logging.info(f"{len(jobs)} jobs fetch hue Arbeitnow se")
        return jobs
    except requests.RequestException as e:
        logging.error(f"API call fail hui: {e}")
        return []


if __name__ == "__main__":
    jobs = fetch_jobs()
    if jobs:
        print("Pehli job ka sample:")
        print(jobs[0])