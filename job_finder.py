import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from serpapi import GoogleSearch
from datetime import datetime, timedelta

# ====== Load ENV Variables ======
SERPAPI_KEY = os.getenv("SERPAPI_KEY")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_NAME = os.getenv("SENDER_NAME", "Job Alerts Bot")
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))  # Gmail uses 587
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
RECIPIENT_EMAILS = os.getenv("RECIPIENT_EMAILS", "")

MAX_RESULTS_PER_QUERY = int(os.getenv("MAX_RESULTS_PER_QUERY", "20") or 20)
DAYS_BACK_LIMIT = int(os.getenv("DAYS_BACK_LIMIT", "7") or 7)
STRICT_MATCH = os.getenv("STRICT_MATCH", "false").lower() == "true"

print(f"DEBUG ENV VALUES: MAX_RESULTS_PER_QUERY='{MAX_RESULTS_PER_QUERY}' DAYS_BACK_LIMIT='{DAYS_BACK_LIMIT}' SMTP_PORT='{SMTP_PORT}'")

# ====== Search Config ======
QUERIES = ["Agile Program Manager", "Program Manager", "Scrum Master", "Project Manager"]
REGIONS = ["United States", "Europe", "Australia", "New Zealand"]

# ====== Functions ======
def search_jobs(query, location):
    params = {
        "engine": "google_jobs",
        "q": query,
        "location": location,
        "hl": "en",
        "api_key": SERPAPI_KEY
    }
    search = GoogleSearch(params)
    results = search.get_dict()
    jobs = results.get("jobs_results", [])
    return jobs[:MAX_RESULTS_PER_QUERY]

def filter_jobs(jobs):
    cutoff_date = datetime.now() - timedelta(days=DAYS_BACK_LIMIT)
    filtered = []
    for job in jobs:
        title = job.get("title", "").lower()
        company = job.get("company_name", "Unknown")
        location = job.get("location", "Unknown")
        link = job.get("apply_options", [{}])[0].get("link", "")

        if not link:  # Skip jobs without a valid application link
            continue

        desc = " ".join([e.get("description", "") for e in job.get("detected_extensions", [])]).lower()
        date_str = job.get("detected_extensions", {}).get("posted_at", "")
        try:
            posted_at = datetime.strptime(date_str, "%Y-%m-%d")
        except:
            posted_at = datetime.now()

        if posted_at < cutoff_date:
            continue

        visa_keywords = ["visa", "relocation", "sponsorship", "work permit"]
        visa_support = "Yes" if any(kw in desc for kw in visa_keywords) else "No"

        filtered.append({
            "title": job.get("title", "N/A"),
            "company": company,
            "location": location,
            "visa": visa_support,
            "link": link
        })
    return filtered

def send_email(jobs):
    if not jobs:
        print("⚠️ No jobs found today, skipping email.")
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Daily Job Alerts"
    msg["From"] = f"{SENDER_NAME} <{SENDER_EMAIL}>"
    msg["To"] = ", ".join(RECIPIENT_EMAILS.split(","))

    html_content = "<h2>Job Alerts</h2><ul>"
    for job in jobs:
        html_content += f'<li><a href="{job["link"]}">{job["title"]}</a> - {job["company"]} ({job["location"]}) | Visa/Relocation: {job["visa"]}</li>'
    html_content += "</ul>"

    msg.attach(MIMEText(html_content, "html"))

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.sendmail(SENDER_EMAIL, RECIPIENT_EMAILS.split(","), msg.as_string())
        print(f"✅ Sent {len(jobs)} jobs via Gmail")
    except Exception as e:
        print(f"❌ Gmail sending failed: {e}")

# ====== Main ======
if __name__ == "__main__":
    all_jobs = []
    for query in QUERIES:
        for region in REGIONS:
            print(f"Searching: {query} jobs in {region}")
            jobs = search_jobs(query, region)
            all_jobs.extend(jobs)

    filtered_jobs = filter_jobs(all_jobs)
    print(f"DEBUG: Jobs found = {len(filtered_jobs)}")

    send_email(filtered_jobs)