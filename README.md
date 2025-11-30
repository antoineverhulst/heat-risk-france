# 🌡️ Risque de Chaleur en France

Une application Streamlit interactive pour analyser et visualiser le risque de chaleur urbaine dans les villes françaises en combinant l'exposition thermique et les indicateurs de vulnérabilité de la population.

## 🎯 À propos

Cette application explore l'intersection entre les îlots de chaleur urbains et la vulnérabilité sociale dans les villes françaises, inspirée par les recherches d'Eric Klinenberg qui ont montré le lien entre la mortalité liée à la chaleur et l'isolement social.

**Question centrale** : *Quelles zones à risques pour les populations urbaines âgées face à la canicule?*

## ✨ Fonctionnalités

### 📊 Vue d'ensemble et statistiques
- **8 métriques clés** pour chaque ville :
  - Population totale et nombre de zones IRIS
  - Nombre de personnes âgées (55+ et 80+) vivant seules
  - Pourcentages de population dans les zones à chaleur élevée
  - Pourcentages de personnes âgées dans les zones à risque
- **Points clés** : zones à chaleur élevée et populations vulnérables

### 🗺️ Découvrir la composition du territoire
- **Cartes interactives** avec Plotly pour visualiser :
  - Catégorie de chaleur (Élevée/Moyenne/Faible)
  - Densité de population
  - Pourcentage de personnes âgées (55+)
  - Pourcentage de personnes âgées vivant seules
  - Nombre de personnes âgées (55+ et 80+) seules par zone IRIS
