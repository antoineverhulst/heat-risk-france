"""
Risque de Chaleur en France - Application
Analyse du risque de chaleur urbaine dans les villes françaises en combinant
l'exposition thermique et la vulnérabilité de la population
"""

import streamlit as st
import geopandas as gpd
import pandas as pd
import plotly.express as px
from pathlib import Path

# Configuration de la page
st.set_page_config(
    page_title="Risque de Chaleur France",
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
    Charge et fusionne toutes les données pour une ville
    Retourne un GeoDataFrame avec toutes les métriques
    """
    city_lower = city_name.lower()

    # Charger le GeoJSON avec les scores de chaleur et la géométrie
    geojson_file = PROCESSED_DATA_DIR / f"{city_lower}_iris_heat_vulnerability.geojson"
    elderly_file = PROCESSED_DATA_DIR / f"{city_lower}_iris_elderly_pct.csv"

    if not geojson_file.exists() or not elderly_file.exists():
        return None

    # Charger les données géographiques
    iris_geo = gpd.read_file(geojson_file)

    # Charger les données démographiques
    elderly_data = pd.read_csv(elderly_file)

    # S'assurer que les types correspondent pour la fusion
    iris_geo['code_iris'] = iris_geo['code_iris'].astype(str)
    elderly_data['IRIS'] = elderly_data['IRIS'].astype(str)

    # Fusionner les ensembles de données
    combined = iris_geo.merge(
        elderly_data,
        left_on='code_iris',
        right_on='IRIS',
        how='left'
    )

    # Calculer la densité de population (projeter d'abord en CRS métrique pour un calcul précis de la surface)
    # EPSG:2154 est Lambert-93, la projection officielle pour la France
    combined_projected = combined.to_crs(epsg=2154)
    combined['area_km2'] = combined_projected.geometry.area / 1_000_000  # Convertir m² en km²
    combined['population_density'] = combined['total_population'] / combined['area_km2']

    # Calculer les indicateurs de risque en utilisant le heat_score catégoriel
    def calculate_heat_multiplier(heat_score):
        """Calcule le multiplicateur de chaleur à partir du score de chaleur catégoriel"""
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
    """Affiche la section d'accueil"""
    st.title("🌡️ Risque de Chaleur en France")
    st.markdown("""
    ### Comprendre le Risque de Chaleur Urbaine et la Vulnérabilité Sociale

    Les îlots de chaleur urbains se forment lorsque les villes remplacent la couverture végétale naturelle
    par des concentrations denses de chaussées, bâtiments et autres surfaces qui absorbent et retiennent la chaleur.
    Cela crée des « îlots » de températures plus élevées par rapport aux zones environnantes.

    **La vulnérabilité sociale** amplifie le risque de chaleur. Les recherches d'Eric Klinenberg sur la canicule
    de Chicago en 1995 ont montré que l'isolement social, en particulier chez les personnes âgées,
    augmente considérablement la mortalité lors d'épisodes de chaleur extrême.

    Cet outil combine :
    - 🌡️ **Exposition à la Chaleur** : Classification par zones climatiques locales (Élevée/Moyenne/Faible)
    - 👴 **Vulnérabilité Démographique** : Données de population âgée de l'INSEE
    - 🏠 **Isolement Social** : Pourcentage de personnes âgées vivant seules
    """)

    st.markdown("---")

    if city_data is not None and len(city_data) > 0:
        st.subheader("🔍 Points Clés")

        col1, col2 = st.columns(2)

        with col1:
            high_heat = len(city_data[city_data['heat_score'] == 'High'])
            high_heat_pct = (high_heat / len(city_data)) * 100
            st.info(f"""
            **🔥 Zones à Chaleur Élevée**
            - {high_heat} zones IRIS classées à chaleur élevée
            - Représente {high_heat_pct:.1f}% de {selected_city}
            - Zones à rétention de chaleur la plus forte
            """)

        with col2:
            high_vulnerable = len(city_data[city_data['elderly_55_plus_alone'] > 200])
            high_vulnerable_pct = (high_vulnerable / len(city_data)) * 100
            st.info(f"""
            **👴 Populations Vulnérables**
            - {high_vulnerable} zones IRIS avec >200 personnes âgées (55+) vivant seules
            - Représente {high_vulnerable_pct:.1f}% de {selected_city}
            - Zones prioritaires pour l'intervention
            """)
    else:
        st.warning(f"Aucune donnée disponible pour {selected_city}")


def create_plotly_map(city_data, city_center, metric_col, metric_name, colormap='YlOrRd'):
    """Créer une carte choroplèthe Plotly mapbox avec des couleurs adaptées au daltonisme"""

    if metric_col not in city_data.columns:
        return None

    # Reprojeter en EPSG:4326 (WGS84) pour la compatibilité avec mapbox
    city_data_map = city_data.copy()
    if city_data_map.crs is not None and city_data_map.crs.to_epsg() != 4326:
        city_data_map = city_data_map.to_crs(epsg=4326)

    # Vérifier s'il s'agit du heat_score catégoriel
    if metric_col == 'heat_score':
        # Créer une carte de couleurs discrètes pour les catégories de heat_score
        color_discrete_map = {
            'High': '#e31a1c',    # Rouge
            'Medium': '#fd8d3c',  # Orange
            'Low': '#91cf60'      # Vert
        }

        # S'assurer que la colonne heat_score a les bonnes catégories
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
        # Échelle continue pour les métriques numériques
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
    """Affiche la section d'analyse cartographique"""
    st.title("Découvrir la composition du territoire")
    st.markdown(f"### Cartographie interactive de la chaleur et de la démographie pour {selected_city}")

    if city_data is None or len(city_data) == 0:
        st.warning(f"Aucune donnée disponible pour {selected_city}")
        return

    # Sélecteur de métrique en haut de cette section
    metric_options = {
        'Catégorie de chaleur': 'heat_score',
        'Densité de population': 'population_density',
        '% personnes âgées (55+)': 'pct_elderly_55',
        '% personnes âgées vivant seules': 'pct_elderly_55_alone',
        'Nombre de personnes âgées (55+) seules': 'elderly_55_plus_alone',
        'Nombre de personnes âgées (80+) seules': 'elderly_80_plus_alone'
    }

    selected_metric_name = st.selectbox(
        "Sélectionner la métrique à visualiser sur la carte :",
        options=list(metric_options.keys()),
        index=0,
        key="iris_map_metric",
        help="Choisissez quelle métrique afficher sur la carte IRIS"
    )

    metric_col = metric_options[selected_metric_name]

    st.markdown("---")

    # Carte
    st.subheader("Carte interactive")

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
    """Affiche la section d'analyse de risque - Carte et tableau Top 20"""
    st.title("Déterminer les zones à risques")
    st.markdown(f"### Indicateurs de risque basés sur la chaleur pour {selected_city}")

    if city_data is None or len(city_data) == 0:
        st.warning(f"Aucune donnée disponible pour {selected_city}")
        return

    # Explication de la méthodologie
    with st.expander("📖 Méthodologie", expanded=False):
        st.markdown("""
        ### Calcul des indicateurs de risque

        Nos indicateurs de risque combinent l'exposition à la chaleur avec les populations vulnérables :

        **Classification des scores de chaleur :**
        - **Faible** : classes LCZ avec rétention de chaleur minimale (parcs, eau, végétation)
        - **Moyenne** : classes LCZ 4, 5, 6, 7, E (zones urbaines ouvertes)
        - **Élevée** : classes LCZ 1, 2, 3, 8, 10 (zones urbaines compactes)

        **Multiplicateur de chaleur :**
        - 0 pour score de chaleur faible
        - 1 pour score de chaleur moyen
        - 2 pour score de chaleur élevé

        **Indicateur de risque** = multiplicateur de chaleur × nombre de personnes âgées (55+) vivant seules

        **Indicateur de risque extrême** = multiplicateur de chaleur × nombre de personnes âgées (80+) vivant seules

        Cette approche priorise les zones où :
        1. L'exposition à la chaleur est significative (moyenne ou élevée)
        2. Des populations vulnérables sont présentes
        3. L'isolement social augmente le risque
        """)

    st.markdown("---")

    # Sélecteur de métrique de risque en haut de cette section
    risk_options = {
        'Indicateur de risque (55+ seules)': {
            'col': 'risk_indicator',
            'elderly_col': 'elderly_55_plus_alone',
            'label': 'Indicateur de risque'
        },
        'Indicateur de risque extrême (80+ seules)': {
            'col': 'extreme_risk_indicator',
            'elderly_col': 'elderly_80_plus_alone',
            'label': 'Indicateur de risque extrême'
        }
    }

    selected_risk_name = st.selectbox(
        "Sélectionner l'indicateur de risque à visualiser :",
        options=list(risk_options.keys()),
        index=0,
        key="risk_calculator_metric",
        help="Choisissez l'indicateur de risque à analyser"
    )

    risk_info = risk_options[selected_risk_name]
    risk_col = risk_info['col']
    elderly_col = risk_info['elderly_col']

    # Carte de risque
    st.markdown("---")
    st.subheader(f"Carte : {selected_risk_name}")

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

    # Tableau des 20 zones à risque le plus élevé
    st.markdown("---")
    st.subheader(f"Top 20 des zones IRIS par {selected_risk_name}")

    top_20 = city_data.nlargest(20, risk_col)[
        ['nom_iris', 'nom_com', 'heat_score', 'heat_multiplier',
         elderly_col, risk_col]
    ].reset_index(drop=True)

    top_20.columns = ['Nom IRIS', 'Arrondissement', 'Score de chaleur', 'Multiplicateur de chaleur',
                      risk_info['elderly_col'].replace('_', ' ').title(), risk_info['label']]
    top_20.index = top_20.index + 1

    st.dataframe(
        top_20.style.background_gradient(
            subset=[risk_info['label']],
            cmap='Oranges' if 'risque' in selected_risk_name else 'Reds'
        ),
        use_container_width=True
    )


def render_about(selected_city, city_data):
    """Affiche la section À Propos"""
    st.title("📖 À Propos de ce Projet")

    st.markdown("""
    ### Méthodologie

    Cette application analyse le risque de chaleur urbaine en combinant les données d'exposition thermique
    avec des indicateurs de vulnérabilité démographique au niveau IRIS (îlot regroupé pour l'information statistique).

    #### Évaluation de l'Exposition à la Chaleur

    Les scores de chaleur sont dérivés de la classification des **Zones Climatiques Locales (LCZ)** :
    - **Source** : Données LCZ 2022 du CEREMA pour les villes françaises
    - **Classification** : Catégorielle (Élevée/Moyenne/Faible)
    - **Agrégation** : Catégorie LCZ la plus commune au sein de chaque zone IRIS

    | Score de Chaleur | Classes LCZ | Description |
    |------------------|-------------|-------------|
    | **Élevée** | 1, 2, 3, 8, 10 | Zones urbaines compactes avec bâtiments denses |
    | **Moyenne** | 4, 5, 6, 7, E | Zones urbaines ouvertes et mixtes |
    | **Faible** | 9, A, B, C, D, F, G | Zones végétalisées, plans d'eau, parcs |

    #### Vulnérabilité Démographique

    Données de population de l'INSEE (Institut national de la statistique) :
    - **% Personnes Âgées (55+)** : Pourcentage de la population âgée de 55 ans et plus
    - **% Personnes Âgées Vivant Seules** : Indicateur d'isolement social
    - **Comptes absolus** : Nombre d'individus vulnérables par IRIS

    Les populations âgées sont plus sensibles au stress thermique, et l'isolement social
    augmente significativement le risque de mortalité pendant les vagues de chaleur.

    #### Indicateurs de Risque

    Nos indicateurs de risque combinent les catégories d'exposition à la chaleur avec les populations vulnérables :

    **Multiplicateur de Chaleur :**
    - Chaleur Faible = 0 (aucun risque lié à la chaleur)
    - Chaleur Moyenne = 1 (risque modéré)
    - Chaleur Élevée = 2 (risque significatif)

    **Indicateur de Risque** = Multiplicateur de Chaleur × Nombre de Personnes Âgées (55+) Vivant Seules

    Cette approche priorise les zones avec :
    1. **Une exposition significative à la chaleur** (Moyenne ou Élevée)
    2. **Des populations vulnérables** (personnes âgées vivant seules)
    3. **Un risque combiné** (multiplicateur de chaleur × nombre de personnes vulnérables)

    ### Contexte de Recherche

    Ce travail est inspiré par :

    **📚 Livres & Articles :**
    - **Klinenberg, E. (2002)** - *Heat Wave: A Social Autopsy of Disaster in Chicago*
      - Recherche pionnière montrant que l'isolement social, et non la pauvreté seule,
        était le facteur principal de mortalité liée à la chaleur pendant la canicule de Chicago en 1995
    - **Harlan, S. L., et al. (2006)** - "Neighborhood Effects on Heat Deaths"
      - Analyse des schémas spatiaux de la vulnérabilité à la chaleur

    ### Sources de Données

    - **Données LCZ** : CEREMA (2022) via data.gouv.fr
    - **Limites IRIS** : IGN (Institut national de l'information géographique et forestière) - [IRIS GE](https://geoservices.ign.fr/irisge)
    - **Données démographiques** : INSEE (2022)
    - **Licence** : Licence Ouverte / Open License

    ### Limitations

    - Les LCZ sont un **proxy** pour l'exposition à la chaleur, pas une mesure directe de température
    - Ne prend pas en compte les événements de canicule spécifiques ou les conditions en temps réel
    - Les données démographiques sont mises à jour annuellement, peuvent ne pas refléter les changements récents
    - Les scores de risque sont des **indicateurs relatifs**, pas des prédictions absolues
    - Ne prend pas en compte :
      - La prévalence de la climatisation
      - L'accès aux espaces verts
      - Les réseaux de soutien social
      - L'accessibilité aux soins de santé

    ### Télécharger les Données
    """)

    # Boutons de téléchargement
    if city_data is not None and len(city_data) > 0:
        st.subheader(f"📥 Télécharger les Données de {selected_city}")

        col1, col2 = st.columns(2)

        with col1:
            # Préparer les données CSV (sans géométrie)
            csv_data = city_data.drop(columns=['geometry']).copy()
            csv_string = csv_data.to_csv(index=False)

            st.download_button(
                label="📄 Télécharger l'Ensemble de Données Complet (CSV)",
                data=csv_string,
                file_name=f"{selected_city.lower()}_donnees_risque_chaleur.csv",
                mime="text/csv",
                help="Ensemble de données complet avec toutes les métriques"
            )

        with col2:
            # Scores de risque uniquement
            risk_data = city_data[[
                'code_iris', 'nom_iris', 'nom_com',
                'heat_score', 'heat_multiplier',
                'elderly_55_plus_alone', 'elderly_80_plus_alone',
                'risk_indicator', 'extreme_risk_indicator'
            ]].copy()
            risk_csv = risk_data.to_csv(index=False)

            st.download_button(
                label="⚖️ Télécharger les Scores de Risque (CSV)",
                data=risk_csv,
                file_name=f"{selected_city.lower()}_scores_risque.csv",
                mime="text/csv",
                help="Indicateurs de risque uniquement"
            )

    st.markdown("---")
    st.markdown("""
    ### Contact & Contribuer

    Ceci est un projet open-source. Les contributions, suggestions et retours sont les bienvenus !

    **Réalisé avec Streamlit 🎈**
    """)


def main():
    """Application principale - Page unique consolidée"""

    # Titre de la page
    st.title("Quelles zones à risques pour les populations urbaines âgées face à la canicule?")

    st.markdown("---")

    # ========================================================================
    # SECTIONS ÉDUCATIVES
    # ========================================================================
    st.markdown("""
    ### Comprendre le Risque de Chaleur Urbaine et la Vulnérabilité Sociale

    Les îlots de chaleur urbains se forment lorsque les villes remplacent la couverture végétale naturelle
    par des concentrations denses de chaussées, bâtiments et autres surfaces qui absorbent et retiennent la chaleur.
    Cela crée des « îlots » de températures plus élevées par rapport aux zones environnantes.

    **La vulnérabilité sociale** amplifie le risque de chaleur. Les recherches d'Eric Klinenberg sur la canicule
    de Chicago en 1995 ont montré que l'isolement social, en particulier chez les personnes âgées,
    augmente considérablement la mortalité lors d'épisodes de chaleur extrême.

    Cet outil combine :
    - 🌡️ **Exposition à la Chaleur** : Classification par zones climatiques locales (Élevée/Moyenne/Faible)
    - 👴 **Vulnérabilité Démographique** : Données de population âgée de l'INSEE
    - 🏠 **Isolement Social** : Pourcentage de personnes âgées vivant seules
    """)

    st.markdown("---")

    # ========================================================================
    # SÉLECTEUR DE VILLE
    # ========================================================================
    st.markdown("**Choisissez une ville à analyser :**")
    selected_city = st.selectbox(
        "",
        options=CITIES,
        index=0,
        label_visibility="collapsed"
    )

    # Charger les données pour la ville sélectionnée
    city_data = load_city_data(selected_city)

    st.markdown("---")

    # ========================================================================
    # POINTS CLÉS
    # ========================================================================
    if city_data is not None and len(city_data) > 0:
        st.subheader("🔍 Points Clés")

        col1, col2 = st.columns(2)

        with col1:
            high_heat = len(city_data[city_data['heat_score'] == 'High'])
            high_heat_pct = (high_heat / len(city_data)) * 100
            st.info(f"""
            **🔥 Zones à chaleur élevée**
            - {high_heat} zones IRIS classées à chaleur élevée
            - Représente {high_heat_pct:.1f}% de {selected_city}
            - Zones à rétention de chaleur la plus forte
            """)

        with col2:
            high_vulnerable = len(city_data[city_data['elderly_55_plus_alone'] > 200])
            high_vulnerable_pct = (high_vulnerable / len(city_data)) * 100
            st.info(f"""
            **👴 Populations vulnérables**
            - {high_vulnerable} zones IRIS avec >200 personnes âgées (55+) vivant seules
            - Représente {high_vulnerable_pct:.1f}% de {selected_city}
            - Zones prioritaires pour l'intervention
            """)

    st.markdown("---")

    # ========================================================================
    # STATISTIQUES - Deux lignes de 4 métriques
    # ========================================================================
    if city_data is not None and len(city_data) > 0:
        st.subheader("Statistiques")

        # Ligne 1 : Chiffres absolus
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            total_pop = city_data['total_population'].sum()
            st.metric(
                label="Population",
                value=f"{total_pop:,.0f}",
                help="Population totale dans toutes les zones IRIS"
            )

        with col2:
            total_iris = len(city_data)
            st.metric(
                label="Nombre d'IRIS",
                value=f"{total_iris:,}",
                help="Nombre de zones IRIS dans la ville"
            )

        with col3:
            total_elderly_55_alone = city_data['elderly_55_plus_alone'].sum()
            st.metric(
                label="Nombre de personnes âgées (55+) seules",
                value=f"{total_elderly_55_alone:,.0f}",
                help="Nombre total de personnes de 55 ans et plus vivant seules"
            )

        with col4:
            total_elderly_80_alone = city_data['elderly_80_plus_alone'].sum()
            st.metric(
                label="Nombre de personnes âgées (80+) seules",
                value=f"{total_elderly_80_alone:,.0f}",
                help="Nombre total de personnes de 80 ans et plus vivant seules"
            )

        # Ligne 2 : Pourcentages dans les IRIS à score de chaleur élevé
        col5, col6, col7, col8 = st.columns(4)

        # Filtrer les zones à score de chaleur élevé
        high_heat_zones = city_data[city_data['heat_score'] == 'High']

        with col5:
            pop_high_heat = high_heat_zones['total_population'].sum() if len(high_heat_zones) > 0 else 0
            pct_pop_high_heat = (pop_high_heat / total_pop * 100) if total_pop > 0 else 0
            st.metric(
                label="% de population dans les IRIS à chaleur élevée",
                value=f"{pct_pop_high_heat:.1f}%",
                help="Pourcentage de la population vivant dans des zones à chaleur élevée"
            )

        with col6:
            num_high_heat_iris = len(high_heat_zones)
            pct_iris_high_heat = (num_high_heat_iris / total_iris * 100) if total_iris > 0 else 0
            st.metric(
                label="% d'IRIS en zones à chaleur élevée",
                value=f"{pct_iris_high_heat:.1f}%",
                help="Pourcentage de zones IRIS classées à chaleur élevée"
            )

        with col7:
            elderly_55_high_heat = high_heat_zones['elderly_55_plus_alone'].sum() if len(high_heat_zones) > 0 else 0
            pct_elderly_55_high_heat = (elderly_55_high_heat / total_elderly_55_alone * 100) if total_elderly_55_alone > 0 else 0
            st.metric(
                label="% de personnes âgées (55+) seules dans IRIS à chaleur élevée",
                value=f"{pct_elderly_55_high_heat:.1f}%",
                help="Pourcentage de personnes âgées (55+) vivant seules dans des zones à chaleur élevée"
            )

        with col8:
            elderly_80_high_heat = high_heat_zones['elderly_80_plus_alone'].sum() if len(high_heat_zones) > 0 else 0
            pct_elderly_80_high_heat = (elderly_80_high_heat / total_elderly_80_alone * 100) if total_elderly_80_alone > 0 else 0
            st.metric(
                label="% de personnes âgées (80+) seules dans IRIS à chaleur élevée",
                value=f"{pct_elderly_80_high_heat:.1f}%",
                help="Pourcentage de personnes âgées (80+) vivant seules dans des zones à chaleur élevée"
            )

    st.markdown("---")

    # ========================================================================
    # SECTION CARTE IRIS
    # ========================================================================
    render_map_analysis(selected_city, city_data)

    st.markdown("---")

    # ========================================================================
    # SECTION CALCULATEUR DE RISQUE
    # ========================================================================
    render_risk_analysis(selected_city, city_data)

    st.markdown("---")

    # ========================================================================
    # SECTION À PROPOS
    # ========================================================================
    render_about(selected_city, city_data)


if __name__ == "__main__":
    main()
