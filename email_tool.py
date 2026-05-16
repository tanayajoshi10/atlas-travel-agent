"""
tools/email_tool.py
Atlas Travel Agent — Email Tool
Drafts and sends trip summary emails and pre-trip reminders.
ALWAYS shows the user a draft before sending — never sends without confirmation.

Setup required:
  pip install google-auth google-auth-oauthlib google-api-python-client
  Same credentials.json as google_calendar.py (add Gmail scope).
"""

import base64
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
TOKEN_PATH = os.path.join(os.path.dirname(__file__), "gmail_token.json")
CREDS_PATH = os.path.join(os.path.dirname(__file__), "credentials.json")


def _get_service():
    """Authenticate and return a Gmail service object."""
    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, "w") as token:
            token.write(creds.to_json())
    return build("gmail", "v1", credentials=creds)


def draft_trip_summary(
    trip_name: str,
    destination: str,
    travel_dates: str,
    travelers: list[str],
    itinerary: str,
    flight_info: str,
    hotel_info: str,
    packing_tips: str,
    special_notes: str = "",
) -> dict:
    """
    Draft a trip summary email. Returns the draft for user review — does NOT send.
    Call send_email() after user confirms.
    """
    subject = f"🌍 Your {destination} Trip — Everything You Need to Know"
    body = f"""Hi everyone,

Your {trip_name} trip is coming up! Here's everything you need.

📅 DATES
{travel_dates}

✈️ FLIGHTS
{flight_info}

🏨 HOTEL
{hotel_info}

📋 ITINERARY
{itinerary}

🧳 WHAT TO PACK
{packing_tips}
"""
    if special_notes:
        body += f"\n📌 SPECIAL NOTES\n{special_notes}\n"

    body += "\nSafe travels,\nAtlas — your trip planning agent"

    return {
        "to": travelers,
        "subject": subject,
        "body": body,
        "status": "DRAFT — not sent. Confirm before sending.",
    }


def draft_pretrip_reminder(
    destination: str,
    days_until_trip: int,
    traveler_email: str,
    traveler_name: str,
    key_reminders: list[str],
) -> dict:
    """
    Draft a pre-trip reminder email for a specific traveler.
    Returns the draft — does NOT send until confirmed.
    """
    subject = f"✈️ Your {destination} trip is in {days_until_trip} days!"
    reminders_text = "\n".join(f"  • {r}" for r in key_reminders)
    body = f"""Hi {traveler_name},

Just a reminder — your trip to {destination} is coming up in {days_until_trip} days!

Here's what to double-check before you go:
{reminders_text}

Have an amazing trip!
Atlas — your trip planning agent
"""
    return {
        "to": [traveler_email],
        "subject": subject,
        "body": body,
        "status": "DRAFT — not sent. Confirm before sending.",
    }


def send_email(draft: dict) -> dict:
    """
    Send a previously drafted email.
    Only call this after the user has reviewed the draft and confirmed.
    """
    service = _get_service()

    msg = MIMEMultipart()
    msg["To"] = ", ".join(draft["to"])
    msg["Subject"] = draft["subject"]
    msg.attach(MIMEText(draft["body"], "plain"))

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    sent = service.users().messages().send(userId="me", body={"raw": raw}).execute()

    return {
        "sent": True,
        "message_id": sent["id"],
        "to": draft["to"],
        "subject": draft["subject"],
    }


def preview_draft(draft: dict) -> str:
    """
    Return a formatted preview of a draft for the user to review.
    """
    recipients = ", ".join(draft["to"])
    return (
        f"--- EMAIL DRAFT ---\n"
        f"To: {recipients}\n"
        f"Subject: {draft['subject']}\n"
        f"---\n"
        f"{draft['body']}\n"
        f"---\n"
        f"Reply 'send' to send this, or tell me what to change."
    )


if __name__ == "__main__":
    print("Testing email_tool.py — draft only, no send...")
    draft = draft_trip_summary(
        trip_name="Tokyo Adventure",
        destination="Tokyo",
        travel_dates="Oct 15–22, 2025",
        travelers=["alice@example.com", "bob@example.com"],
        itinerary="Day 1: Arrive, Shinjuku\nDay 2: Asakusa, Senso-ji\nDay 3: Shibuya, TeamLab",
        flight_info="UA837, SFO→NRT, departs 11:30am",
        hotel_info="Trunk Hotel, Shibuya — check-in Oct 15",
        packing_tips="Light layers, comfortable walking shoes, IC card for transit",
    )
    print(preview_draft(draft))
