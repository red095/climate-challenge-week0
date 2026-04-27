# Climate Challenge Week 0 — African Climate Trend Analysis

## Project Overview
Exploratory analysis of historical climate data across five African nations
(Ethiopia, Kenya, Sudan, Tanzania, Nigeria) to support Ethiopia's COP32 position.

## Setup Instructions

### 1. Clone the repository
```bash
git clone https://github.com/red095/climate-challenge-week0.git
cd climate-challenge-week0
```

### 2. Create and activate virtual environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Place data files
Download the country CSV files and place them in a local `data/` folder.
This folder is gitignored and will never be committed.

## Project Structure
- `notebooks/` — EDA notebooks per country + comparison notebook
- `scripts/` — reusable Python scripts
- `app/` — Streamlit dashboard
- `tests/` — unit tests
- `.github/workflows/` — CI/CD pipeline
