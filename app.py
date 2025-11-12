"""
Heat Risk France - Main Streamlit Application
Homepage: Overview and city selection
"""

import streamlit as st
import geopandas as gpd
import pandas as pd
from pathlib import Path
from config import PROCESSED_DATA_DIR, APP_TITLE, APP_ICON, PAGE_LAYOUT

# Page configuration
st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout=PAGE_LAYOUT,
    initial_sidebar_state="expanded"
)

# Title and introduction
st.title(f"{APP_ICON} {APP_TITLE}")

st.markdown("""
## Understanding Urban Heat Risk at IRIS Level

Urban heat islands occur when cities replace natural land cover with dense concentrations
of pavement, buildings, and other surfaces that absorb and retain heat. This creates
"islands" of higher temperatures compared to surrounding areas.

**Why IRIS-Level Analysis?**
- IRIS (Îlots Regroupés pour l'Information Statistique) are French census districts
- Provides granular, actionable insights for local interventions
- Combines precise heat exposure data with demographic vulnerability
- Enables targeted resource allocation

### About This Tool

This application provides **IRIS-level heat risk analysis for Paris**, combining:
- 🌡️ **Heat Exposure**: Average heat scores from Local Climate Zones (LCZ)
- 👴 **Elderly Population**: % of residents aged 55+
- 🏠 **Social Isolation**: % of elderly living alone
- ⚖️ **Composite Risk**: Customizable weighted risk scores

**Available Features:**
1. **🗺️ IRIS Map**: Visualize individual metrics across Paris IRIS zones
2. **⚖️ Risk Calculator**: Create custom risk assessments with adjustable weights

---
""")

# Load IRIS statistics
@st.cache_data
def load_iris_stats():
    """Load IRIS-level statistics for Paris"""
    iris_file = PROCESSED_DATA_DIR / "paris_iris_heat_vulnerability.csv"
    elderly_file = PROCESSED_DATA_DIR / "paris_iris_elderly_pct.csv"

    if iris_file.exists() and elderly_file.exists():
        iris_data = pd.read_csv(iris_file)
        elderly_data = pd.read_csv(elderly_file)
        return iris_data, elderly_data
    return None, None

iris_data, elderly_data = load_iris_stats()

# Display quick statistics
st.subheader("📊 Paris IRIS Statistics")

if iris_data is not None and elderly_data is not None:
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "IRIS Zones",
            f"{len(iris_data):,}",
            help="Number of IRIS census districts in Paris"
        )

    with col2:
        avg_heat = iris_data['avg_heat_score'].mean()
        st.metric(
            "Avg Heat Score",
            f"{avg_heat:.2f}/10",
            help="Average heat retention score across IRIS zones"
        )

    with col3:
        avg_elderly = elderly_data['pct_elderly_55'].mean()
        st.metric(
            "Avg % Elderly",
            f"{avg_elderly:.1f}%",
            help="Average percentage of population aged 55+"
        )

    with col4:
        avg_alone = elderly_data['pct_elderly_55_alone'].mean()
        st.metric(
            "Avg % Elderly Alone",
            f"{avg_alone:.1f}%",
            help="Average percentage of elderly living alone"
        )

    # Additional insights
    st.markdown("---")
    st.subheader("🔍 Key Insights")

    col1, col2 = st.columns(2)

    with col1:
        high_heat = len(iris_data[iris_data['avg_heat_score'] >= 8])
        high_heat_pct = (high_heat / len(iris_data)) * 100
        st.info(f"""
        **🌡️ High Heat Exposure**
        - {high_heat} IRIS zones with heat score ≥ 8
        - Represents {high_heat_pct:.1f}% of Paris
        - These areas have dense urban heat island characteristics
        """)

    with col2:
        high_elderly = len(elderly_data[elderly_data['pct_elderly_55'] > 30])
        high_elderly_pct = (high_elderly / len(elderly_data)) * 100
        st.info(f"""
        **👴 High Elderly Population**
        - {high_elderly} IRIS zones with >30% elderly (55+)
        - Represents {high_elderly_pct:.1f}% of Paris
        - Higher vulnerability to heat-related health impacts
        """)
else:
    st.warning("No IRIS data found. Please run `notebooks/04_iris_aggregation_paris.ipynb` to generate the data.")

