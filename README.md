# 🌡️ Urban Heat Risk Analysis in France

An interactive Streamlit application for analyzing and visualizing urban heat risk across French cities by combining thermal exposure data with population vulnerability indicators.

## 📖 Project Overview

This project explores the intersection of urban heat islands and social vulnerability in French cities, inspired by Eric Klinenberg's research showing the link between heat-related mortality and social isolation.

### Key Features (Planned)
- Interactive maps of urban heat islands (88 French cities)
- Population vulnerability analysis (elderly populations)
- Composite risk assessment combining heat exposure and demographic data
- Comparative analysis across multiple cities
- Data export capabilities

## 🗂️ Project Status

**Current Phase**: Phase 1 - Setup & Data Acquisition  
**Last Updated**: 2025-10-29

### Completed
- [x] Project structure created
- [x] Development environment configured
- [ ] Sample data downloaded
- [ ] Data exploration notebooks

## 📊 Data Sources

All data comes from French open data sources:

1. **Local Climate Zones (LCZ)** - CEREMA via data.gouv.fr
   - 88 urban areas with >50,000 inhabitants
   - URL: https://www.data.gouv.fr/datasets/cartographie-des-zones-climatiques-locales-lcz-des-88-aires-urbaines-de-plus-de-50-000-habitants-de-france-metropolitaine

2. **Population Data** - INSEE
   - Census data with age breakdowns by commune
   - URL: https://www.insee.fr/fr/statistiques/fichier/7655475/base-pop-legales-2023.zip

3. **Elderly Living Alone Data** - INSEE TD_POP4_2020
   - Household composition data including elderly living alone
   - URL: https://www.insee.fr/fr/statistiques/fichier/7631680/TD_POP4_2020_csv.zip

4. **Administrative Boundaries** - Paris Open Data / IGN
   - Paris arrondissement boundaries for mapping
   - French commune boundaries

## 🚀 Getting Started

### Prerequisites
- Python 3.9 or higher
- Git
- 2-5 GB free disk space (for spatial data)

### Installation

1. Clone this repository:
```bash
git clone <your-repo-url>
cd heat_risk_france
```

2. Create and activate virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Mac/Linux
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

### Quick Start

*Coming soon - after Phase 1 completion*

## 📁 Project Structure

```
heat_risk_france/
├── app.py                  # Main Streamlit application (coming soon)
├── config.py              # Configuration settings (coming soon)
├── requirements.txt       # Python dependencies
├── README.md             # This file
│
├── src/                  # Source code modules
│   ├── data_loader.py    # Data loading functions
│   ├── spatial_processor.py  # GIS operations
│   ├── risk_calculator.py    # Risk scoring logic
│   └── visualizations.py     # Map and chart functions
│
├── pages/                # Streamlit pages (multi-page app)
│   ├── 1_🏠_Overview.py
│   ├── 2_🌡️_Heat_Exposure.py
│   ├── 3_👥_Vulnerability.py
│   └── 4_⚠️_Risk_Assessment.py
│
├── data/                 # Data directory (gitignored)
│   ├── raw/             # Original downloaded data
│   ├── processed/       # Pre-processed datasets
│   └── cache/           # Streamlit cache
│
├── notebooks/           # Jupyter notebooks for exploration
├── scripts/            # Data processing scripts
├── tests/              # Unit tests
└── assets/             # Static assets (images, CSS)
```

## 🧪 Development

### Running Tests
```bash
pytest tests/
```

### Code Formatting
```bash
black src/
```

### Starting Jupyter Notebook
```bash
jupyter notebook
```

## 📝 Methodology

### Heat and Vulnerability Scoring

1. **Heat Exposure Score**: Based on Local Climate Zone (LCZ) classification (0-10 scale)
   - Compact urban areas score higher (more heat retention)
   - Green spaces and water bodies score lower (cooling effect)

2. **Age-Based Vulnerability Score**: Based on % population aged 65+ (0-10 scale)
   - <5%: Very Low (1-2)
   - 5-10%: Low (3-4)
   - 10-15%: Moderate (5-6)
   - 15-20%: High (7-8)
   - >20%: Very High (9-10)

3. **Isolation Vulnerability Score**: Based on % of elderly living alone (0-10 scale)
   - <20%: Very Low (1-2)
   - 20-30%: Low (3-4)
   - 30-40%: Moderate (5-6)
   - 40-50%: High (7-8)
   - >50%: Very High (9-10)

4. **Enhanced Vulnerability Score**: Combines age and isolation factors
   - Formula: 60% × Age Score + 40% × Isolation Score
   - Accounts for both demographic profile and social vulnerability

5. **Composite Risk Index**: Weighted combination of heat and vulnerability (0-100 scale)
   - Default: 50% heat exposure + 50% vulnerability
   - User-adjustable weights in the app

### Data Processing

To process the elderly living alone data:

```bash
# 1. Download the INSEE TD_POP4_2020 data manually from:
# https://www.insee.fr/fr/statistiques/fichier/7631680/TD_POP4_2020_csv.zip

# 2. Place the ZIP file in: data/raw/population/

# 3. Run the processing script:
python scripts/process_elderly_living_alone.py

# 4. Download Paris arrondissement boundaries for mapping:
python scripts/download_paris_boundaries.py
```

This will:
- Extract elderly living alone statistics for Paris arrondissements
- Calculate isolation vulnerability scores
- Merge with existing vulnerability data
- Update the enhanced vulnerability scores

## 🤝 Contributing

This is currently a personal project in development. Contributions, suggestions, and feedback are welcome!

## 📄 License

This project uses open data from French public sources under Licence Ouverte / Open License.

## 🙏 Acknowledgments

- **Eric Klinenberg** - Research on heat waves and social vulnerability
- **CEREMA** - Local Climate Zone data
- **INSEE** - Population statistics
- **IGN** - Geographic data

## 📧 Contact

*Add your contact information here*

---

**Note**: This project is under active development. Check back for updates!