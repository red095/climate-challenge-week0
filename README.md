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

The Streamlit app can also load the cleaned CSV files from Google Drive, which
is useful for deployment because the local `data/` folder is not committed.

### 5. Configure Google Drive data for Streamlit deployment

1. Upload these files to Google Drive:
   - `ethiopia_clean.csv`
   - `kenya_clean.csv`
   - `sudan_clean.csv`
   - `tanzania_clean.csv`
   - `nigeria_clean.csv`
2. Set each file's sharing to **Anyone with the link can view**.
3. Copy the file ID from each share link. For example:
   `https://drive.google.com/file/d/FILE_ID/view?usp=sharing`
4. In Streamlit Community Cloud, add secrets in this format:

```toml
[google_drive]
ethiopia_file_id = "..."
kenya_file_id = "..."
sudan_file_id = "..."
tanzania_file_id = "..."
nigeria_file_id = "..."
```

For local testing, copy `.streamlit/secrets.toml.example` to
`.streamlit/secrets.toml` and fill in the same IDs. The real secrets file is
gitignored.

## Project Structure
- `notebooks/` — EDA notebooks per country + comparison notebook
- `scripts/` — reusable Python scripts
- `app/` — Streamlit dashboard
- `tests/` — unit tests
- `.github/workflows/` — CI/CD pipeline

## Run the Dashboard

```bash
streamlit run app/main.py
```

## Run Tests

```bash
python -m unittest
```
