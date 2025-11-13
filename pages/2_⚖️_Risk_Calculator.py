"""
Risk Calculator
Calculate and visualize composite heat risk with customizable weights
"""

import streamlit as st
import geopandas as gpd
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sys
import numpy as np

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))
from config import PROCESSED_DATA_DIR

# Page config
st.set_page_config(page_title="Risk Calculator", page_icon="⚖️", layout="wide")

st.title("⚖️ Heat Risk Calculator")
st.markdown("Calculate composite risk scores by weighting different vulnerability factors")

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

    # Convert IRIS column to string to match code_iris type in GeoJSON
    elderly_data['IRIS'] = elderly_data['IRIS'].astype(str)

    # Merge on IRIS code - only merge columns not already in iris_geo
    # GeoJSON already has pct_elderly_55 and total_population
    # We only need to add pct_elderly_55_alone and elderly_55_plus
    iris_combined = iris_geo.merge(
        elderly_data[['IRIS', 'pct_elderly_55_alone', 'elderly_55_plus']],
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

# Filter to only IRIS with complete data
iris_data_complete = iris_data[
    iris_data['avg_heat_score'].notna() &
    iris_data['pct_elderly_55'].notna() &
    iris_data['pct_elderly_55_alone'].notna()
].copy()

# Check if we have any complete data
if len(iris_data_complete) == 0:
    st.error("❌ No IRIS zones with complete data found!")
    st.info(f"""
    **Missing data detected.** Please check:

    1. **Heat scores**: Ensure you have run `notebooks/03_heat_score_analysis.ipynb`
    2. **Elderly demographics**: Ensure you have run `notebooks/04_iris_aggregation_paris.ipynb`
    3. **Data files**: Verify the following files exist:
       - `data/processed/paris_iris_heat_vulnerability.geojson`
       - `data/processed/paris_iris_elderly_pct.csv`

    **Debug information:**
    - Total IRIS zones loaded: {len(iris_data)}
    - IRIS with heat scores: {iris_data['avg_heat_score'].notna().sum()}
    - IRIS with elderly data (55+): {iris_data['pct_elderly_55'].notna().sum()}
    - IRIS with elderly alone data: {iris_data['pct_elderly_55_alone'].notna().sum()}
    """)
    st.stop()

st.success(f"✅ Loaded {len(iris_data_complete):,} IRIS zones with complete data")

# Sidebar: Weight configuration
st.sidebar.markdown("## 🎛️ Risk Weight Configuration")
st.sidebar.markdown("Adjust the importance of each factor in calculating composite risk:")

# Weight sliders
heat_weight = st.sidebar.slider(
    "🌡️ Heat Exposure Weight",
    min_value=0.0,
    max_value=1.0,
    value=0.40,
    step=0.05,
    help="Weight for average heat score in risk calculation"
)

elderly_weight = st.sidebar.slider(
    "👴 Elderly Population Weight",
    min_value=0.0,
    max_value=1.0,
    value=0.30,
    step=0.05,
    help="Weight for % of population aged 55+"
)

isolation_weight = st.sidebar.slider(
    "🏠 Social Isolation Weight",
    min_value=0.0,
    max_value=1.0,
    value=0.30,
    step=0.05,
    help="Weight for % of elderly living alone"
)

# Normalize weights
total_weight = heat_weight + elderly_weight + isolation_weight

if total_weight > 0:
    heat_weight_norm = heat_weight / total_weight
    elderly_weight_norm = elderly_weight / total_weight
    isolation_weight_norm = isolation_weight / total_weight
else:
    heat_weight_norm = elderly_weight_norm = isolation_weight_norm = 0
    st.error("⚠️ Total weight must be greater than zero!")

# Display normalized weights
st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 Normalized Weights")
st.sidebar.markdown(f"🌡️ Heat: **{heat_weight_norm:.1%}**")
st.sidebar.markdown(f"👴 Elderly: **{elderly_weight_norm:.1%}**")
st.sidebar.markdown(f"🏠 Isolation: **{isolation_weight_norm:.1%}**")
st.sidebar.markdown(f"**Total: 100%**")

# Calculate composite risk score
st.markdown("---")
st.subheader("🧮 Risk Calculation Formula")

st.latex(r"""
\text{Risk Score} = w_1 \times \left(\frac{\text{Heat Score}}{10}\right) +
w_2 \times \left(\frac{\text{\% Elderly}}{100}\right) +
w_3 \times \left(\frac{\text{\% Elderly Alone}}{100}\right)
""")

st.markdown(f"""
Where:
- $w_1$ = {heat_weight_norm:.2f} (Heat Weight)
- $w_2$ = {elderly_weight_norm:.2f} (Elderly Weight)
- $w_3$ = {isolation_weight_norm:.2f} (Isolation Weight)

**Result:** Risk Score on a 0-100 scale
""")

# Normalize metrics to 0-1 scale and calculate composite risk
iris_data_complete['heat_normalized'] = iris_data_complete['avg_heat_score'] / 10.0
iris_data_complete['elderly_normalized'] = iris_data_complete['pct_elderly_55'] / 100.0
iris_data_complete['isolation_normalized'] = iris_data_complete['pct_elderly_55_alone'] / 100.0

iris_data_complete['composite_risk'] = (
    heat_weight_norm * iris_data_complete['heat_normalized'] +
    elderly_weight_norm * iris_data_complete['elderly_normalized'] +
    isolation_weight_norm * iris_data_complete['isolation_normalized']
) * 100

# Categorize risk
iris_data_complete['risk_category'] = pd.cut(
    iris_data_complete['composite_risk'],
    bins=[0, 20, 40, 60, 80, 100],
    labels=['Very Low', 'Low', 'Moderate', 'High', 'Very High'],
    include_lowest=True
)

# Overview metrics
st.markdown("---")
st.subheader("📊 Risk Score Overview")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Mean Risk Score",
        f"{iris_data_complete['composite_risk'].mean():.1f}",
        help="Average composite risk score across all IRIS zones"
    )

