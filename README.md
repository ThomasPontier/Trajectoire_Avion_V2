# 🛩️ Simulateur de Trajectoire d'Avion

**Projet P21 - ESTACA 4ème année**

Simulation et visualisation de trajectoires aériennes optimales pour l'approche finale d'un aéroport.

![Version](https://img.shields.io/badge/version-1.4-blue)
![Python](https://img.shields.io/badge/python-3.8+-green)

---

## 📥 Téléchargement Direct

### 🚀 Version Exécutable (Recommandé)

**[📦 Télécharger SimulateurTrajectoireAvion.exe](https://github.com/ThomasPontier/Trajectoire_Avion_V2/releases/download/v1.4/SimulateurTrajectoireAvion.exe)**

> **💡 Instructions :**
> 1. Cliquez sur le lien ci-dessus
> 2. Le téléchargement démarre automatiquement
> 3. Double-cliquez sur le fichier pour lancer l'application
> 
> *Alternative : générez localement avec `python build_exe.py`*

**Caractéristiques :**
- ✅ **Prêt à utiliser** : double-clic et c'est parti !
- ✅ **Aucune installation** Python nécessaire
- ✅ **Taille** : ~150 MB
- ✅ **Compatible** Windows 10/11

---

## 🎯 Description

Calculez et visualisez en 3D la trajectoire optimale d'un avion vers le FAF (Final Approach Fix) :

- **Physique réaliste** : contraintes de pente, rayon de virage, vitesse
- **Évitement d'obstacles** : zones cylindriques interdites 
- **Types d'avions** : léger, commercial, cargo
- **Modes de vol** : approche directe ou interception d'axe
- **Simulations multiples** : 1 à 50 trajectoires aléatoires
- **Système de sécurité** : refus des trajectoires dangereuses

---

## 🚀 Installation Alternative

### Code Source (Développeurs)

```powershell
git clone https://github.com/ThomasPontier/Trajectoire_Avion_V2.git
cd Trajectoire_Avion_V2
pip install -r requirements.txt
python main.py
```

---

## ✨ Interface

### 4 Onglets Principaux

**🌍 Configuration**
- Environnement (dimensions, aéroport, FAF)
- Obstacles cylindriques 
- Types d'avions (léger/commercial/cargo)
- Simulations multiples (1-50 trajectoires)

**📦 Vue 3D**
- Visualisation interactive
- Navigation : rotation, zoom, pan
- Trajectoire colorée par phase

**📐 Vues 2D**
- Plans XY, XZ, YZ
- Projections orthogonales

**📊 Paramètres**
- Graphiques altitude/vitesse/pente
- Analyse temporelle

---

## 🎮 Utilisation

1. **Lancer** l'application
2. **Configurer** l'environnement et l'avion
3. **Calculer** une trajectoire ou plusieurs simulations
4. **Visualiser** en 3D et analyser les résultats

### Types d'Avions

| Type | Vitesse | Pente Max | Rayon Min |
|------|---------|-----------|-----------|
| 🛩️ Léger | 180 km/h | ±15°/-10° | 0.4 km |
| ✈️ Commercial | 250 km/h | ±10°/-6° | 0.8 km |
| 🛫 Cargo | 220 km/h | ±8°/-5° | 1.0 km |

---

## 🔨 Build Exécutable

```powershell
python build_exe.py
```

Génère `SimulateurTrajectoireAvion.exe` (~150 MB) standalone.

---

## ⚙️ Configuration

Fichier `config.json` auto-sauvegardé :
- Dimensions environnement
- Positions aéroport/FAF
- Obstacles
- Paramètres avion

---


**GitHub** : [Trajectoire_Avion_V2](https://github.com/ThomasPontier/Trajectoire_Avion_V2)
