import pandas as pd
import numpy as np
import os

COUNTRIES = ['Ethiopia', 'Kenya', 'Sudan', 'Tanzania', 'Nigeria']

COLORS = {
    'Ethiopia': '#e74c3c',
    'Kenya':    '#2ecc71',
    'Sudan':    '#f39c12',
    'Tanzania': '#3498db',
    'Nigeria':  '#9b59b6'
}

def load_country_data(country: str, data_dir: str = 'data') -> pd.DataFrame:
    """Load cleaned CSV for a single country."""
    path = os.path.join(data_dir, f'{country.lower()}_clean.csv')
    if not os.path.exists(path):
        return pd.DataFrame()
    df = pd.read_csv(path, parse_dates=['Date'])
    df['Country'] = country
    df['Year'] = df['Date'].dt.year
    df['Month'] = df['Date'].dt.month
    return df


def load_all_countries(data_dir: str = 'data') -> pd.DataFrame:
    """Load and concatenate all five country datasets."""
    dfs = []
    for country in COUNTRIES:
        df = load_country_data(country, data_dir)
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
    """Count days per year where T2M_MAX exceeds threshold."""
    heat = df[df['T2M_MAX'] > threshold]
    return (heat.groupby(['Country', 'Year'])
                .size()
                .reset_index(name='Extreme_Heat_Days'))


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
    summary['Rank'] = summary['Vuln_Score'].rank().astype(int)
    return summary.sort_values('Rank').reset_index()