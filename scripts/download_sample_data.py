"""
Download sample data for Heat Risk France project.
This script downloads data for a few test cities to get started.

Usage:
    python scripts/download_sample_data.py
"""

import requests
from pathlib import Path
import sys

# Add parent directory to path to import config
sys.path.append(str(Path(__file__).parent.parent))
from config import LCZ_DIR, POPULATION_DIR, TEST_CITIES

def download_file(url, destination):
    """
    Download a file from URL to destination path.
    
    Args:
        url: URL to download from
        destination: Path object for where to save file
    """
    print(f"Downloading from {url}...")
    print(f"Saving to {destination}...")
    
    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        
        # Create parent directory if needed
        destination.parent.mkdir(parents=True, exist_ok=True)
        
        # Write file in chunks
        with open(destination, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"✅ Downloaded successfully: {destination.name}\n")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error downloading: {e}\n")
        return False

def download_lcz_cities_list():
    """
    Download the CSV file listing all available LCZ cities.
    This helps us understand which cities are available.
    """
    print("\n" + "="*60)
    print("STEP 1: Downloading list of available cities")
    print("="*60 + "\n")
    
    # URL for the CSV listing all cities
    url = "https://www.data.gouv.fr/fr/datasets/r/fb8028d6-8018-40fa-b655-4672e8f6feaf"
    destination = LCZ_DIR / "cities_list.csv"
    
    return download_file(url, destination)

def download_population_data():
    """
    Download INSEE population data.
    Note: This is a large file (~50MB), so it may take a moment.
    """
    print("\n" + "="*60)
    print("STEP 2: Downloading INSEE population data")
    print("="*60 + "\n")
    
    url = "https://www.insee.fr/fr/statistiques/fichier/7655475/base-pop-legales-2023.zip"
    destination = POPULATION_DIR / "base-pop-legales-2023.zip"
    
    print("⚠️  This is a large file (~50MB), please be patient...")
    return download_file(url, destination)

def print_next_steps():
    """Print instructions for what to do next."""
    print("\n" + "="*60)
    print("✅ DOWNLOAD COMPLETE!")
    print("="*60 + "\n")
    
    print("📋 Next Steps:\n")
    print("1. MANUAL DOWNLOAD REQUIRED FOR LCZ DATA:")
    print("   The LCZ shapefiles must be downloaded manually from:")
    print("   https://www.data.gouv.fr/fr/datasets/cartographie-des-zones-climatiques-locales-lcz-des-88-aires-urbaines-de-plus-de-50-000-habitants-de-france-metropolitaine/\n")
    
    print("   For each test city, download the ZIP file and extract to:")
    print(f"   {LCZ_DIR}/[city_name]/\n")
    
    print("   Test cities to download:")
    for city in TEST_CITIES:
        print(f"   - {city}")
    
    print("\n2. Extract the population data ZIP:")
    print(f"   cd {POPULATION_DIR}")
    print("   unzip base-pop-legales-2023.zip\n")
    
    print("3. Create your first exploration notebook:")
    print("   jupyter notebook notebooks/01_data_exploration.ipynb\n")
    
    print("4. I'll help you write code to load and explore the data!\n")

def main():
    """Main function to download all sample data."""
    print("\n" + "="*60)
    print("🌡️  HEAT RISK FRANCE - DATA DOWNLOAD")
    print("="*60)
    print("\nThis script will download sample data for the project.")
    print("Note: LCZ shapefiles require manual download from data.gouv.fr\n")
    
    # Download city list
    success1 = download_lcz_cities_list()
    
    # Download population data
    success2 = download_population_data()
    
    # Print next steps
    print_next_steps()
    
    # Summary
    if success1 and success2:
        print("✅ Automated downloads completed successfully!")
    else:
        print("⚠️  Some downloads failed. Check errors above.")
    
    print("\n💡 TIP: The LCZ data is organized by urban area.")
    print("   You can browse available areas in the cities_list.csv file.\n")

if __name__ == "__main__":
    main()
