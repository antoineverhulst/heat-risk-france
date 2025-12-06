"""
Page À Propos - Documentation du projet
"""

import streamlit as st

# Configuration de la page
st.set_page_config(
    page_title="À Propos - Risque de Chaleur France",
    page_icon="📖",
    layout="wide"
)

st.title("📖 À Propos de ce Projet")

# ========================================================================
# SECTION 1 : OBJECTIF
# ========================================================================
st.header("Objectif")

st.subheader("Comprendre le Risque de Chaleur Urbaine et la Vulnérabilité Sociale")

st.markdown("""
Les îlots de chaleur urbains se forment lorsque les villes remplacent la couverture végétale naturelle
par des concentrations denses de chaussées, bâtiments et autres surfaces qui absorbent et retiennent la chaleur.
Cela crée des « îlots » de températures plus élevées par rapport aux zones environnantes.

La vulnérabilité sociale amplifie le risque de chaleur. Les recherches d'Eric Klinenberg sur la canicule
de Chicago en 1995 ont montré que l'isolement social, en particulier chez les personnes âgées,
augmente considérablement la mortalité lors d'épisodes de chaleur extrême.

À partir de données de 2017, l'INSEE (Institut National de la Statistique et des Études Économiques)
a montré comment les populations à faibles revenus et âgées étaient plus vulnérables aux fortes chaleurs
dans 9 villes françaises, non seulement en raison d'une plus faible végétation, isolation des bâtiments
mais également à cause de plus faibles moyens d'adaptation.
""")

st.subheader("Outil d'aide à la décision")

st.markdown("""
Cet outil d'aide à la décision permet d'identifier, au sein des dix principales métropoles françaises,
les zones géographiques où se concentrent les populations âgées vivant seules dans des secteurs
particulièrement exposés aux îlots de chaleur urbains.

Cette cartographie des zones à risque facilite le déploiement ciblé de mesures préventives
en période de fortes chaleurs :
* Organisation de rondes de surveillance et de contact auprès des personnes vulnérables
* Ouverture d'espaces de rafraîchissement dans les secteurs prioritaires
* Mise en place de navettes vers des zones moins exposées thermiquement
""")

st.subheader("Sources de données")

st.markdown("""
L'analyse croise trois sources de données officielles :
* **Exposition thermique** : Classification par zones climatiques locales (niveaux élevé/moyen/faible)
  établie par le CEREMA - [Cartographie des zones climatiques locales](https://www.cerema.fr/fr/centre-ressources/boutique/zones-climatiques-locales-france)
* **Vulnérabilité démographique** : Données sur les personnes âgées vivant seules,
  issues des statistiques de l'INSEE - [Statistiques démographiques](https://www.insee.fr)
* **Référentiel géographique** : Contours des IRIS (Îlots Regroupés pour l'Information Statistique)
  fournis par l'IGN - [Contours IRIS](https://geoservices.ign.fr/contoursiris)
""")

st.markdown("---")

# ========================================================================
# SECTION 2 : MÉTHODOLOGIE
# ========================================================================
st.header("Méthodologie")

st.markdown("""
Cette application analyse le risque de chaleur urbaine en combinant les données d'exposition thermique
avec des indicateurs de vulnérabilité démographique au niveau IRIS (îlot regroupé pour l'information statistique).

#### Évaluation de l'Exposition à la Chaleur

Les scores de chaleur sont dérivés de la classification des **Zones Climatiques Locales (LCZ)** :
- **Source** : Données LCZ 2022 du CEREMA pour les villes françaises
- **Classification** : Catégorielle (Élevée/Moyenne/Faible)
- **Agrégation** : Catégorie LCZ la plus commune au sein de chaque zone IRIS

| Score de Chaleur | Classes LCZ | Description |
|------------------|-------------|-------------|
| **Élevée** | 1, 2, 3, 8, 10 | Zones urbaines compactes avec bâtiments denses |
| **Moyenne** | 4, 5, 6, 7, E | Zones urbaines ouvertes et mixtes |
| **Faible** | 9, A, B, C, D, F, G | Zones végétalisées, plans d'eau, parcs |

#### Vulnérabilité Démographique

Données de population de l'INSEE (Institut national de la statistique) :
- **% Personnes Âgées (55+)** : Pourcentage de la population âgée de 55 ans et plus
- **% Personnes Âgées Vivant Seules** : Indicateur d'isolement social
- **Comptes absolus** : Nombre d'individus vulnérables par IRIS

Les populations âgées sont plus sensibles au stress thermique, et l'isolement social
augmente significativement le risque de mortalité pendant les vagues de chaleur.

#### Indicateurs de Risque

Nos indicateurs de risque combinent les catégories d'exposition à la chaleur avec les populations vulnérables :

**Multiplicateur de Chaleur :**
- Chaleur Faible = 0 (aucun risque lié à la chaleur)
- Chaleur Moyenne = 1 (risque modéré)
- Chaleur Élevée = 2 (risque significatif)

**Indicateur de Risque** = Multiplicateur de Chaleur × Nombre de Personnes Âgées (55+) Vivant Seules

Cette approche priorise les zones avec :
1. **Une exposition significative à la chaleur** (Moyenne ou Élevée)
2. **Des populations vulnérables** (personnes âgées vivant seules)
3. **Un risque combiné** (multiplicateur de chaleur × nombre de personnes vulnérables)

### Contexte de Recherche

Ce travail est inspiré par :

**📚 Livres & Articles :**
- **Klinenberg, E. (2002)** - *Heat Wave: A Social Autopsy of Disaster in Chicago*
  - Recherche pionnière montrant que l'isolement social, et non la pauvreté seule,
    était le facteur principal de mortalité liée à la chaleur pendant la canicule de Chicago en 1995
- **Harlan, S. L., et al. (2006)** - "Neighborhood Effects on Heat Deaths"
  - Analyse des schémas spatiaux de la vulnérabilité à la chaleur

### Sources de Données

- **Données LCZ** : CEREMA (2022) via data.gouv.fr
- **Limites IRIS** : IGN (Institut national de l'information géographique et forestière) - [IRIS GE](https://geoservices.ign.fr/irisge)
- **Données démographiques** : INSEE (2022)
- **Licence** : Licence Ouverte / Open License

### Limitations

- Les LCZ sont un **proxy** pour l'exposition à la chaleur, pas une mesure directe de température
- Ne prend pas en compte les événements de canicule spécifiques ou les conditions en temps réel
- Les données démographiques sont mises à jour annuellement, peuvent ne pas refléter les changements récents
- Les scores de risque sont des **indicateurs relatifs**, pas des prédictions absolues
- Ne prend pas en compte :
  - La prévalence de la climatisation
  - L'accès aux espaces verts
  - Les réseaux de soutien social
  - L'accessibilité aux soins de santé

### Contact & Contribuer

Ceci est un projet open-source. Les contributions, suggestions et retours sont les bienvenus !

**Réalisé avec Streamlit 🎈**
""")