st.markdown("---")

# Navigation guide
st.subheader("🧭 Explore the Analysis")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    ### 🗺️ IRIS Map Viewer

    **Visualize individual metrics:**
    - Heat exposure per IRIS zone
    - Percentage of elderly population
    - Percentage of elderly living alone

    **Features:**
    - Interactive map with color-coded zones
    - Statistical distributions and rankings
    - Identify hotspots and coolspots
    - Download data for further analysis

    👉 Use the sidebar to navigate to **🗺️ IRIS Map**
    """)

with col2:
    st.markdown("""
    ### ⚖️ Risk Calculator

    **Create custom risk assessments:**
    - Adjust weights for each factor
    - See real-time risk score updates
    - Compare different scenarios
    - Identify priority intervention areas

    **Features:**
    - Customizable weight sliders
    - Composite risk visualization
    - Scenario comparison
    - High-risk zone identification

    👉 Use the sidebar to navigate to **⚖️ Risk Calculator**
    """)

st.markdown("---")

# Methodology section
with st.expander("📖 Methodology & Data Sources"):
    st.markdown("""
    ### IRIS-Level Aggregation

    This analysis aggregates data at the IRIS (Îlots Regroupés pour l'Information Statistique) level:
    - **IRIS zones**: French census districts, smallest unit for demographic statistics
    - **Paris**: ~900 IRIS zones, averaging ~2,000 residents per zone
    - **Spatial join**: LCZ zones matched to IRIS boundaries using geographic intersection

    ### Heat Exposure (Local Climate Zones)

    Heat scores are based on LCZ classification:
    - **Source**: CEREMA Local Climate Zone data (2022)
    - **Scale**: 0-10 (0=cool, 10=hot)
    - **Aggregation**: Average heat score computed across all LCZ zones within each IRIS
    - **High scores (8-10)**: Compact urban areas with dense buildings
    - **Medium scores (4-7)**: Open urban and mixed areas
    - **Low scores (0-3)**: Vegetated areas, water bodies

    ### Demographic Vulnerability

    Population data from INSEE (Institut national de la statistique et des études économiques):
    - **% Elderly (55+)**: Percentage of population aged 55 and older
    - **% Elderly Living Alone**: Percentage of elderly (55+) living in single-person households
    - **Source**: INSEE 2022 demographic census data
    - **Vulnerability**: Elderly populations are more susceptible to heat stress, especially when socially isolated

    ### Composite Risk Score

    The risk calculator combines multiple factors:
    ```
    Risk = w₁ × (Heat/10) + w₂ × (% Elderly/100) + w₃ × (% Alone/100)
    ```
    Where w₁, w₂, w₃ are user-defined weights (normalized to sum to 1)

    ### Data Sources

    - **LCZ Data**: CEREMA (2022)
    - **IRIS Boundaries**: data.gouv.fr
    - **Demographics**: INSEE (2022)
    - **License**: Licence Ouverte / Open License

    ### Limitations

    - LCZ is a proxy for heat exposure, not direct temperature measurement
    - Does not account for specific heat wave events or real-time conditions
    - Demographic data updated annually, may not reflect recent changes
    - Risk scores are relative indicators, not absolute predictions
    """)

# Sidebar information
with st.sidebar:
    st.markdown("### About")
    st.info("""
    This tool provides **IRIS-level heat risk analysis for Paris**,
    combining thermal exposure data with demographic vulnerability indicators.

    Inspired by research on heat mortality and social isolation
    (Klinenberg, 2002).
    """)

    st.markdown("### Navigation")
    st.markdown("""
    - 🏠 **Home**: Overview and statistics
    - 🗺️ **IRIS Map**: Visualize individual metrics
    - ⚖️ **Risk Calculator**: Custom risk assessment
    """)

    st.markdown("---")
    st.markdown("### 📊 Data Coverage")
    st.markdown("""
    **Paris IRIS Zones**: ~900 districts

    **Metrics Available:**
    - Heat exposure scores
    - Elderly population (55+)
    - Social isolation rates
    """)

    st.markdown("---")
    st.caption("Data updated: 2024")
    st.caption("Made with Streamlit 🎈")