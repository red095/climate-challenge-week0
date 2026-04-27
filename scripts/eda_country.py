import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
from scipy import stats
import warnings
import sys
import os

warnings.filterwarnings('ignore')

plt.rcParams['figure.figsize'] = (14, 5)
plt.rcParams['axes.grid'] = True
plt.rcParams['grid.alpha'] = 0.3
sns.set_theme(style="whitegrid")


def run_eda(country_name, csv_path, output_dir='notebooks'):
    """
    Full EDA pipeline for a single country.
    Loads, cleans, analyzes, and exports charts + cleaned CSV.
    """
    print(f"\n{'='*50}")
    print(f"  Running EDA for: {country_name.upper()}")
    print(f"{'='*50}\n")

    # ── 1. LOAD & PARSE ──────────────────────────────────
    df = pd.read_csv(csv_path)
    df['Country'] = country_name
    df['Date'] = pd.to_datetime(df['YEAR'] * 1000 + df['DOY'], format='%Y%j')
    df['Month'] = df['Date'].dt.month
    print(f"Loaded {len(df)} rows")

    # ── 2. REPLACE SENTINELS ─────────────────────────────
    df.replace(-999, np.nan, inplace=True)

    # ── 3. DUPLICATES ────────────────────────────────────
    dupes = df.duplicated().sum()
    print(f"Duplicate rows: {dupes}")
    df.drop_duplicates(inplace=True)

    # ── 4. MISSING VALUE REPORT ──────────────────────────
    missing_pct = (df.isna().sum() / len(df) * 100).round(2)
    high_missing = missing_pct[missing_pct > 5]
    if len(high_missing) > 0:
        print(f"Columns with >5% missing:\n{high_missing}")
    else:
        print("No columns exceed 5% missing ✅")

    # ── 5. OUTLIER DETECTION & CAPPING ───────────────────
    outlier_cols = ['T2M', 'T2M_MAX', 'T2M_MIN', 
                    'PRECTOTCORR', 'RH2M', 'WS2M', 'WS2M_MAX']
    
    for col in outlier_cols:
        mean = df[col].mean()
        std = df[col].std()
        df[col] = df[col].clip(lower=mean - 3*std, upper=mean + 3*std)
    print("Outliers capped at ±3 std ✅")

    # ── 6. FORWARD FILL MISSING VALUES ───────────────────
    weather_cols = ['T2M', 'T2M_MAX', 'T2M_MIN', 'T2M_RANGE',
                    'PRECTOTCORR', 'RH2M', 'WS2M', 'WS2M_MAX', 'PS', 'QV2M']
    df[weather_cols] = df[weather_cols].ffill()
    threshold = len(df.columns) * 0.7
    df.dropna(thresh=int(threshold), inplace=True)
    print("Missing values forward-filled ✅")

    # ── 7. EXPORT CLEAN CSV ──────────────────────────────
    clean_path = f'data/{country_name.lower()}_clean.csv'
    df.to_csv(clean_path, index=False)
    print(f"Clean CSV saved → {clean_path} ✅")

    country_label = country_name.capitalize()

    # ── 8. TEMPERATURE TIME SERIES ───────────────────────
    monthly_temp = df.groupby(df['Date'].dt.to_period('M'))['T2M'].mean()
    monthly_temp.index = monthly_temp.index.to_timestamp()
    warmest = monthly_temp.idxmax()
    coolest = monthly_temp.idxmin()

    fig, ax = plt.subplots(figsize=(16, 5))
    ax.plot(monthly_temp.index, monthly_temp.values, 
            color='#e74c3c', linewidth=1.8)
    ax.fill_between(monthly_temp.index, monthly_temp.values, 
                    alpha=0.15, color='#e74c3c')
    ax.annotate(
        f'Warmest\n{warmest.strftime("%b %Y")}\n{monthly_temp[warmest]:.1f}°C',
        xy=(warmest, monthly_temp[warmest]),
        xytext=(30, 15), textcoords='offset points',
        arrowprops=dict(arrowstyle='->', color='black'),
        fontsize=9, color='darkred'
    )
    ax.annotate(
        f'Coolest\n{coolest.strftime("%b %Y")}\n{monthly_temp[coolest]:.1f}°C',
        xy=(coolest, monthly_temp[coolest]),
        xytext=(30, -30), textcoords='offset points',
        arrowprops=dict(arrowstyle='->', color='black'),
        fontsize=9, color='navy'
    )
    ax.set_title(f'{country_label} — Monthly Average Temperature (2015–2026)',
                 fontsize=14, fontweight='bold')
    ax.set_xlabel('Date')
    ax.set_ylabel('Temperature (°C)')
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    plt.tight_layout()
    plt.savefig(f'{output_dir}/{country_name.lower()}_temp_timeseries.png', dpi=150)
    plt.close()
    print("Temperature chart saved ✅")

    # ── 9. PRECIPITATION BAR CHART ───────────────────────
    monthly_precip = df.groupby(
        df['Date'].dt.to_period('M'))['PRECTOTCORR'].sum()
    monthly_precip.index = monthly_precip.index.to_timestamp()
    top3 = monthly_precip.nlargest(3)

    fig, ax = plt.subplots(figsize=(16, 5))
    colors = ['#e67e22' if m in top3.index else '#2ecc71'
              for m in monthly_precip.index]
    ax.bar(monthly_precip.index, monthly_precip.values,
           width=25, color=colors, alpha=0.85)
    for month, val in top3.items():
        ax.annotate(
            f'{month.strftime("%b %Y")}\n{val:.0f}mm',
            xy=(month, val), xytext=(0, 8),
            textcoords='offset points',
            ha='center', fontsize=8, color='darkred', fontweight='bold'
        )
    ax.set_title(f'{country_label} — Monthly Total Precipitation (2015–2026)',
                 fontsize=14, fontweight='bold')
    ax.set_xlabel('Date')
    ax.set_ylabel('Precipitation (mm)')
    plt.tight_layout()
    plt.savefig(f'{output_dir}/{country_name.lower()}_precip_bar.png', dpi=150)
    plt.close()
    print("Precipitation chart saved ✅")

    # ── 10. CORRELATION HEATMAP ──────────────────────────
    numeric_cols = ['T2M', 'T2M_MAX', 'T2M_MIN', 'T2M_RANGE',
                    'PRECTOTCORR', 'RH2M', 'WS2M', 'WS2M_MAX', 'PS', 'QV2M']
    corr = df[numeric_cols].corr()
    fig, ax = plt.subplots(figsize=(12, 9))
    mask = np.triu(np.ones_like(corr, dtype=bool))
    sns.heatmap(corr, mask=mask, annot=True, fmt='.2f',
                cmap='RdBu_r', center=0, square=True,
                linewidths=0.5, ax=ax, vmin=-1, vmax=1)
    ax.set_title(f'{country_label} — Correlation Matrix',
                 fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(f'{output_dir}/{country_name.lower()}_correlation.png', dpi=150)
    plt.close()
    print("Correlation heatmap saved ✅")

    # ── 11. SCATTER PLOTS ────────────────────────────────
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    axes[0].scatter(df['T2M'], df['RH2M'], alpha=0.2, s=5, color='steelblue')
    axes[0].set_xlabel('Mean Temperature (°C)')
    axes[0].set_ylabel('Relative Humidity (%)')
    axes[0].set_title('Temperature vs Relative Humidity')
    axes[1].scatter(df['T2M_RANGE'], df['WS2M'], alpha=0.2, s=5, color='coral')
    axes[1].set_xlabel('Daily Temp Range (°C)')
    axes[1].set_ylabel('Wind Speed (m/s)')
    axes[1].set_title('Temp Range vs Wind Speed')
    plt.suptitle(f'{country_label} — Relationship Analysis',
                 fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(f'{output_dir}/{country_name.lower()}_scatter.png', dpi=150)
    plt.close()
    print("Scatter plots saved ✅")

    # ── 12. PRECIPITATION DISTRIBUTION ──────────────────
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    precip_nonzero = df['PRECTOTCORR'][df['PRECTOTCORR'] > 0]
    axes[0].hist(precip_nonzero, bins=60, color='steelblue',
                 alpha=0.8, edgecolor='white')
    axes[0].set_yscale('log')
    axes[0].set_xlabel('Precipitation (mm/day)')
    axes[0].set_ylabel('Frequency (log scale)')
    axes[0].set_title('Daily Precipitation Distribution (log scale)')

    sample = df.sample(min(1000, len(df)), random_state=42)
    bubble_size = (sample['PRECTOTCORR'] + 1) * 8
    scatter = axes[1].scatter(
        sample['T2M'], sample['RH2M'],
        s=bubble_size, alpha=0.4,
        c=sample['PRECTOTCORR'], cmap='Blues'
    )
    axes[1].set_xlabel('Mean Temperature (°C)')
    axes[1].set_ylabel('Relative Humidity (%)')
    axes[1].set_title('Temp vs Humidity (bubble = precipitation)')
    plt.colorbar(scatter, ax=axes[1], label='Precipitation (mm)')
    plt.suptitle(f'{country_label} — Precipitation Distribution',
                 fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(f'{output_dir}/{country_name.lower()}_precip_dist.png', dpi=150)
    plt.close()
    print("Precipitation distribution saved ✅")

    print(f"\n✅ {country_label} EDA complete!\n")
    return df


# ── RUN ALL COUNTRIES ────────────────────────────────────────
if __name__ == '__main__':
    countries = {
        'kenya':    'data/kenya.csv',
        'sudan':    'data/sudan.csv',
        'tanzania': 'data/tanzania.csv',
        'nigeria':  'data/nigeria.csv',
    }

    for country, path in countries.items():
        if os.path.exists(path):
            run_eda(country, path, output_dir='notebooks')
        else:
            print(f"⚠️  File not found: {path} — skipping {country}")