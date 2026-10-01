# JobScout

Local job search app that combines **Arbeitnow** (no API key) and **Adzuna** into one list, with a FastAPI backend and a plain HTML/CSS/JavaScript UI. Search from the browser or from the command line. Results are saved to SQLite.

No React, no npm, no build step. One Python process serves the API and the frontend.

## Features

- **Web UI (JobScout)** — search bar with keyword, country, and optional city; two-column results (job cards + sticky detail pane); mobile full-screen detail with “Back to results”
- **Two sources at once** — Arbeitnow and Adzuna run in parallel; one source failing does not drop the other
- **Normalized jobs** — shared fields: title, company, location, job types, description, apply URL, source, posted date
- **Deduping** — duplicate apply URLs are removed
- **Local cache** — new jobs are stored in SQLite (`data/jobs.db`); a database error never fails the search
- **Client-side filters** — date posted, job type (from the current results), source, sort (relevance or newest), pagination (10 per page)
- **CLI** — same scrapers via `python src/main.py`
- **Interactive API docs** — Swagger UI at `/docs`
- **Remote search** — country `remote` maps Arbeitnow to remote jobs and Adzuna to a US search with `remote` added to the keyword

## Tech stack

| Layer | Stack |
| --- | --- |
| Backend | Python 3, FastAPI, Uvicorn |
| HTTP clients | `requests` |
| Config | `python-dotenv` (`.env`) |
| Database | SQLite |
| Frontend | HTML, CSS, vanilla JavaScript (static files served by FastAPI) |

## How it works

1. The UI (or CLI) sends a keyword, country code, and optional city.
2. `GET /api/search` fetches Arbeitnow and Adzuna concurrently (`asyncio.gather` + `asyncio.to_thread`).
3. Raw payloads are normalized in `main.py` (`normalize_arbeitnow_job` / `normalize_adzuna_job`).
4. HTML descriptions are converted to plain text. Each job gets a stable `id` (first 12 characters of the SHA-1 of the apply URL).
5. Jobs are returned as JSON. The same normalized rows are inserted into SQLite; duplicates skip on unique `apply_link`.
6. Filters, sort, and pagination run **in the browser** on that response — no extra API calls.

**Remote vs country:** if country is `remote`, Arbeitnow uses location `remote` and Adzuna uses country `us` with `" remote"` appended to the keyword. Otherwise Arbeitnow uses the city text only, and Adzuna uses the selected country code plus city.

Adzuna credentials stay on the server. They are never logged or sent to the frontend.

## Project structure

```
job-scraper-agent/
├── frontend/
│   ├── index.html
│   ├── css/style.css
│   └── js/app.js
├── src/
│   ├── api.py            # FastAPI app: health, countries, search, static UI
│   ├── main.py           # Normalize jobs + CLI
│   ├── fetch_jobs.py     # Arbeitnow client
│   ├── adzuna.py         # Adzuna client
│   └── database.py       # SQLite init + insert
├── data/jobs.db          # Created on first save
├── .env                  # ADZUNA_APP_ID, ADZUNA_APP_KEY (not committed)
├── requirements.txt
└── README.md
```

Python modules under `src/` use **flat imports** (`from fetch_jobs import fetch_jobs`). Run Uvicorn from `src/` or pass `--app-dir src`.

## Prerequisites

- Python 3.10+ (developed against Python 3.14)
- An [Adzuna](https://developer.adzuna.com/) app ID and key for Adzuna results (Arbeitnow works without a key)

## Setup

```bash
git clone https://github.com/Muhammad-Hamzaah/job-scraper-agent.git
cd job-scraper-agent
python -m pip install -r requirements.txt
```

Create a `.env` file in the project root:

```env
ADZUNA_APP_ID=your_app_id
ADZUNA_APP_KEY=your_app_key
```

If Adzuna credentials are missing, Adzuna returns an empty list and Arbeitnow results still appear.

## Run the web app

From `src/`:

```bash
cd src
python -m uvicorn api:app --reload
```

From the project root:

```bash
python -m uvicorn api:app --reload --app-dir src
```

Then open:

| URL | What you get |
| --- | --- |
| [http://127.0.0.1:8000](http://127.0.0.1:8000) | JobScout UI |
| [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) | Swagger |
| [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health) | `{ "status": "ok" }` |

A search can take several seconds because both job APIs are called live.

## Run the CLI

```bash
python src/main.py
```

You will be prompted for keyword, country code (`us`, `gb`, `de`, … or `remote`), and optional city. The first 10 combined jobs print to the terminal and all results are saved to SQLite.

## HTTP API

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/api/health` | Liveness check |
| `GET` | `/api/countries` | Dropdown list: Adzuna country codes (sorted, with names) plus `remote` |
| `GET` | `/api/search` | Combined search |

### `GET /api/search`

| Query | Rules |
| --- | --- |
| `keyword` | Required, 1–100 characters |
| `country` | `remote` or an Adzuna code (`us`, `gb`, `fr`, `de`, `ca`, `in`, `au`, `br`, `nl`, `sg`, `za`, `pl`, `it`, `es`, `mx`, `nz`). Default: `us` |
| `city` | Optional, max 100 characters |

Invalid input returns **400**. Example:

```
/api/search?keyword=python&country=de
```

Response shape:

```json
{
  "count": 1,
  "jobs": [
    {
      "id": "a1b2c3d4e5f6",
      "title": "Software Engineer",
      "company": "Example Co",
      "location": "Berlin",
      "job_types": ["full_time"],
      "snippet": "First ~220 characters of plain text…",
      "description": "Full plain-text description",
      "url": "https://…",
      "source": "Arbeitnow",
      "posted_at": "2026-09-20"
    }
  ]
}
```

`posted_at` is `YYYY-MM-DD` or `"Unknown"`.

## Frontend behavior

- Last search (keyword, country, city) is stored in `localStorage` and restored on load
- Job text is assigned with `textContent` (third-party HTML is never injected)
- **Apply now** opens the listing in a new tab (`rel="noopener noreferrer"`)
- Loading, empty, and error states (including **Try again**)
- Arrow keys move focus between job cards; inputs have labels and `:focus-visible` styles

## Database

`init_db()` creates `data/jobs.db` if needed. Table `jobs`: title, company, location, job type, requirements (description), unique apply link, source, posted date, fetch timestamp. Inserts skip rows that already have the same apply link.

## Security

- `.env` is gitignored; never commit Adzuna keys
- Keys are not included in API responses or frontend files
- Query parameters are length- and country-validated
- Job HTML is stripped to plain text on the server before it reaches the UI

## License

Use and modify this project as you like unless you add a license file later.
