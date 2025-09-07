import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from google_search_results import GoogleSearch   # ✅ Correct import

# ----------------- ENV VARIABLES -----------------
SERPAPI_KEY = os.getenv("SERPAPI_KEY")

SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_NAME = os.getenv("SENDER_NAME", "Job Alerts Bot")
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", SENDER_EMAIL)
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
RECIPIENT_EMAILS = os.getenv("RECIPIENT_EMAILS", "").split(",")

MAX_RESULTS_PER_QUERY = int(os.getenv("MAX_RESULTS_PER_QUERY", "20") or 20)
DAYS_BACK_LIMIT = int(os.getenv("DAYS_BACK_LIMIT", "7") or 7)
STRICT_MATCH = os.getenv("STRICT_MATCH", "false").lower() == "true"

WORKFLOW_NAME = os.getenv("WORKFLOW_NAME", "Global Jobs")  # ✅ Differentiate Pune vs Global

print(f"DEBUG ENV VALUES: MAX_RESULTS_PER_QUERY='{MAX_RESULTS_PER_QUERY}' DAYS_BACK_LIMIT='{DAYS_BACK_LIMIT}' SMTP_PORT='{SMTP_PORT}' WORKFLOW='{WORKFLOW_NAME}'")

# ----------------- SEARCH CONFIG -----------------
QUERIES = [
    "Agile Program Manager",
    "Program Manager",
    "Scrum Master",
    "Project Manager",
]

LOCATIONS = os.getenv("JOB_LOCATIONS", "").split(",")
if not LOCATIONS or LOCATIONS == [""]:
    LOCATIONS = ["United States", "Europe", "Australia", "New Zealand"]

# ----------------- FETCH JOBS -----------------
def fetch_jobs(query, location):
    print(f"Searching: {query} jobs in {location}")
    params = {
        "engine": "google_jobs",
        "q": f"{query} {location}",
        "hl": "en",
        "api_key": SERPAPI_KEY,
    }
    search = GoogleSearch(params)
    results = search.get_dict()
    return results.get("jobs_results", [])

# ----------------- FILTER JOBS -----------------
def filter_jobs(jobs):
    filtered = []
    cutoff_date = datetime.now() - timedelta(days=DAYS_BACK_LIMIT)

    for job in jobs:
        title = job.get("title", "").lower()
        company = job.get("company_name", "")
        location = job.get("location", "")
        link = job.get("apply_options", [{}])[0].get("link", job.get("share_link", ""))

        detected_ext = job.get("detected_extensions", {})
        posted_at = detected_ext.get("posted_at")

        # Parse date if available
        job_date = None
        if posted_at:
            try:
                if "day" in posted_at:
                    days = int(posted_at.split()[0])
                    job_date = datetime.now() - timedelta(days=days)
                elif "hour" in posted_at:
                    job_date = datetime.now()
            except Exception:
                job_date = None

        if job_date and job_date < cutoff_date:
            continue

        if STRICT_MATCH and not any(q.lower() in title for q in QUERIES):
            continue

        filtered.append({
            "title": job.get("title", "No title"),
            "company": company,
            "location": location,
            "link": link
        })

    return filtered

# ----------------- SEND EMAIL -----------------
def send_email(jobs):
    if not jobs:
        print("⚠️ No jobs found, skipping email.")
        return

    subject = f"📢 {WORKFLOW_NAME} - {len(jobs)} new jobs found"
    body = f"<h3>Here are the latest {WORKFLOW_NAME} jobs:</h3><ul>"
    for job in jobs:
        body += f'<li><a href="{job["link"]}">{job["title"]}</a> - {job["company"]} ({job["location"]})</li>'
    body += "</ul>"

    message = MIMEMultipart()
    message["From"] = f"{SENDER_NAME} <{SENDER_EMAIL}>"
    message["To"] = ", ".join(RECIPIENT_EMAILS)
    message["Subject"] = subject
    message.attach(MIMEText(body, "html"))

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context) as server:
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.sendmail(SENDER_EMAIL, RECIPIENT_EMAILS, message.as_string())
        print(f"✅ Email sent successfully with {len(jobs)} jobs.")
    except Exception as e:
        print(f"❌ Email sending failed: {e}")

# ----------------- MAIN -----------------
if __name__ == "__main__":
    all_jobs = []
    for query in QUERIES:
        for location in LOCATIONS:
            all_jobs.extend(fetch_jobs(query, location))

    filtered_jobs = filter_jobs(all_jobs)
    print(f"DEBUG: Jobs found = {len(filtered_jobs)}")

    send_email(filtered_jobs)