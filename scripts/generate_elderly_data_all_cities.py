"""
Generate elderly demographic data for all cities
Based on INSEE base-ic-couples-familles-menages-2022 data

This script:
1. Downloads INSEE demographic data
2. Filters for each city's IRIS codes
3. Calculates elderly population percentages
4. Saves CSV files for each city
"""

import pandas as pd
from pathlib import Path
import zipfile
import io
from urllib.request import urlopen
import warnings
warnings.filterwarnings('ignore')

# Configuration
BASE_DIR = Path(__file__).parent.parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"

# Cities configuration - matching the IRIS codes from each city
CITIES_CONFIG = {
    'Paris': {'dept_prefix': '75'},
    'Lille': {'comm_codes': ['59350']},
    'Lyon': {'comm_codes': [f"69{str(i)}" for i in range(381, 390)]},
    'Marseille': {'comm_codes': [f"13{str(i)}" for i in range(201, 217)]},
    'Toulouse': {'comm_codes': ['31555']},
    'Bordeaux': {'comm_codes': ['33063']},
    'Nantes': {'comm_codes': ['44109']},
    'Strasbourg': {'comm_codes': ['67482']},
    'Nice': {'comm_codes': ['06088']},
    'Montpellier': {'comm_codes': ['34172']}
}

# INSEE data URL
INSEE_URL = 'https://www.insee.fr/fr/statistiques/fichier/8647008/base-ic-couples-familles-menages-2022_csv.zip'

def download_insee_data():
    """Download and load INSEE demographic data"""
    print('='*70)
    print('DOWNLOADING INSEE DEMOGRAPHIC DATA')
    print('='*70)
    print(f'\n📥 Downloading from INSEE...')

    try:
        response = urlopen(INSEE_URL)
        zip_buffer = io.BytesIO(response.read())

        with zipfile.ZipFile(zip_buffer, 'r') as zip_ref:
            file_list = zip_ref.namelist()
            print(f'✅ Downloaded! Files in archive: {len(file_list)}')

            # Find CSV file
            csv_files = [f for f in file_list if f.endswith('.CSV')]
            if not csv_files:
                raise ValueError('No CSV file found in archive')

            csv_file = csv_files[0]
            print(f'📂 Loading: {csv_file}')

            # Read CSV
            insee_data = pd.read_csv(
                io.StringIO(zip_ref.read(csv_file).decode('utf-8')),
                dtype={"IRIS": "string", "COM": "string", "LAB_IRIS": "string"},
                sep=';'
            )

            print(f'✅ Loaded {len(insee_data):,} records')
            return insee_data

    except Exception as e:
        print(f'❌ Error downloading INSEE data: {e}')
        return None

def filter_city_data(insee_data, city_name, config):
    """Filter INSEE data for a specific city"""
    print(f'\n  Filtering for {city_name}...')

    # Filter by department prefix or commune codes
    if 'dept_prefix' in config:
        dept_prefix = config['dept_prefix']
        city_data = insee_data[insee_data['IRIS'].astype(str).str.startswith(dept_prefix)].copy()
    elif 'comm_codes' in config:
        comm_codes = config['comm_codes']
        # IRIS codes start with commune code
        city_data = insee_data[
            insee_data['IRIS'].astype(str).str[:5].isin(comm_codes)
        ].copy()
    else:
        print(f'  ⚠️ No filter configuration for {city_name}')
        return None

    print(f'  ✅ Found {len(city_data):,} IRIS zones')
    return city_data

