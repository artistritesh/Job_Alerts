import os
import requests
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ---------------------------
# Safe int getter for env vars
# ---------------------------
def getenv_int(name: str, default: int) -> int:
    val = os.getenv(name, "")
    try:
        return int(val)
    except (TypeError, ValueError):
        return default

# ---------------------------
# Load configuration
# ---------------------------
SERPAPI_KEY = os.getenv("SERPAPI_KEY")

SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_NAME = os.getenv("SENDER_NAME", "Job Bot").replace("_", " ")
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = getenv_int("SMTP_PORT", 465)
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
RECIPIENT_EMAILS = os.getenv("RECIPIENT_EMAILS", "").split(",")

MAX_RESULTS_PER_QUERY = getenv_int("MAX_RESULTS_PER_QUERY", 20)
DAYS_BACK_LIMIT = getenv_int("DAYS_BACK_LIMIT", 14)
STRICT_MATCH = os.getenv("STRICT_MATCH", "false").lower() == "true"

# Debug logging for safety
print("DEBUG ENV VALUES:",
      "MAX_RESULTS_PER_QUERY=", repr(os.getenv("MAX_RESULTS_PER_QUERY")),
      "DAYS_BACK_LIMIT=", repr(os.getenv("DAYS_BACK_LIMIT")),
      "SMTP_PORT=", repr(os.getenv("SMTP_PORT")))

# ---------------------------
# Job search configuration
# ---------------------------
QUERIES = [
    "Agile Program Manager jobs",
    "Program Manager jobs",
    "Scrum Master jobs",
    "Project Manager jobs"
]

REGIONS = [
    "United States",
    "Europe",
    "Australia",
    "New Zealand"
]

# ---------------------------
# Search jobs using SerpAPI
# ---------------------------
def search_jobs(query, location):
    url = "https://serpapi.com/search"
    params = {
        "engine": "google_jobs",
        "q": query,
        "location": location,
        "hl": "en",
        "api_key": SERPAPI_KEY
    }
    resp = requests.get(url, params=params)
    data = resp.json()

    jobs = []
    for j in data.get("jobs_results", []):
        jobs.append({
            "Company": j.get("company_name", ""),
            "Job Title": j.get("title", ""),
            "Location": j.get("location", ""),
            "Visa/Relocation Sponsorship": "Yes" if "visa" in j.get("description", "").lower() or "relocation" in j.get("description", "").lower() else "No",
            "Application Link": j.get("apply_options", [{}])[0].get("link", "")
        })
    return jobs

# ---------------------------
# Send email
# ---------------------------
def send_email(job_data):
    df = pd.DataFrame(job_data)
    if df.empty:
        body = "<p>No new job postings found today.</p>"
    else:
        body = df.to_html(index=False, escape=False)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Daily Job Alerts"
    msg["From"] = f"{SENDER_NAME} <{SENDER_EMAIL}>"
    msg["To"] = ", ".join(RECIPIENT_EMAILS)

    part = MIMEText(body, "html")
    msg.attach(part)

    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECIPIENT_EMAILS, msg.as_string())

# ---------------------------
# Main
# ---------------------------
if __name__ == "__main__":
    all_jobs = []
    for query in QUERIES:
        for region in REGIONS:
            print(f"Searching: {query} in {region}")
            jobs = search_jobs(query, region)
            all_jobs.extend(jobs)

    # Filter only visa/relocation supported jobs
    filtered = [j for j in all_jobs if j["Visa/Relocation Sponsorship"] == "Yes"]

    send_email(filtered)
    print(f"✅ Sent {len(filtered)} jobs via email")