with col2:
    high_risk = len(iris_data_complete[iris_data_complete['composite_risk'] >= 60])
    high_risk_pct = (high_risk / len(iris_data_complete)) * 100
    st.metric(
        "High Risk Zones",
        f"{high_risk}",
        f"{high_risk_pct:.1f}%",
        help="IRIS zones with risk score ≥ 60"
    )

with col3:
    st.metric(
        "Min Risk Score",
        f"{iris_data_complete['composite_risk'].min():.1f}",
        help="Lowest risk score"
    )

with col4:
    st.metric(
        "Max Risk Score",
        f"{iris_data_complete['composite_risk'].max():.1f}",
        help="Highest risk score"
    )

# Risk category distribution
col1, col2, col3, col4, col5 = st.columns(5)

risk_counts = iris_data_complete['risk_category'].value_counts()

with col1:
    count = risk_counts.get('Very Low', 0)
    pct = (count / len(iris_data_complete)) * 100
    st.metric("🟢 Very Low (0-20)", f"{count}", f"{pct:.1f}%")

with col2:
    count = risk_counts.get('Low', 0)
    pct = (count / len(iris_data_complete)) * 100
    st.metric("🟡 Low (20-40)", f"{count}", f"{pct:.1f}%")

with col3:
    count = risk_counts.get('Moderate', 0)
    pct = (count / len(iris_data_complete)) * 100
    st.metric("🟠 Moderate (40-60)", f"{count}", f"{pct:.1f}%")

with col4:
    count = risk_counts.get('High', 0)
    pct = (count / len(iris_data_complete)) * 100
    st.metric("🔴 High (60-80)", f"{count}", f"{pct:.1f}%")

with col5:
    count = risk_counts.get('Very High', 0)
    pct = (count / len(iris_data_complete)) * 100
    st.metric("🔴🔴 Very High (80-100)", f"{count}", f"{pct:.1f}%")

# Interactive map
st.markdown("---")
st.subheader("🗺️ Composite Risk Map")

# Create choropleth map
fig_map = px.choropleth_mapbox(
    iris_data_complete,
    geojson=iris_data_complete.geometry,
    locations=iris_data_complete.index,
    color='composite_risk',
    hover_name='nom_iris',
    hover_data={
        'nom_com': True,
        'avg_heat_score': ':.2f',
        'pct_elderly_55': ':.2f',
        'pct_elderly_55_alone': ':.2f',
        'composite_risk': ':.1f',
        'risk_category': True
    },
    color_continuous_scale='RdYlGn_r',
    range_color=[0, 100],
    zoom=11,
    center={'lat': 48.8566, 'lon': 2.3522},
    opacity=0.7,
    labels={
        'composite_risk': 'Risk Score',
        'nom_iris': 'IRIS Name',
        'nom_com': 'Arrondissement',
        'avg_heat_score': 'Heat Score',
        'pct_elderly_55': '% Elderly (55+)',
        'pct_elderly_55_alone': '% Elderly Alone',
        'risk_category': 'Risk Category'
    }
)

fig_map.update_layout(
    mapbox_style='open-street-map',
    height=700,
    margin={"r": 0, "t": 0, "l": 0, "b": 0}
)

st.plotly_chart(fig_map, use_container_width=True)

st.caption("🔍 Hover over IRIS zones to see detailed risk breakdown. Red areas indicate higher composite risk.")

# Risk analysis tabs
st.markdown("---")

