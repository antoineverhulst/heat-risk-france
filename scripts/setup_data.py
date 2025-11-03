"""
Setup script to generate processed data files for deployment.
Run this once to create the paris_heat_zones.gpkg file.

Usage:
    python scripts/setup_data.py
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from config import PROCESSED_DATA_DIR, LCZ_DIR, CRS_WEB
import geopandas as gpd
import pandas as pd

def setup_processed_data():
    """
    Generate processed data files from raw data.
    This is needed because paris_heat_zones.gpkg is too large for GitHub.
    """
    print("=" * 60)
    print("SETTING UP PROCESSED DATA FOR DEPLOYMENT")
    print("=" * 60)
    
    # Check if data already exists
    paris_heat_file = PROCESSED_DATA_DIR / "paris_heat_zones.gpkg"
    
    if paris_heat_file.exists():
        print(f"\n✅ {paris_heat_file.name} already exists!")
        size_mb = paris_heat_file.stat().st_size / 1_000_000
        print(f"   Size: {size_mb:.2f} MB")
        return True
    
    # Find Paris LCZ shapefile
    paris_lcz_dir = LCZ_DIR / "Paris"
    
    if not paris_lcz_dir.exists():
        print(f"\n❌ Paris LCZ data not found at: {paris_lcz_dir}")
        print("\n📥 Please download Paris LCZ data from:")
        print("https://www.data.gouv.fr/datasets/cartographie-des-zones-climatiques-locales-lcz-des-88-aires-urbaines-de-plus-de-50-000-habitants-de-france-metropolitaine/")
        print(f"\nExtract to: {paris_lcz_dir}")
        return False
    
    shapefiles = list(paris_lcz_dir.glob("*.shp"))
    
    if not shapefiles:
        print(f"\n❌ No .shp file found in {paris_lcz_dir}")
        return False
    
    shapefile_path = shapefiles[0]
    
    print(f"\n📂 Loading Paris LCZ data from: {shapefile_path.name}")
    
    try:
        # Load shapefile
        paris_lcz = gpd.read_file(shapefile_path)
        print(f"✅ Loaded {len(paris_lcz):,} zones")
        
        # Import heat mapping
        from config import LCZ_HEAT_MAPPING
        
        # Calculate heat scores
        paris_lcz['heat_score'] = paris_lcz['lcz'].astype(str).map(LCZ_HEAT_MAPPING)
        
        # Convert column names to lowercase
        paris_lcz.columns = paris_lcz.columns.str.lower()
        
        # Reproject to WGS84
        print(f"🌍 Reprojecting to {CRS_WEB}...")
        paris_lcz_web = paris_lcz.to_crs(CRS_WEB)
        
        # Simplify geometries
        print("📐 Simplifying geometries...")
        paris_lcz_web['geometry'] = paris_lcz_web['geometry'].simplify(tolerance=0.0001)
        
        # Select needed columns
        columns_to_keep = [
            'identifier', 'lcz', 'heat_score', 
            'hre', 'bur', 'ror', 'ver', 'vhr',
            'geometry'
        ]
        
        # Only keep columns that exist
        existing_cols = [col for col in columns_to_keep if col in paris_lcz_web.columns]
        paris_lcz_final = paris_lcz_web[existing_cols].copy()
        
        # Save
        print(f"\n💾 Saving to: {paris_heat_file}")
        paris_lcz_final.to_file(paris_heat_file, driver='GPKG')
        
        size_mb = paris_heat_file.stat().st_size / 1_000_000
        print(f"✅ Saved successfully! Size: {size_mb:.2f} MB")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = setup_processed_data()
    
    if success:
        print("\n🎉 Setup complete!")
        print("You can now run: streamlit run app.py")
    else:
        print("\n⚠️  Setup incomplete. Please check errors above.")
        sys.exit(1)