"""
tools/memory.py
Atlas Travel Agent — Persistent Memory Tool
Saves and loads trip details and traveler profiles across sessions.
Uses local JSON files in the OpenClaw workspace memory directory.
"""

import json
import os
from datetime import datetime
from typing import Optional

MEMORY_DIR = os.path.expanduser("~/.openclaw/workspace/memory")
TRIPS_FILE = os.path.join(MEMORY_DIR, "trips.json")
TRAVELERS_FILE = os.path.join(MEMORY_DIR, "travelers.json")


def _ensure_dir():
    os.makedirs(MEMORY_DIR, exist_ok=True)


def _load(filepath: str) -> dict:
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            return json.load(f)
    return {}


def _save(filepath: str, data: dict):
    _ensure_dir()
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)


# ── TRIP MEMORY ──────────────────────────────────────────────────────────────

def save_trip(trip_name: str, trip_data: dict) -> dict:
    """
    Save or update a trip. trip_data can include any fields:
    destination, dates, travelers, status, flights, hotels,
    itinerary, open_todos, decisions_made, budget, etc.
    """
    trips = _load(TRIPS_FILE)
    if trip_name not in trips:
        trips[trip_name] = {"created": datetime.now().isoformat()}
    trips[trip_name].update(trip_data)
    trips[trip_name]["last_updated"] = datetime.now().isoformat()
    _save(TRIPS_FILE, trips)
    return trips[trip_name]


def get_trip(trip_name: str) -> Optional[dict]:
    """Retrieve a trip by name. Returns None if not found."""
    trips = _load(TRIPS_FILE)
    return trips.get(trip_name)


def list_trips() -> list[dict]:
    """List all saved trips with their name and status."""
    trips = _load(TRIPS_FILE)
    return [
        {
            "name": name,
            "destination": data.get("destination", "Unknown"),
            "dates": data.get("dates", "TBD"),
            "status": data.get("status", "planning"),
            "last_updated": data.get("last_updated", ""),
        }
        for name, data in trips.items()
    ]


def update_trip_field(trip_name: str, field: str, value) -> dict:
    """Update a single field in a trip (e.g. status, flights, open_todos)."""
    trips = _load(TRIPS_FILE)
    if trip_name not in trips:
        trips[trip_name] = {"created": datetime.now().isoformat()}
    trips[trip_name][field] = value
    trips[trip_name]["last_updated"] = datetime.now().isoformat()
    _save(TRIPS_FILE, trips)
    return trips[trip_name]


def add_todo(trip_name: str, todo: str) -> list:
    """Add an open to-do item to a trip."""
    trips = _load(TRIPS_FILE)
    if trip_name not in trips:
        trips[trip_name] = {}
    todos = trips[trip_name].get("open_todos", [])
    todos.append({"item": todo, "done": False, "added": datetime.now().isoformat()})
    trips[trip_name]["open_todos"] = todos
    trips[trip_name]["last_updated"] = datetime.now().isoformat()
    _save(TRIPS_FILE, trips)
    return todos


def complete_todo(trip_name: str, todo_index: int) -> list:
    """Mark a to-do item as complete by index."""
    trips = _load(TRIPS_FILE)
    todos = trips.get(trip_name, {}).get("open_todos", [])
    if 0 <= todo_index < len(todos):
        todos[todo_index]["done"] = True
    trips[trip_name]["open_todos"] = todos
    trips[trip_name]["last_updated"] = datetime.now().isoformat()
    _save(TRIPS_FILE, trips)
    return todos


# ── TRAVELER MEMORY ───────────────────────────────────────────────────────────

def save_traveler(name: str, traveler_data: dict) -> dict:
    """
    Save or update a traveler profile.
    traveler_data can include: email, preferences, special_needs,
    passport_expiry, dietary_restrictions, travel_style, past_trips.
    """
    travelers = _load(TRAVELERS_FILE)
    if name not in travelers:
        travelers[name] = {"created": datetime.now().isoformat()}
    travelers[name].update(traveler_data)
    travelers[name]["last_updated"] = datetime.now().isoformat()
    _save(TRAVELERS_FILE, travelers)
    return travelers[name]


def get_traveler(name: str) -> Optional[dict]:
    """Retrieve a traveler profile by name. Returns None if not found."""
    travelers = _load(TRAVELERS_FILE)
    return travelers.get(name)


def list_travelers() -> list[str]:
    """List all saved traveler names."""
    return list(_load(TRAVELERS_FILE).keys())


def update_traveler_field(name: str, field: str, value) -> dict:
    """Update a single field in a traveler profile."""
    travelers = _load(TRAVELERS_FILE)
    if name not in travelers:
        travelers[name] = {}
    travelers[name][field] = value
    travelers[name]["last_updated"] = datetime.now().isoformat()
    _save(TRAVELERS_FILE, travelers)
    return travelers[name]


# ── QUICK SUMMARY ─────────────────────────────────────────────────────────────

def session_summary() -> str:
    """
    Return a plain-text summary of all active trips and known travelers.
    Injected at the start of each session so Atlas has full context.
    """
    trips = list_trips()
    travelers = list_travelers()

    lines = ["=== ATLAS MEMORY SUMMARY ===\n"]

    if trips:
        lines.append("ACTIVE TRIPS:")
        for t in trips:
            lines.append(
                f"  • {t['name']} → {t['destination']} | {t['dates']} | Status: {t['status']}"
            )
    else:
        lines.append("No trips saved yet.")

    lines.append("")

    if travelers:
        lines.append("KNOWN TRAVELERS:")
        for name in travelers:
            profile = get_traveler(name)
            prefs = profile.get("preferences", "not set")
            lines.append(f"  • {name} — preferences: {prefs}")
    else:
        lines.append("No traveler profiles saved yet.")

    return "\n".join(lines)


if __name__ == "__main__":
    print("Testing memory.py...")
    save_trip("Tokyo 2025", {
        "destination": "Tokyo, Japan",
        "dates": "Oct 15–22, 2025",
        "status": "planning",
        "travelers": ["Alice", "Bob"],
    })
    save_traveler("Alice", {
        "email": "alice@example.com",
        "preferences": ["food-focused", "authentic"],
        "dietary_restrictions": "vegetarian",
    })
    print(session_summary())
