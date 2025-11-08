"""
Configuration file for Heat Risk France application.
Contains all constants, paths, and settings.
"""

from pathlib import Path

# ============================================================================
# PROJECT PATHS
# ============================================================================

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
CACHE_DIR = DATA_DIR / "cache"

# Raw data subdirectories
LCZ_DIR = RAW_DATA_DIR / "lcz"
POPULATION_DIR = RAW_DATA_DIR / "population"
ADMIN_DIR = RAW_DATA_DIR / "admin"

# Ensure directories exist
for directory in [RAW_DATA_DIR, PROCESSED_DATA_DIR, CACHE_DIR, 
                  LCZ_DIR, POPULATION_DIR, ADMIN_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# ============================================================================
# COORDINATE REFERENCE SYSTEMS
# ============================================================================

# Official French projection system (Lambert 93)
CRS_FRANCE = "EPSG:2154"

# Web Mercator for web maps
CRS_WEB = "EPSG:4326"  # WGS84 (latitude/longitude)

# ============================================================================
# DATA SOURCES (URLs)
# ============================================================================

# CEREMA LCZ Data
LCZ_DATA_URL = "https://www.data.gouv.fr/fr/datasets/r/fb8028d6-8018-40fa-b655-4672e8f6feaf"  # City list CSV

# INSEE Population Data
POPULATION_DATA_URL = "https://www.insee.fr/fr/statistiques/fichier/7655475/base-pop-legales-2023.zip"

# INSEE Elderly Living Alone Data (TD_POP4_2020)
ELDERLY_LIVING_ALONE_URL = "https://www.insee.fr/fr/statistiques/fichier/7631680/TD_POP4_2020_csv.zip"

# IGN Administrative Boundaries
ADMIN_BOUNDARIES_URL = "https://wxs.ign.fr/static/vectorTiles/data/ADMIN-EXPRESS-COG-CARTO.gpkg"

# ============================================================================
# TEST CITIES (for Phase 1 development)
# ============================================================================

TEST_CITIES = [
    "Paris",
    "Lyon", 
    "Marseille",
    "Toulouse",
    "Nice"
]

# ============================================================================
# LCZ CLASSIFICATION
# ============================================================================

# Mapping of LCZ classes to heat retention scores (0-10)
# Higher score = more heat retention / urban heat island effect
LCZ_HEAT_MAPPING = {
    # Compact urban forms (high heat retention)
    '1': 10,  # Compact high-rise
    '2': 9,   # Compact mid-rise
    '3': 8,   # Compact low-rise
    
    # Open urban forms
    '4': 7,   # Open high-rise
    '5': 6,   # Open mid-rise
    '6': 5,   # Open low-rise
    
    # Lightweight/sparse
    '7': 4,   # Lightweight low-rise
    '8': 5,   # Large low-rise
    '9': 3,   # Sparsely built
    '10': 3,  # Heavy industry
    
    # Natural/vegetated (cooling effect)
    'A': 2,   # Dense trees
    'B': 1,   # Scattered trees
    'C': 1,   # Bush, scrub
    'D': 2,   # Low plants
    'E': 1,   # Bare rock/paved
    'F': 0,   # Bare soil/sand
    'G': 0,   # Water
}

# LCZ descriptions for tooltips
LCZ_DESCRIPTIONS = {
    '1': 'Compact high-rise: Dense tall buildings',
    '2': 'Compact mid-rise: Dense medium buildings',
    '3': 'Compact low-rise: Dense low buildings',
    '4': 'Open high-rise: Tall buildings with open space',
    '5': 'Open mid-rise: Medium buildings with open space',
    '6': 'Open low-rise: Low buildings with open space',
    '7': 'Lightweight low-rise: Light construction',
    '8': 'Large low-rise: Large footprint buildings',
    '9': 'Sparsely built: Scattered structures',
    '10': 'Heavy industry: Industrial areas',
    'A': 'Dense trees: Forest/heavily vegetated',
    'B': 'Scattered trees: Parks with trees',
    'C': 'Bush/scrub: Low vegetation',
    'D': 'Low plants: Grassland/agriculture',
    'E': 'Bare rock/paved: Impervious surfaces',
    'F': 'Bare soil/sand: Natural bare ground',
    'G': 'Water: Lakes/rivers',
}

# ============================================================================
# VULNERABILITY SETTINGS
# ============================================================================

# Age threshold for vulnerability (years)
AGE_THRESHOLD = 65

# Population 65+ percentage thresholds for vulnerability scoring
VULNERABILITY_THRESHOLDS = {
    'very_low': (0, 5),      # 0-5%: Score 1-2
    'low': (5, 10),          # 5-10%: Score 3-4
    'moderate': (10, 15),    # 10-15%: Score 5-6
    'high': (15, 20),        # 15-20%: Score 7-8
    'very_high': (20, 100),  # >20%: Score 9-10
}

# Elderly living alone percentage thresholds for isolation vulnerability scoring
# Based on % of elderly (65+) living alone among total elderly population
ISOLATION_VULNERABILITY_THRESHOLDS = {
    'very_low': (0, 20),     # 0-20%: Score 1-2
    'low': (20, 30),         # 20-30%: Score 3-4
    'moderate': (30, 40),    # 30-40%: Score 5-6
    'high': (40, 50),        # 40-50%: Score 7-8
    'very_high': (50, 100),  # >50%: Score 9-10
}

# Enhanced vulnerability weights (age + isolation)
VULNERABILITY_AGE_WEIGHT = 0.6      # Weight for age-based vulnerability
VULNERABILITY_ISOLATION_WEIGHT = 0.4  # Weight for isolation-based vulnerability

# ============================================================================
# RISK CALCULATION
# ============================================================================

# Default weights for composite risk index
DEFAULT_HEAT_WEIGHT = 0.5
DEFAULT_VULNERABILITY_WEIGHT = 0.5

# Risk categories based on composite score (0-100)
RISK_CATEGORIES = {
    'Very Low': (0, 20),
    'Low': (21, 40),
    'Moderate': (41, 60),
    'High': (61, 80),
    'Very High': (81, 100),
}

# ============================================================================
# VISUALIZATION SETTINGS
# ============================================================================

# Color schemes for maps (hex colors)
# Heat exposure: warm colors (yellow to red)
HEAT_COLORSCALE = [
    '#ffffcc',  # Very light yellow
    '#ffeda0',  # Light yellow
    '#fed976',  # Yellow
    '#feb24c',  # Orange-yellow
    '#fd8d3c',  # Orange
    '#fc4e2a',  # Red-orange
    '#e31a1c',  # Red
    '#bd0026',  # Dark red
]

# Vulnerability: blue scale
VULNERABILITY_COLORSCALE = [
    '#f7fbff',  # Very light blue
    '#deebf7',  # Light blue
    '#c6dbef',  # Blue
    '#9ecae1',  # Medium blue
    '#6baed6',  # Blue
    '#4292c6',  # Dark blue
    '#2171b5',  # Darker blue
    '#084594',  # Very dark blue
]

# Risk: green to red (traffic light)
RISK_COLORSCALE = [
    '#1a9850',  # Dark green (very low risk)
    '#91cf60',  # Green (low risk)
    '#d9ef8b',  # Yellow-green (moderate risk)
    '#fee08b',  # Yellow (moderate-high risk)
    '#fc8d59',  # Orange (high risk)
    '#e0301e',  # Red (very high risk)
    '#a50026',  # Dark red (extreme risk)
]

# Map settings
DEFAULT_MAP_CENTER = [46.603354, 1.888334]  # Center of France
DEFAULT_ZOOM_LEVEL = 6
CITY_ZOOM_LEVEL = 11

# ============================================================================
# STREAMLIT APP SETTINGS
# ============================================================================

# Page title and configuration
APP_TITLE = "Urban Heat Risk Analysis in France"
APP_ICON = "🌡️"
PAGE_LAYOUT = "wide"

# Cache TTL (time to live) in seconds
CACHE_TTL = 3600  # 1 hour

# ============================================================================
# DATA QUALITY SETTINGS
# ============================================================================

# Minimum population for commune to be included in analysis
MIN_POPULATION = 1000

# Maximum acceptable percentage of missing data
MAX_MISSING_DATA_PCT = 10

# ============================================================================
# FILE FORMATS
# ============================================================================

# Preferred formats for processed data
PROCESSED_SPATIAL_FORMAT = ".gpkg"  # GeoPackage
PROCESSED_TABULAR_FORMAT = ".csv"   # CSV
CACHE_FORMAT = ".parquet"           # Parquet for fast loading

# ============================================================================
# LOGGING
# ============================================================================

LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# ============================================================================
# API SETTINGS (for future use)
# ============================================================================

# Rate limiting
MAX_REQUESTS_PER_HOUR = 100

# Timeout for HTTP requests (seconds)
REQUEST_TIMEOUT = 30
