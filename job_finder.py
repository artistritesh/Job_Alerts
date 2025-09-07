import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from serpapi.google_search_results import GoogleSearch   # ✅ FIXED IMPORT
from datetime import datetime, timedelta

# ✅ Load ENV vars with defaults
MAX_RESULTS_PER_QUERY = int(os.getenv("MAX_RESULTS_PER_QUERY", "20") or 20)
DAYS_BACK_LIMIT = int(os.getenv("DAYS_BACK_LIMIT", "7") or 7)
STRICT_MATCH = os.getenv("STRICT_MATCH", "false").lower() == "true"

SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
RECIPIENT_EMAILS = os.getenv("RECIPIENT_EMAILS", "").split(",")
SEARCH_TERMS = os.getenv("SEARCH_TERMS", "Agile Program Manager,Program Manager,Scrum Master,Project Manager").split(",")
SEARCH_LOCATIONS = os.getenv("SEARCH_LOCATIONS", "United States,Europe,Australia,New Zealand").split(",")

# Debugging
print(f"DEBUG ENV VALUES: MAX_RESULTS_PER_QUERY='{MAX_RESULTS_PER_QUERY}' DAYS_BACK_LIMIT='{DAYS_BACK_LIMIT}' SMTP_PORT='{SMTP_PORT}'")

def search_jobs(query, location):
    print(f"Searching: {query} jobs in {location}")
    params = {
        "engine": "google_jobs",
        "q": f"{query} {location}",
        "api_key": os.getenv("SERPAPI_KEY"),
    }
    search = GoogleSearch(params)
    results = search.get_dict()
    return results.get("jobs_results", [])

def filter_jobs(jobs):
    filtered = []
    cutoff_date = datetime.now() - timedelta(days=DAYS_BACK_LIMIT)
    for job in jobs:
        title = job.get("title", "").lower()
        company = job.get("company_name", "")
        location = job.get("location", "")
        link = job.get("related_links", [{}])[0].get("link", "")

        # Date filtering
        extensions = job.get("detected_extensions", {})
        posted = extensions.get("posted_at") or extensions.get("posted_at_relative")
        if posted:
            if "day" in posted:
                try:
                    days = int(posted.split()[0])
                    post_date = datetime.now() - timedelta(days=days)
                except Exception:
                    post_date = datetime.now()
            else:
                post_date = datetime.now()
        else:
            post_date = datetime.now()

        if post_date < cutoff_date:
            continue

        filtered.append({
            "title": title.title(),
            "company": company,
            "location": location,
            "link": link
        })
    return filtered

def send_email(jobs, subject="Job Alerts"):
    if not jobs:
        print("No jobs to send.")
        return

    msg = MIMEMultipart("alternative")
    msg["From"] = SENDER_EMAIL
    msg["To"] = ", ".join(RECIPIENT_EMAILS)
    msg["Subject"] = subject

    html_content = "<h3>New Job Alerts</h3><ul>"
    for job in jobs:
        html_content += f'<li><a href="{job["link"]}">{job["title"]}</a> - {job["company"]} ({job["location"]})</li>'
    html_content += "</ul>"

    msg.attach(MIMEText(html_content, "html"))

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.sendmail(SENDER_EMAIL, RECIPIENT_EMAILS, msg.as_string())
        print(f"✅ Sent {len(jobs)} jobs via email with subject '{subject}'")
    except Exception as e:
        print(f"❌ Email sending failed: {e}")

if __name__ == "__main__":
    all_jobs = []
    for query in SEARCH_TERMS:
        for location in SEARCH_LOCATIONS:
            all_jobs.extend(search_jobs(query.strip(), location.strip()))

    filtered_jobs = filter_jobs(all_jobs)
    print(f"DEBUG: Jobs found = {len(filtered_jobs)}")
    send_email(filtered_jobs, subject=os.getenv("EMAIL_SUBJECT", "Job Alerts"))