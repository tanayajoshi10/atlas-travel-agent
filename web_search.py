"""
tools/web_search.py
Atlas Travel Agent — Web Search Tool
Handles all web search queries: flights, hotels, visa info,
restaurants, activities, weather, and baggage policies.
"""

import os
import requests

NVIDIA_API_KEY = os.environ.get("NVIDIA_API_KEY", "")
NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"


def search(query: str) -> str:
    """
    Send a search query to Nemotron and return the result.
    The model uses its web-grounded knowledge to answer.
    """
    headers = {
        "Authorization": f"Bearer {NVIDIA_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "nvidia/llama-3.1-nemotron-ultra-253b-v1",
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a travel research assistant. "
                    "Answer the query with accurate, current travel information. "
                    "Be concise and factual. Include prices, dates, or links where relevant."
                ),
            },
            {"role": "user", "content": query},
        ],
        "max_tokens": 1000,
    }
    response = requests.post(
        f"{NVIDIA_BASE_URL}/chat/completions", headers=headers, json=payload
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]


def search_flights(origin: str, destination: str, date: str, passengers: int = 1) -> str:
    query = (
        f"Find flights from {origin} to {destination} on {date} "
        f"for {passengers} passenger(s). Include cheapest, most reliable, "
        f"and best value options. Note baggage allowances and airline reliability."
    )
    return search(query)


def search_hotels(destination: str, checkin: str, checkout: str, preferences: str = "") -> str:
    query = (
        f"Find hotels in {destination} from {checkin} to {checkout}. "
        f"Traveler preferences: {preferences}. "
        f"Include boutique, mid-range, and comfortable options with cancellation policies."
    )
    return search(query)


def search_visa_requirements(passport_country: str, destination: str) -> str:
    query = (
        f"What are the visa requirements for a {passport_country} passport holder "
        f"traveling to {destination}? Include processing time and any fees."
    )
    return search(query)


def search_restaurants(destination: str, preferences: str = "") -> str:
    query = (
        f"Best restaurants and food experiences in {destination}. "
        f"Preferences: {preferences}. Include one must-try local food experience."
    )
    return search(query)


def search_activities(destination: str, interests: str = "") -> str:
    query = (
        f"Top activities and experiences in {destination}. "
        f"Traveler interests: {interests}. "
        f"Include cultural, outdoor, food, and unique local experiences."
    )
    return search(query)


def search_baggage_policy(airline: str) -> str:
    query = (
        f"What is {airline}'s baggage policy? "
        f"Include carry-on limits, checked bag allowances, weight limits, "
        f"and overweight/extra bag fees."
    )
    return search(query)


def search_weather(destination: str, travel_dates: str) -> str:
    query = (
        f"What is the weather like in {destination} during {travel_dates}? "
        f"Include typical temperatures, rainfall, and what to pack."
    )
    return search(query)


def search_ground_transport(destination: str) -> str:
    query = (
        f"Best ways to get around {destination} as a tourist. "
        f"Include airport transfers, public transit, taxis, rental cars, and walking areas."
    )
    return search(query)


if __name__ == "__main__":
    print("Testing web_search.py...")
    result = search_flights("San Francisco", "Tokyo", "2025-10-15", 2)
    print(result)
