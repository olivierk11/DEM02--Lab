"""
clean.py
--------
Data cleaning and preprocessing for the TMDb movie dataset.

Use `clean_movies(df_raw)` to run the full pipeline, or call the
individual steps in a notebook to inspect the data between them.
"""

from pathlib import Path

import numpy as np
import pandas as pd

COLUMNS_TO_DROP = ["adult", "imdb_id", "original_title", "video", "homepage"]

JSON_COLUMNS = [
    "belongs_to_collection",
    "genres",
    "production_countries",
    "production_companies",
    "spoken_languages",
]

TEXT_PLACEHOLDERS = {"", "No Data", "No overview found.", "No overview found", "N/A", "n/a", "TBA", "None"}

FINAL_COLUMNS = [
    "id", "title", "tagline", "release_date", "genres", "belongs_to_collection",
    "original_language", "budget_musd", "revenue_musd", "production_companies",
    "production_countries", "vote_count", "vote_average", "popularity", "runtime",
    "overview", "spoken_languages", "poster_path", "cast", "cast_size", "director", "crew_size",
]


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _join_names(value, key="name", sep="|"):
    """Turn a list of dicts like [{'name': 'Action'}, ...] into 'Action|...'."""
    if not isinstance(value, list):
        return np.nan
    names = [item.get(key) for item in value if isinstance(item, dict) and item.get(key)]
    return sep.join(names) if names else np.nan


def _collection_name(value):
    """Extract the collection name from the belongs_to_collection dict."""
    if isinstance(value, dict):
        return value.get("name", np.nan)
    return np.nan


def _director(credits):
    """Return director name(s) from the credits dict, joined with '|'."""
    if not isinstance(credits, dict):
        return np.nan
    names = [p.get("name") for p in credits.get("crew", []) if p.get("job") == "Director"]
    return "|".join(names) if names else np.nan


def _list_size(credits, key):
    """Length of credits['cast'] or credits['crew']."""
    if not isinstance(credits, dict):
        return np.nan
    return len(credits.get(key, []))


def _clean_text(value):
    """Return NaN for missing values or known placeholders."""
    if pd.isna(value) or str(value).strip() in TEXT_PLACEHOLDERS:
        return np.nan
    return value


# --------------------------------------------------------------------------- #
# Pipeline steps
# --------------------------------------------------------------------------- #
def drop_irrelevant_columns(df):
    """Drop columns not needed for the analysis."""
    return df.drop(columns=[c for c in COLUMNS_TO_DROP if c in df.columns])


def extract_json_columns(df):
    """Flatten JSON-like columns into readable, pipe-separated strings."""
    df = df.copy()

    if "belongs_to_collection" in df:
        df["belongs_to_collection"] = df["belongs_to_collection"].apply(_collection_name)

    for col in ["genres", "production_countries", "production_companies"]:
        if col in df:
            df[col] = df[col].apply(_join_names)

    # 'english_name' gives "Spanish" instead of the native "Español"
    if "spoken_languages" in df:
        df["spoken_languages"] = df["spoken_languages"].apply(_join_names, key="english_name")

    return df


def extract_credits(df):
    """Create cast, cast_size, director and crew_size from the credits column."""
    df = df.copy()
    if "credits" not in df:
        for col in ["cast", "cast_size", "director", "crew_size"]:
            df[col] = np.nan
        return df

    credits = df["credits"]
    df["cast"] = credits.apply(lambda c: _join_names(c.get("cast")) if isinstance(c, dict) else np.nan)
    df["cast_size"] = credits.apply(_list_size, key="cast")
    df["director"] = credits.apply(_director)
    df["crew_size"] = credits.apply(_list_size, key="crew")

    return df.drop(columns="credits")


def inspect_value_counts(df, columns=None, top=10):
    """
    Print value_counts for extracted columns to spot anomalies.

    Pipe-separated columns are split so each genre/country/etc. is counted individually.
    Returns a dict of {column: value_counts Series}.
    """
    columns = columns or JSON_COLUMNS
    results = {}
    for col in columns:
        if col not in df:
            continue
        counts = df[col].dropna().str.split("|").explode().value_counts()
        results[col] = counts
        print(f"\n=== {col} ({counts.size} unique) ===")
        print(counts.head(top).to_string())
    return results


def convert_dtypes(df):
    """Convert numeric columns (invalid -> NaN) and parse release_date."""
    df = df.copy()
    numeric_cols = ["budget", "id", "popularity", "revenue", "runtime", "vote_count", "vote_average"]
    for col in numeric_cols:
        if col in df:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "release_date" in df:
        df["release_date"] = pd.to_datetime(df["release_date"], errors="coerce")
    return df


def handle_unrealistic_values(df):
    """
    - Replace 0 budget/revenue/runtime with NaN
    - Convert budget and revenue to million USD
    - Set vote_average to NaN when vote_count is 0 (a rating with no votes is meaningless)
    - Replace placeholder text in overview/tagline with NaN
    """
    df = df.copy()

    for col in ["budget", "revenue", "runtime"]:
        if col in df:
            df[col] = df[col].replace(0, np.nan)

    if "budget" in df:
        df["budget_musd"] = df["budget"] / 1_000_000
    if "revenue" in df:
        df["revenue_musd"] = df["revenue"] / 1_000_000
    df = df.drop(columns=[c for c in ["budget", "revenue"] if c in df.columns])

    if {"vote_count", "vote_average"}.issubset(df.columns):
        df.loc[df["vote_count"] == 0, "vote_average"] = np.nan

    for col in ["overview", "tagline"]:
        if col in df:
            df[col] = df[col].apply(_clean_text)

    return df


def remove_invalid_rows(df, min_non_null=10):
    """
    - Drop duplicate movies (by id)
    - Drop rows with missing id or title
    - Keep rows with at least `min_non_null` non-NaN values
    - Keep only 'Released' movies, then drop the status column
    """
    df = df.dropna(subset=["id", "title"])
    df = df.drop_duplicates(subset="id")
    df = df.dropna(thresh=min_non_null)

    if "status" in df:
        df = df[df["status"] == "Released"].drop(columns="status")

    df = df.copy()
    df["id"] = df["id"].astype(int)
    return df


def finalize(df):
    """Reorder columns to the required layout and reset the index."""
    cols = [c for c in FINAL_COLUMNS if c in df.columns]
    return df[cols].reset_index(drop=True)


# --------------------------------------------------------------------------- #
# Full pipeline
# --------------------------------------------------------------------------- #
def clean_movies(df_raw, verbose=False):
    """Run every cleaning step in order and return the final DataFrame."""
    df = drop_irrelevant_columns(df_raw)
    df = extract_json_columns(df)
    df = extract_credits(df)
    if verbose:
        inspect_value_counts(df)
    df = convert_dtypes(df)
    df = handle_unrealistic_values(df)
    df = remove_invalid_rows(df)
    return finalize(df)


def save_processed(df, path=None):
    """Save the cleaned DataFrame to data/processed/movies_clean.csv."""
    path = Path(path) if path else Path(__file__).resolve().parents[1] / "data" / "processed" / "movies_clean.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    print(f"Clean data saved to {path}")
    return path