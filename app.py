"""
Heat Risk France - Single Page Application
Analyzing urban heat risk across French cities by combining thermal exposure with population vulnerability
"""

import streamlit as st
import geopandas as gpd
import pandas as pd
import plotly.express as px
from pathlib import Path

# Page configuration
st.set_page_config(
    page_title="Heat Risk France",
    page_icon="🌡️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Configuration
PROCESSED_DATA_DIR = Path(__file__).parent / "data" / "processed"
CITIES = ['Paris', 'Lille', 'Lyon', 'Marseille', 'Toulouse']

# City center coordinates for maps
CITY_CENTERS = {
    'Paris': {'lat': 48.8566, 'lon': 2.3522, 'zoom': 11},
    'Lille': {'lat': 50.6292, 'lon': 3.0573, 'zoom': 11},
    'Lyon': {'lat': 45.7640, 'lon': 4.8357, 'zoom': 11},
    'Marseille': {'lat': 43.2965, 'lon': 5.3698, 'zoom': 11},
    'Toulouse': {'lat': 43.6047, 'lon': 1.4442, 'zoom': 11}
}

# Colorblind-friendly palettes
HEAT_COLORS = ['#fee5d9', '#fcbba1', '#fc9272', '#fb6a4a', '#ef3b2c', '#cb181d', '#99000d']
RISK_COLORS = ['#ffffcc', '#ffeda0', '#fed976', '#feb24c', '#fd8d3c', '#fc4e2a', '#e31a1c', '#b10026']


@st.cache_data
def load_city_data(city_name):
    """
    Load and merge all data for a city
    Returns GeoDataFrame with all metrics
    """
    city_lower = city_name.lower()

    # Load GeoJSON with heat scores and geometry
    geojson_file = PROCESSED_DATA_DIR / f"{city_lower}_iris_heat_vulnerability.geojson"
    elderly_file = PROCESSED_DATA_DIR / f"{city_lower}_iris_elderly_pct.csv"

    if not geojson_file.exists() or not elderly_file.exists():
        return None

    # Load geographic data
    iris_geo = gpd.read_file(geojson_file)

    # Load demographic data
    elderly_data = pd.read_csv(elderly_file)

    # Ensure matching types for merge
    iris_geo['code_iris'] = iris_geo['code_iris'].astype(str)
    elderly_data['IRIS'] = elderly_data['IRIS'].astype(str)

    # Merge datasets
    combined = iris_geo.merge(
        elderly_data,
        left_on='code_iris',
        right_on='IRIS',
        how='left'
    )

    # Calculate population density (project to metric CRS first for accurate area calculation)
    # EPSG:2154 is Lambert-93, the official projection for France
    combined_projected = combined.to_crs(epsg=2154)
    combined['area_km2'] = combined_projected.geometry.area / 1_000_000  # Convert m² to km²
    combined['population_density'] = combined['total_population'] / combined['area_km2']

    # Calculate risk indicators using categorical heat_score
    def calculate_heat_multiplier(heat_score):
        """Calculate heat multiplier from categorical heat score"""
        if pd.isna(heat_score):
            return 0
        elif heat_score == 'Low':
            return 0
        elif heat_score == 'Medium':
            return 1
        elif heat_score == 'High':
            return 2
        else:
            return 0

    combined['heat_multiplier'] = combined['heat_score'].apply(calculate_heat_multiplier)
    combined['risk_indicator'] = combined['heat_multiplier'] * combined['elderly_55_plus_alone']
    combined['extreme_risk_indicator'] = combined['heat_multiplier'] * combined['elderly_80_plus_alone']

    return combined


def render_home(selected_city, city_data):
    """Render Home section"""
    st.title("🌡️ Heat Risk France")
    st.markdown("""
    ### Understanding Urban Heat Risk and Social Vulnerability

    Urban heat islands occur when cities replace natural land cover with dense concentrations
    of pavement, buildings, and other surfaces that absorb and retain heat. This creates
    "islands" of higher temperatures compared to surrounding areas.

    **Social vulnerability** amplifies heat risk. Research by Eric Klinenberg on the 1995
    Chicago heat wave showed that social isolation, particularly among elderly populations,
    significantly increases mortality during extreme heat events.

    This tool combines:
    - 🌡️ **Heat Exposure**: Local Climate Zone (LCZ) classification (High/Medium/Low)
    - 👴 **Demographic Vulnerability**: Elderly population data from INSEE
    - 🏠 **Social Isolation**: Percentage of elderly living alone
    """)

    st.markdown("---")

    if city_data is not None and len(city_data) > 0:
        st.subheader("🔍 Key Insights")

        col1, col2 = st.columns(2)

        with col1:
            high_heat = len(city_data[city_data['heat_score'] == 'High'])
            high_heat_pct = (high_heat / len(city_data)) * 100
            st.info(f"""
            **🔥 High Heat Zones**
            - {high_heat} IRIS zones classified as High heat
            - Represents {high_heat_pct:.1f}% of {selected_city}
            - Highest heat retention areas
            """)

        with col2:
            high_vulnerable = len(city_data[city_data['elderly_55_plus_alone'] > 200])
            high_vulnerable_pct = (high_vulnerable / len(city_data)) * 100
            st.info(f"""
            **👴 Vulnerable Populations**
            - {high_vulnerable} IRIS zones with >200 elderly (55+) living alone
            - Represents {high_vulnerable_pct:.1f}% of {selected_city}
            - Priority areas for intervention
            """)
    else:
        st.warning(f"No data available for {selected_city}")


def create_plotly_map(city_data, city_center, metric_col, metric_name, colormap='YlOrRd'):
    """Create a Plotly choropleth mapbox with colorblind-friendly colors"""

    if metric_col not in city_data.columns:
        return None

    # Reproject to EPSG:4326 (WGS84) for mapbox compatibility
    city_data_map = city_data.copy()
    if city_data_map.crs is not None and city_data_map.crs.to_epsg() != 4326:
        city_data_map = city_data_map.to_crs(epsg=4326)

    # Check if this is the categorical heat_score
    if metric_col == 'heat_score':
        # Create discrete color map for heat_score categories
        color_discrete_map = {
            'High': '#e31a1c',    # Red
            'Medium': '#fd8d3c',  # Orange
            'Low': '#91cf60'      # Green
        }

        # Ensure the heat_score column has the correct categories
        category_order = ['Low', 'Medium', 'High']

        fig = px.choropleth_mapbox(
            city_data_map,
            geojson=city_data_map.geometry.__geo_interface__,
            locations=city_data_map.index,
            color=metric_col,
            hover_name='nom_iris',
            hover_data={'nom_com': True, metric_col: True},
            color_discrete_map=color_discrete_map,
            category_orders={metric_col: category_order},
            mapbox_style='carto-positron',
            center={'lat': city_center['lat'], 'lon': city_center['lon']},
            zoom=city_center['zoom'],
            opacity=0.7,
            labels={metric_col: metric_name}
        )
    else:
        # Continuous scale for numeric metrics
        fig = px.choropleth_mapbox(
            city_data_map,
            geojson=city_data_map.geometry.__geo_interface__,
            locations=city_data_map.index,
            color=metric_col,
            hover_name='nom_iris',
            hover_data={'nom_com': True, metric_col: ':.2f'},
            color_continuous_scale=colormap,
            mapbox_style='carto-positron',
            center={'lat': city_center['lat'], 'lon': city_center['lon']},
            zoom=city_center['zoom'],
            opacity=0.7,
            labels={metric_col: metric_name}
        )

    fig.update_layout(
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        height=600
    )

    return fig


def render_map_analysis(selected_city, city_data):
    """Render Map Analysis section"""
    st.title("🗺️ IRIS Map")
    st.markdown(f"### Interactive heat and demographic mapping for {selected_city}")

    if city_data is None or len(city_data) == 0:
        st.warning(f"No data available for {selected_city}")
        return

    # Metric selector at top of this section
    metric_options = {
        'Heat Score Category': 'heat_score',
        'Population Density': 'population_density',
        '% Elderly (55+)': 'pct_elderly_55',
        '% Elderly Living Alone': 'pct_elderly_55_alone',
        'Elderly (55+) Alone Count': 'elderly_55_plus_alone',
        'Elderly (80+) Alone Count': 'elderly_80_plus_alone'
    }

    selected_metric_name = st.selectbox(
        "Select metric to visualize on the map:",
        options=list(metric_options.keys()),
        index=0,
        key="iris_map_metric",
        help="Choose which metric to display on the IRIS map"
    )

    metric_col = metric_options[selected_metric_name]

    # Statistics panel
    st.markdown("---")
    st.subheader("📊 Statistics")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Total IRIS Zones",
            f"{len(city_data):,}",
            help="Number of census districts"
        )

    with col2:
        high_heat_count = len(city_data[city_data['heat_score'] == 'High'])
        st.metric(
            "High Heat IRIS",
            f"{high_heat_count:,}",
            help="IRIS zones with High heat classification"
        )

    with col3:
        high_vulnerable = len(city_data[city_data['elderly_55_plus_alone'] > 200])
        st.metric(
            "High Vulnerability",
            f"{high_vulnerable:,}",
            help="IRIS with >200 elderly (55+) living alone"
        )

    with col4:
        high_risk = len(city_data[
            (city_data['heat_score'] == 'High') &
            (city_data['elderly_55_plus_alone'] > 200)
        ])
        st.metric(
            "High Risk IRIS",
            f"{high_risk:,}",
            help="IRIS with both High heat AND high vulnerability"
        )

    st.markdown("---")

    # Map
    st.subheader("🗺️ Interactive Map")

    city_center = CITY_CENTERS.get(selected_city, CITY_CENTERS['Paris'])

    # Determine colormap based on metric
    if 'heat' in metric_col.lower():
        colormap = 'YlOrRd'
    elif 'density' in metric_col.lower():
        colormap = 'YlGnBu'
    elif 'elderly' in metric_col.lower() and 'alone' in metric_col.lower():
        colormap = 'OrRd'
    else:
        colormap = 'YlOrRd'

    plotly_map = create_plotly_map(
        city_data,
        city_center,
        metric_col,
        selected_metric_name,
        colormap=colormap
    )

    if plotly_map:
        st.plotly_chart(plotly_map, use_container_width=True)