tab1, tab2, tab3 = st.tabs(["🎯 High-Risk Zones", "📈 Distribution Analysis", "🔄 Factor Comparison"])

# TAB 1: High-Risk Zones
with tab1:
    st.subheader("🎯 Highest Risk IRIS Zones")

    high_risk_zones = iris_data_complete[iris_data_complete['composite_risk'] >= 60].copy()
    high_risk_zones = high_risk_zones.sort_values('composite_risk', ascending=False)

    if len(high_risk_zones) > 0:
        st.info(f"""
        **{len(high_risk_zones)} IRIS zones identified as high or very high risk** (score ≥ 60)

        These areas should be prioritized for heat adaptation interventions.
        """)

        # Top 20 table
        st.markdown("**Top 20 Highest Risk Zones:**")

        display_cols = ['nom_iris', 'nom_com', 'avg_heat_score', 'pct_elderly_55',
                       'pct_elderly_55_alone', 'composite_risk', 'risk_category']

        display_data = high_risk_zones[display_cols].head(20).reset_index(drop=True)
        display_data.columns = ['IRIS Name', 'Arrondissement', 'Heat Score',
                               '% Elderly', '% Elderly Alone', 'Risk Score', 'Category']

        display_data.index = display_data.index + 1

        st.dataframe(
            display_data.style.background_gradient(subset=['Risk Score'], cmap='Reds'),
            use_container_width=True,
            height=400
        )

        # Characteristics of high-risk zones
        st.markdown("---")
        st.markdown("**📊 Characteristics of High-Risk Zones:**")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Avg Heat Score",
                f"{high_risk_zones['avg_heat_score'].mean():.2f}",
                help="Average heat score in high-risk zones"
            )

        with col2:
            st.metric(
                "Avg % Elderly",
                f"{high_risk_zones['pct_elderly_55'].mean():.1f}%",
                help="Average elderly population in high-risk zones"
            )

        with col3:
            st.metric(
                "Avg % Elderly Alone",
                f"{high_risk_zones['pct_elderly_55_alone'].mean():.1f}%",
                help="Average elderly living alone in high-risk zones"
            )

    else:
        st.success("✅ No high-risk zones identified with current weights!")

