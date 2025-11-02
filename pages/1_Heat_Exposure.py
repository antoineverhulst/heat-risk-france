"""
Heat Exposure Analysis Page
Displays interactive maps and analysis of thermal characteristics
"""

import streamlit as st
import geopandas as gpd
import pandas as pd
import folium
from streamlit_folium import folium_static
import plotly.express as px
from pathlib import Path
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))
from config import PROCESSED_DATA_DIR, LCZ_DESCRIPTIONS

# Page config
st.set_page_config(page_title="Heat Exposure Analysis", page_icon="🌡️", layout="wide")

st.title("🌡️ Urban Heat Exposure Analysis")
st.markdown("Explore thermal characteristics and heat island patterns")

# Load data
@st.cache_data
def load_city_data(city_name):
    """Load processed city heat data"""
    file_path = PROCESSED_DATA_DIR / f"{city_name.lower()}_heat_zones.gpkg"
    if file_path.exists():
        return gpd.read_file(file_path)
    return None

@st.cache_data
def load_summary():
    """Load summary statistics"""
    summary_file = PROCESSED_DATA_DIR / "city_summary.csv"
    if summary_file.exists():
        return pd.read_csv(summary_file)
    return None

# City selector
summary = load_summary()
if summary is not None:
    cities = summary['city'].tolist()
    selected_city = st.sidebar.selectbox("Select City", cities, index=0)
    
    # Load city data
    city_data = load_city_data(selected_city)
    
    if city_data is not None:
        st.success(f"✅ Loaded {len(city_data):,} climate zones for {selected_city}")
        
        # Sidebar filters
        st.sidebar.markdown("---")
        st.sidebar.subheader("🎛️ Filters")
        
        min_heat = st.sidebar.slider(
            "Minimum Heat Score",
            min_value=0,
            max_value=10,
            value=0,
            help="Filter zones by minimum heat score"
        )
        
        # Filter data
        filtered_data = city_data[city_data['heat_score'] >= min_heat].copy()
        st.sidebar.info(f"Showing {len(filtered_data):,} zones")
        
        # Main content - tabs
        tab1, tab2, tab3 = st.tabs(["🗺️ Heat Map", "📊 Statistics", "🔍 Zone Details"])
        
        # TAB 1: Heat Map
        with tab1:
            st.subheader("Interactive Heat Island Map")
            
            # Create folium map
            center = [filtered_data.geometry.centroid.y.mean(), 
                     filtered_data.geometry.centroid.x.mean()]
            
            m = folium.Map(location=center, zoom_start=11, tiles='OpenStreetMap')
            
            # Add choropleth layer
            folium.Choropleth(
                geo_data=filtered_data,
                data=filtered_data,
                columns=['identifier', 'heat_score'],
                key_on='feature.properties.identifier',
                fill_color='YlOrRd',
                fill_opacity=0.7,
                line_opacity=0.2,
                legend_name='Heat Retention Score (0=Cool, 10=Hot)',
                highlight=True
            ).add_to(m)
            
            # Add tooltips
            for idx, row in filtered_data.iterrows():
                folium.GeoJson(
                    row['geometry'],
                    style_function=lambda x: {
                        'fillColor': 'transparent',
                        'color': 'transparent'
                    },
                    tooltip=folium.Tooltip(
                        f"""
                        <b>LCZ Type:</b> {row['lcz']}<br>
                        <b>Heat Score:</b> {row['heat_score']}/10<br>
                        <b>Building Height:</b> {row['hre']:.1f}m<br>
                        <b>Vegetation:</b> {row['ver']:.1f}%<br>
                        <b>Built Surface:</b> {row['bur']:.1f}%
                        """
                    )
                ).add_to(m)
                
                # Only add first 1000 tooltips to avoid performance issues
                if idx > 1000:
                    break
            
            # Display map
            folium_static(m, width=1200, height=600)
            
            st.caption("🔍 Hover over zones for details. Red = high heat retention, Yellow = low heat retention.")
        
        # TAB 2: Statistics
        with tab2:
            st.subheader("📈 Heat Exposure Statistics")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Heat score distribution
                fig_hist = px.histogram(
                    filtered_data,
                    x='heat_score',
                    nbins=11,
                    title='Heat Score Distribution',
                    labels={'heat_score': 'Heat Score', 'count': 'Number of Zones'},
                    color_discrete_sequence=['#d6604d']
                )
                fig_hist.update_layout(showlegend=False)
                st.plotly_chart(fig_hist, use_container_width=True)
                
                # Summary stats
                st.markdown("**Summary Statistics:**")
                st.dataframe({
                    'Metric': ['Mean', 'Median', 'Std Dev', 'Min', 'Max'],
                    'Heat Score': [
                        f"{filtered_data['heat_score'].mean():.2f}",
                        f"{filtered_data['heat_score'].median():.2f}",
                        f"{filtered_data['heat_score'].std():.2f}",
                        f"{filtered_data['heat_score'].min():.0f}",
                        f"{filtered_data['heat_score'].max():.0f}"
                    ]
                }, hide_index=True)
            
            with col2:
                # LCZ type distribution
                lcz_counts = filtered_data['lcz'].value_counts().reset_index()
                lcz_counts.columns = ['LCZ Type', 'Count']
                lcz_counts['Description'] = lcz_counts['LCZ Type'].astype(str).map(LCZ_DESCRIPTIONS)
                
                fig_bar = px.bar(
                    lcz_counts.head(10),
                    x='LCZ Type',
                    y='Count',
                    title='Top 10 LCZ Types',
                    hover_data=['Description'],
                    color='Count',
                    color_continuous_scale='YlOrRd'
                )
                st.plotly_chart(fig_bar, use_container_width=True)
                
                st.markdown("**Risk Categories:**")
                high_risk = len(filtered_data[filtered_data['heat_score'] >= 8])
                moderate = len(filtered_data[(filtered_data['heat_score'] >= 5) & (filtered_data['heat_score'] < 8)])
                low_risk = len(filtered_data[filtered_data['heat_score'] < 5])
                
                st.dataframe({
                    'Category': ['🔥 High Risk (8-10)', '🌡️ Moderate (5-7)', '❄️ Low Risk (0-4)'],
                    'Zones': [high_risk, moderate, low_risk],
                    'Percentage': [
                        f"{high_risk/len(filtered_data)*100:.1f}%",
                        f"{moderate/len(filtered_data)*100:.1f}%",
                        f"{low_risk/len(filtered_data)*100:.1f}%"
                    ]
                }, hide_index=True)
            
            # Urban characteristics comparison
            st.markdown("---")
            st.subheader("🏢 Urban Characteristics by Heat Level")
            
            # Create heat categories
            filtered_data['heat_category'] = pd.cut(
                filtered_data['heat_score'],
                bins=[0, 4, 7, 10],
                labels=['Low', 'Moderate', 'High']
            )
            
            comparison = filtered_data.groupby('heat_category').agg({
                'hre': 'mean',
                'ver': 'mean',
                'ror': 'mean',
                'bur': 'mean'
            }).round(1)
            
            comparison.columns = ['Avg Building Height (m)', 'Avg Vegetation (%)', 
                                 'Avg Impervious Surface (%)', 'Avg Built Surface (%)']
            
            st.dataframe(comparison, use_container_width=True)
        
        # TAB 3: Zone Details
        with tab3:
            st.subheader("🔍 Detailed Zone Information")
            
            # Show data table with filters
            st.markdown("Browse individual climate zones:")
            
            # Select columns to display
            display_cols = ['lcz', 'heat_score', 'hre', 'bur', 'ror', 'ver']
            display_data = filtered_data[display_cols].copy()
            display_data.columns = ['LCZ Type', 'Heat Score', 'Building Height (m)', 
                                   'Built Surface (%)', 'Impervious Surface (%)', 'Vegetation (%)']
            
            # Round numeric columns
            for col in display_data.columns[1:]:
                display_data[col] = display_data[col].round(1)
            
            # Display table
            st.dataframe(
                display_data,
                use_container_width=True,
                height=400
            )
            
            # Download button
            csv = display_data.to_csv(index=False)
            st.download_button(
                label="📥 Download Data as CSV",
                data=csv,
                file_name=f"{selected_city.lower()}_heat_zones.csv",
                mime="text/csv"
            )
    
    else:
        st.error(f"❌ No data found for {selected_city}")
        st.info("Please ensure data processing is complete for this city.")

else:
    st.error("No summary data found. Please run data processing first.")

# Sidebar info
with st.sidebar:
    st.markdown("---")
    st.markdown("### 💡 Understanding Heat Scores")
    st.info("""
    **0-3**: Cool areas with vegetation
    
    **4-7**: Mixed urban areas
    
    **8-10**: Dense urban heat islands
    """)