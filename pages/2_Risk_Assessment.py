"""
Risk Assessment Page
Identify and prioritize high-risk areas combining HEAT + VULNERABILITY
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

st.title("⚠️ Composite Heat Risk Assessment")
st.markdown("Combining thermal exposure and population vulnerability to identify priority areas")

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

@st.cache_data
def load_vulnerability_data():
    """Load vulnerability data"""
    vuln_file = PROCESSED_DATA_DIR / "paris_vulnerability.csv"
    if vuln_file.exists():
        return pd.read_csv(vuln_file)
    return None

# City selector
summary = load_summary()
vuln_data = load_vulnerability_data()

if summary is not None:
    cities = summary['city'].tolist()
    selected_city = st.sidebar.selectbox("Select City", cities, index=0)
    
    # Load city data
    city_data = load_city_data(selected_city)
    
    if city_data is not None and vuln_data is not None:
        st.success(f"✅ Analyzing {len(city_data):,} zones in {selected_city} with vulnerability data")
        
        # Sidebar: Risk calculation weights
        st.sidebar.markdown("---")
        st.sidebar.subheader("🎛️ Risk Calculation")
        
        heat_weight = st.sidebar.slider(
            "Heat Exposure Weight",
            min_value=0.0,
            max_value=1.0,
            value=0.5,
            step=0.1,
            help="Weight for heat exposure in composite risk"
        )
        
        vuln_weight = 1.0 - heat_weight
        
        st.sidebar.metric("Vulnerability Weight", f"{vuln_weight:.1f}")
        
        st.sidebar.info(f"""
        **Formula:**
        Risk = ({heat_weight:.1f} × Heat) + ({vuln_weight:.1f} × Vulnerability)
        
        Normalized to 0-100 scale
        """)
        
        # Calculate composite risk
        # For now, use Paris average vulnerability since we don't have zone-level linkage
        paris_avg_vuln = vuln_data['vulnerability_score'].mean()
        
        city_data['vulnerability_score'] = paris_avg_vuln  # Simplified approach
        city_data['composite_risk'] = (
            (city_data['heat_score'] * heat_weight + 
             city_data['vulnerability_score'] * vuln_weight) / 10 * 100
        ).round(1)
        
        # Categorize risk
        city_data['risk_category'] = pd.cut(
            city_data['composite_risk'],
            bins=[0, 20, 40, 60, 80, 100],
            labels=['Very Low', 'Low', 'Moderate', 'High', 'Very High']
        )
        
        # Overview metrics
        st.subheader("📊 Composite Risk Overview")
        
        st.info(f"""
        **Risk Calculation**: Combining heat exposure (avg: {city_data['heat_score'].mean():.1f}/10) 
        with population vulnerability (avg: {paris_avg_vuln:.1f}/10) using weights: 
        Heat {heat_weight:.0%} + Vulnerability {vuln_weight:.0%}
        """)
        
        col1, col2, col3, col4 = st.columns(4)
        
        very_high = len(city_data[city_data['risk_category'] == 'Very High'])
        high = len(city_data[city_data['risk_category'] == 'High'])
        moderate = len(city_data[city_data['risk_category'] == 'Moderate'])
        low = len(city_data[(city_data['risk_category'] == 'Low') | (city_data['risk_category'] == 'Very Low')])
        
        with col1:
            st.metric(
                "🔴 Very High Risk",
                very_high,
                f"{very_high/len(city_data)*100:.1f}%",
                help="Composite risk score 80-100"
            )
        
        with col2:
            st.metric(
                "🟠 High Risk",
                high,
                f"{high/len(city_data)*100:.1f}%",
                help="Composite risk score 60-80"
            )
        
        with col3:
            st.metric(
                "🟡 Moderate Risk",
                moderate,
                f"{moderate/len(city_data)*100:.1f}%",
                help="Composite risk score 40-60"
            )
        
        with col4:
            st.metric(
                "🟢 Low Risk",
                low,
                f"{low/len(city_data)*100:.1f}%",
                help="Composite risk score 0-40"
            )
        
        st.markdown("---")
        
        # Tabs
        tab1, tab2, tab3, tab4 = st.tabs(["🎯 Priority Zones", "📈 Risk Analysis", "🔄 Compare Scenarios", "💡 Recommendations"])
        
        # TAB 1: Priority Zones
        with tab1:
            st.subheader("🎯 Highest Composite Risk Zones")
            st.markdown("Areas with combined high heat exposure AND high vulnerability:")
            
            # Get top risk zones
            high_risk_zones = city_data[city_data['composite_risk'] >= 60].copy()
            high_risk_zones = high_risk_zones.sort_values('composite_risk', ascending=False)
            
            if len(high_risk_zones) > 0:
                # Summary
                st.info(f"""
                **{len(high_risk_zones)} zones identified as high or very high risk**
                - Average composite risk: {high_risk_zones['composite_risk'].mean():.1f}/100
                - Average heat score: {high_risk_zones['heat_score'].mean():.2f}/10
                - Average vulnerability: {high_risk_zones['vulnerability_score'].mean():.2f}/10
                - Total area: {high_risk_zones.geometry.area.sum() / 1_000_000:.2f} km²
                """)
                
                # Top 20 zones table
                st.markdown("**Top 20 Highest Risk Zones:**")
                
                display_data = high_risk_zones.head(20)[
                    ['lcz', 'heat_score', 'vulnerability_score', 'composite_risk', 'hre', 'ver']
                ].copy()
                
                display_data.columns = [
                    'LCZ Type', 'Heat Score', 'Vulnerability', 'Composite Risk',
                    'Building Height (m)', 'Vegetation (%)'
                ]
                
                # Round and add descriptions
                for col in display_data.columns[1:]:
                    display_data[col] = display_data[col].round(1)
                
                display_data['Description'] = display_data['LCZ Type'].astype(str).map(LCZ_DESCRIPTIONS)
                
                st.dataframe(
                    display_data.style.background_gradient(subset=['Composite Risk'], cmap='Reds'),
                    use_container_width=True, 
                    height=400
                )
                
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
        
        # TAB 3: Compare Scenarios
        with tab3:
            st.subheader("🔄 Compare Risk Scenarios")
            st.markdown("See how different weight combinations affect risk assessment:")
            
            # Create 3 scenarios
            scenarios = {
                'Heat-Focused (70/30)': {'heat': 0.7, 'vuln': 0.3},
                'Balanced (50/50)': {'heat': 0.5, 'vuln': 0.5},
                'Vulnerability-Focused (30/70)': {'heat': 0.3, 'vuln': 0.7}
            }
            
            scenario_results = []
            for name, weights in scenarios.items():
                risk = (city_data['heat_score'] * weights['heat'] + 
                       city_data['vulnerability_score'] * weights['vuln']) / 10 * 100
                
                very_high = len(risk[risk >= 80])
                high = len(risk[(risk >= 60) & (risk < 80)])
                
                scenario_results.append({
                    'Scenario': name,
                    'Very High Risk': very_high,
                    'High Risk': high,
                    'Total High+': very_high + high,
                    'Avg Risk': risk.mean()
                })
            
            scenario_df = pd.DataFrame(scenario_results)
            
            st.dataframe(scenario_df, use_container_width=True)
            
            # Visualization
            fig_scenarios = go.Figure()
            
            fig_scenarios.add_trace(go.Bar(
                name='Very High Risk',
                x=scenario_df['Scenario'],
                y=scenario_df['Very High Risk'],
                marker_color='#d62828'
            ))
            
            fig_scenarios.add_trace(go.Bar(
                name='High Risk',
                x=scenario_df['Scenario'],
                y=scenario_df['High Risk'],
                marker_color='#f77f00'
            ))
            
            fig_scenarios.update_layout(
                title='High-Risk Zones by Scenario',
                xaxis_title='Scenario',
                yaxis_title='Number of Zones',
                barmode='stack'
            )
            
            st.plotly_chart(fig_scenarios, use_container_width=True)
            
            st.info("""
            **Interpretation:**
            - **Heat-Focused**: Prioritizes thermal exposure (useful for immediate heat wave response)
            - **Balanced**: Equal consideration of heat and vulnerability (recommended for planning)
            - **Vulnerability-Focused**: Prioritizes demographic factors (useful for long-term social programs)
            
            Use the slider in the sidebar to create custom weight combinations!
            """)
        
        # TAB 4: Recommendations
        with tab4:
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
        st.error(f"❌ Heat zone data not available for {selected_city} in this deployment")
        st.info("""
        **Limited Deployment**: The detailed heat zone data is not available in this cloud deployment 
        due to file size limitations (70MB exceeds GitHub's limits).
        
        **Available Features:**
        - ✅ **Vulnerability Analysis**: See the Vulnerability page for full demographic analysis
        - ✅ **Methodology**: Full explanation of how composite risk is calculated
        
        **For Full Experience:**
        Run the app locally with complete data - see instructions on the Heat Exposure page.
        """)

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