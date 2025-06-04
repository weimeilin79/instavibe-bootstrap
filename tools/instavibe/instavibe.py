import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()
BASE_URL = os.environ.get("INSTAVIBE_BASE_URL")

def create_post(author_name: str, text: str, sentiment: str, base_url: str = BASE_URL):
    """
    Sends a POST request to the /posts endpoint to create a new post.

    Args:
        author_name (str): The name of the post's author.
        text (str): The content of the post.
        sentiment (str): The sentiment associated with the post (e.g., 'positive', 'negative', 'neutral').
        base_url (str, optional): The base URL of the API. Defaults to BASE_URL.

    Returns:
        dict: The JSON response from the API if the request is successful.
              Returns None if an error occurs.

    Raises:
        requests.exceptions.RequestException: If there's an issue with the network request (e.g., connection error, timeout).
    """
    url = f"{base_url}/posts"
    headers = {"Content-Type": "application/json"}
    payload = {
        "author_name": author_name,
        "text": text,
        "sentiment": sentiment
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
        print(f"Successfully created post. Status Code: {response.status_code}")
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error creating post: {e}")
        # Optionally re-raise the exception if the caller needs to handle it
        # raise e
        return None
    except json.JSONDecodeError:
        print(f"Error decoding JSON response from {url}. Response text: {response.text}")
        return None

def create_event(event_name: str, description: str, event_date: str, locations: list, attendee_names: list[str], base_url: str = BASE_URL):
    """
    Sends a POST request to the /events endpoint to create a new event registration.

    Args:
        event_name (str): The name of the event.
        description (str): The detailed description of the event.
        event_date (str): The date and time of the event (ISO 8601 format recommended, e.g., "2025-06-10T09:00:00Z").
        locations (list): A list of location dictionaries. Each dictionary should contain:
                          'name' (str), 'description' (str, optional),
                          'latitude' (float), 'longitude' (float),
                          'address' (str, optional).
        attendee_names (list[str]): A list of names of the people attending the event.
        base_url (str, optional): The base URL of the API. Defaults to BASE_URL.

    Returns:
        dict: The JSON response from the API if the request is successful.
              Returns None if an error occurs.

    Raises:
        requests.exceptions.RequestException: If there's an issue with the network request (e.g., connection error, timeout).
    """
    url = f"{base_url}/events"
    headers = {"Content-Type": "application/json"}
    payload = {
        "event_name": event_name,
        "description": description,
        "event_date": event_date,
        "locations": locations,
        "attendee_names": attendee_names,
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
        print(f"Successfully created event registration. Status Code: {response.status_code}")
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error creating event registration: {e}")
        # Optionally re-raise the exception if the caller needs to handle it
        # raise e
        return None
    except json.JSONDecodeError:
        print(f"Error decoding JSON response from {url}. Response text: {response.text}")
        return None




  
