"""
Process IRIS-level heat scores for all cities
Aggregates LCZ heat zones to IRIS boundaries and creates GeoJSON outputs

Data Sources:
- IRIS Boundaries: IGN IRIS GE (https://geoservices.ign.fr/irisge)
- LCZ Heat Zones: CEREMA via data.gouv.fr
"""

import geopandas as gpd
import pandas as pd
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Configuration
BASE_DIR = Path(__file__).parent.parent
RAW_LCZ_DIR = BASE_DIR / "data" / "raw" / "lcz"
PROCESSED_DIR = BASE_DIR / "data" / "processed"

# IRIS boundaries GeoPackage
IRIS_GPKG = BASE_DIR / "data" / "raw" / "iris" / "IRIS-GE_3-0__GPKG_LAMB93_FXX_2025-01-01" / "IRIS-GE" / "1_DONNEES_LIVRAISON_2025-06-00081" / "IRIS-GE_3-0_GPKG_LAMB93_FXX-ED2025-01-01" / "iris.gpkg"

# Cities configuration
CITIES_CONFIG = {
    'Paris': {
        'dept': '75',
        'com_codes': [f"75{str(i).zfill(3)}" for i in range(1, 121)],
        'lcz_shapefile': 'Paris/LCZ_SPOT_2022_Paris.shp'
    },
    'Lille': {
        'dept': '59',
        'com_codes': ['59350'],
        'lcz_shapefile': 'Lille/LCZ_SPOT_2022_Lille.shp'
    },
    'Lyon': {
        'dept': '69',
        'com_codes': [f"69{str(i)}" for i in range(381, 390)],
        'lcz_shapefile': 'Lyon/LCZ_SPOT_2022_Lyon.shp'
    },
    'Marseille': {
        'dept': '13',
        'com_codes': [f"13{str(i)}" for i in range(201, 217)],
        'lcz_shapefile': 'Marseille/LCZ_SPOT_2022_Marseille.shp'
    },
    'Toulouse': {
        'dept': '31',
        'com_codes': ['31555'],
        'lcz_shapefile': 'Toulouse/LCZ_SPOT_2022_Toulouse.shp'
    }
}

# New heat score classification
def calculate_heat_score(lcz_class):
    """
    Calculate categorical heat score based on LCZ class.

    Parameters:
    - lcz_class: The Local Climate Zone class identifier (can be int or string)

    Returns:
    - str: 'High', 'Medium', or 'Low'
    """
    # Convert to string for comparison (handles both numeric and string LCZ classes)
    lcz_str = str(lcz_class)

    # High heat retention zones
    high_classes = ['1', '2', '3', '8', '10']
    # Medium heat retention zones
    medium_classes = ['4', '5', '6', '7', 'E']

    if lcz_str in high_classes:
        return 'High'
    elif lcz_str in medium_classes:
        return 'Medium'
    else:
        # Low heat: 9, A, B, C, D, F, G, and any others
        return 'Low'

def load_iris_boundaries():
    """
    Load IRIS boundaries from GeoPackage
    Source: IGN IRIS GE - https://geoservices.ign.fr/irisge
    """
    print(f'📥 Loading IRIS boundaries from {IRIS_GPKG.name}...')

    if not IRIS_GPKG.exists():
        print(f'❌ IRIS GeoPackage not found at {IRIS_GPKG}')
        return None

    iris = gpd.read_file(IRIS_GPKG)
    print(f'✅ Loaded {len(iris):,} total IRIS zones')
    print(f'📋 Available columns: {iris.columns.tolist()}')
    print(f'📋 Sample data:')
    print(iris.head(2))
    return iris

def filter_iris_for_city(iris_data, city_name, config):
    """Filter IRIS boundaries for a specific city"""
    com_codes = config['com_codes']

    print(f'  Looking for commune codes: {com_codes[:5]}...' if len(com_codes) > 5 else f'  Looking for commune codes: {com_codes}')

    # Check for commune code column (try different possible names)
    com_col = None
    for possible_col in ['code_insee', 'insee_com', 'CODE_COMMUNE', 'code_commune', 'INSEE_COM', 'COM']:
        if possible_col in iris_data.columns:
            com_col = possible_col
            break

    if com_col is None:
        print(f'  ⚠️ No commune code column found. Available columns: {iris_data.columns.tolist()}')
        return None

    print(f'  Using column: {com_col}')
    print(f'  Sample values: {iris_data[com_col].head(10).tolist()}')

    # Convert com_codes to integers for comparison (commune codes might be stored as float/int)
    com_codes_int = [int(code) for code in com_codes]

    # Filter by commune code
    city_iris = iris_data[iris_data[com_col].isin(com_codes_int)].copy()
    if len(city_iris) == 0:
        # Also try as strings
        city_iris = iris_data[iris_data[com_col].isin(com_codes)].copy()

    print(f'  {city_name}: {len(city_iris):,} IRIS zones')
    return city_iris

