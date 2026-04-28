import pandas as pd
import os
from urllib.parse import urlparse, parse_qs

COUNTRIES = ['Ethiopia', 'Kenya', 'Sudan', 'Tanzania', 'Nigeria']

COLORS = {
    'Ethiopia': '#e74c3c',
    'Kenya':    '#2ecc71',
    'Sudan':    '#f39c12',
    'Tanzania': '#3498db',
    'Nigeria':  '#9b59b6'
}

REQUIRED_COLUMNS = {
    'T2M', 'T2M_MAX', 'T2M_MIN', 'T2M_RANGE', 'PRECTOTCORR',
    'RH2M', 'WS2M', 'WS2M_MAX', 'PS', 'QV2M'
}


def google_drive_download_url(file_id: str) -> str:
    """Build a direct-download URL for a public Google Drive file."""
    return f'https://drive.google.com/uc?export=download&id={file_id}'


def extract_google_drive_file_id(url: str) -> str:
    """Extract a Google Drive file ID from common share URL formats."""
    parsed = urlparse(url)
    if parsed.netloc not in {'drive.google.com', 'docs.google.com'}:
        return ''

    parts = [part for part in parsed.path.split('/') if part]
    if 'file' in parts and 'd' in parts:
        file_id_index = parts.index('d') + 1
        if file_id_index < len(parts):
            return parts[file_id_index]

    query_id = parse_qs(parsed.query).get('id', [''])[0]
    return query_id


def normalize_csv_source(source: str) -> str:
    """Convert Google Drive share URLs to direct CSV download URLs."""
    if not source:
        return source

    file_id = extract_google_drive_file_id(source)
    if file_id:
        return google_drive_download_url(file_id)

    return source


def _prepare_country_frame(df: pd.DataFrame, country: str, source: str) -> pd.DataFrame:
    """Validate and standardize a country dataframe."""
    df = df.copy()

    missing = sorted(REQUIRED_COLUMNS - set(df.columns))
    if missing:
        raise ValueError(f'{source} is missing required columns: {", ".join(missing)}')

    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    elif {'YEAR', 'DOY'}.issubset(df.columns):
        year_start = pd.to_datetime(df['YEAR'].astype(str), format='%Y', errors='coerce')
        df['Date'] = year_start + pd.to_timedelta(df['DOY'] - 1, unit='D')
    else:
        raise ValueError(f'{source} must include Date, or YEAR and DOY columns')

    if df['Date'].isna().any():
        raise ValueError(f'{source} contains invalid Date/YEAR/DOY values')

    df['Country'] = country
    df['Year'] = df['Date'].dt.year
    df['Month'] = df['Date'].dt.month
    return df


def load_country_data(
    country: str,
    data_dir: str = 'data',
    remote_sources: dict | None = None
) -> pd.DataFrame:
    """Load cleaned CSV for a single country from local disk or a remote source."""
    path = os.path.join(data_dir, f'{country.lower()}_clean.csv')
    if not os.path.exists(path):
        source = (remote_sources or {}).get(country)
        if not source:
            return pd.DataFrame()
        source = normalize_csv_source(source)
    else:
        source = path

    df = pd.read_csv(source)
    return _prepare_country_frame(df, country, source)


def load_all_countries(
    data_dir: str = 'data',
    remote_sources: dict | None = None
) -> pd.DataFrame:
    """Load and concatenate all five country datasets."""
    dfs = []
    for country in COUNTRIES:
        df = load_country_data(country, data_dir, remote_sources)
        if not df.empty:
            dfs.append(df)
    if not dfs:
        return pd.DataFrame()
    return pd.concat(dfs, ignore_index=True)


def filter_data(df: pd.DataFrame, countries: list, year_range: tuple) -> pd.DataFrame:
    """Filter combined dataframe by selected countries and year range."""
    mask = (
        df['Country'].isin(countries) &
        (df['Year'] >= year_range[0]) &
        (df['Year'] <= year_range[1])
    )
    return df[mask].copy()


def monthly_avg(df: pd.DataFrame, variable: str) -> pd.DataFrame:
    """Compute monthly average of a variable per country."""
    df = df.copy()
    df['YearMonth'] = df['Date'].dt.to_period('M').dt.to_timestamp()
    return (df.groupby(['Country', 'YearMonth'])[variable]
              .mean()
              .reset_index()
              .rename(columns={variable: 'Value'}))


def monthly_total(df: pd.DataFrame, variable: str) -> pd.DataFrame:
    """Compute monthly total of a variable per country."""
    df = df.copy()
    df['YearMonth'] = df['Date'].dt.to_period('M').dt.to_timestamp()
    return (df.groupby(['Country', 'YearMonth'])[variable]
              .sum()
              .reset_index()
              .rename(columns={variable: 'Value'}))


def extreme_heat_days(df: pd.DataFrame, threshold: float = 35.0) -> pd.DataFrame:
    """Count days per year where T2M_MAX exceeds threshold, including zero years."""
    years = df[['Country', 'Year']].drop_duplicates()
    heat = (df.assign(Is_Extreme_Heat=df['T2M_MAX'] > threshold)
              .groupby(['Country', 'Year'])['Is_Extreme_Heat']
              .sum()
              .reset_index(name='Extreme_Heat_Days'))
    result = years.merge(heat, on=['Country', 'Year'], how='left').fillna(
        {'Extreme_Heat_Days': 0}
    )
    result['Extreme_Heat_Days'] = result['Extreme_Heat_Days'].astype(int)
    return result.sort_values(['Country', 'Year']).reset_index(drop=True)


def consecutive_dry_days(df: pd.DataFrame, threshold: float = 1.0) -> pd.DataFrame:
    """Compute max consecutive dry days per country per year."""
    results = []
    for (country, year), group in df.groupby(['Country', 'Year']):
        group = group.sort_values('Date')
        max_streak = streak = 0
        for val in group['PRECTOTCORR']:
            if val < threshold:
                streak += 1
                max_streak = max(max_streak, streak)
            else:
                streak = 0
        results.append({'Country': country, 'Year': year,
                        'Max_Dry_Streak': max_streak})
    return pd.DataFrame(results)


def vulnerability_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Build a vulnerability summary table across all countries."""
    temp = df.groupby('Country')['T2M'].agg(
        Mean_Temp='mean', Temp_Std='std').round(2)

    precip = df.groupby('Country')['PRECTOTCORR'].agg(
        Mean_Precip='mean', Precip_Std='std').round(3)

    heat = (df[df['T2M_MAX'] > 35]
            .groupby('Country').size()
            .reset_index(name='Total_Heat_Days')
            .set_index('Country'))

    summary = temp.join(precip).join(heat).fillna(0)
    summary['Vuln_Score'] = (
        summary['Mean_Temp'].rank(ascending=False) +
        summary['Precip_Std'].rank(ascending=False) +
        summary['Total_Heat_Days'].rank(ascending=False)
    )
    summary['Rank'] = summary['Vuln_Score'].rank(method='dense').astype(int)
    return summary.sort_values('Rank').reset_index()
