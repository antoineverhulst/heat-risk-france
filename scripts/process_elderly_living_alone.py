"""
Process INSEE TD_POP4_2020 data to extract elderly living alone statistics.

This script processes data from:
https://www.insee.fr/fr/statistiques/fichier/7631680/TD_POP4_2020_csv.zip

The TD_POP4 dataset contains household composition data including:
- Number of people living alone by age groups
- Total population by age groups

Usage:
    1. Download the ZIP file manually from the URL above
    2. Place it in data/raw/population/TD_POP4_2020_csv.zip
    3. Run: python scripts/process_elderly_living_alone.py
"""

import sys
from pathlib import Path
import zipfile

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from config import RAW_DATA_DIR, PROCESSED_DATA_DIR
import pandas as pd
import numpy as np

# Input file path
INSEE_ZIP_FILE = RAW_DATA_DIR / "population" / "TD_POP4_2020_csv.zip"
OUTPUT_FILE = PROCESSED_DATA_DIR / "paris_elderly_living_alone.csv"

def extract_and_load_csv(zip_path):
    """Extract CSV from ZIP and load it."""
    print(f"📂 Extracting {zip_path.name}...")

    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        # List files in the ZIP
        file_list = zip_ref.namelist()
        print(f"   Found {len(file_list)} file(s) in ZIP")

        # Find CSV file (should be TD_POP4_2020.csv or similar)
        csv_files = [f for f in file_list if f.endswith('.csv')]

        if not csv_files:
            raise ValueError("No CSV file found in ZIP archive")

        csv_file = csv_files[0]
        print(f"   Loading {csv_file}...")

        # Read CSV with proper encoding (INSEE uses latin1 or cp1252)
        with zip_ref.open(csv_file) as f:
            try:
                df = pd.read_csv(f, sep=';', encoding='latin1', low_memory=False)
            except:
                # Try alternative encoding
                f.seek(0)
                df = pd.read_csv(f, sep=';', encoding='cp1252', low_memory=False)

        return df

def process_elderly_living_alone_data(df):
    """
    Process INSEE household composition data.

    Expected columns (TD_POP4 format):
    - CODGEO: Geographic code
    - Various columns for household composition by age groups

    We're looking for:
    - People aged 65+ living alone (PM65P_PSEUL or similar)
    - Total people aged 65+ (PM65P or similar)
    """
    print("\n📊 Analyzing data structure...")
    print(f"   Rows: {len(df):,}")
    print(f"   Columns: {len(df.columns)}")

    # Display first few column names to understand structure
    print(f"\n   Sample columns:")
    for col in df.columns[:10]:
        print(f"      - {col}")

    # Filter for Paris arrondissements (codes 75101-75120)
    print("\n🗼 Filtering Paris arrondissements...")
    paris_codes = [f"751{str(i).zfill(2)}" for i in range(1, 21)]
    paris_df = df[df['CODGEO'].isin(paris_codes)].copy()

    if len(paris_df) == 0:
        # Try without leading zero
        paris_codes_alt = [f"75{i}" for i in range(101, 121)]
        paris_df = df[df['CODGEO'].isin(paris_codes_alt)].copy()

    print(f"   Found {len(paris_df)} arrondissements")

    if len(paris_df) == 0:
        print("\n❌ No Paris data found. Available codes sample:")
        print(df['CODGEO'].head(20).tolist())
        raise ValueError("No Paris arrondissements found in dataset")

    # Identify columns for elderly living alone
    # Common patterns in INSEE data:
    # - PM65P: Population aged 65+
    # - PSEUL: People living alone
    # - PM65P_PSEUL: People 65+ living alone

    elderly_cols = [col for col in df.columns if '65' in col.upper() or 'PM' in col.upper()]
    alone_cols = [col for col in df.columns if 'SEUL' in col.upper()]

    print(f"\n🔍 Identified columns:")
    print(f"   Elderly-related: {elderly_cols[:5]}")
    print(f"   Living alone-related: {alone_cols[:5]}")

    # Try to find the exact columns we need
    # Look for columns matching elderly living alone pattern
    elderly_alone_col = None
    elderly_total_col = None

    for col in df.columns:
        col_upper = col.upper()
        # Look for 65+ living alone
        if ('65' in col_upper or 'PM' in col_upper) and 'SEUL' in col_upper:
            elderly_alone_col = col
            print(f"   ✓ Found elderly living alone: {col}")
            break

    for col in df.columns:
        col_upper = col.upper()
        # Look for total 65+
        if ('P65' in col_upper or 'PM65' in col_upper) and 'SEUL' not in col_upper:
            elderly_total_col = col
            print(f"   ✓ Found elderly total: {col}")
            break

    # Create output dataframe
    result = pd.DataFrame()
    result['CODGEO'] = paris_df['CODGEO'].values

    # Extract numeric values (INSEE uses string format sometimes)
    if elderly_alone_col:
        result['elderly_living_alone'] = pd.to_numeric(
            paris_df[elderly_alone_col].astype(str).str.replace(',', '.'),
            errors='coerce'
        )
    else:
        print("\n⚠️  Could not find elderly living alone column")
        result['elderly_living_alone'] = np.nan

    if elderly_total_col:
        result['elderly_total'] = pd.to_numeric(
            paris_df[elderly_total_col].astype(str).str.replace(',', '.'),
            errors='coerce'
        )
    else:
        print("\n⚠️  Could not find elderly total column")
        result['elderly_total'] = np.nan

    # Calculate percentage
    result['pct_elderly_living_alone'] = (
        result['elderly_living_alone'] / result['elderly_total'] * 100
    ).round(2)

    # Calculate isolation vulnerability score (0-10 scale)
    # Higher percentage of elderly living alone = higher vulnerability
    result['isolation_vulnerability'] = result['pct_elderly_living_alone'].apply(
        lambda x: calculate_isolation_score(x) if pd.notna(x) else np.nan
    )

    return result