def render_risk_analysis(selected_city, city_data):
    """Render Risk Analysis section - Map and Top 20 table"""
    st.title("⚖️ Risk Calculator")
    st.markdown(f"### Heat-based risk indicators for {selected_city}")

    if city_data is None or len(city_data) == 0:
        st.warning(f"No data available for {selected_city}")
        return

    # Methodology explanation
    with st.expander("📖 Methodology", expanded=False):
        st.markdown("""
        ### Risk Indicator Calculation

        Our risk indicators combine heat exposure with vulnerable populations:

        **Heat Score Classification:**
        - **Low**: LCZ classes with minimal heat retention (parks, water, vegetation)
        - **Medium**: LCZ classes 4, 5, 6, 7, E (open urban areas)
        - **High**: LCZ classes 1, 2, 3, 8, 10 (compact urban areas)

        **Heat Multiplier:**
        - 0 for Low heat score
        - 1 for Medium heat score
        - 2 for High heat score

        **Risk Indicator** = Heat Multiplier × Number of Elderly (55+) Living Alone

        **Extreme Risk Indicator** = Heat Multiplier × Number of Elderly (80+) Living Alone

        This approach prioritizes areas where:
        1. Heat exposure is significant (Medium or High)
        2. Vulnerable populations are present
        3. Social isolation increases risk
        """)

    st.markdown("---")

    # Risk metric selector at top of this section
    risk_options = {
        'Risk Indicator (55+ alone)': {
            'col': 'risk_indicator',
            'elderly_col': 'elderly_55_plus_alone',
            'label': 'Risk Indicator'
        },
        'Extreme Risk Indicator (80+ alone)': {
            'col': 'extreme_risk_indicator',
            'elderly_col': 'elderly_80_plus_alone',
            'label': 'Extreme Risk Indicator'
        }
    }

    selected_risk_name = st.selectbox(
        "Select risk indicator to visualize:",
        options=list(risk_options.keys()),
        index=0,
        key="risk_calculator_metric",
        help="Choose which risk indicator to analyze"
    )

    risk_info = risk_options[selected_risk_name]
    risk_col = risk_info['col']
    elderly_col = risk_info['elderly_col']

    # Risk Map
    st.markdown("---")
    st.subheader(f"🗺️ {selected_risk_name} Map")

    city_center = CITY_CENTERS.get(selected_city, CITY_CENTERS['Paris'])

    plotly_map = create_plotly_map(
        city_data,
        city_center,
        risk_col,
        risk_info['label'],
        colormap='YlOrRd'
    )

    if plotly_map:
        st.plotly_chart(plotly_map, use_container_width=True)

    # Top 20 highest risk zones table
    st.markdown("---")
    st.subheader(f"🔝 Top 20 IRIS Zones by {selected_risk_name}")

    top_20 = city_data.nlargest(20, risk_col)[
        ['nom_iris', 'nom_com', 'heat_score', 'heat_multiplier',
         elderly_col, risk_col]
    ].reset_index(drop=True)

    top_20.columns = ['IRIS Name', 'Arrondissement', 'Heat Score', 'Heat Multiplier',
                      risk_info['elderly_col'].replace('_', ' ').title(), risk_info['label']]
    top_20.index = top_20.index + 1

    st.dataframe(
        top_20.style.background_gradient(
            subset=[risk_info['label']],
            cmap='Oranges' if 'Risk Indicator' in selected_risk_name else 'Reds'
        ),
        use_container_width=True
    )


