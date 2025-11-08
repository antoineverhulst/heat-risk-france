"""
Download Paris arrondissement geographic boundaries.

Source: Paris Open Data (data.gouv.fr)
Creates a GeoJSON file with arrondissement boundaries that can be used for mapping.

Usage:
    python scripts/download_paris_boundaries.py
"""

import sys
from pathlib import Path
import json

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from config import PROCESSED_DATA_DIR, RAW_DATA_DIR, ADMIN_DIR
import requests

# URLs for Paris arrondissement boundaries
PARIS_BOUNDARIES_URL = "https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/arrondissements/exports/geojson"

OUTPUT_FILE = PROCESSED_DATA_DIR / "paris_arrondissements.geojson"

def download_paris_boundaries():
    """Download Paris arrondissement boundaries from Open Data Paris."""
    print("=" * 70)
    print("DOWNLOADING PARIS ARRONDISSEMENT BOUNDARIES")
    print("=" * 70)

    if OUTPUT_FILE.exists():
        print(f"\n✅ Boundaries file already exists: {OUTPUT_FILE}")
        response = input("Overwrite? (y/n): ")
        if response.lower() != 'y':
            print("Skipping download.")
            return True

    print(f"\n📥 Downloading from: {PARIS_BOUNDARIES_URL}")

    try:
        # Download GeoJSON
        response = requests.get(PARIS_BOUNDARIES_URL, timeout=30)
        response.raise_for_status()

        geojson_data = response.json()

        print(f"✅ Downloaded {len(geojson_data.get('features', []))} features")

        # Process features to add standardized CODGEO
        print("\n🔧 Processing boundaries...")

        features_processed = []
        for feature in geojson_data.get('features', []):
            props = feature.get('properties', {})

            # Try to find arrondissement code
            code = None
            for key in ['c_ar', 'code', 'c_arinsee', 'n_sq_ar']:
                if key in props:
                    code = props[key]
                    break

            if code:
                # Create standardized CODGEO (751XX format)
                codgeo = f"751{str(code).zfill(2)}"
                props['CODGEO'] = codgeo

            features_processed.append(feature)

        geojson_data['features'] = features_processed

        # Save as GeoJSON
        print(f"\n💾 Saving to: {OUTPUT_FILE}")
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(geojson_data, f, ensure_ascii=False, indent=2)

        file_size = OUTPUT_FILE.stat().st_size / 1024
        print(f"✅ Saved successfully! Size: {file_size:.1f} KB")

        # Display summary
        print("\n📊 Summary:")
        print(f"   Arrondissements: {len(geojson_data['features'])}")
        print(f"   CRS: EPSG:4326 (WGS84)")
        codes = [f['properties'].get('CODGEO', 'N/A') for f in geojson_data['features']]
        print(f"   Sample codes: {sorted([c for c in codes if c != 'N/A'])[:5]} ...")

        return True

    except requests.RequestException as e:
        print(f"\n❌ Download error: {e}")
        print("\n💡 Alternative: You can manually download Paris arrondissement boundaries from:")
        print("   https://opendata.paris.fr/explore/dataset/arrondissements/")
        return False
    except Exception as e:
        print(f"\n❌ Processing error: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_fallback_boundaries():
    """
    Create a simplified GeoJSON with approximate arrondissement locations.
    This is a fallback if download fails - uses simplified polygons.
    """
    print("\n⚠️  Creating fallback boundary file...")
    print("   (This uses simplified center points - download real boundaries for production)")

    # Approximate centers of Paris arrondissements (lat, lon)
    # These are rough approximations for visualization purposes only
    arrondissements = {
        '75101': {'name': '1er', 'lat': 48.8630, 'lon': 2.3349},
        '75102': {'name': '2e', 'lat': 48.8682, 'lon': 2.3419},
        '75103': {'name': '3e', 'lat': 48.8638, 'lon': 2.3634},
        '75104': {'name': '4e', 'lat': 48.8550, 'lon': 2.3577},
        '75105': {'name': '5e', 'lat': 48.8445, 'lon': 2.3504},
        '75106': {'name': '6e', 'lat': 48.8509, 'lon': 2.3316},
        '75107': {'name': '7e', 'lat': 48.8568, 'lon': 2.3140},
        '75108': {'name': '8e', 'lat': 48.8742, 'lon': 2.3119},
        '75109': {'name': '9e', 'lat': 48.8768, 'lon': 2.3394},
        '75110': {'name': '10e', 'lat': 48.8760, 'lon': 2.3622},
        '75111': {'name': '11e', 'lat': 48.8587, 'lon': 2.3813},
        '75112': {'name': '12e', 'lat': 48.8412, 'lon': 2.3889},
        '75113': {'name': '13e', 'lat': 48.8322, 'lon': 2.3561},
        '75114': {'name': '14e', 'lat': 48.8334, 'lon': 2.3270},
        '75115': {'name': '15e', 'lat': 48.8401, 'lon': 2.2998},
        '75116': {'name': '16e', 'lat': 48.8636, 'lon': 2.2686},
        '75117': {'name': '17e', 'lat': 48.8873, 'lon': 2.3089},
        '75118': {'name': '18e', 'lat': 48.8927, 'lon': 2.3466},
        '75119': {'name': '19e', 'lat': 48.8845, 'lon': 2.3809},
        '75120': {'name': '20e', 'lat': 48.8638, 'lon': 2.3998},
    }

    # Create point features (very simple fallback)
    features = []
    for code, info in arrondissements.items():
        features.append({
            'type': 'Feature',
            'properties': {
                'CODGEO': code,
                'name': info['name']
            },
            'geometry': {
                'type': 'Point',
                'coordinates': [info['lon'], info['lat']]
            }
        })

    geojson = {
        'type': 'FeatureCollection',
        'features': features
    }

    fallback_file = PROCESSED_DATA_DIR / "paris_arrondissements_points.geojson"
    with open(fallback_file, 'w') as f:
        json.dump(geojson, f)

    print(f"✅ Created fallback file: {fallback_file}")
    print("   Note: This contains center points only, not actual boundaries")

    return True

def main():
    """Main function."""
    success = download_paris_boundaries()

    if not success:
        print("\n" + "=" * 70)
        create_fallback_boundaries()

    print("\n🎉 Done!")
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
