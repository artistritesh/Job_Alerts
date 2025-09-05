# Daily Job Search Automation (Visa/Relocation Friendly)

This package creates a once-a-day job search that emails roles mentioning **visa sponsorship** or **relocation support** across the US, Europe, Australia, and New Zealand. It targets titles: Agile Program Manager, Program Manager, Scrum Master, Project Manager.

## How it works
- Uses **SerpAPI Google Jobs** to fetch live postings.
- Checks job **title/description** for keywords: visa, sponsorship, work permit, relocation, etc.
- Sends a **formatted HTML table** with Company, Job Title, Location, Visa/Relocation (Yes/No), and Application Link.
- Scheduled at **20:00 IST** (Indian Standard Time) via GitHub Actions (cron `30 14 * * *`).

## Quick Start (GitHub Actions)
1. Create a **private GitHub repository** (can be empty).
2. Add the workflow file at `.github/workflows/daily-job-search.yml`.
3. In the repo, go to **Settings → Secrets and variables → Actions** and add the following **Secrets**:
   - `SERPAPI_KEY`
   - `SENDER_EMAIL`
   - `SENDER_NAME` (e.g., Radiant Vibes Job Bot)
   - `SMTP_SERVER` (e.g., smtp.gmail.com)
   - `SMTP_PORT` (e.g., 465)
   - `SMTP_USERNAME`
   - `SMTP_PASSWORD` (App password if Gmail)
   - `RECIPIENT_EMAILS` (comma-separated, e.g., `artistritesh@gmail.com`)
4. (Optional) Add **Variables** for tuning:
   - `MAX_RESULTS_PER_QUERY` (default 30)
   - `DAYS_BACK_LIMIT` (default 14)
   - `STRICT_MATCH` (default false)
5. Commit the workflow. It will run daily at **20:00 IST**. You can also trigger it via **Actions → Run workflow**.

## Run Locally (optional)
- Copy `.env.example` to `.env` and fill values.
- Run:
  ```bash
  pip install -r requirements.txt  # or: pip install requests pandas
  python job_finder.py
  ```

## Notes & Tips
- **Filtering**: We keep only postings where keywords appear in the title/description. Set `STRICT_MATCH=true` to be extra strict.
- **Coverage**: Add more granular locations (e.g., city/country) in `REGIONS` inside `job_finder.py` to improve results.
- **Email**: For Gmail, create an **App Password** (2FA required) and use that as `SMTP_PASSWORD`.
- **Compliance**: This script uses search engine results; always respect each site's terms of service for downstream scraping. Prefer the **Apply** links from official career portals (Greenhouse, Workday, Lever, Taleo, etc.).
- **Time Zone**: The workflow cron is set for **14:30 UTC** which equals **20:00 IST**.

Happy hunting!
