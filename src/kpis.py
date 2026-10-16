"""
kpis.py
-------
KPI calculations, rankings, search queries, and franchise/director analysis.
"""

import numpy as np
import pandas as pd


# --------------------------------------------------------------------------- #
# Derived metrics
# --------------------------------------------------------------------------- #
def add_financial_metrics(df):
    """Add profit_musd (revenue - budget) and roi (revenue / budget)."""
    df = df.copy()
    df["profit_musd"] = df["revenue_musd"] - df["budget_musd"]
    df["roi"] = df["revenue_musd"] / df["budget_musd"]
    return df


# --------------------------------------------------------------------------- #
# Ranking UDF
# --------------------------------------------------------------------------- #
def rank_movies(df, metric, n=5, ascending=False, filter_col=None, min_value=None, columns=None):
    """
    Rank movies by `metric`.

    Parameters
    ----------
    df : DataFrame
    metric : column to rank by
    n : number of movies to return
    ascending : False = highest first, True = lowest first
    filter_col, min_value : optional threshold, e.g. filter_col='budget_musd', min_value=10
    columns : extra columns to display alongside title and metric
    """
    data = df.dropna(subset=[metric])
    if filter_col is not None and min_value is not None:
        data = data[data[filter_col] >= min_value]

    display_cols = ["title", metric] + [c for c in (columns or []) if c not in ("title", metric)]
    return (
        data.sort_values(metric, ascending=ascending)
        .head(n)[display_cols]
        .reset_index(drop=True)
    )


KPI_DEFINITIONS = {
    "Highest Revenue":       dict(metric="revenue_musd"),
    "Highest Budget":        dict(metric="budget_musd"),
    "Highest Profit":        dict(metric="profit_musd"),
    "Lowest Profit":         dict(metric="profit_musd", ascending=True),
    "Highest ROI":           dict(metric="roi", filter_col="budget_musd", min_value=10),
    "Lowest ROI":            dict(metric="roi", ascending=True, filter_col="budget_musd", min_value=10),
    "Most Voted":            dict(metric="vote_count"),
    "Highest Rated":         dict(metric="vote_average", filter_col="vote_count", min_value=10),
    "Lowest Rated":          dict(metric="vote_average", ascending=True, filter_col="vote_count", min_value=10),
    "Most Popular":          dict(metric="popularity"),
}


def get_all_rankings(df, n=5):
    """Run every KPI ranking and return {kpi_name: DataFrame}."""
    if "roi" not in df:
        df = add_financial_metrics(df)
    return {name: rank_movies(df, n=n, **params) for name, params in KPI_DEFINITIONS.items()}


# --------------------------------------------------------------------------- #
# Search queries
# --------------------------------------------------------------------------- #
def search_movies(df, genres=None, actor=None, director=None, sort_by=None, ascending=False):
    """
    Filter movies by genres (all must match), an actor in the cast, and/or a director.
    """
    mask = pd.Series(True, index=df.index)

    for genre in genres or []:
        mask &= df["genres"].str.contains(genre, regex=False, na=False)
    if actor:
        mask &= df["cast"].str.contains(actor, regex=False, na=False)
    if director:
        mask &= df["director"].str.contains(director, regex=False, na=False)

    result = df[mask]
    if sort_by:
        result = result.sort_values(sort_by, ascending=ascending)
    return result.reset_index(drop=True)


def search_bruce_willis_scifi_action(df):
    """Search 1: Sci-Fi Action movies starring Bruce Willis, highest rated first."""
    return search_movies(
        df, genres=["Science Fiction", "Action"], actor="Bruce Willis",
        sort_by="vote_average", ascending=False,
    )[["title", "genres", "vote_average", "release_date"]]


def search_uma_thurman_tarantino(df):
    """Search 2: Uma Thurman movies directed by Quentin Tarantino, shortest first."""
    return search_movies(
        df, actor="Uma Thurman", director="Quentin Tarantino",
        sort_by="runtime", ascending=True,
    )[["title", "director", "runtime", "release_date"]]


# --------------------------------------------------------------------------- #
# Franchise vs. standalone
# --------------------------------------------------------------------------- #
def franchise_vs_standalone(df):
    """Compare franchise movies against standalone movies."""
    if "roi" not in df:
        df = add_financial_metrics(df)

    group = np.where(df["belongs_to_collection"].notna(), "Franchise", "Standalone")
    summary = df.groupby(group).agg(
        movie_count=("id", "count"),
        mean_revenue_musd=("revenue_musd", "mean"),
        median_roi=("roi", "median"),
        mean_budget_musd=("budget_musd", "mean"),
        mean_popularity=("popularity", "mean"),
        mean_rating=("vote_average", "mean"),
    )
    summary.index.name = "type"
    return summary.round(2)


# --------------------------------------------------------------------------- #
# Franchises & directors
# --------------------------------------------------------------------------- #
def top_franchises(df, sort_by="total_revenue_musd", n=10):
    """Most successful franchises by movie count, budget, revenue and rating."""
    summary = (
        df.dropna(subset=["belongs_to_collection"])
        .groupby("belongs_to_collection")
        .agg(
            movie_count=("id", "count"),
            total_budget_musd=("budget_musd", "sum"),
            mean_budget_musd=("budget_musd", "mean"),
            total_revenue_musd=("revenue_musd", "sum"),
            mean_revenue_musd=("revenue_musd", "mean"),
            mean_rating=("vote_average", "mean"),
        )
    )
    return summary.sort_values(sort_by, ascending=False).head(n).round(2)


def top_directors(df, sort_by="total_revenue_musd", n=10):
    """
    Most successful directors by movie count, total revenue and mean rating.

    Co-directed movies (e.g. 'Anthony Russo|Joe Russo') are credited to each director.
    """
    directors = df.dropna(subset=["director"]).assign(director=lambda d: d["director"].str.split("|"))
    summary = (
        directors.explode("director")
        .groupby("director")
        .agg(
            movie_count=("id", "count"),
            total_revenue_musd=("revenue_musd", "sum"),
            mean_rating=("vote_average", "mean"),
        )
    )
    return summary.sort_values(sort_by, ascending=False).head(n).round(2)