- **Sélecteur de métrique** pour changer la visualisation en temps réel
- **Données au niveau IRIS** (îlot regroupé pour l'information statistique)

### ⚖️ Déterminer les zones à risques
- **Indicateurs de risque** calculés automatiquement :
  - Indicateur de risque (55+ seules)
  - Indicateur de risque extrême (80+ seules)
- **Formule** : Multiplicateur de chaleur × Nombre de personnes âgées seules
  - Chaleur Faible = 0
  - Chaleur Moyenne = 1
  - Chaleur Élevée = 2
- **Carte de risque** interactive
- **Top 20** des zones IRIS les plus à risque avec détails

### 📖 À propos
- Méthodologie détaillée
- Sources de données
- Limitations et contexte de recherche
- Téléchargement des données en CSV

## 🏙️ Villes disponibles

L'application couvre actuellement **5 grandes villes françaises** :
- **Paris** (987 zones IRIS)
- **Lille** (110 zones IRIS)
- **Lyon** (arrondissements)
- **Marseille** (arrondissements)
- **Toulouse**

## 📊 Méthodologie

### Scores de chaleur

Les scores de chaleur sont basés sur la classification des **Zones Climatiques Locales (LCZ)** du CEREMA :

| Score de chaleur | Classes LCZ | Description |
|------------------|-------------|-------------|
| **Élevée** | 1, 2, 3, 8, 10 | Zones urbaines compactes avec bâtiments denses (forte rétention de chaleur) |
| **Moyenne** | 4, 5, 6, 7, E | Zones urbaines ouvertes et mixtes (rétention modérée) |
| **Faible** | 9, A, B, C, D, F, G | Zones végétalisées, plans d'eau, parcs (faible rétention) |

### Agrégation IRIS

- **Méthode** : Catégorie LCZ la plus commune au sein de chaque zone IRIS
- **Précision** : Attribution basée sur le centroïde pour éviter les chevauchements

### Indicateurs de risque

L'application calcule deux indicateurs :

1. **Indicateur de risque** = Multiplicateur de chaleur × Personnes âgées (55+) seules
2. **Indicateur de risque extrême** = Multiplicateur de chaleur × Personnes âgées (80+) seules

Cette approche priorise les zones où :
- L'exposition à la chaleur est significative (moyenne ou élevée)
- Des populations vulnérables sont présentes
- L'isolement social augmente le risque

## 🚀 Démarrage rapide

### Prérequis
- Python 3.9 ou supérieur
- Git
- 500 MB d'espace disque libre

### Installation

1. Cloner le dépôt :
```bash
git clone https://github.com/antoineverhulst/heat-risk-france.git
cd heat-risk-france
```

2. Créer et activer l'environnement virtuel :
```bash
python3 -m venv venv
source venv/bin/activate  # Mac/Linux
# ou
venv\Scripts\activate  # Windows
```

3. Installer les dépendances :
```bash
pip install -r requirements.txt
```

### Lancer l'application

```bash
streamlit run app.py
```

L'application s'ouvrira automatiquement dans votre navigateur à l'adresse `http://localhost:8501`

## 📁 Structure du projet

```
heat_risk_france/
├── app.py                          # Application Streamlit principale
├── requirements.txt                # Dépendances Python
├── README.md                       # Ce fichier
│
├── data/
│   ├── processed/                  # Données traitées (GeoJSON, CSV)
│   │   ├── paris_iris_heat_vulnerability.geojson
│   │   ├── paris_iris_elderly_pct.csv
│   │   ├── lille_iris_heat_vulnerability.geojson
│   │   ├── lyon_iris_heat_vulnerability.geojson
│   │   ├── marseille_iris_heat_vulnerability.geojson
│   │   └── toulouse_iris_heat_vulnerability.geojson
│   └── raw/                        # Données brutes (non incluses dans git)
│       ├── lcz/                    # Données LCZ du CEREMA
│       └── iris/                   # Limites IRIS de l'IGN
│
├── scripts/                        # Scripts de traitement de données
│   └── process_iris_heat_all_cities.py
│
└── notebooks/                      # Notebooks Jupyter d'exploration
```

## 📊 Sources de données

Toutes les données proviennent de sources ouvertes françaises :

1. **Zones Climatiques Locales (LCZ)** - CEREMA (2022)
   - 88 aires urbaines de plus de 50 000 habitants
   - Source : [data.gouv.fr](https://www.data.gouv.fr)
   - Licence : Licence Ouverte

2. **Limites IRIS** - IGN (Institut national de l'information géographique et forestière)
   - IRIS GE (entités géographiques) - Limites des districts de recensement
   - Source : [IRIS GE](https://geoservices.ign.fr/irisge)
   - Licence : Licence Ouverte

3. **Données démographiques** - INSEE (2022)
   - Composition des ménages incluant les personnes âgées vivant seules
   - Pourcentages de personnes âgées par IRIS
   - Licence : Licence Ouverte

## 🛠️ Technologies utilisées

- **Streamlit** : Framework web pour l'application
- **GeoPandas** : Manipulation de données géospatiales
- **Plotly** : Visualisations interactives
- **Pandas** : Traitement de données
- **Python 3.9+** : Langage de programmation

## 📝 Limitations

- Les scores LCZ sont un **proxy** pour l'exposition à la chaleur, pas une mesure directe de température
- Ne prend pas en compte les événements de canicule spécifiques ou les conditions en temps réel
- Les données démographiques sont mises à jour annuellement
- Les scores de risque sont des **indicateurs relatifs**, pas des prédictions absolues
- Ne prend pas en compte :
  - La prévalence de la climatisation
  - L'accès aux espaces verts
  - Les réseaux de soutien social
  - L'accessibilité aux soins de santé

## 🤝 Contribution

Les contributions, suggestions et retours sont les bienvenus ! N'hésitez pas à ouvrir une issue ou une pull request.

## 📄 Licence

Ce projet utilise des données ouvertes provenant de sources publiques françaises sous Licence Ouverte / Open License.

## 🙏 Remerciements

- **Eric Klinenberg** - Recherche sur les canicules et la vulnérabilité sociale
- **CEREMA** - Données sur les zones climatiques locales
- **INSEE** - Statistiques de population
- **IGN** - Données géographiques
- **Streamlit** - Framework d'application web

## 📧 Contact

Pour toute question ou suggestion concernant ce projet, n'hésitez pas à ouvrir une issue sur GitHub.

---

**Réalisé avec Streamlit 🎈**
