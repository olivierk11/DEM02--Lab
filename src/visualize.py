"""
visualize.py
------------
Matplotlib visualizations for the TMDb analysis.

Every function returns the Matplotlib Figure and optionally saves it
when `save_path` is given (e.g. 'reports/figures/revenue_vs_budget.png').
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


def _finish(fig, save_path=None):
    """Tidy layout and optionally save the figure."""
    fig.tight_layout()
    if save_path:
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
    return fig


def _short(title, max_len=22):
    return title if len(title) <= max_len else title[: max_len - 1] + "…"


# --------------------------------------------------------------------------- #
# 1. Revenue vs. Budget
# --------------------------------------------------------------------------- #
def plot_revenue_vs_budget(df, annotate=True, save_path=None):
    """Scatter of budget vs revenue with a break-even line."""
    data = df.dropna(subset=["budget_musd", "revenue_musd"])
    fig, ax = plt.subplots(figsize=(10, 6))

    ax.scatter(data["budget_musd"], data["revenue_musd"], s=60, alpha=0.75, edgecolor="k")

    max_val = data["budget_musd"].max() * 1.05
    ax.plot([0, max_val], [0, max_val], "--", color="gray", label="Break-even (revenue = budget)")

    if annotate:
        for _, row in data.iterrows():
            ax.annotate(_short(row["title"]), (row["budget_musd"], row["revenue_musd"]),
                        fontsize=7, xytext=(4, 4), textcoords="offset points")

    ax.set(title="Revenue vs. Budget", xlabel="Budget (M USD)", ylabel="Revenue (M USD)")
    ax.legend()
    ax.grid(alpha=0.3)
    return _finish(fig, save_path)


# --------------------------------------------------------------------------- #
# 2. ROI distribution by genre
# --------------------------------------------------------------------------- #
def plot_roi_by_genre(df, save_path=None):
    """Box plot of ROI per genre (a movie counts once for each of its genres)."""
    data = df.dropna(subset=["roi", "genres"]).copy()
    data["genre"] = data["genres"].str.split("|")
    data = data.explode("genre")

    order = data.groupby("genre")["roi"].median().sort_values(ascending=False).index
    values = [data.loc[data["genre"] == g, "roi"].values for g in order]

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.boxplot(values)
    ax.set_xticks(range(1, len(order) + 1))
    ax.set_xticklabels(order, rotation=45, ha="right")
    ax.axhline(1, color="red", linestyle="--", linewidth=1, label="ROI = 1 (break-even)")
    ax.set(title="ROI Distribution by Genre", xlabel="Genre", ylabel="ROI (Revenue / Budget)")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    return _finish(fig, save_path)


# --------------------------------------------------------------------------- #
# 3. Popularity vs. Rating
# --------------------------------------------------------------------------- #
def plot_popularity_vs_rating(df, annotate=True, save_path=None):
    """Scatter of rating vs popularity; point size reflects vote count."""
    data = df.dropna(subset=["vote_average", "popularity"])
    sizes = 30 + 300 * data["vote_count"] / data["vote_count"].max()

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.scatter(data["vote_average"], data["popularity"], s=sizes, alpha=0.6, edgecolor="k")

    if annotate:
        for _, row in data.iterrows():
            ax.annotate(_short(row["title"]), (row["vote_average"], row["popularity"]),
                        fontsize=7, xytext=(4, 4), textcoords="offset points")

    corr = data["vote_average"].corr(data["popularity"])
    ax.set(title=f"Popularity vs. Rating (r = {corr:.2f}; bubble size = vote count)",
           xlabel="Average Rating", ylabel="Popularity")
    ax.grid(alpha=0.3)
    return _finish(fig, save_path)


# --------------------------------------------------------------------------- #
# 4. Yearly box office trends
# --------------------------------------------------------------------------- #
def plot_yearly_trends(df, save_path=None):
    """Total budget vs revenue per release year, plus number of movies per year."""
    data = df.dropna(subset=["release_date"]).copy()
    data["year"] = data["release_date"].dt.year

    yearly = data.groupby("year").agg(
        total_budget=("budget_musd", "sum"),
        total_revenue=("revenue_musd", "sum"),
        movie_count=("id", "count"),
    )

    x = np.arange(len(yearly))
    width = 0.4

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 8), sharex=True,
                                   gridspec_kw={"height_ratios": [3, 1]})
    ax1.bar(x - width / 2, yearly["total_budget"], width, label="Total Budget")
    ax1.bar(x + width / 2, yearly["total_revenue"], width, label="Total Revenue")
    ax1.set(title="Yearly Box Office Performance", ylabel="M USD")
    ax1.legend()
    ax1.grid(axis="y", alpha=0.3)

    ax2.bar(x, yearly["movie_count"], color="gray")
    ax2.set(ylabel="Movies", xlabel="Release Year")
    ax2.set_xticks(x)
    ax2.set_xticklabels(yearly.index.astype(int), rotation=45)
    ax2.grid(axis="y", alpha=0.3)
    return _finish(fig, save_path)


# --------------------------------------------------------------------------- #
# 5. Franchise vs. standalone
# --------------------------------------------------------------------------- #
def plot_franchise_vs_standalone(summary, save_path=None):
    """
    Bar charts comparing franchise and standalone movies.

    `summary` is the output of kpis.franchise_vs_standalone(df).
    """
    metrics = {
        "mean_revenue_musd": "Mean Revenue (M USD)",
        "median_roi": "Median ROI",
        "mean_budget_musd": "Mean Budget (M USD)",
        "mean_popularity": "Mean Popularity",
        "mean_rating": "Mean Rating",
    }
    colors = ["tab:blue", "tab:orange"][: len(summary)]

    fig, axes = plt.subplots(1, len(metrics), figsize=(16, 4))
    for ax, (col, label) in zip(axes, metrics.items()):
        ax.bar(summary.index, summary[col], color=colors)
        ax.set_title(label, fontsize=10)
        for i, v in enumerate(summary[col]):
            ax.text(i, v, f"{v:.2f}", ha="center", va="bottom", fontsize=8)
        ax.grid(axis="y", alpha=0.3)

    fig.suptitle("Franchise vs. Standalone Movies", fontsize=13)
    return _finish(fig, save_path)