# Golf Market Opportunity Explorer ⛳

An interactive Streamlit app to identify high-potential U.S. counties for golf equipment marketing.

## Live Demo

[View the app on Streamlit Cloud](https://golf-market-explorer.streamlit.app/)

## Overview

This tool helps golf equipment marketers identify target markets by analyzing county-level demographics. It uses Census data to calculate an "opportunity score" based on factors that correlate with golf participation:

- **Income** (35%) - Golfers have ~2x median household income
- **Education** (25%) - 70%+ of golfers have college degrees  
- **Diversity** (15%) - Hispanic/Asian golfers grew 43% since 2018
- **Population** (15%) - Larger markets = more customers
- **Age** (10%) - Younger counties = emerging golfers

## Features

- 🗺️ Interactive US map showing opportunity by state
- 🎚️ Adjustable weights to customize the scoring formula
- 🔍 Filter by region, affluence, minimum score
- 📊 Visualizations: box plots, scatter plots
- 📋 Sortable top counties table
- 📥 Download filtered data as CSV

## Data

- **Source:** U.S. Census Bureau American Community Survey (2015-2019)
- **Scope:** 3,142 U.S. counties
- **Variables:** Income, education, age, race/ethnicity, population, metro status

## Run Locally

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## Files

| File | Description |
|------|-------------|
| `streamlit_app.py` | Main Streamlit application |
| `census.csv` | County demographic data |
| `requirements.txt` | Python dependencies |
| `CodingProject_FinalDraft.html` | Full analysis notebook |


## Author

Cook Welch  
MBA Candidate, Boston College Carroll School of Management

---

*Created as part of a data analytics course project, February 2026*