# TAB 2: Distribution Analysis
with tab2:
    st.subheader("📈 Risk Score Distribution")

    col1, col2 = st.columns(2)

    with col1:
        # Histogram
        fig_hist = px.histogram(
            iris_data_complete,
            x='composite_risk',
            nbins=30,
            title='Distribution of Composite Risk Scores',
            labels={'composite_risk': 'Risk Score'},
            color_discrete_sequence=['#EF553B']
        )
        fig_hist.update_layout(showlegend=False)
        st.plotly_chart(fig_hist, use_container_width=True)

    with col2:
        # Risk category pie chart
        risk_dist = iris_data_complete['risk_category'].value_counts()
        fig_pie = px.pie(
            values=risk_dist.values,
            names=risk_dist.index,
            title='Risk Category Distribution',
            color=risk_dist.index,
            color_discrete_map={
                'Very Low': '#2ca02c',
                'Low': '#98df8a',
                'Moderate': '#ffdd57',
                'High': '#ff8c42',
                'Very High': '#d62828'
            }
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    # Scatter plot: factors vs risk
    st.markdown("---")
    st.markdown("**🔍 Factor Contributions to Risk:**")

    col1, col2 = st.columns(2)

    with col1:
        fig_scatter1 = px.scatter(
            iris_data_complete,
            x='avg_heat_score',
            y='composite_risk',
            color='risk_category',
            title='Heat Score vs Composite Risk',
            labels={'avg_heat_score': 'Heat Score', 'composite_risk': 'Risk Score'},
            color_discrete_map={
                'Very Low': '#2ca02c',
                'Low': '#98df8a',
                'Moderate': '#ffdd57',
                'High': '#ff8c42',
                'Very High': '#d62828'
            },
            opacity=0.6
        )
        st.plotly_chart(fig_scatter1, use_container_width=True)

    with col2:
        fig_scatter2 = px.scatter(
            iris_data_complete,
            x='pct_elderly_55',
            y='composite_risk',
            color='risk_category',
            title='% Elderly vs Composite Risk',
            labels={'pct_elderly_55': '% Elderly (55+)', 'composite_risk': 'Risk Score'},
            color_discrete_map={
                'Very Low': '#2ca02c',
                'Low': '#98df8a',
                'Moderate': '#ffdd57',
                'High': '#ff8c42',
                'Very High': '#d62828'
            },
            opacity=0.6
        )
        st.plotly_chart(fig_scatter2, use_container_width=True)

# TAB 3: Factor Comparison
with tab3:
    st.subheader("🔄 Compare Different Weight Scenarios")

    st.markdown("""
    See how different weight combinations affect risk assessment:
    """)

    # Predefined scenarios
    scenarios = {
        'Heat-Focused (70/15/15)': {'heat': 0.70, 'elderly': 0.15, 'isolation': 0.15},
        'Balanced (33/33/33)': {'heat': 0.33, 'elderly': 0.33, 'isolation': 0.33},
        'Demographics-Focused (20/40/40)': {'heat': 0.20, 'elderly': 0.40, 'isolation': 0.40},
        'Current Settings': {
            'heat': heat_weight_norm,
            'elderly': elderly_weight_norm,
            'isolation': isolation_weight_norm
        }
    }

    scenario_results = []

    for name, weights in scenarios.items():
        # Calculate risk for this scenario
        risk = (
            weights['heat'] * iris_data_complete['heat_normalized'] +
            weights['elderly'] * iris_data_complete['elderly_normalized'] +
            weights['isolation'] * iris_data_complete['isolation_normalized']
        ) * 100

        very_high = len(risk[risk >= 80])
        high = len(risk[(risk >= 60) & (risk < 80)])
        moderate = len(risk[(risk >= 40) & (risk < 60)])
        low = len(risk[risk < 40])

        scenario_results.append({
            'Scenario': name,
            'Very High (80-100)': very_high,
            'High (60-80)': high,
            'Moderate (40-60)': moderate,
            'Low (0-40)': low,
            'Avg Risk': risk.mean()
        })

    scenario_df = pd.DataFrame(scenario_results)

    st.dataframe(scenario_df, use_container_width=True)

    # Visualization
    fig_scenarios = go.Figure()

    fig_scenarios.add_trace(go.Bar(
        name='Very High (80-100)',
        x=scenario_df['Scenario'],
        y=scenario_df['Very High (80-100)'],
        marker_color='#d62828'
    ))

    fig_scenarios.add_trace(go.Bar(
        name='High (60-80)',
        x=scenario_df['Scenario'],
        y=scenario_df['High (60-80)'],
        marker_color='#ff8c42'
    ))

    fig_scenarios.add_trace(go.Bar(
        name='Moderate (40-60)',
        x=scenario_df['Scenario'],
        y=scenario_df['Moderate (40-60)'],
        marker_color='#ffdd57'
    ))

    fig_scenarios.add_trace(go.Bar(
        name='Low (0-40)',
        x=scenario_df['Scenario'],
        y=scenario_df['Low (0-40)'],
        marker_color='#98df8a'
    ))

    fig_scenarios.update_layout(
        title='Risk Zones by Scenario',
        xaxis_title='Scenario',
        yaxis_title='Number of IRIS Zones',
        barmode='stack',
        height=500
    )

    st.plotly_chart(fig_scenarios, use_container_width=True)

    st.info("""
    **Interpretation:**
    - **Heat-Focused**: Prioritizes thermal exposure (useful for immediate heat wave response)
    - **Balanced**: Equal consideration of all factors (recommended for general planning)
    - **Demographics-Focused**: Prioritizes vulnerable populations (useful for social programs)
    - **Current Settings**: Your custom weight configuration

    Adjust the sliders in the sidebar to create your own scenario!
    """)

# Download data
st.markdown("---")
st.subheader("💾 Download Risk Assessment Data")

export_data = iris_data_complete[[
    'code_iris', 'nom_iris', 'nom_com',
    'avg_heat_score', 'pct_elderly_55', 'pct_elderly_55_alone',
    'composite_risk', 'risk_category'
]].copy()

export_data.columns = [
    'IRIS Code', 'IRIS Name', 'Arrondissement',
    'Heat Score', '% Elderly (55+)', '% Elderly Alone',
    'Composite Risk Score', 'Risk Category'
]

csv = export_data.to_csv(index=False)
st.download_button(
    label="📥 Download Risk Assessment as CSV",
    data=csv,
    file_name=f"paris_iris_risk_assessment.csv",
    mime="text/csv"
)

# Sidebar additional info
with st.sidebar:
    st.markdown("---")
    st.markdown("### 💡 How to Use")
    st.info("""
    1. **Adjust weights** using the sliders above
    2. **View the map** to see how risk distribution changes
    3. **Explore tabs** for detailed analysis
    4. **Compare scenarios** to understand trade-offs
    5. **Download data** for further analysis
    """)

    st.markdown("---")
    st.markdown("### 📖 About Risk Categories")
    st.markdown("""
    **🔴🔴 Very High (80-100)**
    Immediate intervention needed

    **🔴 High (60-80)**
    Priority areas for action

    **🟠 Moderate (40-60)**
    Monitor and plan interventions

    **🟡 Low (20-40)**
    Lower priority

    **🟢 Very Low (0-20)**
    Minimal risk
    """)
