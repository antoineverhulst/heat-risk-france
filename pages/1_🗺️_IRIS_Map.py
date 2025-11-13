"""
IRIS Map Viewer
Display Paris IRIS zones with selectable metrics
"""

import streamlit as st
import geopandas as gpd
import pandas as pd
import plotly.express as px
from pathlib import Path
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))
from config import PROCESSED_DATA_DIR

# Page config
st.set_page_config(page_title="IRIS Map Viewer", page_icon="🗺️", layout="wide")

st.title("🗺️ Paris IRIS Heat & Vulnerability Map")
st.markdown("Explore heat exposure and demographic vulnerability at IRIS level (census districts)")

# Load data
@st.cache_data
def load_iris_data():
    """Load IRIS geographic data with heat scores and demographic data"""
    # Load GeoJSON with heat scores and geometry
    geojson_file = PROCESSED_DATA_DIR / "paris_iris_heat_vulnerability.geojson"
    if not geojson_file.exists():
        return None, "GeoJSON file not found"

    iris_geo = gpd.read_file(geojson_file)

    # Load elderly population data
    elderly_file = PROCESSED_DATA_DIR / "paris_iris_elderly_pct.csv"
    if not elderly_file.exists():
        return iris_geo, "Elderly data not available"

    elderly_data = pd.read_csv(elderly_file)

    # Convert IRIS codes to strings to ensure consistent types for merging
    iris_geo['code_iris'] = iris_geo['code_iris'].astype(str)
    elderly_data['IRIS'] = elderly_data['IRIS'].astype(str)

    # Drop conflicting columns from GeoJSON if they exist (they may be empty placeholders)
    columns_to_drop = ['pct_elderly_55', 'pct_elderly_55_alone', 'total_population', 'elderly_55_plus']
    iris_geo = iris_geo.drop(columns=[col for col in columns_to_drop if col in iris_geo.columns])

    # Merge on IRIS code
    # The GeoJSON uses 'code_iris' (e.g., '751010101')
    # The CSV uses 'IRIS' (e.g., '751010101')
    iris_combined = iris_geo.merge(
        elderly_data[['IRIS', 'pct_elderly_55', 'pct_elderly_55_alone', 'total_population', 'elderly_55_plus']],
        left_on='code_iris',
        right_on='IRIS',
        how='left'
    )

    return iris_combined, None

# Load data
iris_data, error_msg = load_iris_data()

if iris_data is None:
    st.error(f"❌ Error loading data: {error_msg}")
    st.info("""
    Please ensure you have run the IRIS aggregation notebook:
    `notebooks/04_iris_aggregation_paris.ipynb`
    """)
    st.stop()

if error_msg:
    st.warning(f"⚠️ {error_msg}")

st.success(f"✅ Loaded {len(iris_data):,} IRIS zones for Paris")

# Metric selector
st.sidebar.subheader("🎯 Select Metric to Display")

metric_options = {
    "Heat Exposure": {
        "column": "avg_heat_score",
        "label": "Average Heat Score (0-10)",
        "color_scale": "RdYlBu_r",
        "description": "Average heat retention score based on Local Climate Zones. Higher values indicate areas with more heat retention."
    },
    "% Elderly (55+)": {
        "column": "pct_elderly_55",
        "label": "% Population 55+",
        "color_scale": "Blues",
        "description": "Percentage of population aged 55 and older. Elderly populations are more vulnerable to heat stress."
    },
    "% Elderly Living Alone": {
        "column": "pct_elderly_55_alone",
        "label": "% Elderly Living Alone",
        "color_scale": "Purples",
        "description": "Percentage of elderly (55+) living alone. Social isolation increases heat vulnerability risk."
    }
}

selected_metric = st.sidebar.radio(
    "Choose a metric:",
    options=list(metric_options.keys()),
    help="Select which metric to visualize on the map"
)

metric_info = metric_options[selected_metric]
metric_col = metric_info["column"]

# Check if data is available for selected metric
if metric_col not in iris_data.columns or iris_data[metric_col].isna().all():
    st.error(f"❌ Data not available for {selected_metric}")
    st.info("""
    To enable this metric, please run:
    `notebooks/04_iris_aggregation_paris.ipynb`
    """)
    st.stop()

# Display metric description
st.info(f"**{selected_metric}**: {metric_info['description']}")

# Filter out IRIS zones with no data
iris_data_filtered = iris_data[iris_data[metric_col].notna()].copy()

if len(iris_data_filtered) == 0:
    st.warning(f"No data available for {selected_metric}")
    st.stop()

st.markdown(f"Showing {len(iris_data_filtered):,} IRIS zones with {selected_metric} data")

# Statistics
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Mean",
        f"{iris_data_filtered[metric_col].mean():.2f}",
        help=f"Average {selected_metric} across all IRIS zones"
    )

with col2:
    st.metric(
        "Median",
        f"{iris_data_filtered[metric_col].median():.2f}",
        help=f"Median {selected_metric}"
    )

with col3:
    st.metric(
        "Min",
        f"{iris_data_filtered[metric_col].min():.2f}",
        help=f"Minimum {selected_metric}"
    )

with col4:
    st.metric(
        "Max",
        f"{iris_data_filtered[metric_col].max():.2f}",
        help=f"Maximum {selected_metric}"
    )

st.markdown("---")

# Create the map
st.subheader(f"📍 Interactive Map: {selected_metric}")

# Prepare hover data
hover_data_dict = {
    'nom_iris': True,
    'nom_com': True,
    'avg_heat_score': ':.2f',
    metric_col: False  # Will be shown as color
}

