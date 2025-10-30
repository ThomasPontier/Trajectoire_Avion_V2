# Simulateur de Trajectoire d'Avion - Projet P21

## Description

Ce projet permet de calculer et visualiser la trajectoire optimale d'un avion pour atteindre le point FAF (Final Approach Fix) d'un aéroport dans un espace aérien configurable.

## 🎯 Version Actuelle : 1.1+

### ✨ Nouveautés Version 1.1+
- **Interface à onglets** : Organisation claire avec 3 onglets (Environnement, Obstacles, Avion)
- **Environnement personnalisable** : Dimensions configurables (X, Y, Z)
- **Positions configurables** : Aéroport et FAF repositionnables
- **Obstacles cylindriques** : Ajout de zones interdites de vol
- **Axe d'approche** : Visualisation de la trajectoire d'approche finale (demi-droite pointillée)
- **Sauvegarde persistante** : Configuration automatiquement sauvegardée et restaurée
- **Types d'avions** : Léger, Commercial, Cargo avec spécifications différentes
- **Contrainte de pente maximale** : Respect de la pente max selon le type d'avion
- **Vol en palier optimisé** : L'avion vole en palier et descend au plus tard
- **Visualisation améliorée** : Phases colorées (palier vert, descente orange)
- **Graphiques détaillés** : Affichage des limites de pente

[📖 Documentation complète V1.1](VERSION_1_1.md)

## Fonctionnalités Principales

### 🌍 Onglet Environnement
- **Dimensions personnalisables** : Taille de l'espace aérien (X, Y, Z)
- **Position de l'aéroport** : Coordonnées configurables (X, Y, Z)
- **Position du FAF** : Point d'approche finale configurable (X, Y, Z)
- **Axe d'approche** : Demi-droite pointillée partant de la piste et passant par le FAF
- **Validation instantanée** : Application immédiate de la configuration

### 🚧 Onglet Obstacles
- **Cylindres 3D** : Obstacles représentant des zones interdites
- **Interface scrollable** : Gestion d'un nombre illimité d'obstacles
- **Édition complète** :
  - Ajout avec position (X, Y), rayon et hauteur
  - Édition par sélection (double-clic)
  - Suppression individuelle ou globale
- **Sauvegarde automatique** : Persistance après chaque modification
- **Liste détaillée** : Visualisation de tous les cylindres actifs

### ✈️ Onglet Avion
- **Types d'avions** : 
  - 🛩️ Léger : Pentes ±15°/±10°, vitesse 200 km/h
  - ✈️ Commercial : Pentes ±10°/±6°, vitesse 250 km/h
  - 🛫 Cargo : Pentes ±8°/±5°, vitesse 220 km/h
- **Position initiale** : Configuration X, Y, Altitude
- **Paramètres de vol** : Vitesse et cap initial
- **Spécifications affichées** : Contraintes visibles en temps réel

### 📊 Visualisation
- **Vue 3D interactive** : 
  - Espace aérien avec grille
  - Aéroport (carré rouge)
  - FAF (triangle bleu)
  - Axe d'approche (demi-droite pointillée noire)
  - Obstacles cylindriques (surfaces 3D)
  - Trajectoire colorée par phase
- **Graphiques temporels** :
  - Altitude au cours du temps
  - Pente au cours du temps (avec limites)
  - Vitesse au cours du temps

### Simulation
- Calcul de trajectoire directe vers le FAF
- Affichage en temps réel de la trajectoire

## 💾 Sauvegarde Automatique

La configuration est automatiquement sauvegardée dans `config.json` :
- **Environnement** : Dimensions, positions de l'aéroport et du FAF
- **Obstacles** : Tous les cylindres avec leurs caractéristiques
- **Avion** : Type, position, vitesse et cap

Au redémarrage de l'application, toute la configuration est restaurée automatiquement.

## Installation

### Prérequis
- Python 3.8 ou supérieur
- pip

### Installation des dépendances

```powershell
pip install -r requirements.txt
```

## Utilisation

### Lancer le simulateur

```powershell
python main.py
```

### Étapes d'utilisation

