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
## Understanding Urban Heat Risk

Urban heat islands occur when cities replace natural land cover with dense concentrations 
of pavement, buildings, and other surfaces that absorb and retain heat. This creates 
"islands" of higher temperatures compared to surrounding areas.

**Why it matters:**
- Heat waves are becoming more frequent and intense
- Vulnerable populations (elderly, low-income) are most at risk
- Understanding heat exposure helps target interventions

### About This Tool

This application combines:
- 🌡️ **Thermal exposure data** from Local Climate Zones (LCZ)
- 👥 **Population vulnerability** indicators (coming soon)
- ⚠️ **Risk assessment** to identify priority areas

---
""")

# Load summary statistics
@st.cache_data
def load_summary_stats():
    """Load city summary statistics"""
    summary_file = PROCESSED_DATA_DIR / "city_summary.csv"
    if summary_file.exists():
        return pd.read_csv(summary_file)
    return None

summary = load_summary_stats()

# Display quick statistics
st.subheader("📊 Quick Statistics")

if summary is not None:
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Cities Analyzed", 
            len(summary),
            help="Number of cities currently in the database"
        )
    
    with col2:
        st.metric(
            "Total Zones Mapped", 
            f"{summary['total_zones'].sum():,.0f}",
            help="Number of climate zones analyzed"
        )
    
    with col3:
        avg_heat = summary['avg_heat_score'].mean()
        st.metric(
            "Avg Heat Score", 
            f"{avg_heat:.1f}/10",
            help="Average heat retention score (0=cool, 10=hot)"
        )
    
    with col4:
        high_risk_pct = summary['high_risk_percentage'].mean()
        st.metric(
            "High-Risk Areas", 
            f"{high_risk_pct:.1f}%",
            help="Percentage of zones with high heat retention (score ≥8)"
        )
else:
    st.warning("No processed data found. Please run data processing first.")

st.markdown("---")

# City selection and navigation
st.subheader("🏙️ Explore City Heat Risk")

if summary is not None:
    # Create columns for city cards
    cities = summary['city'].tolist()
    
    st.markdown("Select a city to view detailed heat risk analysis:")
    
    # City selector
    selected_city = st.selectbox(
        "Choose a city:",
        cities,
        help="Select a city to analyze"
    )
    
    if selected_city:
        city_data = summary[summary['city'] == selected_city].iloc[0]
        
        # Display city info card
        st.info(f"""
        **{selected_city} Overview**
        - Total zones: {city_data['total_zones']:,.0f}
        - Average heat score: {city_data['avg_heat_score']:.2f}/10
        - High-risk zones: {city_data['high_risk_zones']:.0f} ({city_data['high_risk_percentage']:.1f}%)
        - Average vegetation: {city_data['avg_vegetation']:.1f}%
        - Average building height: {city_data['avg_building_height']:.1f}m
        """)
        
        # Navigation info
        st.markdown("""
        **Explore the data:**
        - 📊 Use the sidebar to navigate to **Heat Exposure** page
        - 🔍 Or go to **Risk Assessment** page
        - All pages are available in the sidebar navigation
        """)

st.markdown("---")

# Methodology section
with st.expander("📖 Methodology & Data Sources"):
    st.markdown("""
    ### Local Climate Zones (LCZ)
    
    LCZ classification divides urban and rural areas into 17 standard types based on:
    - Building height, density, and spacing
    - Land cover (vegetation, water, bare soil)
    - Surface materials
    
    Each zone type has different heat retention characteristics.
    
    ### Heat Score Calculation
    
    We assign heat scores (0-10) based on LCZ classification:
    - **High scores (8-10)**: Compact urban areas with tall, dense buildings
    - **Medium scores (4-7)**: Open urban and mixed areas
    - **Low scores (0-3)**: Vegetated areas, water bodies (cooling effect)
    
    ### Data Sources
    
    - **CEREMA**: Local Climate Zone data (2022)
    - **data.gouv.fr**: French open data portal
    - **License**: Licence Ouverte / Open License
    
    ### Limitations
    
    - LCZ is a proxy for heat exposure, not direct temperature measurement
    - Does not account for specific heat wave events
    - Population vulnerability data to be added in future updates
    """)

# Sidebar information
with st.sidebar:
    st.markdown("### About")
    st.info("""
    This tool analyzes urban heat risk in French cities by combining 
    thermal exposure data with vulnerability indicators.
    
    Inspired by research showing the link between heat mortality 
    and social isolation (Klinenberg, 2002).
    """)
    
    st.markdown("### Navigation")
    st.markdown("""
    - 🏠 **Home**: Overview and statistics
    - 🌡️ **Heat Exposure**: Thermal maps
    - ⚠️ **Risk Assessment**: Priority areas
    """)
    
    st.markdown("---")
    st.caption("Data updated: 2024")
    st.caption("Made with Streamlit 🎈")