# Add demographic data to hover if available
if 'pct_elderly_55' in iris_data_filtered.columns:
    hover_data_dict['pct_elderly_55'] = ':.2f'
if 'pct_elderly_55_alone' in iris_data_filtered.columns:
    hover_data_dict['pct_elderly_55_alone'] = ':.2f'

# Create choropleth map
fig = px.choropleth_mapbox(
    iris_data_filtered,
    geojson=iris_data_filtered.geometry,
    locations=iris_data_filtered.index,
    color=metric_col,
    hover_name='nom_iris',
    hover_data=hover_data_dict,
    color_continuous_scale=metric_info['color_scale'],
    zoom=11,
    center={'lat': 48.8566, 'lon': 2.3522},
    opacity=0.7,
    labels={
        metric_col: metric_info['label'],
        'nom_iris': 'IRIS Name',
        'nom_com': 'Arrondissement',
        'avg_heat_score': 'Heat Score',
        'pct_elderly_55': '% Elderly (55+)',
        'pct_elderly_55_alone': '% Elderly Alone'
    }
)

fig.update_layout(
    mapbox_style='open-street-map',
    height=700,
    margin={"r": 0, "t": 0, "l": 0, "b": 0}
)

st.plotly_chart(fig, use_container_width=True)

st.caption("🔍 Hover over IRIS zones to see detailed information. Click and drag to pan, scroll to zoom.")

# Distribution visualization
st.markdown("---")
st.subheader(f"📊 Distribution of {selected_metric}")

col1, col2 = st.columns(2)

with col1:
    # Histogram
    fig_hist = px.histogram(
        iris_data_filtered,
        x=metric_col,
        nbins=30,
        title=f'Distribution of {selected_metric}',
        labels={metric_col: metric_info['label']},
        color_discrete_sequence=['#636EFA']
    )
    fig_hist.update_layout(showlegend=False)
    st.plotly_chart(fig_hist, use_container_width=True)

with col2:
    # Box plot
    fig_box = px.box(
        iris_data_filtered,
        y=metric_col,
        title=f'Statistical Summary of {selected_metric}',
        labels={metric_col: metric_info['label']},
        color_discrete_sequence=['#636EFA']
    )
    st.plotly_chart(fig_box, use_container_width=True)

# Top/Bottom zones
st.markdown("---")
st.subheader(f"🔝 Top & Bottom IRIS Zones by {selected_metric}")

col1, col2 = st.columns(2)

with col1:
    st.markdown(f"**🔴 Highest {selected_metric}**")
    top_10 = iris_data_filtered.nlargest(10, metric_col)[
        ['nom_iris', 'nom_com', metric_col]
    ].reset_index(drop=True)
    top_10.columns = ['IRIS Name', 'Arrondissement', selected_metric]
    top_10.index = top_10.index + 1
    st.dataframe(
        top_10.style.background_gradient(subset=[selected_metric], cmap='Reds'),
        use_container_width=True
    )

with col2:
    st.markdown(f"**🟢 Lowest {selected_metric}**")
    bottom_10 = iris_data_filtered.nsmallest(10, metric_col)[
        ['nom_iris', 'nom_com', metric_col]
    ].reset_index(drop=True)
    bottom_10.columns = ['IRIS Name', 'Arrondissement', selected_metric]
    bottom_10.index = bottom_10.index + 1
    st.dataframe(
        bottom_10.style.background_gradient(subset=[selected_metric], cmap='Greens_r'),
        use_container_width=True
    )

# Download data
st.markdown("---")
st.subheader("💾 Download Data")

# Prepare export data
export_cols = ['code_iris', 'nom_iris', 'nom_com', 'avg_heat_score']
if 'pct_elderly_55' in iris_data_filtered.columns:
    export_cols.append('pct_elderly_55')
if 'pct_elderly_55_alone' in iris_data_filtered.columns:
    export_cols.append('pct_elderly_55_alone')

export_data = iris_data_filtered[export_cols].copy()
export_data.columns = ['IRIS Code', 'IRIS Name', 'Arrondissement', 'Heat Score',
                       '% Elderly (55+)', '% Elderly Living Alone'][:len(export_cols)]

csv = export_data.to_csv(index=False)
st.download_button(
    label="📥 Download Current Data as CSV",
    data=csv,
    file_name=f"paris_iris_{selected_metric.lower().replace(' ', '_')}.csv",
    mime="text/csv"
)

# Sidebar info
with st.sidebar:
    st.markdown("---")
    st.markdown("### 📖 About IRIS")
    st.info("""
    **IRIS** (Îlots Regroupés pour l'Information Statistique) are
    French census districts, the smallest geographic unit for which
    demographic data is published.

    **Paris IRIS Zones**: ~900 districts

    **Average Population**: ~2,000 per IRIS
    """)

    st.markdown("---")
    st.markdown("### 💡 Interpretation")

    if selected_metric == "Heat Exposure":
        st.markdown("""
        **Heat Score Scale:**
        - **0-3**: Cool areas with vegetation
        - **4-7**: Mixed urban areas
        - **8-10**: Dense urban heat islands

        Higher scores indicate greater heat retention.
        """)
    elif selected_metric == "% Elderly (55+)":
        st.markdown("""
        **Vulnerability Indicators:**
        - **<10%**: Low elderly population
        - **10-20%**: Moderate elderly population
        - **>20%**: High elderly population

        Elderly populations are more vulnerable to heat stress.
        """)
    else:
        st.markdown("""
        **Isolation Risk:**
        - **<30%**: Low isolation
        - **30-50%**: Moderate isolation
        - **>50%**: High isolation risk

        Living alone increases vulnerability during heat waves.
        """)