1. **🌍 Configurer l'environnement** (Onglet Environnement) :
   - Définir les dimensions de l'espace aérien (X, Y, Z)
   - Placer l'aéroport (X, Y, Z = 0 pour le sol)
   - Placer le FAF (généralement quelques km avant l'aéroport)
   - Cliquer sur "Appliquer Configuration"
   - L'axe d'approche (pointillés noirs) apparaît automatiquement

2. **🚧 Ajouter des obstacles** (Onglet Obstacles) :
   - Saisir position X, Y (km)
   - Définir rayon et hauteur du cylindre
   - Cliquer sur "Ajouter ce Cylindre"
   - Gérer via la liste : éditer (double-clic) ou supprimer
   - Configuration sauvegardée automatiquement

3. **✈️ Configurer l'avion** (Onglet Avion) :
   - Choisir le type : Léger, Commercial ou Cargo
   - Observer les spécifications (pentes max, vitesse typique)
   - Entrer la position X et Y (km)
   - Définir l'altitude (km)
   - Régler la vitesse (km/h)
   - Définir le cap initial (degrés, 0° = Nord, 90° = Est)

4. **✅ Valider et simuler** :
   - Cliquer sur "Valider Position"
   - L'avion apparaît dans la vue 3D
   - Cliquer sur "Lancer Simulation"
   - La trajectoire s'affiche avec phases colorées :
     - 🟢 Vert : Vol en palier
     - 🟡 Doré : Transition progressive
     - 🟠 Orange-Rouge : Descente
   - Les graphiques montrent l'évolution avec limites de pente

5. **📊 Analyser les résultats** :
   - Vue 3D avec trajectoire, obstacles et axe d'approche
   - Distance de vol en palier et de descente
   - Pente utilisée (respect des contraintes)
   - Évolution temporelle : altitude, pente, vitesse

6. **🔄 Réinitialiser** :
   - Cliquer sur "Réinitialiser" pour recommencer
   - La configuration reste sauvegardée

## Architecture du Projet

```
V2/
├── main.py                      # Interface graphique avec onglets
├── environment.py               # Gestion de l'environnement aérien
├── aircraft.py                  # Types d'avions et spécifications
├── trajectory_calculator.py     # Calcul de trajectoires optimales
├── config.json                  # Sauvegarde persistante (généré automatiquement)
├── requirements.txt             # Dépendances Python
├── README.md                    # Documentation (ce fichier)
├── VERSION_1_1.md              # Documentation détaillée V1.1
└── ROADMAP.md                   # Feuille de route du projet
```

### Fichiers Principaux

- **main.py** (1100+ lignes) : Interface graphique tkinter avec 3 onglets
  - Onglet Environnement : Configuration de l'espace aérien
  - Onglet Obstacles : Gestion des cylindres
  - Onglet Avion : Configuration du vol
  - Visualisation 3D et graphiques matplotlib

- **trajectory_calculator.py** : Algorithmes de calcul
  - Vol en palier jusqu'au point optimal
  - Transition progressive (fonction cosinus)
  - Descente linéaire jusqu'au FAF
  - Respect des contraintes de pente

- **aircraft.py** : Modèle d'avion avec 3 types
  - Spécifications par type (pentes, vitesse)
  - Validation des paramètres

- **environment.py** : Modèle de l'espace aérien
  - Dimensions configurables
  - Positions de l'aéroport et du FAF
  - Validation des coordonnées

## Évolutions

### ✅ Version 1.1+ - IMPLÉMENTÉE
- ✅ Interface à onglets (Environnement, Obstacles, Avion)
- ✅ Environnement personnalisable (dimensions, positions)
- ✅ Obstacles cylindriques avec gestion complète
- ✅ Axe d'approche visualisé (demi-droite pointillée)
- ✅ Sauvegarde persistante (config.json)
- ✅ Types d'avions (Léger, Commercial, Cargo)
- ✅ Contrainte de pente maximale respectée
- ✅ Vol en palier puis descente optimale
- ✅ Transitions progressives lisses (cosinus)
- ✅ Visualisation avec phases colorées
- ✅ Graphiques avec limites

### 🔄 Version 1.2 - PROCHAINE
- Rayon de virage minimal
- Détection de collision avec obstacles
- Recalcul automatique pour éviter les obstacles
- Implémentation de trajectoires courbes réalistes

### Version 2.0 - FUTUR
- Optimisation multi-critères (temps, carburant, confort)
- Algorithmes d'évitement avancés
- Conditions météorologiques (vent, turbulences)
- Export des trajectoires

## Structure des Données

### Système de Coordonnées
- X : Axe Est-Ouest (0 à 50 km)
- Y : Axe Nord-Sud (0 à 50 km)
- Z : Altitude (0 à 5 km)

### Paramètres de l'Avion
- Position : [x, y, z] en km
- Vitesse : en km/h
- Cap : en degrés (0° = Nord)

## Auteur

Projet P21 - ESTACA 4ème année

## Date

Octobre 2025