def render_about(selected_city, city_data):
    """Render About section"""
    st.title("📖 About This Project")

    st.markdown("""
    ### Methodology

    This application analyzes urban heat risk by combining thermal exposure data with
    demographic vulnerability indicators at the IRIS (census district) level.

    #### Heat Exposure Assessment

    Heat scores are derived from **Local Climate Zones (LCZ)** classification:
    - **Source**: CEREMA 2022 LCZ data for French cities
    - **Classification**: Categorical (High/Medium/Low)
    - **Aggregation**: Most common LCZ category within each IRIS zone

    | Heat Score | LCZ Classes | Description |
    |------------|-------------|-------------|
    | **High** | 1, 2, 3, 8, 10 | Compact urban areas with dense buildings |
    | **Medium** | 4, 5, 6, 7, E | Open urban and mixed areas |
    | **Low** | 9, A, B, C, D, F, G | Vegetated areas, water bodies, parks |

    #### Demographic Vulnerability

    Population data from INSEE (French national statistics):
    - **% Elderly (55+)**: Percentage of population aged 55 and older
    - **% Elderly Living Alone**: Social isolation indicator
    - **Absolute counts**: Number of vulnerable individuals per IRIS

    Elderly populations are more susceptible to heat stress, and social isolation
    significantly increases mortality risk during heat waves.

    #### Risk Indicators

    Our risk indicators combine heat exposure categories with vulnerable populations:

    **Heat Multiplier:**
    - Low heat = 0 (no risk from heat)
    - Medium heat = 1 (moderate risk)
    - High heat = 2 (significant risk)

    **Risk Indicator** = Heat Multiplier × Number of Elderly (55+) Living Alone

    This approach prioritizes areas with:
    1. **Significant heat exposure** (Medium or High)
    2. **Vulnerable populations** (elderly living alone)
    3. **Combined risk** (heat multiplier × vulnerable population count)

    ### Research Background

    This work is inspired by:

    **📚 Books & Articles:**
    - **Klinenberg, E. (2002)** - *Heat Wave: A Social Autopsy of Disaster in Chicago*
      - Groundbreaking research showing that social isolation, not poverty alone,
        was the primary factor in heat-related mortality during the 1995 Chicago heat wave
    - **Harlan, S. L., et al. (2006)** - "Neighborhood Effects on Heat Deaths"
      - Analysis of spatial patterns in heat vulnerability

    ### Data Sources

    - **LCZ Data**: CEREMA (2022) via data.gouv.fr
    - **IRIS Boundaries**: IGN (Institut national de l'information géographique et forestière) - [IRIS GE](https://geoservices.ign.fr/irisge)
    - **Demographics**: INSEE (2022)
    - **License**: Licence Ouverte / Open License

    ### Limitations

    - LCZ is a **proxy** for heat exposure, not direct temperature measurement
    - Does not account for specific heat wave events or real-time conditions
    - Demographic data updated annually, may not reflect recent changes
    - Risk scores are **relative indicators**, not absolute predictions
    - Does not account for:
      - Air conditioning prevalence
      - Green space access
      - Social support networks
      - Healthcare accessibility

    ### Download Data
    """)

    # Download buttons
    if city_data is not None and len(city_data) > 0:
        st.subheader(f"📥 Download {selected_city} Data")

        col1, col2 = st.columns(2)

        with col1:
            # Prepare CSV data (without geometry)
            csv_data = city_data.drop(columns=['geometry']).copy()
            csv_string = csv_data.to_csv(index=False)

            st.download_button(
                label="📄 Download Full Dataset (CSV)",
                data=csv_string,
                file_name=f"{selected_city.lower()}_heat_risk_data.csv",
                mime="text/csv",
                help="Complete dataset with all metrics"
            )

        with col2:
            # Risk scores only
            risk_data = city_data[[
                'code_iris', 'nom_iris', 'nom_com',
                'heat_score', 'heat_multiplier',
                'elderly_55_plus_alone', 'elderly_80_plus_alone',
                'risk_indicator', 'extreme_risk_indicator'
            ]].copy()
            risk_csv = risk_data.to_csv(index=False)

            st.download_button(
                label="⚖️ Download Risk Scores (CSV)",
                data=risk_csv,
                file_name=f"{selected_city.lower()}_risk_scores.csv",
                mime="text/csv",
                help="Risk indicators only"
            )

    st.markdown("---")
    st.markdown("""
    ### Contact & Contribute

    This is an open-source project. Contributions, suggestions, and feedback are welcome!

    **Made with Streamlit 🎈**
    """)


