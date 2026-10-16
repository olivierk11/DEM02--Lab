# TMDB Movie Data Analysis

A data analysis pipeline that fetches movie data from the TMDb API, cleans and
transforms it with Pandas, computes performance KPIs, and visualizes key insights.

## Project Structure

```
tmdb-movie-analysis/
├── data/
│   ├── raw/            # raw API responses
│   └── processed/      # cleaned dataset
├── notebooks/
│   └── analysis.ipynb  # main workflow
├── src/
│   ├── fetch.py        # API data extraction
│   ├── clean.py        # cleaning and preprocessing
│   ├── kpis.py         # ranking and KPI functions
│   └── visualize.py    # plotting functions
├── requirements.txt
└── README.md
```

## Setup

1. Clone the repository and create a virtual environment:
```bash
   python -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   pip install -r requirements.txt
```
2. Get a free API key from [TMDb](https://www.themoviedb.org/settings/api).
3. Create a `.env` file in the project root:
```
   TMDB_API_KEY=your_api_key
   TMDB_ACCESS_TOKEN=your_access_token
```
4. Open `notebooks/analysis.ipynb` and run all cells.

## Methodology

1. **Data extraction:** fetched 19 movie IDs from the TMDb `/movie/{id}` endpoint, including credits.
2. **Cleaning:** dropped irrelevant columns, flattened JSON fields, fixed data types, handled missing values.
3. **KPI analysis:** ranked movies by revenue, profit, ROI, ratings, and popularity.
4. **Visualization:** explored budget vs. revenue, ROI by genre, yearly trends, and franchise performance.

## Key Findings

_To be completed after analysis._

## Tools

Python, Pandas, NumPy, Requests, Matplotlib, Jupyter