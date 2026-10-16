"""
fetch.py
--------
Fetch movie data (including credits) from the TMDb API and store it
as a Pandas DataFrame. Raw responses are saved to disk so the rest of
the analysis can run without calling the API again.
"""

import json
import os
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")

BASE_URL = "https://api.themoviedb.org/3/movie/{}"
DEFAULT_RAW_PATH = PROJECT_ROOT / "data" / "raw" / "movies_raw.json"

MOVIE_IDS = [
    0, 299534, 19995, 140607, 299536, 597, 135397,
    420818, 24428, 168259, 99861, 284054, 12445,
    181808, 330457, 351286, 109445, 321612, 260513,
]


def _get_auth():
    """
    Build request params and headers for authentication.

    Prefers the v4 Bearer access token; falls back to the v3 API key.
    """
    token = os.getenv("TMDB_ACCESS_TOKEN")
    api_key = os.getenv("TMDB_API_KEY")
    headers = {"accept": "application/json"}

    if token:
        headers["Authorization"] = f"Bearer {token}"
        return {}, headers
    if api_key:
        return {"api_key": api_key}, headers

    raise EnvironmentError(
        "No TMDb credentials found. Add TMDB_ACCESS_TOKEN or TMDB_API_KEY to your .env file."
    )


def fetch_movie(movie_id, session, params, headers, timeout=10):
    """
    Fetch a single movie (with credits) by ID.

    Returns the movie as a dict, or None if the request fails
    (e.g. invalid ID such as 0, network error, rate limit).
    """
    request_params = {**params, "append_to_response": "credits"}
    try:
        response = session.get(
            BASE_URL.format(movie_id),
            params=request_params,
            headers=headers,
            timeout=timeout,
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as err:
        print(f"[skip] movie_id={movie_id}: {err}")
        return None


def fetch_movies(movie_ids=MOVIE_IDS, save_path=DEFAULT_RAW_PATH):
    """
    Fetch all movies in `movie_ids`, save the raw JSON, and return a DataFrame.
    """
    params, headers = _get_auth()

    with requests.Session() as session:
        movies = [
            movie
            for movie_id in movie_ids
            if (movie := fetch_movie(movie_id, session, params, headers)) is not None
        ]

    print(f"Fetched {len(movies)} of {len(movie_ids)} movies.")

    if save_path:
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(movies, f, ensure_ascii=False, indent=2)
        print(f"Raw data saved to {save_path}")

    return pd.DataFrame(movies)


def load_raw_movies(path=DEFAULT_RAW_PATH):
    """Load previously saved raw API data into a DataFrame (no API call)."""
    with open(path, encoding="utf-8") as f:
        return pd.DataFrame(json.load(f))


if __name__ == "__main__":
    df = fetch_movies()
    print(df.shape)