def calculate_elderly_stats(city_data):
    """Calculate elderly population statistics"""
    # Required columns from INSEE data
    IRIS_COL = 'IRIS'
    TOTAL_POP_COL = 'P22_POP15P'  # Total population 15+
    ELDERLY_55_79_COL = 'P22_POP5579'  # Population 55-79
    ELDERLY_80_COL = 'P22_POP80P'  # Population 80+
    ELDERLY_55_79_ALONE_COL = 'P22_POP5579_PSEUL'  # 55-79 living alone
    ELDERLY_80_ALONE_COL = 'P22_POP80P_PSEUL'  # 80+ living alone

    # Create results dataframe
    results = pd.DataFrame()
    results['IRIS'] = city_data[IRIS_COL]
    results['total_population'] = city_data[TOTAL_POP_COL]

    # Calculate elderly 55+ (55-79 + 80+)
    results['elderly_55_plus'] = (
        city_data[ELDERLY_55_79_COL] + city_data[ELDERLY_80_COL]
    )

    # Calculate percentage elderly 55+
    results['pct_elderly_55'] = (
        (results['elderly_55_plus'] / results['total_population'] * 100)
        .round(2)
    )

    # Calculate elderly 55+ living alone
    results['elderly_55_plus_alone'] = (
        city_data[ELDERLY_55_79_ALONE_COL] + city_data[ELDERLY_80_ALONE_COL]
    )

    # Calculate percentage of elderly living alone (among elderly population)
    results['pct_elderly_55_alone'] = (
        (results['elderly_55_plus_alone'] / results['elderly_55_plus'] * 100)
        .round(2)
    )

    # Elderly 80+ living alone
    results['elderly_80_plus_alone'] = city_data[ELDERLY_80_ALONE_COL]

    return results

def process_city(insee_data, city_name, config):
    """Process elderly data for a single city"""
    print(f'\n{"="*70}')
    print(f'Processing {city_name}')
    print(f'{"="*70}')

    # Filter data for city
    city_data = filter_city_data(insee_data, city_name, config)
    if city_data is None or len(city_data) == 0:
        print(f'  ❌ No data found for {city_name}')
        return False

    # Calculate elderly statistics
    print(f'  📊 Calculating elderly statistics...')
    elderly_stats = calculate_elderly_stats(city_data)

    # Save to CSV
    output_file = PROCESSED_DIR / f"{city_name.lower()}_iris_elderly_pct.csv"
    elderly_stats.to_csv(output_file, index=False)
    print(f'  ✅ Saved: {output_file.name}')

    # Print summary statistics
    print(f'\n  📈 Summary Statistics:')
    print(f'    - Total IRIS zones: {len(elderly_stats):,}')
    print(f'    - Mean % elderly (55+): {elderly_stats["pct_elderly_55"].mean():.2f}%')
    print(f'    - Mean % elderly alone: {elderly_stats["pct_elderly_55_alone"].mean():.2f}%')
    print(f'    - Total elderly 80+ alone: {elderly_stats["elderly_80_plus_alone"].sum():.0f}')

    return True

def main():
    """Main processing function"""
    print('\n' + '='*70)
    print('GENERATING ELDERLY DEMOGRAPHIC DATA FOR ALL CITIES')
    print('='*70)

    # Download INSEE data
    insee_data = download_insee_data()
    if insee_data is None:
        print('\n❌ Failed to download INSEE data')
        return

    # Process each city
    results = {}
    for city_name, config in CITIES_CONFIG.items():
        try:
            success = process_city(insee_data, city_name, config)
            results[city_name] = success
        except Exception as e:
            print(f'\n❌ Error processing {city_name}: {e}')
            import traceback
            traceback.print_exc()
            results[city_name] = False

    # Summary
    print('\n' + '='*70)
    print('PROCESSING SUMMARY')
    print('='*70)
    for city_name, success in results.items():
        status = '✅' if success else '❌'
        print(f'{status} {city_name}')

    successful = sum(results.values())
    print(f'\n{successful}/{len(CITIES_CONFIG)} cities processed successfully')

    if successful == len(CITIES_CONFIG):
        print('\n✅ ALL CITIES PROCESSED SUCCESSFULLY!')
    else:
        print('\n⚠️ Some cities failed to process. Check errors above.')

if __name__ == '__main__':
    main()
