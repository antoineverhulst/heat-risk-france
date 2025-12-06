"""
Download LCZ data for new cities (Bordeaux, Nantes, Strasbourg, Nice, Montpellier)
"""

import requests
from pathlib import Path
import zipfile
import shutil

BASE_DIR = Path(__file__).parent.parent
LCZ_DIR = BASE_DIR / "data" / "raw" / "lcz"

CITIES_URLS = {
    'Bordeaux': 'https://www.data.gouv.fr/api/1/datasets/r/621cb2fa-6f0b-4833-bfa0-2b0a48d59275',
    'Nice': 'https://www.data.gouv.fr/api/1/datasets/r/ce71193c-b478-4d85-851c-d34519a9592e',
    'Strasbourg': 'https://www.data.gouv.fr/api/1/datasets/r/a8f73744-deac-44bb-9143-a5fa2974471d',
    'Montpellier': 'https://www.data.gouv.fr/api/1/datasets/r/08b03af4-a0cc-4db4-91f9-580926115684',
    'Nantes': 'https://www.data.gouv.fr/api/1/datasets/r/dfe6ad34-28fe-4cd2-a5c5-94573d1b0322'
}

def download_and_extract_city(city_name, url):
    """Download and extract LCZ data for a city"""
    print(f'\n{"="*70}')
    print(f'Downloading {city_name}...')
    print(f'{"="*70}')

    # Create city directory
    city_dir = LCZ_DIR / city_name
    city_dir.mkdir(parents=True, exist_ok=True)

    # Download ZIP file
    zip_path = LCZ_DIR / f"{city_name}.zip"
    print(f'📥 Downloading from {url}...')

    try:
        response = requests.get(url, stream=True, timeout=300)
        response.raise_for_status()

        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0

        with open(zip_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                downloaded += len(chunk)
                if total_size > 0:
                    percent = (downloaded / total_size) * 100
                    print(f'\r  Progress: {percent:.1f}%', end='', flush=True)

        print(f'\n✅ Downloaded {zip_path.name} ({downloaded / 1024 / 1024:.1f} MB)')

        # Extract ZIP
        print(f'📦 Extracting to {city_dir.name}/...')
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(city_dir)

        print(f'✅ Extracted successfully')

        # Clean up ZIP file
        zip_path.unlink()
        print(f'🗑️  Removed temporary ZIP file')

        # List extracted files
        files = list(city_dir.glob('*'))
        print(f'📁 Extracted {len(files)} files:')
        for f in sorted(files)[:5]:
            print(f'   - {f.name}')
        if len(files) > 5:
            print(f'   ... and {len(files) - 5} more')

        return True

    except Exception as e:
        print(f'❌ Error: {e}')
        if zip_path.exists():
            zip_path.unlink()
        return False

def main():
    print('='*70)
    print('DOWNLOADING LCZ DATA FOR NEW CITIES')
    print('='*70)
    print(f'\nTarget directory: {LCZ_DIR}')
    print(f'Cities to download: {len(CITIES_URLS)}')

    results = {}
    for city_name, url in CITIES_URLS.items():
        results[city_name] = download_and_extract_city(city_name, url)

    # Summary
    print('\n' + '='*70)
    print('DOWNLOAD SUMMARY')
    print('='*70)
    for city_name, success in results.items():
        status = '✅' if success else '❌'
        print(f'{status} {city_name}')

    successful = sum(results.values())
    print(f'\n{successful}/{len(CITIES_URLS)} cities downloaded successfully')

if __name__ == '__main__':
    main()
