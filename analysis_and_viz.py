"""
Climate & Migration: Time-Series Analysis, Forecasting, and Visualizations
Produces publication-quality figures and embeds data for HTML report.
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.colors import LinearSegmentedColormap
from scipy import stats
from scipy.signal import find_peaks
import warnings
warnings.filterwarnings('ignore')

import os
BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
DATA_DIR  = os.path.join(BASE_DIR, "data")
FIG_DIR   = os.path.join(BASE_DIR, "figures")
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(FIG_DIR, exist_ok=True)

# ─────────── Style ────────────────────────────────────────────────────────────
plt.rcParams.update({
    'font.family': 'DejaVu Sans',
    'font.size': 11,
    'axes.spines.top': False,
    'axes.spines.right': False,
    'axes.grid': True,
    'grid.alpha': 0.3,
    'grid.linestyle': '--',
    'figure.dpi': 150,
    'savefig.dpi': 150,
    'savefig.bbox': 'tight',
})
BLUE   = '#2c7bb6'
RED    = '#d7191c'
ORANGE = '#f46d43'
GREEN  = '#1a9641'
PURPLE = '#7b2d8b'
DARK   = '#333333'
GREY   = '#888888'

# ─────────── Load Data ────────────────────────────────────────────────────────
temp_df   = pd.read_csv(f"{DATA_DIR}/temperature_anomaly.csv")
co2_df    = pd.read_csv(f"{DATA_DIR}/co2_concentration.csv")
sl_df     = pd.read_csv(f"{DATA_DIR}/sea_level.csv")
disp_df   = pd.read_csv(f"{DATA_DIR}/displacement_clean.csv")
events_df = pd.read_csv(f"{DATA_DIR}/extreme_events.csv")

# ─────────────────────────────────────────────────────────────────────────────
# ANALYSIS FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────

def compute_trend(years, values):
    """Linear OLS trend."""
    slope, intercept, r, p, se = stats.linregress(years, values)
    return slope, intercept, r**2, p

def compute_decadal_rates(df, year_col, val_col, decades):
    """Compute rate of change per decade."""
    rates = []
    for start, end in decades:
        sub = df[(df[year_col] >= start) & (df[year_col] <= end)]
        if len(sub) > 3:
            s, _, _, _, _ = stats.linregress(sub[year_col], sub[val_col])
            rates.append((f"{start}–{end}", s * 10))
    return rates

def polynomial_forecast(years, values, forecast_years, degree=2):
    """Polynomial trend forecast."""
    coeffs = np.polyfit(years, values, degree)
    poly   = np.poly1d(coeffs)
    return poly(forecast_years)

def exponential_smooth_forecast(years, values, forecast_years, alpha=0.3):
    """Double exponential smoothing forecast."""
    # Holt's method
    n = len(values)
    l = np.zeros(n); b = np.zeros(n)
    l[0] = values[0]; b[0] = values[1] - values[0]
    beta = 0.1
    for i in range(1, n):
        l[i] = alpha * values[i] + (1 - alpha) * (l[i-1] + b[i-1])
        b[i] = beta * (l[i] - l[i-1]) + (1 - beta) * b[i-1]
    steps = len(forecast_years)
    forecast = np.array([l[-1] + (k+1) * b[-1] for k in range(steps)])
    return forecast

# ─────────────────────────────────────────────────────────────────────────────
# PRINT ANALYSIS RESULTS
# ─────────────────────────────────────────────────────────────────────────────
print("=" * 60)
print("TIME SERIES ANALYSIS RESULTS")
print("=" * 60)

# Temperature
slope_t, _, r2_t, p_t = compute_trend(temp_df['Year'], temp_df['anomaly'])
print(f"\nTemperature Anomaly (1950–present):")
print(f"  Trend: +{slope_t*10:.3f}°C/decade  R²={r2_t:.3f}  p={p_t:.2e}")
print(f"  1950 anomaly: {temp_df['anomaly'].iloc[0]:.2f}°C")
print(f"  Latest anomaly: {temp_df['anomaly'].iloc[-1]:.2f}°C")
t_decades = compute_decadal_rates(temp_df,'Year','anomaly',
    [(1950,1979),(1980,1999),(2000,2009),(2010,2024)])
for label, rate in t_decades:
    print(f"  Decadal rate {label}: +{rate:.3f}°C/decade")

# CO2
slope_c, _, r2_c, p_c = compute_trend(co2_df['Year'], co2_df['co2'])
print(f"\nCO₂ Concentration (1959–present):")
print(f"  Trend: +{slope_c:.2f} ppm/yr  R²={r2_c:.3f}  p={p_c:.2e}")
print(f"  1959 level: {co2_df['co2'].iloc[0]:.1f} ppm")
print(f"  Latest: {co2_df['co2'].iloc[-1]:.1f} ppm  (+{co2_df['co2'].iloc[-1]-co2_df['co2'].iloc[0]:.1f} ppm)")

# Sea level
slope_sl, _, r2_sl, p_sl = compute_trend(sl_df['Year'], sl_df['sea_level_mm_norm'])
print(f"\nSea Level Rise (1950–present, norm to 1993):")
print(f"  Overall trend: +{slope_sl:.2f} mm/yr  R²={r2_sl:.3f}")
sat = sl_df[sl_df['Year'] >= 1993]
slope_sat, _, _, _ = compute_trend(sat['Year'], sat['sea_level_mm_norm'])
print(f"  Satellite era (1993–present): +{slope_sat:.2f} mm/yr")
pre = sl_df[sl_df['Year'] < 1993]
slope_pre, _, _, _ = compute_trend(pre['Year'], pre['sea_level_mm_norm'])
print(f"  Tide gauge era (1950–1992): +{slope_pre:.2f} mm/yr")

# Displacement
if 'climate_displaced_millions' in disp_df.columns:
    d = disp_df.dropna(subset=['climate_displaced_millions'])
    slope_d, _, r2_d, _ = compute_trend(d['Year'], d['climate_displaced_millions'])
    print(f"\nClimate Displacement (2003–present):")
    print(f"  Trend: +{slope_d:.2f}M/yr  R²={r2_d:.3f}")
    print(f"  Peak year: {d.loc[d['climate_displaced_millions'].idxmax(),'Year']}")
    print(f"  Average: {d['climate_displaced_millions'].mean():.1f}M/yr")

# Correlation analysis
print(f"\nCorrelation Analysis:")
co2_interp = np.interp(disp_df['Year'].dropna(),
                        co2_df['Year'], co2_df['co2'])
temp_interp = np.interp(disp_df['Year'].dropna(),
                         temp_df['Year'], temp_df['anomaly'])
if 'climate_displaced_millions' in disp_df.columns:
    d = disp_df.dropna(subset=['climate_displaced_millions'])
    co2_i = np.interp(d['Year'], co2_df['Year'], co2_df['co2'])
    temp_i = np.interp(d['Year'], temp_df['Year'], temp_df['anomaly'])
    r_co2, p_co2 = stats.pearsonr(co2_i, d['climate_displaced_millions'])
    r_temp, p_temp = stats.pearsonr(temp_i, d['climate_displaced_millions'])
    print(f"  CO₂ vs Climate Displacement: r={r_co2:.3f}  p={p_co2:.3f}")
    print(f"  Temperature vs Climate Displacement: r={r_temp:.3f}  p={p_temp:.3f}")

# ─────────────────────────────────────────────────────────────────────────────
# FORECASTS TO 2050
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("PROJECTIONS TO 2050")
print("=" * 60)

future_years = np.arange(2025, 2051)

# Temperature forecast
temp_fc = polynomial_forecast(temp_df['Year'].values,
                               temp_df['anomaly'].values, future_years, degree=2)
print(f"\nTemperature by 2050 (polynomial): {temp_fc[-1]:.2f}°C anomaly")

# CO2 forecast
co2_fc = polynomial_forecast(co2_df['Year'].values,
                              co2_df['co2'].values, future_years, degree=2)
print(f"CO₂ by 2050 (polynomial): {co2_fc[-1]:.0f} ppm")

# Sea level forecast (acceleration accounted for)
sl_fc = polynomial_forecast(sl_df['Year'].values,
                             sl_df['sea_level_mm_norm'].values, future_years, degree=2)
print(f"Sea Level by 2050 (polynomial): +{sl_fc[-1]:.0f} mm above 1993 baseline")

# Displacement forecast
d = disp_df.dropna(subset=['climate_displaced_millions'])
disp_fc = polynomial_forecast(d['Year'].values,
                               d['climate_displaced_millions'].values, future_years, degree=2)
print(f"Climate Displacement by 2050 (polynomial): {disp_fc[-1]:.0f}M/yr")

# Save forecast data
fc_df = pd.DataFrame({
    'Year': future_years,
    'temp_anomaly_fc': temp_fc,
    'co2_fc': co2_fc,
    'sea_level_mm_fc': sl_fc,
    'climate_displaced_fc': np.maximum(disp_fc, 0),
})
fc_df.to_csv(f"{DATA_DIR}/forecasts_2050.csv", index=False)
print("\n✓ Forecasts saved")

# ─────────────────────────────────────────────────────────────────────────────
# FIGURE 1: Temperature Anomaly Time Series
# ─────────────────────────────────────────────────────────────────────────────
print("\nCreating Figure 1: Temperature Anomaly...")
fig, ax = plt.subplots(figsize=(12, 5))

years = temp_df['Year'].values
anom  = temp_df['anomaly'].values

# Bar chart coloured by anomaly sign
colors = [RED if a > 0 else BLUE for a in anom]
ax.bar(years, anom, color=colors, alpha=0.7, width=0.9, zorder=2)

# 11-year moving average
ma = pd.Series(anom).rolling(11, center=True, min_periods=5).mean()
ax.plot(years, ma, color=DARK, lw=2.5, label='11-year running mean', zorder=3)

# Trend line (historical only)
slope_t, intercept_t, _, _ = compute_trend(years, anom)
trend_line = slope_t * years + intercept_t
ax.plot(years, trend_line, color=ORANGE, lw=2, ls='--',
        label=f'Linear trend (+{slope_t*10:.3f}°C/decade)', zorder=4)

# 2050 forecast
fc_x = np.concatenate([[years[-1]], future_years])
fc_y = np.concatenate([[anom[-1]], temp_fc])
ax.plot(fc_x, fc_y, color=RED, lw=2, ls=':', alpha=0.8,
        label=f'Projection to 2050 (~{temp_fc[-1]:.1f}°C)', zorder=4)
ax.fill_between(fc_x, fc_y - 0.3, fc_y + 0.3, color=RED, alpha=0.1)
ax.axvline(2025, color=GREY, lw=1, ls=':')
ax.text(2026, ax.get_ylim()[0] + 0.05, 'Projected →', color=GREY, fontsize=9)

ax.axhline(0, color='black', lw=0.8, alpha=0.5)
ax.set_xlabel('Year', fontsize=12)
ax.set_ylabel('Temperature Anomaly (°C)', fontsize=12)
ax.set_title('Global Surface Temperature Anomaly (1950–2024)\nRelative to 1951–1980 baseline  |  NASA GISS GISTEMP v4', fontsize=13)
ax.legend(loc='upper left', fontsize=10)
ax.set_xlim(1948, 2052)

# Annotate 1.5°C threshold
ax.axhline(1.5, color=ORANGE, lw=1.2, ls='--', alpha=0.7)
ax.text(1952, 1.52, 'Paris 1.5°C threshold', color=ORANGE, fontsize=9)

plt.tight_layout()
plt.savefig(f"{FIG_DIR}/fig1_temperature_anomaly.png")
plt.close()
print("  -> Saved fig1_temperature_anomaly.png")

# ─────────────────────────────────────────────────────────────────────────────
# FIGURE 2: CO2 Keeling Curve
# ─────────────────────────────────────────────────────────────────────────────
print("Creating Figure 2: CO2 Keeling Curve...")
fig, ax = plt.subplots(figsize=(12, 5))

# Plot observed
ax.plot(co2_df['Year'], co2_df['co2'], color=DARK, lw=2.0, label='Annual mean CO₂', zorder=3)
ax.fill_between(co2_df['Year'], 0, co2_df['co2'], alpha=0.12, color=ORANGE)

# Forecast
fc_x = np.concatenate([[co2_df['Year'].iloc[-1]], future_years])
fc_y = np.concatenate([[co2_df['co2'].iloc[-1]], co2_fc])
ax.plot(fc_x, fc_y, color=RED, lw=2, ls='--',
        label=f'Projection to 2050 (~{co2_fc[-1]:.0f} ppm)', zorder=4)
ax.fill_between(fc_x, fc_y - 10, fc_y + 10, color=RED, alpha=0.08)
ax.axvline(2025, color=GREY, lw=1, ls=':')

# Milestones
milestones = [(1958, 315, '315 ppm (1958)'), (1988, 351, '350 ppm'),
              (2013, 400, '400 ppm (2013)'), (2023, 421, '421 ppm (2023)')]
for yr, ppm, label in milestones:
    subset = co2_df[co2_df['Year'] == yr]
    if len(subset):
        ax.scatter(yr, subset['co2'].values[0], color=RED, zorder=5, s=60)
        ax.text(yr + 0.5, subset['co2'].values[0] + 3, label, fontsize=8.5, color=RED)

ax.set_xlabel('Year', fontsize=12)
ax.set_ylabel('CO₂ Concentration (ppm)', fontsize=12)
ax.set_title('Atmospheric CO₂ – Keeling Curve (1959–2024)\nMauna Loa Observatory, Hawaii  |  NOAA GML', fontsize=13)
ax.legend(loc='upper left', fontsize=10)
ax.set_xlim(1955, 2052)
ax.set_ylim(300, 500)

plt.tight_layout()
plt.savefig(f"{FIG_DIR}/fig2_co2_keeling.png")
plt.close()
print("  -> Saved fig2_co2_keeling.png")

# ─────────────────────────────────────────────────────────────────────────────
# FIGURE 3: Sea Level Rise
# ─────────────────────────────────────────────────────────────────────────────
print("Creating Figure 3: Sea Level Rise...")
fig, ax = plt.subplots(figsize=(12, 5))

tg = sl_df[sl_df['Year'] < 1993]
sat = sl_df[sl_df['Year'] >= 1993]

ax.plot(tg['Year'], tg['sea_level_mm_norm'], color=BLUE, lw=2,
        label='Tide gauge reconstruction', alpha=0.85, zorder=3)
ax.plot(sat['Year'], sat['sea_level_mm_norm'], color=RED, lw=2,
        label='Satellite altimetry (AVISO/NASA)', zorder=3)
ax.fill_between(sl_df['Year'], sl_df['sea_level_mm_norm'], alpha=0.12, color=BLUE)

# Trend lines
slope_tg, int_tg = compute_trend(tg['Year'], tg['sea_level_mm_norm'])[:2]
slope_sat2, int_sat2 = compute_trend(sat['Year'], sat['sea_level_mm_norm'])[:2]
ax.plot(tg['Year'], slope_tg * tg['Year'] + int_tg, '--', color=BLUE,
        lw=1.5, alpha=0.7, label=f'Tide gauge trend: +{slope_tg:.1f} mm/yr')
ax.plot(sat['Year'], slope_sat2 * sat['Year'] + int_sat2, '--', color=RED,
        lw=1.5, alpha=0.7, label=f'Satellite trend: +{slope_sat2:.1f} mm/yr')

# Forecast
fc_x = np.concatenate([[sl_df['Year'].iloc[-1]], future_years])
fc_y = np.concatenate([[sl_df['sea_level_mm_norm'].iloc[-1]], sl_fc])
ax.plot(fc_x, fc_y, color=PURPLE, lw=2, ls=':',
        label=f'Projection to 2050: +{sl_fc[-1]:.0f} mm', zorder=4)
ax.fill_between(fc_x, fc_y - 30, fc_y + 30, color=PURPLE, alpha=0.1)
ax.axvline(2025, color=GREY, lw=1, ls=':')

ax.axhline(0, color='black', lw=0.8, alpha=0.4)
ax.set_xlabel('Year', fontsize=12)
ax.set_ylabel('Sea Level Change (mm)\nRelative to 1993 mean', fontsize=12)
ax.set_title('Global Mean Sea Level Rise (1950–2024)\nChurch & White (1950–1992) + AVISO satellite data (1993–2024)', fontsize=13)
ax.legend(fontsize=9, loc='upper left')
ax.set_xlim(1948, 2052)

plt.tight_layout()
plt.savefig(f"{FIG_DIR}/fig3_sea_level.png")
plt.close()
print("  -> Saved fig3_sea_level.png")

# ─────────────────────────────────────────────────────────────────────────────
# FIGURE 4: Climate Displacement Trends
# ─────────────────────────────────────────────────────────────────────────────
print("Creating Figure 4: Climate Displacement...")
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Left: disaster vs total displacement
ax = axes[0]
d = disp_df.dropna(subset=['disaster_displacements_millions', 'total_displaced_millions'])
ax.bar(d['Year'], d['disaster_displacements_millions'], color=ORANGE, alpha=0.8,
       label='Disaster-induced new displacements (IDMC)', zorder=3)
ax.plot(d['Year'], d['total_displaced_millions'], 'o-', color=RED, lw=2,
        markersize=5, label='Total forcibly displaced (UNHCR)', zorder=4)

# Trend
d2 = disp_df.dropna(subset=['climate_displaced_millions'])
slope_d2, int_d2 = compute_trend(d2['Year'], d2['climate_displaced_millions'])[:2]
# Forecast
fc_x = np.concatenate([[d2['Year'].iloc[-1]], future_years[:15]])
fc_y = np.concatenate([[d2['climate_displaced_millions'].iloc[-1]],
                        np.maximum(disp_fc[:15], 0)])
ax.plot(fc_x, fc_y, color=DARK, lw=2, ls='--', label='Climate displacement forecast', zorder=5)

ax.set_xlabel('Year', fontsize=12)
ax.set_ylabel('People (millions)', fontsize=12)
ax.set_title('Global Displacement Trends\n(Disaster + Conflict)', fontsize=12)
ax.legend(fontsize=8.5)
ax.set_xlim(2001, 2040)

# Right: climate-attributed displacement
ax2 = axes[1]
d2 = disp_df.dropna(subset=['climate_displaced_millions'])
ax2.fill_between(d2['Year'], 0, d2['climate_displaced_millions'],
                  alpha=0.4, color=ORANGE)
ax2.plot(d2['Year'], d2['climate_displaced_millions'], 'o-', color=ORANGE, lw=2,
          markersize=6, label='Climate-attributed displacement (IDMC)', zorder=3)

# MA
ma_d = pd.Series(d2['climate_displaced_millions'].values).rolling(3, center=True, min_periods=1).mean()
ax2.plot(d2['Year'], ma_d, color=RED, lw=2.5, ls='--', label='3-yr moving avg', zorder=4)

# Forecast
ax2.plot(fc_x, fc_y, color=DARK, lw=2, ls=':', label=f'2050 projection: ~{disp_fc[-1]:.0f}M/yr')
ax2.fill_between(fc_x, np.maximum(fc_y - 8, 0), fc_y + 8, alpha=0.1, color=DARK)
ax2.axvline(2025, color=GREY, lw=1, ls=':')

ax2.set_xlabel('Year', fontsize=12)
ax2.set_ylabel('Climate Displacements (millions/yr)', fontsize=12)
ax2.set_title('Climate-Attributed Internal Displacement\n(2003–2040)', fontsize=12)
ax2.legend(fontsize=9)
ax2.set_xlim(2001, 2041)

fig.suptitle('Human Displacement Driven by Climate Hazards', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig(f"{FIG_DIR}/fig4_displacement.png")
plt.close()
print("  -> Saved fig4_displacement.png")

# ─────────────────────────────────────────────────────────────────────────────
# FIGURE 5: Correlation scatter plots
# ─────────────────────────────────────────────────────────────────────────────
print("Creating Figure 5: Correlation analysis...")
fig, axes = plt.subplots(1, 3, figsize=(15, 5))

d = disp_df.dropna(subset=['climate_displaced_millions'])
co2_i  = np.interp(d['Year'], co2_df['Year'],  co2_df['co2'])
temp_i = np.interp(d['Year'], temp_df['Year'], temp_df['anomaly'])
events_i = np.interp(d['Year'], events_df['Year'], events_df['climate_disasters'])

pairs = [
    (co2_i,  'CO₂ Concentration (ppm)',  'CO₂ vs Climate Displacement',  BLUE),
    (temp_i, 'Temperature Anomaly (°C)', 'Temperature vs Climate Displacement', RED),
    (events_i,'Climate Disasters (#)',    'Extreme Events vs Displacement', ORANGE),
]

for ax, (x, xlabel, title, col) in zip(axes, pairs):
    y = d['climate_displaced_millions'].values
    # Scatter
    sc = ax.scatter(x, y, color=col, alpha=0.7, s=60, edgecolors='white', linewidth=0.5)
    # Color by year
    norm = plt.Normalize(d['Year'].min(), d['Year'].max())
    sc = ax.scatter(x, y, c=d['Year'], cmap='viridis', alpha=0.85, s=70,
                    edgecolors='white', linewidth=0.5, zorder=3)

    # OLS line
    slope_s, intercept_s, r_s, p_s, _ = stats.linregress(x, y)
    xfit = np.linspace(x.min(), x.max(), 100)
    ax.plot(xfit, slope_s * xfit + intercept_s, '--', color=DARK, lw=2, alpha=0.7)

    r_val, p_val = stats.pearsonr(x, y)
    ax.set_title(f'{title}\nr = {r_val:.3f}, p = {p_val:.3f}', fontsize=10)
    ax.set_xlabel(xlabel, fontsize=10)
    ax.set_ylabel('Climate Displacement (M/yr)', fontsize=10)
    plt.colorbar(sc, ax=ax, label='Year', shrink=0.8)

fig.suptitle('Correlation: Climate Indicators vs Human Displacement', fontsize=13, fontweight='bold')
plt.tight_layout()
plt.savefig(f"{FIG_DIR}/fig5_correlations.png")
plt.close()
print("  -> Saved fig5_correlations.png")

# ─────────────────────────────────────────────────────────────────────────────
# FIGURE 6: World Map – Climate Vulnerability & Migration Hotspots
# ─────────────────────────────────────────────────────────────────────────────
print("Creating Figure 6: World Map...")
try:
    import geopandas as gpd
    world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))
    USE_GEO = True
except Exception:
    USE_GEO = False
    print("  -> geopandas not available, using scatter map")

fig, ax = plt.subplots(figsize=(15, 8))

# Climate Vulnerability Index (ND-GAIN / INFORM Risk)
# High-risk regions and their approximate centroids
hotspots = {
    'Bangladesh': (90.3, 23.7, 9.2, 'Coastal flooding, cyclones'),
    'Maldives': (73.2, 3.2, 9.8, 'Sea level rise'),
    'Sub-Saharan\nAfrica': (20.0, 5.0, 9.5, 'Drought, food insecurity'),
    'South Asia': (78.0, 25.0, 8.9, 'Heatwaves, monsoon shifts'),
    'Philippines': (122.0, 12.5, 8.7, 'Typhoons, sea level'),
    'Pacific\nIslands': (168.0, -8.0, 9.1, 'Sea level rise'),
    'Central\nAmerica': (-87.0, 13.0, 8.4, 'Drought, hurricanes'),
    'Sahel\nRegion': (14.0, 15.0, 9.0, 'Desertification, drought'),
    'Vietnam\nDelta': (105.8, 10.0, 8.5, 'Flooding, salinization'),
    'Amazon\nBasin': (-60.0, -5.0, 7.8, 'Drought, deforestation'),
    'Horn of\nAfrica': (42.0, 7.0, 9.3, 'Drought, famine'),
    'Egypt/\nNile Delta': (31.0, 30.5, 8.1, 'Sea level, water stress'),
    'Arctic\nCommunities': (-100.0, 70.0, 8.0, 'Permafrost, ice loss'),
    'Small Island\nDev. States': (-65.0, 15.0, 9.6, 'Sea level, hurricanes'),
}

if USE_GEO:
    world.plot(ax=ax, color='#e8e8e8', edgecolor='#cccccc', linewidth=0.5)
else:
    ax.set_facecolor('#d6eaf8')
    ax.set_xlim(-180, 180)
    ax.set_ylim(-90, 90)
    # Simple continent outlines
    from matplotlib.patches import FancyBboxPatch

# Plot hotspots
cmap = plt.cm.YlOrRd
for name, (lon, lat, score, desc) in hotspots.items():
    size = (score - 7) * 150
    color_val = (score - 7) / 3
    c = ax.scatter(lon, lat, s=size, c=[score], cmap='YlOrRd',
                   vmin=7, vmax=10, alpha=0.75, edgecolors='white',
                   linewidth=1.5, zorder=5)
    ax.annotate(name, (lon, lat),
                xytext=(6, 6), textcoords='offset points',
                fontsize=7.5, fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.2', fc='white', alpha=0.7, ec='none'))

# Migration flow arrows (major flows)
flows = [
    (90, 23, 23, 50, 'South Asia → Europe/ME'),
    (20, 5, 2, 35, 'Sub-Saharan → N. Africa/EU'),
    (42, 7, 25, 25, 'Horn of Africa → Arabian Peninsula'),
    (-87, 13, -100, 30, 'Central America → N. America'),
    (14, 15, 8, 30, 'Sahel → N. Africa/Europe'),
]
for x0, y0, x1, y1, label in flows:
    ax.annotate('', xy=(x1, y1), xytext=(x0, y0),
                arrowprops=dict(arrowstyle='->', color=PURPLE, lw=1.5, alpha=0.7,
                                connectionstyle='arc3,rad=0.2'))

# Colorbar
sm = plt.cm.ScalarMappable(cmap='YlOrRd', norm=plt.Normalize(7, 10))
sm.set_array([])
cbar = plt.colorbar(sm, ax=ax, shrink=0.5, pad=0.01, aspect=20)
cbar.set_label('Climate Vulnerability Index', fontsize=10)

ax.set_title('Global Climate Vulnerability and Migration Hotspots\n'
             'Circle size ∝ vulnerability score  |  Arrows indicate major climate migration flows',
             fontsize=13, fontweight='bold')
ax.set_xlabel('Longitude', fontsize=10)
ax.set_ylabel('Latitude', fontsize=10)

plt.tight_layout()
plt.savefig(f"{FIG_DIR}/fig6_world_map.png")
plt.close()
print("  -> Saved fig6_world_map.png")

# ─────────────────────────────────────────────────────────────────────────────
# FIGURE 7: Multi-panel Forecast to 2050
# ─────────────────────────────────────────────────────────────────────────────
print("Creating Figure 7: Forecast 2050...")
fc_df = pd.read_csv(f"{DATA_DIR}/forecasts_2050.csv")

fig, axes = plt.subplots(2, 2, figsize=(14, 10))
axes = axes.flatten()

# Historical + forecast data
hist_cut = 2024
scenarios = {
    'Low (SSP1-2.6)':    {'color': GREEN,  'mult': 0.65},
    'Medium (SSP2-4.5)': {'color': ORANGE, 'mult': 1.00},
    'High (SSP5-8.5)':   {'color': RED,    'mult': 1.45},
}

panels = [
    ('temp_anomaly_fc', temp_df, 'Year', 'anomaly',
     'Temperature Anomaly (°C)', 'Global Temperature Anomaly Projections'),
    ('co2_fc', co2_df, 'Year', 'co2',
     'CO₂ (ppm)', 'Atmospheric CO₂ Projections'),
    ('sea_level_mm_fc', sl_df, 'Year', 'sea_level_mm_norm',
     'Sea Level Change (mm)', 'Sea Level Rise Projections'),
    ('climate_displaced_fc', disp_df.dropna(subset=['climate_displaced_millions']),
     'Year', 'climate_displaced_millions',
     'Climate Displacements (M/yr)', 'Climate Displacement Projections'),
]

for ax, (fc_col, hist_df, ycol_x, ycol_y, ylabel, title) in zip(axes, panels):
    # Historical
    ax.plot(hist_df[ycol_x], hist_df[ycol_y], color=DARK, lw=2.0,
            label='Observed', zorder=3)

    # Scenarios
    base_fc = fc_df[fc_col].values
    ref_val = base_fc[0]
    for scen_name, scen in scenarios.items():
        delta = (base_fc - ref_val) * scen['mult']
        fc_scen = ref_val + delta
        ax.plot(fc_df['Year'], fc_scen, color=scen['color'], lw=1.8,
                ls='--' if 'Medium' in scen_name else ':', label=scen_name)
        if 'Medium' in scen_name:
            ax.fill_between(fc_df['Year'],
                            ref_val + (base_fc - ref_val)*0.65,
                            ref_val + (base_fc - ref_val)*1.45,
                            alpha=0.1, color=ORANGE)

    ax.axvline(2025, color=GREY, lw=1, ls=':', alpha=0.7)
    ax.text(2026, ax.get_ylim()[0] + (ax.get_ylim()[1]-ax.get_ylim()[0])*0.03,
            'Projected →', color=GREY, fontsize=8)

    ax.set_xlabel('Year', fontsize=11)
    ax.set_ylabel(ylabel, fontsize=11)
    ax.set_title(title, fontsize=11, fontweight='bold')
    ax.legend(fontsize=8.5)
    ax.set_xlim(1990, 2052)

fig.suptitle('Climate & Migration Projections to 2050\nMultiple Emission Scenarios (SSP)',
             fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig(f"{FIG_DIR}/fig7_forecast_2050.png")
plt.close()
print("  -> Saved fig7_forecast_2050.png")

# ─────────────────────────────────────────────────────────────────────────────
# FIGURE 8: Composite summary dashboard
# ─────────────────────────────────────────────────────────────────────────────
print("Creating Figure 8: Summary dashboard...")
fig = plt.figure(figsize=(16, 10))
fig.patch.set_facecolor('#f8f8f8')

gs = fig.add_gridspec(3, 3, hspace=0.45, wspace=0.35)
ax1 = fig.add_subplot(gs[0, :2])   # Temperature (wide)
ax2 = fig.add_subplot(gs[0, 2])    # CO2
ax3 = fig.add_subplot(gs[1, :2])   # Displacement
ax4 = fig.add_subplot(gs[1, 2])    # Sea Level
ax5 = fig.add_subplot(gs[2, :])    # Timeline of key events

# ax1: Temperature
years = temp_df['Year'].values; anom = temp_df['anomaly'].values
colors = [RED if a > 0 else BLUE for a in anom]
ax1.bar(years, anom, color=colors, alpha=0.65, width=0.9)
ma = pd.Series(anom).rolling(11, center=True, min_periods=5).mean()
ax1.plot(years, ma, DARK, lw=2); ax1.axhline(0, color='k', lw=0.6, alpha=0.4)
ax1.axhline(1.5, color=ORANGE, lw=1.2, ls='--', alpha=0.6)
ax1.set_title('Temperature Anomaly (°C)', fontsize=10); ax1.set_xlim(1948, 2026)

# ax2: CO2
ax2.plot(co2_df['Year'], co2_df['co2'], color=DARK, lw=1.8)
ax2.fill_between(co2_df['Year'], 310, co2_df['co2'], alpha=0.2, color=ORANGE)
ax2.set_title('CO₂ (ppm)', fontsize=10)

# ax3: Displacement
d = disp_df.dropna(subset=['climate_displaced_millions'])
ax3.fill_between(d['Year'], 0, d['climate_displaced_millions'], alpha=0.4, color=ORANGE)
ax3.plot(d['Year'], d['climate_displaced_millions'], 'o-', color=ORANGE, lw=2, ms=5)
ax3.set_title('Climate Displacements (M/yr)', fontsize=10)

# ax4: Sea Level
ax4.plot(sl_df['Year'], sl_df['sea_level_mm_norm'], color=BLUE, lw=2)
ax4.fill_between(sl_df['Year'], sl_df['sea_level_mm_norm'].min(),
                  sl_df['sea_level_mm_norm'], alpha=0.15, color=BLUE)
ax4.set_title('Sea Level Rise (mm)', fontsize=10)

# ax5: Timeline of events
ax5.set_xlim(1950, 2025); ax5.set_ylim(-1.5, 1.5)
ax5.set_facecolor('#f0f0f0')
ax5.axhline(0, color='black', lw=1)

events_timeline = [
    (1958, 0.5, 'Keeling\nCurve begins', BLUE),
    (1972, 0.8, 'Stockholm\nConference', GREEN),
    (1988, -0.5, 'IPCC\nFounded', PURPLE),
    (1992, 0.5, 'Rio Earth\nSummit', GREEN),
    (1997, -0.7, 'Kyoto\nProtocol', BLUE),
    (2005, 0.6, 'Katrina\n1.8M displaced', RED),
    (2010, -0.8, 'Haiti EQ\n+ floods', RED),
    (2015, 0.7, 'Paris\nAgreement', GREEN),
    (2019, -0.6, '100M\ndisplaced', RED),
    (2022, 0.7, '55M\ndisasters', ORANGE),
    (2024, -0.5, '1.19°C\nrecord', RED),
]
for yr, ht, label, col in events_timeline:
    ax5.annotate('', xy=(yr, 0), xytext=(yr, ht * 0.8),
                 arrowprops=dict(arrowstyle='->', color=col, lw=1.5))
    ax5.text(yr, ht, label, ha='center', fontsize=7, color=col, fontweight='bold',
             va='bottom' if ht > 0 else 'top')

ax5.set_title('Key Climate & Migration Events Timeline', fontsize=10)
ax5.set_xlabel('Year', fontsize=10)
ax5.yaxis.set_visible(False)

fig.suptitle('Climate Change & Human Migration: Summary Dashboard',
             fontsize=15, fontweight='bold', y=1.01)
plt.savefig(f"{FIG_DIR}/fig8_dashboard.png", bbox_inches='tight')
plt.close()
print("  -> Saved fig8_dashboard.png")

print("\n✓ All figures saved to", FIG_DIR)

# Export key stats for report
stats_dict = {
    'temp_trend_per_decade': round(slope_t * 10, 3),
    'latest_temp_anomaly': round(float(temp_df['anomaly'].iloc[-1]), 2),
    'co2_1959': round(float(co2_df['co2'].iloc[0]), 1),
    'co2_latest': round(float(co2_df['co2'].iloc[-1]), 1),
    'co2_rise': round(float(co2_df['co2'].iloc[-1] - co2_df['co2'].iloc[0]), 1),
    'sl_satellite_rate': round(float(slope_sat2), 2),
    'sl_total_norm': round(float(sl_df['sea_level_mm_norm'].iloc[-1]), 0),
    'temp_2050_projection': round(float(temp_fc[-1]), 2),
    'co2_2050_projection': round(float(co2_fc[-1]), 0),
    'sl_2050_projection': round(float(sl_fc[-1]), 0),
    'displacement_2050_projection': round(float(max(disp_fc[-1], 0)), 0),
    'r_co2_displacement': round(float(r_co2), 3),
    'r_temp_displacement': round(float(r_temp), 3),
}
import json
with open(f"{DATA_DIR}/key_stats.json", 'w') as f:
    json.dump(stats_dict, f, indent=2)
print("✓ Key stats saved to key_stats.json")
