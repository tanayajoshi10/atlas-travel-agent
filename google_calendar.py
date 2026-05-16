"""
tools/google_calendar.py
Atlas Travel Agent — Google Calendar Tool
Checks traveler availability and creates/sends calendar invites.

Setup required:
  1. Enable Google Calendar API in Google Cloud Console
  2. Download credentials.json to this directory
  3. Run once manually to authorize — token.json is saved for future use
  pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
"""

import datetime
import os
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/calendar.events",
]
TOKEN_PATH = os.path.join(os.path.dirname(__file__), "token.json")
CREDS_PATH = os.path.join(os.path.dirname(__file__), "credentials.json")


def _get_service():
    """Authenticate and return a Google Calendar service object."""
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
    return build("calendar", "v3", credentials=creds)


def check_availability(start_date: str, end_date: str, calendar_id: str = "primary") -> dict:
    """
    Check if a traveler is free between start_date and end_date.
    Dates should be in YYYY-MM-DD format.
    Returns a dict with 'is_free' (bool) and 'conflicts' (list of event summaries).
    """
    service = _get_service()
    start = f"{start_date}T00:00:00Z"
    end = f"{end_date}T23:59:59Z"

    events_result = (
        service.events()
        .list(
            calendarId=calendar_id,
            timeMin=start,
            timeMax=end,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    events = events_result.get("items", [])
    conflicts = [e.get("summary", "Busy") for e in events]
    return {
        "is_free": len(conflicts) == 0,
        "conflicts": conflicts,
        "date_range": f"{start_date} to {end_date}",
    }


def check_group_availability(start_date: str, end_date: str, traveler_emails: list[str]) -> dict:
    """
    Check availability for multiple travelers using free/busy query.
    Returns a summary of who is free and who has conflicts.
    """
    service = _get_service()
    start = f"{start_date}T00:00:00Z"
    end = f"{end_date}T23:59:59Z"

    body = {
        "timeMin": start,
        "timeMax": end,
        "items": [{"id": email} for email in traveler_emails],
    }
    result = service.freebusy().query(body=body).execute()
    calendars = result.get("calendars", {})

    summary = {}
    for email in traveler_emails:
        busy_times = calendars.get(email, {}).get("busy", [])
        summary[email] = {
            "is_free": len(busy_times) == 0,
            "busy_periods": busy_times,
        }

    all_free = all(v["is_free"] for v in summary.values())
    return {
        "all_free": all_free,
        "date_range": f"{start_date} to {end_date}",
        "travelers": summary,
    }


def create_trip_invite(
    title: str,
    start_date: str,
    end_date: str,
    description: str,
    location: str,
    attendee_emails: list[str],
    reminders_days: Optional[list[int]] = None,
) -> dict:
    """
    Create and send a Google Calendar invite to all travelers.
    start_date and end_date in YYYY-MM-DD format.
    reminders_days: list of days before event to send reminders (e.g. [7, 1]).
    Returns the created event details.
    """
    service = _get_service()

    if reminders_days is None:
        reminders_days = [7, 1]

    event = {
        "summary": title,
        "location": location,
        "description": description,
        "start": {"date": start_date},
        "end": {"date": end_date},
        "attendees": [{"email": email} for email in attendee_emails],
        "reminders": {
            "useDefault": False,
            "overrides": [
                {"method": "email", "minutes": days * 24 * 60}
                for days in reminders_days
            ],
        },
        "sendUpdates": "all",
    }

    created = service.events().insert(calendarId="primary", body=event).execute()
    return {
        "event_id": created["id"],
        "title": created["summary"],
        "start": start_date,
        "end": end_date,
        "attendees": attendee_emails,
        "link": created.get("htmlLink"),
    }


def create_flight_invite(
    flight_info: str,
    departure_date: str,
    return_date: str,
    destination: str,
    attendee_emails: list[str],
) -> dict:
    """
    Create departure and return flight calendar events for all travelers.
    """
    departure = create_trip_invite(
        title=f"✈️ Depart to {destination}",
        start_date=departure_date,
        end_date=departure_date,
        description=f"Flight details:\n{flight_info}",
        location=destination,
        attendee_emails=attendee_emails,
        reminders_days=[1],
    )
    returning = create_trip_invite(
        title=f"✈️ Return from {destination}",
        start_date=return_date,
        end_date=return_date,
        description=f"Return flight details:\n{flight_info}",
        location="Home",
        attendee_emails=attendee_emails,
        reminders_days=[1],
    )
    return {"departure_event": departure, "return_event": returning}


if __name__ == "__main__":
    print("Testing google_calendar.py...")
    result = check_availability("2025-10-15", "2025-10-22")
    print(result)
