"""
agent.py
Atlas Travel Agent — Main Runner
Wires together the system prompt, memory, and all live tools.
Run this to start a conversation with Atlas.

Usage:
  python agent.py

Requirements:
  pip install requests google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client

Environment variables:
  NVIDIA_API_KEY — your NVIDIA API key (from hackathon organizers)
"""

import os
import sys
import json
import requests

from tools.memory import session_summary, save_trip, save_traveler, add_todo
from tools.web_search import (
    search_flights, search_hotels, search_visa_requirements,
    search_restaurants, search_activities, search_weather, search_baggage_policy,
)
from tools.email_tool import draft_trip_summary, draft_pretrip_reminder, send_email, preview_draft
from tools.google_calendar import check_availability, check_group_availability, create_trip_invite

NVIDIA_API_KEY = os.environ.get("NVIDIA_API_KEY", "")
NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"
MODEL = "nvidia/llama-3.1-nemotron-ultra-253b-v1"

SYSTEM_PROMPT_PATH = os.path.join(os.path.dirname(__file__), "TripAgent_system_prompt.md")


def load_system_prompt() -> str:
    """Load the system prompt and inject current memory context."""
    with open(SYSTEM_PROMPT_PATH, "r") as f:
        base_prompt = f.read()
    memory_context = session_summary()
    return f"{base_prompt}\n\n---\n\n## Current Memory\n\n{memory_context}"


def call_nemotron(messages: list[dict]) -> str:
    """Send messages to Nemotron and return the assistant reply."""
    if not NVIDIA_API_KEY:
        return "ERROR: NVIDIA_API_KEY environment variable not set."

    headers = {
        "Authorization": f"Bearer {NVIDIA_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": MODEL,
        "messages": messages,
        "max_tokens": 1000,
        "temperature": 0.7,
    }
    try:
        response = requests.post(
            f"{NVIDIA_BASE_URL}/chat/completions",
            headers=headers,
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except requests.exceptions.RequestException as e:
        return f"API error: {e}"


def handle_tool_command(user_input: str) -> str | None:
    """
    Check if the user's message implies a direct tool action.
    Returns tool output string if handled, None otherwise.
    Atlas handles these autonomously without waiting to be asked step by step.
    """
    lower = user_input.lower()

    # Flight search
    if "find flights" in lower or "search flights" in lower:
        return (
            "I'll search for flights now. "
            "To get the best results, tell me: origin city, destination, travel dates, "
            "and number of travelers."
        )

    # Calendar availability
    if "check availability" in lower or "are we free" in lower or "calendar" in lower:
        return (
            "I can check Google Calendar availability for your group. "
            "Share the date range and I'll flag any conflicts."
        )

    # Weather
    if "weather" in lower or "what to pack" in lower or "packing" in lower:
        return (
            "I'll look up the weather for your destination and put together a packing list. "
            "Just confirm the destination and travel dates."
        )

    # Visa
    if "visa" in lower or "passport" in lower or "entry requirements" in lower:
        return (
            "I'll check the visa and entry requirements now. "
            "What's your passport country and destination?"
        )

    return None


def chat():
    """Main chat loop for Atlas."""
    print("\n🌍 Atlas — Your Personal Travel Agent")
    print("Type 'quit' to exit, 'memory' to see saved trips and travelers.\n")

    system_prompt = load_system_prompt()
    messages = [{"role": "system", "content": system_prompt}]

    while True:
        try:
            user_input = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nSafe travels! 👋")
            sys.exit(0)

        if not user_input:
            continue

        if user_input.lower() == "quit":
            print("Safe travels! 👋")
            break

        if user_input.lower() == "memory":
            print(f"\n{session_summary()}\n")
            continue

        # Check for direct tool triggers
        tool_response = handle_tool_command(user_input)
        if tool_response:
            print(f"\nAtlas: {tool_response}\n")

        # Add user message and call Nemotron
        messages.append({"role": "user", "content": user_input})
        response = call_nemotron(messages)

        # Add assistant response to history (persistent across turns)
        messages.append({"role": "assistant", "content": response})

        print(f"\nAtlas: {response}\n")


if __name__ == "__main__":
    chat()
