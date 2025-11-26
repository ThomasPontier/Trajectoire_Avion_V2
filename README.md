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

**GitHub** : [Trajectoire_Avion_V2](https://github.com/ThomasPontier/Trajectoire_Avion_V2)