def main():
    """Main application - Single consolidated page"""

    # Page title
    st.title("🌡️ Heat Risk France")

    st.markdown("---")

    # ========================================================================
    # CITY SELECTOR - Top of page
    # ========================================================================
    st.subheader("🏙️ Select City")

    # City selector
    selected_city = st.selectbox(
        "Choose a city to analyze:",
        options=CITIES,
        index=0,
        help="Select which city to analyze"
    )

    # Load data for selected city
    city_data = load_city_data(selected_city)

    st.markdown("---")

    # ========================================================================
    # METRICS DISPLAY - Two rows of 4 metrics
    # ========================================================================
    if city_data is not None and len(city_data) > 0:
        st.subheader("📊 Key Metrics")

        # Row 1: Absolute counts
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            total_pop = city_data['total_population'].sum()
            st.metric(
                label="Population",
                value=f"{total_pop:,.0f}",
                help="Total population across all IRIS zones"
            )

        with col2:
            total_iris = len(city_data)
            st.metric(
                label="# of IRIS",
                value=f"{total_iris:,}",
                help="Number of IRIS zones in the city"
            )

        with col3:
            total_elderly_55_alone = city_data['elderly_55_plus_alone'].sum()
            st.metric(
                label="# of Elderly (55+) Living Alone",
                value=f"{total_elderly_55_alone:,.0f}",
                help="Total count of people aged 55+ living alone"
            )

        with col4:
            total_elderly_80_alone = city_data['elderly_80_plus_alone'].sum()
            st.metric(
                label="# of Elderly (80+) Living Alone",
                value=f"{total_elderly_80_alone:,.0f}",
                help="Total count of people aged 80+ living alone"
            )

        # Row 2: Percentages in High heat score IRIS
        col5, col6, col7, col8 = st.columns(4)

        # Filter for High heat score zones
        high_heat_zones = city_data[city_data['heat_score'] == 'High']

        with col5:
            pop_high_heat = high_heat_zones['total_population'].sum() if len(high_heat_zones) > 0 else 0
            pct_pop_high_heat = (pop_high_heat / total_pop * 100) if total_pop > 0 else 0
            st.metric(
                label="% of Population in High Heat Score IRIS",
                value=f"{pct_pop_high_heat:.1f}%",
                help="Percentage of population living in High heat score zones"
            )

        with col6:
            num_high_heat_iris = len(high_heat_zones)
            pct_iris_high_heat = (num_high_heat_iris / total_iris * 100) if total_iris > 0 else 0
            st.metric(
                label="% of IRIS in High Heat Score Zones",
                value=f"{pct_iris_high_heat:.1f}%",
                help="Percentage of IRIS zones classified as High heat"
            )

        with col7:
            elderly_55_high_heat = high_heat_zones['elderly_55_plus_alone'].sum() if len(high_heat_zones) > 0 else 0
            pct_elderly_55_high_heat = (elderly_55_high_heat / total_elderly_55_alone * 100) if total_elderly_55_alone > 0 else 0
            st.metric(
                label="% of Elderly (55+) Living Alone in High Heat Score IRIS",
                value=f"{pct_elderly_55_high_heat:.1f}%",
                help="Percentage of elderly (55+) living alone in High heat zones"
            )

        with col8:
            elderly_80_high_heat = high_heat_zones['elderly_80_plus_alone'].sum() if len(high_heat_zones) > 0 else 0
            pct_elderly_80_high_heat = (elderly_80_high_heat / total_elderly_80_alone * 100) if total_elderly_80_alone > 0 else 0
            st.metric(
                label="% of Elderly (80+) Living Alone in High Heat Score IRIS",
                value=f"{pct_elderly_80_high_heat:.1f}%",
                help="Percentage of elderly (80+) living alone in High heat zones"
            )

    st.markdown("---")

    # ========================================================================
    # HOME SECTION
    # ========================================================================
    render_home(selected_city, city_data)

    st.markdown("---")

    # ========================================================================
    # IRIS MAP SECTION
    # ========================================================================
    render_map_analysis(selected_city, city_data)

    st.markdown("---")

    # ========================================================================
    # RISK CALCULATOR SECTION
    # ========================================================================
    render_risk_analysis(selected_city, city_data)

    st.markdown("---")

    # ========================================================================
    # ABOUT SECTION
    # ========================================================================
    render_about(selected_city, city_data)


if __name__ == "__main__":
    main()