def calculate_isolation_score(pct_elderly_alone):
    """
    Calculate vulnerability score based on % of elderly living alone.

    Scale 0-10:
    - 0-20%: Score 1-2 (Very Low isolation)
    - 20-30%: Score 3-4 (Low isolation)
    - 30-40%: Score 5-6 (Moderate isolation)
    - 40-50%: Score 7-8 (High isolation)
    - 50%+: Score 9-10 (Very High isolation)
    """
    if pd.isna(pct_elderly_alone):
        return np.nan

    if pct_elderly_alone < 20:
        return 1 + (pct_elderly_alone / 20)
    elif pct_elderly_alone < 30:
        return 3 + ((pct_elderly_alone - 20) / 10)
    elif pct_elderly_alone < 40:
        return 5 + ((pct_elderly_alone - 30) / 10)
    elif pct_elderly_alone < 50:
        return 7 + ((pct_elderly_alone - 40) / 10)
    else:
        return min(10, 9 + ((pct_elderly_alone - 50) / 50))

def merge_with_existing_vulnerability(new_data):
    """Merge with existing vulnerability data."""
    existing_file = PROCESSED_DATA_DIR / "paris_vulnerability.csv"

    if not existing_file.exists():
        print(f"\n⚠️  Existing vulnerability file not found: {existing_file}")
        return new_data

    print(f"\n🔗 Merging with existing vulnerability data...")
    existing = pd.read_csv(existing_file)

    # Merge on CODGEO
    merged = existing.merge(new_data, on='CODGEO', how='left')

    # Calculate enhanced vulnerability score
    # Combine existing vulnerability (65+ population) with isolation (65+ living alone)
    # Weight: 60% age-based, 40% isolation-based
    merged['vulnerability_score_enhanced'] = (
        0.6 * merged['vulnerability_score'] +
        0.4 * merged['isolation_vulnerability']
    ).round(1)

    return merged

def main():
    """Main processing function."""
    print("=" * 70)
    print("PROCESSING INSEE ELDERLY LIVING ALONE DATA")
    print("=" * 70)

    # Check if input file exists
    if not INSEE_ZIP_FILE.exists():
        print(f"\n❌ Input file not found: {INSEE_ZIP_FILE}")
        print("\n📥 Please download the data manually:")
        print("   URL: https://www.insee.fr/fr/statistiques/fichier/7631680/TD_POP4_2020_csv.zip")
        print(f"   Save to: {INSEE_ZIP_FILE}")
        print("\nThen run this script again.")
        return False

    try:
        # Load data
        df = extract_and_load_csv(INSEE_ZIP_FILE)

        # Process data
        processed = process_elderly_living_alone_data(df)

        # Merge with existing data
        final = merge_with_existing_vulnerability(processed)

        # Save results
        print(f"\n💾 Saving results to: {OUTPUT_FILE}")

        # Also update the main vulnerability file
        vulnerability_file = PROCESSED_DATA_DIR / "paris_vulnerability.csv"
        final.to_csv(vulnerability_file, index=False)
        print(f"💾 Updated: {vulnerability_file}")

        # Save separate file for elderly living alone data
        processed.to_csv(OUTPUT_FILE, index=False)
        print(f"💾 Saved: {OUTPUT_FILE}")

        # Display summary
        print("\n📈 Summary Statistics:")
        print(f"   Arrondissements processed: {len(final)}")
        if 'pct_elderly_living_alone' in final.columns:
            print(f"\n   Elderly living alone (%):")
            print(f"      Mean: {final['pct_elderly_living_alone'].mean():.1f}%")
            print(f"      Min: {final['pct_elderly_living_alone'].min():.1f}%")
            print(f"      Max: {final['pct_elderly_living_alone'].max():.1f}%")

        if 'vulnerability_score_enhanced' in final.columns:
            print(f"\n   Enhanced vulnerability score:")
            print(f"      Mean: {final['vulnerability_score_enhanced'].mean():.1f}")
            print(f"      Min: {final['vulnerability_score_enhanced'].min():.1f}")
            print(f"      Max: {final['vulnerability_score_enhanced'].max():.1f}")

        print("\n🎉 Processing complete!")
        return True

    except Exception as e:
        print(f"\n❌ Error during processing: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
