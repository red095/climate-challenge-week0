import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import sys
import os

# Allow imports from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.utils import (
    load_all_countries, filter_data, monthly_avg, monthly_total,
    extreme_heat_days, consecutive_dry_days, vulnerability_summary,
    COLORS, COUNTRIES
)

# ── Page Config ──────────────────────────────────────────────
st.set_page_config(
    page_title="African Climate Dashboard",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ───────────────────────────────────────────────
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 800;
        color: #1a1a2e !important;
        margin-bottom: 0;
    }
    .sub-header {
        font-size: 1rem;
        color: #555555 !important;
        margin-top: 0;
        margin-bottom: 1.5rem;
    }
    .section-header {
        font-size: 1.3rem;
        font-weight: 700;
        color: #1a1a2e !important;
        border-bottom: 2px solid #e74c3c;
        padding-bottom: 0.3rem;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
    }
    .insight-box {
        background-color: #eaf4fb !important;
        border-left: 4px solid #3498db;
        padding: 0.8rem 1rem;
        border-radius: 4px;
        font-size: 0.92rem;
        margin-top: 0.5rem;
        color: #1a1a2e !important;
    }
    .insight-box b {
        color: #1a1a2e !important;
    }
    .metric-card {
        background-color: #f8f9fa !important;
        border-left: 4px solid #e74c3c;
        padding: 0.8rem 1rem;
        border-radius: 4px;
        margin-bottom: 0.5rem;
        color: #1a1a2e !important;
    }
    /* Force all custom div text to be dark */
    div[data-testid="stMarkdownContainer"] .insight-box * {
        color: #1a1a2e !important;
    }
