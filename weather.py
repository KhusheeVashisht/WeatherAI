"""
weather.py - OpenWeatherMap API Integration Module

This module defines the `get_weather` function, which communicates with the 
OpenWeatherMap REST API to retrieve real-time weather information for a specified 
city. It handles input validation, HTTP request execution, error handling, 
and returns a structured dictionary for the LLM tool-calling lifecycle.
"""

import os
import requests
from typing import Dict, Any


def get_weather(city: str) -> Dict[str, Any]:
    """Fetch current weather data for a specified city using OpenWeatherMap API.

    Args:
        city (str): The name of the city or location (e.g., 'Hyderabad', 'London', 'Tokyo').

    Returns:
        Dict[str, Any]: Structured dictionary containing weather details or an error message.
    """
    # 1. Validate input parameter
    if not city or not isinstance(city, str) or not city.strip():
        return {
            "error": "Invalid argument: A valid non-empty city name string must be provided."
        }

    city_clean = city.strip()

    # 2. Retrieve API Key from environment variables
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        return {
            "error": "OpenWeatherMap API key is missing. Please set OPENWEATHER_API_KEY in your .env file."
        }

    # 3. Construct API request parameters
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city_clean,
        "appid": api_key,
        "units": "metric"  # Metric units: Celsius for temp, m/s for wind speed
    }

    # 4. Execute HTTP request with robust exception handling
    try:
        response = requests.get(url, params=params, timeout=10)

        # Handle HTTP 404 City Not Found
        if response.status_code == 404:
            return {
                "error": f"City '{city_clean}' was not found by OpenWeatherMap. Please check the spelling."
            }

        # Handle HTTP 401 Unauthorized (Invalid API Key)
        if response.status_code == 401:
            return {
                "error": "Invalid OpenWeatherMap API key. Please verify OPENWEATHER_API_KEY in .env."
            }

        # Raise exception for other HTTP errors (5xx server errors, etc.)
        response.raise_for_status()

        # Parse JSON response payload
        data = response.json()

        # 5. Extract and format structured result dictionary
        return {
            "city": data.get("name", city_clean),
            "country": data.get("sys", {}).get("country", ""),
            "temperature_celsius": round(data.get("main", {}).get("temp", 0.0), 1),
            "feels_like_celsius": round(data.get("main", {}).get("feels_like", 0.0), 1),
            "humidity_percent": data.get("main", {}).get("humidity"),
            "description": data.get("weather", [{}])[0].get("description", "N/A"),
            "wind_speed_m_s": data.get("wind", {}).get("speed"),
            "status": "success"
        }

    except requests.exceptions.Timeout:
        return {"error": "Weather API request timed out. Please try again later."}
    except requests.exceptions.ConnectionError:
        return {"error": "Network error: Unable to reach OpenWeatherMap servers."}
    except requests.exceptions.RequestException as err:
        return {"error": f"HTTP request failed: {str(err)}"}
    except Exception as err:
        return {"error": f"An unexpected error occurred while fetching weather data: {str(err)}"}
