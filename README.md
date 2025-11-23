# Simulateur de Trajectoire d'Avion



Simulation et visualisation de trajectoires aériennes optimales pour l'approche finale d'un aéroport.

![Version](https://img.shields.io/badge/version-1.4-blue)
![Python](https://img.shields.io/badge/python-3.8+-green)

---


## Description

Calculez et visualisez en 3D la trajectoire optimale d'un avion vers le FAF (Final Approach Fix) :

- **Physique réaliste** : contraintes de pente, rayon de virage, vitesse
- **Évitement d'obstacles** : zones cylindriques interdites 
- **Types d'avions** : léger, commercial, cargo
- **Modes de vol** : approche directe ou interception d'axe
- **Simulations multiples** : 1 à 50 trajectoires aléatoires
- **Système de sécurité** : refus des trajectoires dangereuses

---

## Installation 

### Code Source (Développeurs)

```powershell
git clone https://github.com/ThomasPontier/Trajectoire_Avion_V2.git
cd Trajectoire_Avion_V2
pip install -r requirements.txt
python main.py
```

---

## Interface

### 4 Onglets Principaux

**Configuration**
- Environnement (dimensions, aéroport, FAF)
- Obstacles cylindriques 
- Types d'avions (léger/commercial/cargo)
- Simulations multiples (1-50 trajectoires)

**Vue 3D**
- Visualisation interactive
- Navigation : rotation, zoom, pan
- Trajectoire colorée par phase

**Vues 2D**
- Plans XY, XZ, YZ
- Projections orthogonales

**Paramètres**
- Graphiques altitude/vitesse/pente
- Analyse temporelle

---


## Build Exécutable

```powershell
python build_exe.py
```

Génère `SimulateurTrajectoireAvion.exe` (~150 MB) standalone.

---

## Configuration

Fichier `config.json` auto-sauvegardé :
- Dimensions environnement
- Positions aéroport/FAF
- Obstacles
- Paramètres avion

---

## Schémas Techniques (Dossier `schemas_rapport/`)

### Visualisation des Schémas

**Extensions VS Code requises :**

1. **Pour les fichiers `.drawio`** (trajectoires visuelles) :
   - Extension : **Draw.io Integration** 


2. **Pour les fichiers `.md`** (diagrammes Mermaid) :
   - Extension : **Markdown Preview Mermaid Support**
   
### Contenu des Schémas

**Schémas Draw.io** (trajectoires 3D) :
- `01_trajectoires_types.drawio` - 4 types de trajectoires avec formules
- `06_evitement_obstacles.drawio` - Stratégie d'évitement waypoints tangents

**Diagrammes Mermaid** (architecture et logique) :
- `02_architecture_systeme.md` - Architecture modulaire hiérarchique
- `03_decomposition_trajectory_calculator.md` - Arborescence fonctionnelle détaillée
- `04_flux_decision_calcul.md` - Flowchart logique de décision
- `05_gestion_altitude_3_phases.md` - Profil vertical en 3 phases

---

**GitHub** : [Trajectoire_Avion_V2](https://github.com/ThomasPontier/Trajectoire_Avion_V2)