</style>
""", unsafe_allow_html=True) 

# ── Load Data ────────────────────────────────────────────────
@st.cache_data
def get_data():
    return load_all_countries(data_dir='data')

df_all = get_data()

if df_all.empty:
    st.error("⚠️ No data found. Please ensure cleaned CSV files are in the `data/` folder.")
    st.stop()

# ── Sidebar ──────────────────────────────────────────────────
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/4/4f/Flag_of_Ethiopia.svg/320px-Flag_of_Ethiopia.svg.png",
             width=120)
    st.markdown("## 🌍 Dashboard Controls")
    st.markdown("---")

    # Country multi-select
    selected_countries = st.multiselect(
        "Select Countries",
        options=COUNTRIES,
        default=COUNTRIES,
        help="Choose one or more countries to display"
    )

    # Year range slider
    min_year = int(df_all['Year'].min())
    max_year = int(df_all['Year'].max())
    year_range = st.slider(
        "Year Range",
        min_value=min_year,
        max_value=max_year,
        value=(min_year, max_year),
        help="Zoom into a specific time period"
    )

    # Variable selector
    variable_options = {
        'Mean Temperature (T2M)': 'T2M',
        'Max Temperature (T2M_MAX)': 'T2M_MAX',
        'Min Temperature (T2M_MIN)': 'T2M_MIN',
        'Precipitation (PRECTOTCORR)': 'PRECTOTCORR',
        'Relative Humidity (RH2M)': 'RH2M',
        'Wind Speed (WS2M)': 'WS2M',
        'Specific Humidity (QV2M)': 'QV2M',
    }
    selected_var_label = st.selectbox(
        "Climate Variable",
        options=list(variable_options.keys()),
        index=0
    )
    selected_var = variable_options[selected_var_label]

    st.markdown("---")
    st.markdown("""
    **About this Dashboard**  
    Historical climate data from NASA POWER  
    Period: 2015 – 2026  
    Countries: Ethiopia, Kenya, Sudan, Tanzania, Nigeria  
    
    *Supporting Ethiopia's COP32 preparations*
    """)

# ── Filter data ───────────────────────────────────────────────
if not selected_countries:
    st.warning("Please select at least one country.")
    st.stop()

df = filter_data(df_all, selected_countries, year_range)

# ── Header ────────────────────────────────────────────────────
st.markdown('<p class="main-header">🌍 African Climate Trend Dashboard</p>',
            unsafe_allow_html=True)
st.markdown(
    '<p class="sub-header">Supporting Ethiopia\'s COP32 preparations — '
    'NASA POWER data, 2015–2026</p>',
    unsafe_allow_html=True)

# ── KPI Metrics Row ───────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)

avg_temp   = df['T2M'].mean()
max_temp   = df['T2M_MAX'].max()
avg_precip = df['PRECTOTCORR'].mean()
heat_days  = (df['T2M_MAX'] > 35).sum()

col1.metric("🌡️ Avg Temperature", f"{avg_temp:.1f} °C")
col2.metric("🔥 Max Recorded Temp", f"{max_temp:.1f} °C")
col3.metric("🌧️ Avg Daily Precip", f"{avg_precip:.2f} mm")
col4.metric("☀️ Extreme Heat Days", f"{heat_days:,}")

st.markdown("---")

# ════════════════════════════════════════════════════════════
# TAB LAYOUT
# ════════════════════════════════════════════════════════════
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈 Temperature Trends",
    "🌧️ Precipitation",
    "⚡ Extreme Events",
    "🔗 Correlations",
    "🏆 Vulnerability Ranking"
])

# ── TAB 1: Temperature Trends ────────────────────────────────
with tab1:
    st.markdown('<p class="section-header">Monthly Temperature Trend</p>',
                unsafe_allow_html=True)

    # Use monthly avg for selected variable if it's temperature-related
    if selected_var in ['T2M', 'T2M_MAX', 'T2M_MIN']:
        plot_var = selected_var
    else:
        plot_var = 'T2M'

    monthly = monthly_avg(df, plot_var)

    fig = px.line(
        monthly, x='YearMonth', y='Value',
        color='Country',
        color_discrete_map=COLORS,
        labels={'YearMonth': 'Date', 'Value': f'{plot_var} (°C)', 'Country': 'Country'},
        title=f'Monthly Average {plot_var} — {year_range[0]}–{year_range[1]}'
    )
    fig.update_layout(
        height=420, hovermode='x unified',
        plot_bgcolor='white', paper_bgcolor='white',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        xaxis=dict(showgrid=True, gridcolor='#f0f0f0'),
        yaxis=dict(showgrid=True, gridcolor='#f0f0f0')
    )
    fig.update_traces(line_width=2)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown('<div class="insight-box">💡 <b>Insight:</b> Sudan consistently records the '
                'highest temperatures across the study period, with mean T2M regularly exceeding '
                '30°C. Ethiopia shows a mid-range profile with a visible upward trend post-2020, '
                'consistent with WMO-documented East Africa warming patterns.</div>',
                unsafe_allow_html=True)

    # Annual mean temperature table
    st.markdown('<p class="section-header">Annual Temperature Summary</p>',
                unsafe_allow_html=True)
    temp_table = (df.groupby(['Country', 'Year'])['T2M']
                    .mean().round(2)
                    .reset_index()
                    .pivot(index='Year', columns='Country', values='T2M'))
    st.dataframe(temp_table.style.background_gradient(cmap='RdYlBu_r', axis=None),
                 use_container_width=True)

# ── TAB 2: Precipitation ─────────────────────────────────────
with tab2:
    st.markdown('<p class="section-header">Precipitation Distribution by Country</p>',
                unsafe_allow_html=True)

    col_a, col_b = st.columns(2)

    with col_a:
        # Boxplot
        p99 = df['PRECTOTCORR'].quantile(0.99)
        plot_df = df[df['PRECTOTCORR'] <= p99]
        fig_box = px.box(
            plot_df, x='Country', y='PRECTOTCORR',
            color='Country', color_discrete_map=COLORS,
            title='Daily Precipitation Distribution (capped at 99th pct)',
            labels={'PRECTOTCORR': 'Precipitation (mm/day)'}
        )
        fig_box.update_layout(height=400, showlegend=False,
                               plot_bgcolor='white', paper_bgcolor='white')
        st.plotly_chart(fig_box, use_container_width=True)

    with col_b:
        # Monthly total bar
        monthly_p = monthly_total(df, 'PRECTOTCORR')
        fig_bar = px.bar(
            monthly_p, x='YearMonth', y='Value',
            color='Country', color_discrete_map=COLORS,
            barmode='group',
            title='Monthly Total Precipitation',
            labels={'YearMonth': 'Date', 'Value': 'Total Precipitation (mm)'}
        )
        fig_bar.update_layout(height=400, plot_bgcolor='white',
                               paper_bgcolor='white',
                               legend=dict(orientation='h', y=1.1))
        st.plotly_chart(fig_bar, use_container_width=True)

    # Precipitation summary table
    st.markdown('<p class="section-header">Precipitation Summary Statistics</p>',
                unsafe_allow_html=True)
    precip_stats = df.groupby('Country')['PRECTOTCORR'].agg(
        Mean=lambda x: round(x.mean(), 3),
        Median=lambda x: round(x.median(), 3),
        Std_Dev=lambda x: round(x.std(), 3),
        Max=lambda x: round(x.max(), 2),
        Rainy_Days=lambda x: int((x >= 1).sum())
    ).reset_index()
    precip_stats.columns = ['Country', 'Mean (mm/day)', 'Median',
                             'Std Dev', 'Max (mm/day)', 'Rainy Days (≥1mm)']
    st.dataframe(precip_stats, use_container_width=True, hide_index=True)

    st.markdown('<div class="insight-box">💡 <b>Insight:</b> Nigeria and Tanzania show the '
                'highest precipitation variability, with extreme wet seasons followed by '
                'prolonged dry periods. Sudan records the lowest median precipitation, '
                'reflecting its predominantly arid climate.</div>',
                unsafe_allow_html=True)

# ── TAB 3: Extreme Events ────────────────────────────────────
with tab3:
    st.markdown('<p class="section-header">Extreme Climate Events Analysis</p>',
                unsafe_allow_html=True)

    col_c, col_d = st.columns(2)

    with col_c:
        heat = extreme_heat_days(df)
        heat_avg = heat.groupby('Country')['Extreme_Heat_Days'].mean().round(1).reset_index()
        heat_avg.columns = ['Country', 'Avg Annual Heat Days']
        heat_avg = heat_avg.sort_values('Avg Annual Heat Days', ascending=False)

        fig_heat = px.bar(
            heat_avg, x='Country', y='Avg Annual Heat Days',
            color='Country', color_discrete_map=COLORS,
            title='Avg Annual Extreme Heat Days (T2M_MAX > 35°C)',
            text='Avg Annual Heat Days'
        )
        fig_heat.update_traces(textposition='outside')
        fig_heat.update_layout(height=400, showlegend=False,
                                plot_bgcolor='white', paper_bgcolor='white')
        st.plotly_chart(fig_heat, use_container_width=True)

    with col_d:
        with st.spinner("Computing dry day streaks..."):
            dry = consecutive_dry_days(df)
        dry_avg = dry.groupby('Country')['Max_Dry_Streak'].mean().round(1).reset_index()
        dry_avg.columns = ['Country', 'Avg Max Dry Streak (days)']
        dry_avg = dry_avg.sort_values('Avg Max Dry Streak (days)', ascending=False)

        fig_dry = px.bar(
            dry_avg, x='Country', y='Avg Max Dry Streak (days)',
            color='Country', color_discrete_map=COLORS,
            title='Avg Annual Maximum Consecutive Dry Days',
            text='Avg Max Dry Streak (days)'
        )
        fig_dry.update_traces(textposition='outside')
        fig_dry.update_layout(height=400, showlegend=False,
                               plot_bgcolor='white', paper_bgcolor='white')
        st.plotly_chart(fig_dry, use_container_width=True)

    # Year-by-year heat days line chart
    st.markdown('<p class="section-header">Extreme Heat Days Over Time</p>',
                unsafe_allow_html=True)
    heat_all = extreme_heat_days(df_all)
    heat_filtered = heat_all[
        (heat_all['Country'].isin(selected_countries)) &
        (heat_all['Year'] >= year_range[0]) &
        (heat_all['Year'] <= year_range[1])
    ]
    fig_heat_line = px.line(
        heat_filtered, x='Year', y='Extreme_Heat_Days',
        color='Country', color_discrete_map=COLORS,
        markers=True,
        title='Annual Extreme Heat Days per Country',
        labels={'Extreme_Heat_Days': 'Days with T2M_MAX > 35°C'}
    )
    fig_heat_line.update_layout(height=380, plot_bgcolor='white',
                                 paper_bgcolor='white')
    st.plotly_chart(fig_heat_line, use_container_width=True)

    st.markdown('<div class="insight-box">💡 <b>Insight:</b> Sudan experiences over 200 extreme '
                'heat days per year on average — more than half the calendar year. Combined with '
                'the longest dry streaks, this represents compounding climate stress that '
                'degrades livelihoods and drives displacement, making it the strongest case '
                'for loss-and-damage financing at COP32.</div>',
                unsafe_allow_html=True)

# ── TAB 4: Correlations ───────────────────────────────────────
with tab4:
    st.markdown('<p class="section-header">Variable Correlations</p>',
                unsafe_allow_html=True)

    selected_country_corr = st.selectbox(
        "Select country for correlation analysis",
        options=selected_countries,
        index=0
    )

    df_corr = df[df['Country'] == selected_country_corr]
    numeric_cols = ['T2M', 'T2M_MAX', 'T2M_MIN', 'T2M_RANGE',
                    'PRECTOTCORR', 'RH2M', 'WS2M', 'WS2M_MAX', 'PS', 'QV2M']
    corr = df_corr[numeric_cols].corr().round(2)

    fig_corr = px.imshow(
        corr, text_auto=True,
        color_continuous_scale='RdBu_r',
        zmin=-1, zmax=1,
        title=f'Correlation Matrix — {selected_country_corr}',
        aspect='auto'
    )
    fig_corr.update_layout(height=520, plot_bgcolor='white', paper_bgcolor='white')
    st.plotly_chart(fig_corr, use_container_width=True)

    col_e, col_f = st.columns(2)
    with col_e:
        fig_s1 = px.scatter(
            df_corr.sample(min(2000, len(df_corr)), random_state=42),
            x='T2M', y='RH2M', opacity=0.4,
            color_discrete_sequence=[COLORS.get(selected_country_corr, '#e74c3c')],
            title='Temperature vs Relative Humidity',
            labels={'T2M': 'Mean Temp (°C)', 'RH2M': 'Relative Humidity (%)'}
        )
        fig_s1.update_layout(height=380, plot_bgcolor='white', paper_bgcolor='white')
        st.plotly_chart(fig_s1, use_container_width=True)

    with col_f:
        fig_s2 = px.scatter(
            df_corr.sample(min(2000, len(df_corr)), random_state=42),
            x='T2M_RANGE', y='WS2M', opacity=0.4,
            color_discrete_sequence=[COLORS.get(selected_country_corr, '#e74c3c')],
            title='Temp Range vs Wind Speed',
            labels={'T2M_RANGE': 'Daily Temp Range (°C)', 'WS2M': 'Wind Speed (m/s)'}
        )
        fig_s2.update_layout(height=380, plot_bgcolor='white', paper_bgcolor='white')
        st.plotly_chart(fig_s2, use_container_width=True)

# ── TAB 5: Vulnerability Ranking ──────────────────────────────
with tab5:
    st.markdown('<p class="section-header">Climate Vulnerability Ranking</p>',
                unsafe_allow_html=True)

    vuln = vulnerability_summary(df_all)

    # Ranking bar chart
    fig_vuln = px.bar(
        vuln.sort_values('Rank'),
        x='Country', y='Vuln_Score',
        color='Country', color_discrete_map=COLORS,
        text='Rank',
        title='Climate Vulnerability Score (lower = more vulnerable)',
        labels={'Vuln_Score': 'Composite Vulnerability Score'}
    )
    fig_vuln.update_traces(texttemplate='Rank %{text}', textposition='outside')
    fig_vuln.update_layout(height=420, showlegend=False,
                            plot_bgcolor='white', paper_bgcolor='white')
    st.plotly_chart(fig_vuln, use_container_width=True)

    # Summary table
    st.markdown('<p class="section-header">Full Vulnerability Summary Table</p>',
                unsafe_allow_html=True)
    display_cols = ['Rank', 'Country', 'Mean_Temp', 'Temp_Std',
                    'Mean_Precip', 'Precip_Std', 'Total_Heat_Days']
    rename_map = {
        'Mean_Temp': 'Avg Temp (°C)',
        'Temp_Std': 'Temp Std Dev',
        'Mean_Precip': 'Avg Precip (mm)',
        'Precip_Std': 'Precip Std Dev',
        'Total_Heat_Days': 'Total Heat Days'
    }
    st.dataframe(
        vuln[display_cols].rename(columns=rename_map),
        use_container_width=True, hide_index=True
    )

    # COP32 Insights
    st.markdown('<p class="section-header">COP32 Policy Insights</p>',
                unsafe_allow_html=True)
    insights = [
        ("🌡️ Fastest Warming",
         "Sudan shows the steepest temperature profile. Sustained warming threatens "
         "agricultural viability across the Sahel and demands urgent emissions "
         "accountability from major polluters."),
        ("🌧️ Most Unstable Precipitation",
         "Nigeria and Tanzania exhibit the highest precipitation standard deviation, "
         "reflecting extreme swings between flood and drought years that directly "
         "undermine food security."),
        ("☀️ Heat & Drought Stress",
         "Sudan records the most extreme heat days combined with the longest dry "
         "streaks — compounding climate stress that degrades livelihoods and forces "
         "displacement, creating the strongest case for loss-and-damage compensation."),
        ("🇪🇹 Ethiopia's Climate Profile",
         "Ethiopia sits in a mid-range vulnerability position, yet its exposure to "
         "erratic rainfall directly threatens the Blue Nile basin and the livelihoods "
         "of 85% of its population dependent on rain-fed agriculture."),
        ("💰 Priority Finance Case",
         "The data strongly supports championing Sudan for priority climate finance at "
         "COP32. Its combination of extreme heat, prolonged drought, and lowest "
         "precipitation makes it the most urgent case on the continent."),
    ]
    for title, text in insights:
        st.markdown(
            f'<div class="insight-box"><b>{title}:</b> {text}</div>',
            unsafe_allow_html=True)
        st.markdown("")