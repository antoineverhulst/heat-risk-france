"""
Risk Assessment Page
Identify and prioritize high-risk areas
"""

import streamlit as st
import geopandas as gpd
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))
from config import PROCESSED_DATA_DIR, LCZ_DESCRIPTIONS

# Page config
st.set_page_config(page_title="Risk Assessment", page_icon="⚠️", layout="wide")

st.title("⚠️ Heat Risk Assessment")
st.markdown("Identify priority areas for intervention and adaptation measures")

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
        st.success(f"✅ Analyzing {len(city_data):,} zones in {selected_city}")
        
        # Define risk categories
        city_data['risk_category'] = pd.cut(
            city_data['heat_score'],
            bins=[0, 4, 7, 8, 10],
            labels=['Low', 'Moderate', 'High', 'Very High']
        )
        
        # Overview metrics
        st.subheader("📊 Risk Overview")
        
        col1, col2, col3, col4 = st.columns(4)
        
        very_high = len(city_data[city_data['risk_category'] == 'Very High'])
        high = len(city_data[city_data['risk_category'] == 'High'])
        moderate = len(city_data[city_data['risk_category'] == 'Moderate'])
        low = len(city_data[city_data['risk_category'] == 'Low'])
        
        with col1:
            st.metric(
                "🔴 Very High Risk",
                very_high,
                f"{very_high/len(city_data)*100:.1f}%",
                help="Heat score 8-10"
            )
        
        with col2:
            st.metric(
                "🟠 High Risk",
                high,
                f"{high/len(city_data)*100:.1f}%",
                help="Heat score 7-8"
            )
        
        with col3:
            st.metric(
                "🟡 Moderate Risk",
                moderate,
                f"{moderate/len(city_data)*100:.1f}%",
                help="Heat score 4-7"
            )
        
        with col4:
            st.metric(
                "🟢 Low Risk",
                low,
                f"{low/len(city_data)*100:.1f}%",
                help="Heat score 0-4"
            )
        
        st.markdown("---")
        
        # Tabs
        tab1, tab2, tab3 = st.tabs(["🎯 Priority Zones", "📈 Risk Analysis", "💡 Recommendations"])
        
        # TAB 1: Priority Zones
        with tab1:
            st.subheader("🎯 Highest Risk Zones")
            st.markdown("Top zones requiring immediate attention:")
            
            # Get top risk zones
            high_risk_zones = city_data[city_data['heat_score'] >= 7].copy()
            high_risk_zones = high_risk_zones.sort_values('heat_score', ascending=False)
            
            if len(high_risk_zones) > 0:
                # Summary
                st.info(f"""
                **{len(high_risk_zones)} zones identified as high or very high risk**
                - Average heat score: {high_risk_zones['heat_score'].mean():.2f}/10
                - Total area: {high_risk_zones.geometry.area.sum() / 1_000_000:.2f} km²
                - {len(high_risk_zones[high_risk_zones['ver'] < 10])} zones with <10% vegetation
                """)
                
                # Top 20 zones table
                st.markdown("**Top 20 Highest Risk Zones:**")
                
                display_data = high_risk_zones.head(20)[
                    ['lcz', 'heat_score', 'hre', 'ver', 'ror', 'bur']
                ].copy()
                
                display_data.columns = [
                    'LCZ Type', 'Heat Score', 'Building Height (m)',
                    'Vegetation (%)', 'Impervious Surface (%)', 'Built Surface (%)'
                ]
                
                # Round and add descriptions
                for col in display_data.columns[1:]:
                    display_data[col] = display_data[col].round(1)
                
                display_data['Description'] = display_data['LCZ Type'].astype(str).map(LCZ_DESCRIPTIONS)
                
                st.dataframe(display_data, use_container_width=True, height=400)
                
                # Characteristics of high-risk zones
                st.markdown("---")
                st.markdown("**Characteristics of High-Risk Zones:**")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Building characteristics
                    fig_scatter = px.scatter(
                        high_risk_zones,
                        x='hre',
                        y='heat_score',
                        color='ver',
                        size='bur',
                        title='Building Height vs Heat Score',
                        labels={
                            'hre': 'Building Height (m)',
                            'heat_score': 'Heat Score',
                            'ver': 'Vegetation (%)',
                            'bur': 'Built Surface (%)'
                        },
                        color_continuous_scale='RdYlGn_r'
                    )
                    st.plotly_chart(fig_scatter, use_container_width=True)
                
                with col2:
                    # Vegetation deficit
                    fig_veg = px.histogram(
                        high_risk_zones,
                        x='ver',
                        nbins=20,
                        title='Vegetation Coverage in High-Risk Zones',
                        labels={'ver': 'Vegetation (%)', 'count': 'Number of Zones'},
                        color_discrete_sequence=['#2ca02c']
                    )
                    st.plotly_chart(fig_veg, use_container_width=True)
            
            else:
                st.success("✅ No high-risk zones identified!")
        
        # TAB 2: Risk Analysis
        with tab2:
            st.subheader("📈 Detailed Risk Analysis")
            
            # Risk distribution pie chart
            col1, col2 = st.columns(2)
            
            with col1:
                risk_dist = city_data['risk_category'].value_counts()
                fig_pie = px.pie(
                    values=risk_dist.values,
                    names=risk_dist.index,
                    title='Risk Distribution',
                    color=risk_dist.index,
                    color_discrete_map={
                        'Low': '#2ca02c',
                        'Moderate': '#ffdd57',
                        'High': '#ff8c42',
                        'Very High': '#d62828'
                    }
                )
                st.plotly_chart(fig_pie, use_container_width=True)
            
            with col2:
                # Risk by LCZ type
                risk_by_lcz = city_data.groupby('lcz')['heat_score'].mean().sort_values(ascending=False).head(10)
                fig_lcz = px.bar(
                    x=risk_by_lcz.index.astype(str),
                    y=risk_by_lcz.values,
                    title='Average Heat Score by LCZ Type (Top 10)',
                    labels={'x': 'LCZ Type', 'y': 'Average Heat Score'},
                    color=risk_by_lcz.values,
                    color_continuous_scale='YlOrRd'
                )
                st.plotly_chart(fig_lcz, use_container_width=True)
            
            # Comparison table
            st.markdown("---")
            st.markdown("**Average Characteristics by Risk Category:**")
            
            comparison = city_data.groupby('risk_category').agg({
                'heat_score': 'mean',
                'hre': 'mean',
                'ver': 'mean',
                'ror': 'mean',
                'bur': 'mean'
            }).round(1)
            
            comparison.columns = [
                'Heat Score', 'Building Height (m)', 'Vegetation (%)',
                'Impervious Surface (%)', 'Built Surface (%)'
            ]
            
            st.dataframe(comparison, use_container_width=True)
            
            # Correlation analysis
            st.markdown("---")
            st.markdown("**📊 Correlation: Urban Characteristics vs Heat Score**")
            
            correlations = city_data[['heat_score', 'hre', 'ver', 'ror', 'bur']].corr()['heat_score'].drop('heat_score')
            
            fig_corr = go.Figure(go.Bar(
                x=correlations.values,
                y=['Building Height', 'Vegetation', 'Impervious Surface', 'Built Surface'],
                orientation='h',
                marker_color=['#d6604d' if x > 0 else '#4393c3' for x in correlations.values]
            ))
            fig_corr.update_layout(
                title='Correlation with Heat Score',
                xaxis_title='Correlation Coefficient',
                yaxis_title='Urban Characteristic'
            )
            st.plotly_chart(fig_corr, use_container_width=True)
        
        # TAB 3: Recommendations
        with tab3:
            st.subheader("💡 Adaptation Recommendations")
            
            # Calculate key metrics
            high_risk_count = len(city_data[city_data['heat_score'] >= 7])
            low_veg_count = len(city_data[city_data['ver'] < 20])
            high_imperv = len(city_data[city_data['ror'] > 70])
            
            st.markdown("""
            Based on the heat risk analysis, here are evidence-based recommendations 
            for reducing urban heat island effects:
            """)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 🌳 Increase Urban Greening")
                st.markdown(f"""
                **Priority areas:** {low_veg_count} zones with <20% vegetation
                
                **Actions:**
                - Plant street trees in high-density areas
                - Create pocket parks and green corridors
                - Install green roofs and walls on buildings
                - Preserve existing green spaces
                
                **Expected impact:** Trees can reduce local temperatures by 2-8°C
                """)
                
                st.markdown("### 💧 Manage Water Features")
                st.markdown("""
                **Actions:**
                - Add water fountains and misting stations
                - Create urban water features
                - Use permeable pavements
                - Restore natural waterways
                
                **Expected impact:** Evaporative cooling can reduce temperatures by 1-3°C
                """)
            
            with col2:
                st.markdown("### 🏗️ Improve Built Environment")
                st.markdown(f"""
                **Priority areas:** {high_imperv} zones with >70% impervious surface
                
                **Actions:**
                - Use cool/reflective materials for roofs and pavements
                - Increase building spacing for air circulation
                - Design for natural ventilation
                - Add shading structures
                
                **Expected impact:** Cool materials can reduce surface temperatures by 10-20°C
                """)
                
                st.markdown("### 👥 Protect Vulnerable Populations")
                st.markdown("""
                **Actions:**
                - Establish cooling centers in high-risk areas
                - Develop heat wave early warning systems
                - Target outreach to elderly and isolated residents
                - Ensure access to air conditioning
                
                **Expected impact:** Can reduce heat-related mortality by 50-80%
                """)
            
            st.markdown("---")
            st.success("""
            **Next Steps:**
            1. Prioritize interventions in zones with heat score ≥8
            2. Focus on areas with low vegetation and high impervious surface
            3. Combine with population vulnerability data for targeted action
            4. Monitor effectiveness through temperature measurements
            """)
    
    else:
        st.error(f"❌ No data found for {selected_city}")

else:
    st.error("No summary data found. Please run data processing first.")

# Sidebar
with st.sidebar:
    st.markdown("---")
    st.markdown("### 📋 Risk Categories")
    st.markdown("""
    **🔴 Very High (8-10)**
    Dense urban, immediate action needed
    
    **🟠 High (7-8)**
    Urban cores, priority for intervention
    
    **🟡 Moderate (4-7)**
    Mixed areas, monitor and plan
    
    **🟢 Low (0-4)**
    Vegetated areas, maintain green cover
    """)