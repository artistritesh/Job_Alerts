import os
import argparse
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from serpapi import GoogleSearch

# ------------------- CLI Arguments -------------------
parser = argparse.ArgumentParser()
parser.add_argument("--keywords", type=str, default="Agile Program Manager,Program Manager,Scrum Master,Project Manager")
parser.add_argument("--locations", type=str, default="United States,Europe,Australia,New Zealand")
parser.add_argument("--subject", type=str, default="Daily Job Alerts")
args = parser.parse_args()

SEARCH_KEYWORDS = [kw.strip() for kw in args.keywords.split(",")]
SEARCH_LOCATIONS = [loc.strip() for loc in args.locations.split(",")]
EMAIL_SUBJECT = args.subject

# ------------------- Environment Variables -------------------
SERPAPI_KEY = os.getenv("SERPAPI_KEY")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_NAME = os.getenv("SENDER_NAME")
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
RECIPIENT_EMAILS = os.getenv("RECIPIENT_EMAILS", "")

MAX_RESULTS_PER_QUERY = int(os.getenv("MAX_RESULTS_PER_QUERY", "20"))
DAYS_BACK_LIMIT = int(os.getenv("DAYS_BACK_LIMIT", "7"))
STRICT_MATCH = os.getenv("STRICT_MATCH", "false").lower() == "true"

print(f"DEBUG ENV VALUES: MAX_RESULTS_PER_QUERY='{MAX_RESULTS_PER_QUERY}' DAYS_BACK_LIMIT='{DAYS_BACK_LIMIT}' SMTP_PORT='{SMTP_PORT}'")

# ------------------- Job Fetcher -------------------
def fetch_jobs(query, location):
    print(f"Searching: {query} jobs in {location}")
    search = GoogleSearch({
        "engine": "google_jobs",
        "q": f"{query} jobs in {location}",
        "hl": "en",
        "api_key": SERPAPI_KEY,
    })
    results = search.get_dict()
    return results.get("jobs_results", [])

# ------------------- Job Filter -------------------
def filter_jobs(jobs):
    filtered = []
    for job in jobs:
        title = job.get("title", "").lower()
        company = job.get("company_name", "")
        location = job.get("location", "")
        link = job.get("apply_options", [{}])[0].get("link", "")

        if STRICT_MATCH and not any(k.lower() in title for k in SEARCH_KEYWORDS):
            continue

        # Very basic visa/relocation detection
        desc = job.get("description", "").lower()
        visa_support = "visa" in desc or "sponsorship" in desc
        relocation = "relocation" in desc
        if not (visa_support or relocation):
            continue

        filtered.append({
            "title": job.get("title"),
            "company": company,
            "location": location,
            "link": link,
        })
    return filtered

# ------------------- Email Sender -------------------
def send_email(jobs, subject="Daily Job Alerts"):
    if not jobs:
        print("No jobs found, skipping email.")
        return

    msg = MIMEMultipart("alternative")
    msg["From"] = f"{SENDER_NAME} <{SENDER_EMAIL}>"
    msg["To"] = RECIPIENT_EMAILS
    msg["Subject"] = subject

    html_content = f"<h3>{subject}</h3><ul>"
    for job in jobs:
        html_content += f'<li><a href="{job.get("link", "#")}">{job.get("title")}</a> - {job.get("company")} ({job.get("location")})</li>'
    html_content += "</ul>"

    msg.attach(MIMEText(html_content, "html"))

    try:
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.sendmail(SENDER_EMAIL, RECIPIENT_EMAILS.split(","), msg.as_string())
        print(f"✅ Email sent successfully: {subject}")
    except Exception as e:
        print(f"❌ Email sending failed: {e}")

# ------------------- Main Script -------------------
if __name__ == "__main__":
    all_jobs = []
    for keyword in SEARCH_KEYWORDS:
        for location in SEARCH_LOCATIONS:
            all_jobs.extend(fetch_jobs(keyword, location))

    filtered_jobs = filter_jobs(all_jobs)
    print(f"DEBUG: Jobs found = {len(filtered_jobs)}")
    send_email(filtered_jobs, subject=EMAIL_SUBJECT)