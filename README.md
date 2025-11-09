# 🛩️ Simulateur de Trajectoire d'Avion

**Projet P21 - ESTACA 4ème année**

Application standalone de simulation et visualisation de trajectoires aériennes optimales pour l'approche finale d'un aéroport.

![Version](https://img.shields.io/badge/version-1.3-blue)
![Python](https://img.shields.io/badge/python-3.8+-green)
![License](https://img.shields.io/badge/license-Educational-orange)

---

## 📋 Table des Matières

- [À propos](#-à-propos)
- [Installation Rapide](#-installation-rapide)
- [Architecture du Projet](#-architecture-du-projet)
- [Fonctionnalités](#-fonctionnalités)
- [Guide d'Utilisation](#-guide-dutilisation)
- [Calcul des Trajectoires](#-calcul-des-trajectoires)
- [Logique détaillée (Document séparé)](#-logique-détaillée-document-séparé)
- [Génération de l'Exécutable](#-génération-de-lexécutable)
- [Configuration](#-configuration)
- [Développement](#-développement)

---

## 🎯 À propos

Ce simulateur permet de calculer et visualiser en 3D la trajectoire optimale d'un avion pour atteindre le point FAF (Final Approach Fix) d'un aéroport. Il prend en compte :

- **La physique du vol** : contraintes de pente, rayon de virage, vitesse
- **Les obstacles** : zones interdites de survol (cylindres 3D)
- **Différents types d'avions** : léger, commercial, cargo
- **Deux modes de trajectoire** : approche directe ou interception d'axe

### 🌟 Caractéristiques Principales

- ✅ **Interface graphique intuitive** avec onglets organisés
- ✅ **Visualisation 3D interactive** avec barre d'outils de navigation
- ✅ **Calcul physique réaliste** avec contraintes aéronautiques
- ✅ **Simulations multiples configurables** : 1 à 50 trajectoires paramétrables 🆕
- ✅ **Système de sécurité avancé** : refus absolu des trajectoires dangereuses 🆕
- ✅ **Sauvegarde automatique** de la configuration
- ✅ **Application standalone** : aucune installation Python nécessaire pour l'exécutable

---

## 🚀 Installation Rapide

### Option 1 : Utiliser l'Exécutable (Recommandé pour les Utilisateurs)

1. **Téléchargez** le fichier `SimulateurTrajectoireAvion.exe`
2. **Copiez-le** où vous voulez sur votre ordinateur
3. **Double-cliquez** pour lancer l'application
4. ✨ C'est tout ! Aucune installation nécessaire

> 💡 **Note** : Le fichier `config.json` sera créé automatiquement au premier lancement dans le même dossier que l'exécutable.

### Option 2 : Exécuter depuis le Code Source (Pour les Développeurs)

#### Prérequis
- Python 3.8 ou supérieur
- pip (gestionnaire de packages Python)

#### Installation

```powershell
# 1. Cloner le dépôt
git clone https://github.com/ThomasPontier/Trajectoire_Avion_V2.git
cd Trajectoire_Avion_V2

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. Lancer l'application
python main.py
```

Ou sous Windows, double-cliquez sur `lancer_simulateur.bat`

---

## 📁 Architecture du Projet

### Structure des Fichiers

```
Trajectoire_Avion_V2/
│
├── 📄 main.py                          # Interface graphique principale (1748 lignes)
├── 📄 aircraft.py                      # Gestion des avions et spécifications (149 lignes)
├── 📄 environment.py                   # Environnement aérien et points de navigation (88 lignes)
├── 📄 trajectory_calculator.py         # Calcul des trajectoires optimales (2001 lignes)
│
├── 🔧 config.json                      # Configuration sauvegardée (auto-généré)
├── 🖼️ logo.png                         # Logo de l'application
│
├── 🔨 build_exe.py                     # Script de génération de l'exécutable
├── 🔨 SimulateurTrajectoireAvion.spec  # Configuration PyInstaller
├── 🔨 lancer_simulateur.bat            # Lanceur Windows rapide
│
├── 📦 requirements.txt                 # Dépendances Python
└── 📖 README.md                        # Cette documentation
```

### Modules Principaux

#### 1. **main.py** - Interface Graphique
- Classe `FlightSimulatorGUI` : interface Tkinter avec 4 onglets
- Gestion des événements utilisateur
- Visualisation 3D et 2D avec Matplotlib
- Sauvegarde/chargement de la configuration

#### 2. **aircraft.py** - Modèle d'Avion
- Classe `AircraftType` : spécifications des types d'avions
- Classe `Aircraft` : représentation d'un avion avec :
  - Position, vitesse, cap
  - Contraintes de pente (montée/descente)
  - Calcul du rayon de virage minimal

**Types d'avions disponibles :**

| Type | Pente Max Montée | Pente Max Descente | Vitesse Croisière | Vitesse Approche | Inclinaison Max |
|------|------------------|-------------------|-------------------|------------------|-----------------|
| 🛩️ Léger | +15° | -10° | 180 km/h | 120 km/h | 30° |
| ✈️ Commercial | +10° | -6° | 250 km/h | 180 km/h | 25° |
| 🛫 Cargo | +8° | -5° | 220 km/h | 160 km/h | 20° |

#### 3. **environment.py** - Environnement Aérien
- Classe `Environment` : espace aérien 3D
- Positions de l'aéroport et du FAF
- Validation des positions
- Calcul de l'axe d'approche

#### 4. **trajectory_calculator.py** - Calcul de Trajectoire
- Classe `TrajectoryCalculator` : algorithmes de calcul
- Deux modes de calcul :
  - **Mode simplifié** : virage direct vers FAF
  - **Mode réaliste** : interception tangente de l'axe d'approche
- Gestion des contraintes physiques
- Évitement d'obstacles

---

## ✨ Fonctionnalités

### 🌍 Onglet 1 : Configuration

#### **Environnement**
- Dimensions personnalisables de l'espace aérien (X, Y, Z)
- Position de l'aéroport (X, Y, Z)
- Position du point FAF (X, Y, Z)
- Validation instantanée avec prévisualisation 3D

#### **Obstacles**
- Ajout de cylindres 3D (zones interdites)
- Paramètres : position (X, Y), rayon, hauteur
- Édition par double-clic
- Suppression individuelle ou globale
- Liste scrollable pour nombre illimité d'obstacles

#### **Avion**
- Sélection du type (Léger / Commercial / Cargo)
- Position initiale (X, Y, Altitude)
- Vitesse de croisière (km/h)
- **Cap initial** (0°=Nord, 90°=Est, 180°=Sud, 270°=Ouest)
- Option **"Virages réalistes"** pour mode interception d'axe

#### **Simulations Multiples** 🆕
- **Nombre de trajectoires configurables** : 1 à 50 simulations
- 🎲 **Positions aléatoires** : variations autour de la position de base
- 🧭 **Caps variables** : déviation aléatoire ±30° du cap initial
- ⚡ **Vitesses fluctuantes** : variation ±10% de la vitesse de référence
- 🛡️ **Analyse de sécurité automatique** : refus des trajectoires dangereuses
- 📊 **Rapport de sécurité** : statistiques des trajectoires valides/refusées
- 🎯 **Bouton dynamique** : "X Simulations Aléatoires" selon configuration

### 📦 Onglet 2 : Vue 3D

Visualisation 3D interactive avec :
- **Barre d'outils de navigation** : zoom, rotation, déplacement
- Espace aérien avec grille
- 🟥 Aéroport (carré rouge)
- 🔷 FAF (triangle bleu)
- ➡️ **Flèche verte** : direction initiale de l'avion
- Obstacles cylindriques semi-transparents
- Axe d'approche (ligne pointillée)
- **Trajectoire colorée** :
  - 🔵 **Cyan** : phase de virage
  - 🟢 **Vert** : approche en palier
  - 🟠 **Orange** : descente finale
- ⬥ Point d'interception (losange bleu)

### 📐 Onglet 3 : Vues 2D

Trois projections orthogonales :
- **Vue de dessus (XY)** : plan horizontal
- **Vue de face (XZ)** : profil longitudinal
- **Vue de côté (YZ)** : profil latéral

### 📊 Onglet 4 : Paramètres

Graphiques temporels :
- **Altitude** vs distance/temps
- **Pente** vs temps (avec limites min/max)
- **Vitesse** vs temps (décélération en approche)

### 💾 Sauvegarde Automatique

Toute la configuration est sauvegardée dans `config.json` :
- Dimensions de l'environnement
- Positions aéroport et FAF
- Liste des obstacles
- Paramètres de l'avion
- ✅ Restauration automatique au redémarrage

---

## 🎮 Guide d'Utilisation

### Démarrage Rapide

1. **Lancez l'application** (double-clic sur `.exe` ou `python main.py`)
2. **Configurez l'environnement** (onglet Configuration → Environnement)
3. **Ajoutez des obstacles** (optionnel, onglet Configuration → Obstacles)
4. **Configurez l'avion** (onglet Configuration → Avion)
5. **Choisissez le nombre de trajectoires** 🆕 (1-50 simulations)
6. **Cliquez sur "X Simulations Aléatoires"** 🆕 (ou "Calculer la Trajectoire" pour une seule)
7. **Visualisez** les résultats dans les onglets Vue 3D, Vues 2D et Paramètres

### Options de Simulation 🆕

#### Simulation Unique
- Cliquez sur **"Calculer la Trajectoire"**
- Utilise exactement la configuration définie
- Idéal pour tester des paramètres précis

#### Simulations Multiples
- Configurez le **nombre de trajectoires** (1-50)
- Cliquez sur **"X Simulations Aléatoires"**
- Génère des variations aléatoires :
  - 📍 **Position** : ±5 km autour du point défini
  - 🧭 **Cap** : ±30° autour du cap défini
  - ⚡ **Vitesse** : ±10% autour de la vitesse définie
- ✅ **Analyse de sécurité automatique** : refus des trajectoires dangereuses

### Configuration Exemple

#### Scénario 1 : Approche Simple

```
Environnement:
├─ Taille: 100 × 100 × 10 km
├─ Aéroport: (5, 25, 0)
└─ FAF: (20, 25, 1)

Avion (Léger):
├─ Position: (70, 70, 3)
├─ Cap: 180° (Sud)
├─ Vitesse: 180 km/h
└─ ☐ Virages réalistes: DÉSACTIVÉ

Résultat:
🔵 Virage de ~45° vers l'ouest
🟢 Vol en palier vers le FAF
🟠 Descente de 3→1 km
```

#### Scénario 2 : Interception d'Axe avec Obstacles

```
Environnement:
├─ Taille: 100 × 100 × 10 km
├─ Aéroport: (5, 25, 0)
├─ FAF: (20, 25, 1)
└─ Obstacles:
    ├─ Cylindre 1: (55, 25, R=10, H=3)
    └─ Cylindre 2: (60, 80, R=12, H=3)

Avion (Commercial):
├─ Position: (70, 93, 2)
├─ Cap: 90° (Est)
├─ Vitesse: 250 km/h
└─ ☑️ Virages réalistes: ACTIVÉ

Résultat:
🔵 Virage tangent pour intercepter l'axe aéroport-FAF
🟢 Suivi de l'axe d'approche
🟠 Descente alignée jusqu'au FAF
```

### Navigation 3D

- 🖱️ **Clic gauche + glisser** : rotation
- 🖱️ **Clic droit + glisser** : déplacement (pan)
- 🖱️ **Molette** : zoom
- 🔧 **Barre d'outils** :
  - 🏠 Réinitialiser la vue
  - ↔️ Déplacer
  - 🔍 Zoom sur zone
  - 💾 Sauvegarder l'image

---

## 🧮 Calcul des Trajectoires

### Principe Fondamental

La trajectoire est calculée en fonction du **vecteur vitesse** de l'avion (position + cap + vitesse). L'avion ne peut pas changer instantanément de direction.

### Mode 1 : Trajectoire Directe (☐ Virages désactivés)

**Algorithme :**

1. **Analyse du cap initial**
   - Calculer l'angle θ entre le cap actuel et la direction vers le FAF
   - Si θ > 5° → virage nécessaire

2. **Virage initial**
   - Calcul du rayon minimal : `R_min = V² / (g × tan(φ_max))`
   - Détermination du sens (gauche/droite) pour angle le plus court
   - Tracé d'un arc de cercle jusqu'à pointer vers le FAF

3. **Ligne droite**
   - Vol en ligne droite vers le FAF
   - Altitude : palier puis descente (respectant pente max)

**Formule du rayon de virage :**

```
R_min = V² / (g × tan(φ_max))
```

Où :
- `V` = vitesse (m/s)
- `g` = 9.81 m/s² (gravité)
- `φ_max` = angle d'inclinaison maximum (30° léger, 25° commercial, 20° cargo)

**Exemple** (avion léger, 180 km/h, φ=30°) :
```
V = 50 m/s
R = (50)² / (9.81 × tan(30°))
R = 2500 / 5.66
R ≈ 441 mètres = 0.44 km
```

### Mode 2 : Interception d'Axe (☑️ Virages réalistes)

**Algorithme :**

1. **Définir l'axe d'approche**
   - Direction : Aéroport → FAF (prolongée au-delà)
   - Ligne droite théorique d'atterrissage

2. **Calcul géométrique**
   - Centre du cercle de virage basé sur le cap actuel
   - Résolution d'équation quadratique pour point tangent
   - Arc de cercle jusqu'à l'interception tangente

3. **Suivi de l'axe**
   - Vol aligné sur l'axe d'approche
   - Descente progressive jusqu'au FAF
   - Décélération durant l'approche finale

**Avantages :**
- ✅ Respect des contraintes physiques
- ✅ Trajectoire réaliste (procédure IFR standard)
- ✅ Alignement parfait avec l'axe de la piste
- ✅ Minimise l'angle de correction

**Cas d'échec :**
Si la géométrie rend l'interception impossible (avion trop près, angle impossible), le système bascule automatiquement en Mode 1.

### Gestion de l'Altitude

**Stratégie :**
1. Vol en palier le plus longtemps possible
2. Descente au plus tard pour respecter la pente maximale
3. Décélération progressive en approche finale

**Calcul de la distance de descente :**

```
d_descente = Δh / tan(pente_max)
```

**Exemple** (descente de 2 km, pente -10°) :
```
d = 2000 m / tan(10°)
d ≈ 11 340 m = 11.3 km
```

### Évitement d'Obstacles et Système de Sécurité

#### Système de Sécurité Multi-Niveaux 🆕

Le simulateur implémente un **système de sécurité à 5 niveaux** pour garantir des trajectoires sûres :

**Niveau 1 - Marge Standard (5 km)**
- Première tentative avec marge de sécurité normale
- Évitement préventif des obstacles

**Niveau 2 - Marge Réduite (3 km)**
- Réduction de la marge de sécurité
- Trajectoire plus directe mais sécurisée

**Niveau 3 - Marge Minimale (1 km)**
- Marge de sécurité critique
- Trajectoire de derniers recours

**Niveau 4 - Trajectoire d'Urgence (0.5 km)**
- Calcul de trajectoire d'urgence
- Marge de sécurité absolue minimale

**Niveau 5 - Analyse de Sécurité Critique**
- Extension de la marge jusqu'à 40 km pour analyse
- **Refus absolu** si collision inévitable
- Protection contre les trajectoires dangereuses

#### Fonctionnalités de Sécurité

- ✅ **Détection automatique** des collisions avec les cylindres
- ✅ **Algorithme d'évitement latéral** progressif avec escalade
- ✅ **Préservation de l'altitude** pour éviter les obstacles
- ✅ **Refus catégorique** des trajectoires à risque de collision

---

## 🧠 Logique détaillée (Document séparé)

Pour une explication schématique approfondie (diagrammes ASCII, flux décisionnel, description de chaque fonction de calcul), consultez le fichier dédié :

`docs/logique_trajectoire.md`

Ce document couvre :
1. Vue d'ensemble du pipeline
2. Modes de calcul (standard, virages réalistes, tours automatiques)
3. Gestion de l'altitude (palier → transition → descente → lissage)
4. Évitement d'obstacles (waypoints tangents + recalcul avec marges)
5. Liste exhaustive des fonctions et leur rôle
6. Pistes d'amélioration futures

> Astuce : ouvrez-le dans VS Code avec l'aperçu Markdown pour profiter de la mise en forme.
- ✅ **Rapport de sécurité détaillé** pour chaque simulation
- ✅ **Analyse en temps réel** de la viabilité des trajectoires

#### Messages de Sécurité

Le système affiche des messages explicites :
- 🟢 **"Trajectoire sécurisée"** : aucun obstacle détecté
- 🟡 **"Évitement réussi"** : obstacles contournés avec succès
- 🔴 **"REFUS ABSOLU"** : collision inévitable, trajectoire rejetée

---

## 🔨 Génération de l'Exécutable

### Prérequis
- Python 3.8+
- PyInstaller (installé automatiquement si absent)
- Pillow (pour conversion du logo en icône)

### Commande Unique

```powershell
python build_exe.py
```

### Processus Automatique

Le script `build_exe.py` effectue automatiquement :

1. ✅ Vérification/installation de PyInstaller
2. 🧹 Nettoyage des builds précédents
3. 🖼️ Conversion du logo PNG en icône ICO
4. 📦 Création du fichier .spec avec configuration optimale
5. 🚀 Build de l'exécutable standalone
6. ✅ Validation et affichage de la taille

### Résultat

```
📦 Exécutable créé : dist\SimulateurTrajectoireAvion.exe
📁 Taille : ~150 MB
```

### Configuration Incluse

L'exécutable contient :
- ✅ Python et toutes les bibliothèques
- ✅ Matplotlib, NumPy, Tkinter
- ✅ Fichier config.json par défaut
- ✅ Icône de l'application
- ❌ **Aucune installation externe requise**

### Distribution

Pour distribuer l'application :
1. Copiez uniquement `SimulateurTrajectoireAvion.exe`
2. L'utilisateur double-clique pour lancer
3. Le fichier `config.json` sera créé automatiquement dans le même dossier

---

## ⚙️ Configuration

### Structure de config.json

```json
{
    "environment": {
        "size_x": 100.0,
        "size_y": 100.0,
        "size_z": 10.0,
        "airport": {
            "x": 5.0,
            "y": 25.0,
            "z": 0.0
        },
        "faf": {
            "x": 20.0,
            "y": 25.0,
            "z": 1.0
        }
    },
    "cylinders": [
        {
            "x": 55.0,
            "y": 25.0,
            "radius": 10.0,
            "height": 3.0
        }
    ],
    "aircraft": {
        "type": "commercial",
        "position": {
            "x": 70.0,
            "y": 70.0,
            "z": 3.0
        },
        "speed": 250.0,
        "heading": 180.0
    },
    "simulation": {
        "num_trajectories": 10
    }
}
```

### Paramètres Personnalisables

#### Environnement
- `size_x`, `size_y`, `size_z` : dimensions de l'espace (km)
- `airport.x`, `airport.y`, `airport.z` : position aéroport
- `faf.x`, `faf.y`, `faf.z` : position FAF

#### Obstacles
- `x`, `y` : centre du cylindre (km)
- `radius` : rayon (km)
- `height` : hauteur (km)

#### Avion
- `type` : `"light"`, `"commercial"`, ou `"cargo"`
- `position.x`, `position.y`, `position.z` : position initiale
- `speed` : vitesse de croisière (km/h)
- `heading` : cap initial (0-360°, 0=Nord)

#### Simulation 🆕
- `num_trajectories` : nombre de trajectoires à calculer (1-50)
  - Valeur par défaut : 10
  - Influence les simulations multiples aléatoires
  - Sauvegardé automatiquement dans la configuration

---

## 👨‍💻 Développement

### Dépendances

```txt
numpy>=1.21.0
matplotlib>=3.4.0
```

Pour le build :
```txt
pyinstaller>=5.0
Pillow>=9.0
```

### Structure de Classe

```
FlightSimulatorGUI
├── Environment
├── Aircraft
│   └── AircraftType
└── TrajectoryCalculator
```

### Ajout d'un Nouveau Type d'Avion

Dans `aircraft.py`, ajouter dans `AircraftType.SPECIFICATIONS` :

```python
"nouveau_type": {
    "name": "Nom Affiché",
    "max_climb_slope": 12.0,
    "max_descent_slope": -7.0,
    "typical_speed": 200,
    "approach_speed": 150,
    "max_bank_angle": 28.0,
}
```

### Tests

Configurations de test incluses dans l'interface :
- Approche directe simple
- Interception d'axe
- Évitement d'obstacles multiples
- Différents caps initiaux

---

## 📊 Informations Techniques

### Performances

- **Temps de calcul** : < 1 seconde pour trajectoire standard
- **Points de trajectoire** : 1000-3000 selon distance
- **Fréquence d'échantillonnage** : 0.01 km (10 mètres)

### Contraintes Respectées

✅ Pente maximale de montée/descente par type d'avion  
✅ Rayon de virage minimal basé sur la physique  
✅ Vitesse variable (décélération en approche)  
✅ Altitude minimale (pas de vol souterrain)  
✅ Évitement d'obstacles cylindriques  

### Limitations Connues

⚠️ Pas de gestion du vent  
⚠️ Pas de consommation de carburant  
⚠️ Obstacles uniquement cylindriques  
⚠️ Pas de contraintes de trafic aérien  

---

## 📝 Historique des Versions

### Version 1.4 (2025-01-07) 🆕
- 🎲 **Simulations multiples configurables** : 1 à 50 trajectoires paramétrables
- 🛡️ **Système de sécurité multi-niveaux** : 5 niveaux d'escalade progressifs
- ❌ **Refus absolu des trajectoires dangereuses** : protection contre les collisions
- 📊 **Analyse de sécurité en temps réel** : rapport détaillé des trajectoires
- 🎯 **Interface utilisateur améliorée** : bouton dynamique et contrôles intuitifs
- ⚙️ **Configuration persistante** : sauvegarde des paramètres de simulation
- 🔍 **Marges de sécurité progressives** : de 5 km à 40 km selon le niveau critique

### Version 1.3 (2025-10-30)
- 🧭 Trajectoire basée sur le vecteur vitesse (cap + vitesse)
- 🔄 Virage initial automatique
- 📐 Physique du vol améliorée
- ➡️ Visualisation du cap avec flèche verte
- ⚡ Variation de vitesse en approche

### Version 1.2 (2025-10-28)
- 🔄 Virages réalistes avec rayon de courbure
- 🎯 Interception tangente de l'axe d'approche
- 🔍 Barre d'outils de navigation 3D
- 📊 Visualisation multi-phases colorée

### Version 1.1 (2025-10-25)
- 🌍 Interface à onglets
- 🚧 Gestion d'obstacles cylindriques
- ✈️ Types d'avions multiples
- 💾 Sauvegarde automatique

---

## 📧 Contact et Support

**Projet** : P21 - ESTACA 4ème année  
**Auteur** : Thomas Pontier  
**Repository** : [GitHub - Trajectoire_Avion_V2](https://github.com/ThomasPontier/Trajectoire_Avion_V2)

---

## 📜 License

Ce projet est à usage éducatif dans le cadre du projet P21 à l'ESTACA.

---

**🎓 Développé avec passion par les étudiants de l'ESTACA**

*Simulateur de Trajectoire d'Avion - Version 1.4*