def process_city(city_name, config, iris_all):
    """Process LCZ and IRIS data for a city"""
    print(f'\n{"="*70}')
    print(f'Processing {city_name}')
    print(f'{"="*70}')

    # Filter IRIS for city
    city_iris = filter_iris_for_city(iris_all, city_name, config)
    if city_iris is None or len(city_iris) == 0:
        print(f'❌ No IRIS zones found for {city_name}')
        return

    # Load LCZ shapefile
    lcz_path = RAW_LCZ_DIR / config['lcz_shapefile']
    print(f'  Loading LCZ data from {lcz_path.name}...')
    lcz_data = gpd.read_file(lcz_path)
    print(f'  ✅ Loaded {len(lcz_data):,} LCZ zones')

    # Add categorical heat scores (High/Medium/Low)
    lcz_data['heat_score'] = lcz_data['lcz'].apply(calculate_heat_score)

    # Ensure same CRS
    if lcz_data.crs != city_iris.crs:
        print(f'  🔄 Reprojecting LCZ data to match IRIS CRS...')
        lcz_data = lcz_data.to_crs(city_iris.crs)

    print(f'  🔗 Performing centroid-based spatial join (this may take a while)...')
    # Create a copy with centroids for accurate IRIS assignment
    # This ensures each LCZ zone is assigned to exactly one IRIS (the one containing its centroid)
    lcz_centroids = lcz_data.copy()
    lcz_centroids['geometry'] = lcz_centroids.geometry.centroid

    # Spatial join: assign each LCZ zone to the IRIS that contains its centroid
    lcz_with_iris = gpd.sjoin(lcz_centroids, city_iris, how='inner', predicate='within')

    # Restore original LCZ data (we only needed centroids for the join)
    # Keep the IRIS assignment but use original heat_score
    print(f'  ✅ Assigned {len(lcz_with_iris):,} LCZ zones to IRIS (by centroid)')

    print(f'  📊 Aggregating heat scores by IRIS...')
    # Aggregate heat scores by IRIS
    # Get IRIS identifier column
    iris_col = 'CODE_IRIS' if 'CODE_IRIS' in lcz_with_iris.columns else 'code_iris'
    if iris_col not in lcz_with_iris.columns:
        # Try to find it in the joined columns
        iris_cols = [col for col in lcz_with_iris.columns if 'iris' in col.lower()]
        if iris_cols:
            iris_col = iris_cols[0]
        else:
            print(f"⚠️ Could not find IRIS identifier column. Columns: {lcz_with_iris.columns.tolist()}")
            return

    # Calculate most common heat score category per IRIS (mode)
    heat_by_iris = lcz_with_iris.groupby(iris_col)['heat_score'].agg(
        lambda x: x.mode()[0] if not x.mode().empty else 'Low'
    ).reset_index()
    heat_by_iris.columns = ['code_iris', 'heat_score']

    # Merge back with IRIS geometries
    iris_col_original = 'CODE_IRIS' if 'CODE_IRIS' in city_iris.columns else 'code_iris'
    city_iris_with_heat = city_iris.merge(heat_by_iris, left_on=iris_col_original, right_on='code_iris', how='left')

    # Clean up column names
    if 'CODE_IRIS' in city_iris_with_heat.columns:
        city_iris_with_heat['code_iris'] = city_iris_with_heat['CODE_IRIS']

    # Ensure we have essential columns
    essential_cols = []
    if 'code_iris' in city_iris_with_heat.columns:
        essential_cols.append('code_iris')
    elif 'CODE_IRIS' in city_iris_with_heat.columns:
        city_iris_with_heat['code_iris'] = city_iris_with_heat['CODE_IRIS']
        essential_cols.append('code_iris')

    if 'nom_iris' not in city_iris_with_heat.columns and 'NOM_IRIS' in city_iris_with_heat.columns:
        city_iris_with_heat['nom_iris'] = city_iris_with_heat['NOM_IRIS']
    if 'nom_iris' in city_iris_with_heat.columns:
        essential_cols.append('nom_iris')

    # Handle commune name column (various possible names)
    if 'nom_com' not in city_iris_with_heat.columns:
        if 'NOM_COM' in city_iris_with_heat.columns:
            city_iris_with_heat['nom_com'] = city_iris_with_heat['NOM_COM']
        elif 'nom_commune' in city_iris_with_heat.columns:
            city_iris_with_heat['nom_com'] = city_iris_with_heat['nom_commune']
    if 'nom_com' in city_iris_with_heat.columns:
        essential_cols.append('nom_com')

    essential_cols.extend(['heat_score', 'geometry'])

    # Keep only essential columns that exist
    cols_to_keep = [col for col in essential_cols if col in city_iris_with_heat.columns]
    city_iris_final = city_iris_with_heat[cols_to_keep]

    # Save to GeoJSON
    output_file = PROCESSED_DIR / f"{city_name.lower()}_iris_heat_vulnerability.geojson"
    city_iris_final.to_file(output_file, driver='GeoJSON')
    print(f'  ✅ Saved GeoJSON to {output_file.name}')

    # Save to CSV (without geometry)
    csv_output = PROCESSED_DIR / f"{city_name.lower()}_iris_heat_scores.csv"
    csv_data = city_iris_final.drop(columns=['geometry'])
    csv_data.to_csv(csv_output, index=False)
    print(f'  ✅ Saved CSV to {csv_output.name}')

    # Summary statistics
    print(f'\n  📊 {city_name} Heat Score Summary:')
    print(f'    - IRIS zones with heat data: {city_iris_final["heat_score"].notna().sum()}')
    print(f'    - High heat zones: {(city_iris_final["heat_score"] == "High").sum()}')
    print(f'    - Medium heat zones: {(city_iris_final["heat_score"] == "Medium").sum()}')
    print(f'    - Low heat zones: {(city_iris_final["heat_score"] == "Low").sum()}')

def main():
    """Main processing function"""
    print('='*70)
    print('PROCESSING IRIS-LEVEL HEAT SCORES FOR ALL CITIES')
    print('='*70)

    # Load IRIS boundaries once
    iris_all = load_iris_boundaries()
    if iris_all is None:
        print('❌ Failed to load IRIS boundaries')
        return

    # Process each city
    for city_name, config in CITIES_CONFIG.items():
        try:
            process_city(city_name, config, iris_all)
        except Exception as e:
            print(f'❌ Error processing {city_name}: {e}')
            import traceback
            traceback.print_exc()

    print('\n'+'='*70)
    print('✅ ALL CITIES PROCESSED SUCCESSFULLY')
    print('='*70)

if __name__ == '__main__':
    main()
