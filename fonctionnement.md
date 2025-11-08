# Fonctionnement du Simulateur de Trajectoire d'Avion

## 📋 Vue d'ensemble du projet

Ce simulateur calcule et visualise les trajectoires optimales d'un avion pour atteindre le point FAF (Final Approach Fix) d'un aéroport. Le système prend en compte les contraintes aéronautiques réelles et permet l'évitement d'obstacles.

### 🎯 Objectif principal
Déterminer la **trajectoire optimale** permettant à un avion de rejoindre le point FAF en respectant :
- Les contraintes de pente maximale selon le type d'avion
- L'alignement avec l'axe de piste pour l'approche finale
- L'évitement des obstacles (cylindres)
- Les limitations de vitesse et de manœuvrabilité

---

## 🏗️ Architecture du système

### 📁 Structure des modules

#### 1. **`aircraft.py`** - Modélisation de l'avion
- **Classe `AircraftType`** : Définit les spécifications des différents types d'avions
- **Classe `Aircraft`** : Représente un avion avec ses paramètres de vol

#### 2. **`environment.py`** - Environnement aérien
- **Classe `Environment`** : Définit l'espace aérien, l'aéroport et le point FAF

#### 3. **`trajectory_calculator.py`** - Calcul des trajectoires
- **Classe `TrajectoryCalculator`** : Contient tous les algorithmes de calcul de trajectoires

#### 4. **`main.py`** - Interface utilisateur
- **Classe `FlightSimulatorGUI`** : Interface graphique principale avec visualisation 3D

---

## ✈️ Modélisation de l'avion (`aircraft.py`)

### 🏷️ Types d'avions disponibles

Le système supporte trois types d'avions avec des caractéristiques distinctes :

```python
SPECIFICATIONS = {
    "light": {           # Avion léger
        "max_climb_slope": 15.0,      # Montée maximale : 15°
        "max_descent_slope": -10.0,   # Descente maximale : -10°
        "max_bank_angle": 30.0,       # Inclinaison max : 30°
        "typical_speed": 180,         # Vitesse croisière : 180 km/h
        "faf_speed": 140,            # Vitesse cible au FAF : 140 km/h
    },
    "commercial": {      # Avion de ligne
        "max_climb_slope": 10.0,      # Montée maximale : 10°
        "max_descent_slope": -6.0,    # Descente maximale : -6°
        "max_bank_angle": 25.0,       # Inclinaison max : 25°
        "typical_speed": 250,         # Vitesse croisière : 250 km/h
        "faf_speed": 200,            # Vitesse cible au FAF : 200 km/h
    },
    "cargo": {           # Avion cargo
        "max_climb_slope": 8.0,       # Montée maximale : 8°
        "max_descent_slope": -5.0,    # Descente maximale : -5°
        "max_bank_angle": 20.0,       # Inclinaison max : 20°
        "typical_speed": 220,         # Vitesse croisière : 220 km/h
        "faf_speed": 180,            # Vitesse cible au FAF : 180 km/h
    }
}
```

### 🔢 Calculs physiques de l'avion

#### **Calcul du rayon de virage minimum**
```python
def calculate_min_turn_radius(self, speed=None):
    v_ms = speed / 3.6  # Conversion km/h → m/s
    g = 9.81           # Gravité terrestre
    bank_angle_rad = np.radians(self.max_bank_angle)
    radius_m = (v_ms ** 2) / (g * np.tan(bank_angle_rad))
    return radius_m / 1000.0  # Retour en km
```

**Formule physique utilisée :**
$$R_{min} = \frac{v^2}{g \times \tan(\phi_{max})}$$

Où :
- $R_{min}$ = rayon minimal de virage (m)
- $v$ = vitesse de l'avion (m/s)
- $g$ = accélération gravitationnelle (9.81 m/s²)
- $\phi_{max}$ = angle d'inclinaison maximal (radians)

#### **Vecteur vitesse**
```python
def get_velocity_vector(self):
    heading_rad = np.radians(self.heading)
    vx = self.speed * np.sin(heading_rad)  # Composante Est
    vy = self.speed * np.cos(heading_rad)  # Composante Nord
    vz = 0.0  # Composante verticale (calculée séparément)
    return np.array([vx, vy, vz])
```

---

## 🌍 Environnement aérien (`environment.py`)

### 📍 Points de navigation

#### **Position de l'aéroport**
```python
self.airport_position = np.array([size_x * 0.9, size_y * 0.9, 0.0])
```
- Placé dans le coin opposé de l'espace aérien
- Altitude : 0 km (niveau de la mer)

#### **Position du FAF (Final Approach Fix)**
```python
approach_distance = 5.0  # km avant l'aéroport
approach_altitude = 0.5  # km
direction = np.array([-1, -1, 0])  # Direction sud-ouest
direction = direction / np.linalg.norm(direction)

self.faf_position = np.array([
    self.airport_position[0] - approach_distance * direction[0],
    self.airport_position[1] - approach_distance * direction[1],
    approach_altitude
])
```

#### **Axe d'approche**
```python
def get_approach_axis(self):
    axis = self.airport_position - self.faf_position
    return axis / np.linalg.norm(axis)
```

L'axe d'approche est le vecteur normalisé qui va du FAF vers l'aéroport. C'est la direction que l'avion doit suivre lors de l'approche finale.

---

## 🧮 Calcul des trajectoires (`trajectory_calculator.py`)

### 🚀 Méthodes principales de calcul

Le système propose **quatre stratégies** différentes pour calculer les trajectoires :

#### 1. **Trajectoire avec alignement sur axe piste** (`calculate_trajectory`)
#### 2. **Trajectoire avec virages réalistes** (`calculate_trajectory_with_turn`)
#### 3. **Trajectoire avec virages automatiques** (`calculate_trajectory_with_automatic_turns`)
#### 4. **Trajectoire simple** (`_calculate_simple_trajectory`)

---

### 🎯 **Méthode 1 : Trajectoire avec alignement sur axe piste**

Cette méthode est la **stratégie principale** utilisée par défaut.

#### **Principe de fonctionnement :**

1. **Analyse de la situation initiale**
   - Position actuelle de l'avion
   - Cap actuel
   - Position du FAF et de l'aéroport
   - Calcul de l'axe d'approche (FAF → Aéroport)

2. **Calcul de l'angle d'alignement**
```python
# Direction actuelle de l'avion
heading_rad = np.radians(aircraft.heading)
current_direction = np.array([np.sin(heading_rad), np.cos(heading_rad)])

# Axe de la piste (FAF vers aéroport)
runway_axis = airport_pos[:2] - faf_pos[:2]
runway_direction = runway_axis / np.linalg.norm(runway_axis)

# Angle entre le cap et l'axe
cos_angle = np.dot(current_direction, runway_direction)
angle_to_runway = np.degrees(np.arccos(np.clip(cos_angle, -1.0, 1.0)))
```

3. **Calcul du point d'interception optimal**
```python
def _calculate_runway_intercept_point(self, start_pos, current_dir, airport_pos, 
                                      faf_pos, runway_dir, angle_to_runway):
    # Projection orthogonale sur l'axe
    vec_to_aircraft = start_pos - airport_pos
    projection_dist = np.dot(vec_to_aircraft, runway_dir)
    closest_point = airport_pos + projection_dist * runway_dir
    
    # Distance nécessaire pour l'alignement
    perp_distance = np.linalg.norm(start_pos - closest_point)
    alignment_distance = max(perp_distance * 2, angle_to_runway * 0.1, 3.0)
```

4. **Construction de la trajectoire en 2 phases**
   - **Phase 1** : Vol initial dans le cap actuel (15-25% de la distance)
   - **Phase 2** : Virage progressif jusqu'au FAF avec alignement parfait

#### **Gestion de l'altitude avec contrainte de pente**

Le système respecte la **pente maximale de descente** selon le type d'avion :

```python
# Pente maximale (négative pour descente)
max_descent_slope_rad = np.radians(aircraft.max_descent_slope)

# Distance minimale pour descendre
min_descent_distance = abs(altitude_diff / np.tan(abs(max_descent_slope_rad)))

# Distance de transition (50% de la descente, entre 3-12 km)
transition_distance = max(min(min_descent_distance * 0.50, 12.0), 3.0)
```

**Formule de la pente :**
$$d_{min} = \frac{|\Delta h|}{|\tan(\theta_{max})|}$$

Où :
- $d_{min}$ = distance minimale de descente (km)
- $\Delta h$ = différence d'altitude (km)
- $\theta_{max}$ = pente maximale de descente (radians)

#### **Profil d'altitude en 3 phases :**

1. **Vol en palier** : Altitude constante
2. **Transition progressive** : Courbe lisse (fonction cosinus)
3. **Descente à pente maximale** : Jusqu'au FAF

```python
# Transition smooth avec fonction cosinus
smooth_factor = (1 - np.cos(t * np.pi)) / 2
altitude = altitude_start - altitude_diff * smooth_factor
```

---

### 🌪️ **Méthode 2 : Trajectoire avec virages réalistes**

Cette méthode calcule des **virages physiquement réalistes** basés sur le rayon de virage minimum.

#### **Étapes du calcul :**

1. **Calcul du rayon de virage minimum**
```python
turn_radius = aircraft.calculate_min_turn_radius()
```

2. **Détermination du point d'interception tangent**
```python
def _calculate_tangent_intercept(self, start_pos, current_dir, approach_dir, 
                                turn_radius, faf_pos):
    # Calcul géométrique du point de tangence
    # pour rejoindre l'axe d'approche avec un arc de cercle
```

3. **Construction de l'arc de virage**
   - Centre du cercle de virage
   - Angles de début et fin
   - Points de l'arc calculés trigonométriquement

4. **Suivi de l'axe d'approche**
   - Vol rectiligne le long de l'axe
   - Descente progressive jusqu'au FAF

#### **Calcul géométrique du virage :**

```python
# Vecteur perpendiculaire pour le centre du virage
perp_vector = np.array([-current_dir[1], current_dir[0]])
if turn_direction == "right":
    perp_vector = -perp_vector

# Centre du cercle de virage
turn_center = start_pos[:2] + perp_vector * turn_radius

# Points de l'arc calculés par trigonométrie
for i in range(n_turn):
    angle = start_angle + i * angle_step
    x = turn_center[0] + turn_radius * np.cos(angle)
    y = turn_center[1] + turn_radius * np.sin(angle)
```

---

### 🔄 **Méthode 3 : Trajectoire avec virages automatiques**

Cette méthode gère automatiquement les situations où l'avion a **trop d'altitude** et doit effectuer des **spirales descendantes**.

#### **Logique de décision :**

```python
# Vérification si descente directe possible
required_slope = np.degrees(np.arctan(altitude_diff / horizontal_distance))
if abs(required_slope) > abs(aircraft.max_descent_slope):
    # TROP RAIDE → Calcul de spirales
    excess_altitude = altitude_diff - max_descent_distance * np.tan(max_slope_rad)
    return self._calculate_altitude_reduction_turns(
        aircraft, start_pos, faf_pos, excess_altitude, cylinders
    )
```

#### **Calcul des spirales descendantes :**

1. **Estimation du nombre de tours nécessaires**
```python
# Altitude perdue par tour (descente en spirale)
altitude_per_turn = 2 * np.pi * turn_radius * np.tan(abs(max_slope_rad))
num_turns = excess_altitude / altitude_per_turn
```

2. **Construction de la spirale**
```python
for turn in range(int(num_turns)):
    # Chaque tour = cercle complet avec descente progressive
    for i in range(points_per_turn):
        angle = i * angle_step + turn * 2 * np.pi
        
        # Position horizontale (cercle)
        x = spiral_center[0] + turn_radius * np.cos(angle)
        y = spiral_center[1] + turn_radius * np.sin(angle)
        
        # Position verticale (descente progressive)
        z = current_altitude - (excess_altitude * progress)
```

---

### 🛡️ **Évitement d'obstacles**

Le système peut **éviter automatiquement** les obstacles cylindriques.

#### **Détection de collision :**
```python
def _check_cylinder_collision(self, start_pos, end_pos, cylinder):
    # Distance du segment à l'axe du cylindre
    # Vérification 2D (plan horizontal) puis 3D (altitude)
```

#### **Calcul de points d'évitement :**
```python
def _calculate_avoidance_point(self, start_pos, target_pos, cylinder, safety_margin=0.5):
    # Calcul du vecteur perpendiculaire pour contourner l'obstacle
    # Ajout d'une marge de sécurité
```

#### **Stratégie d'évitement :**
1. **Détection** des collisions sur la trajectoire directe
2. **Calcul** de points de contournement avec marge de sécurité
3. **Construction** d'une trajectoire par segments évitant tous les obstacles
4. **Optimisation** pour minimiser la distance totale

---

## 📊 **Calcul des paramètres de vol**

### ⏱️ **Profil temporel**

```python
def _calculate_parameters(self, trajectory, speed):
    # Calcul des distances entre points consécutifs
    distances = np.linalg.norm(np.diff(trajectory, axis=0), axis=1)
    
    # Temps cumulé (vitesse constante)
    times = np.cumsum(distances) / speed * 3600  # secondes
    
    # Vitesses instantanées
    velocities = np.full(len(trajectory), speed)
    
    # Caps instantanés
    headings = []
    for i in range(len(trajectory) - 1):
        delta = trajectory[i+1] - trajectory[i]
        heading = np.degrees(np.arctan2(delta[0], delta[1]))
        headings.append(heading)
```

### 📈 **Profil de vitesse variable**

Pour des trajectoires plus réalistes, le système peut calculer un **profil de vitesse variable** :

```python
def calculate_speed_profile(self, trajectory_points, target_faf_speed=None):
    # Vitesse initiale → vitesse de croisière → vitesse au FAF
    
    # Phase d'accélération (20% du trajet)
    acceleration_points = int(trajectory_points * 0.2)
    
    # Phase de croisière (60% du trajet)  
    cruise_points = int(trajectory_points * 0.6)
    
    # Phase de décélération (20% du trajet)
    deceleration_points = trajectory_points - acceleration_points - cruise_points
```

---

## 🎮 **Interface utilisateur et visualisation**

### 📋 **Paramètres configurables**

L'interface permet de configurer :
- **Type d'avion** (léger, commercial, cargo)
- **Position initiale** (x, y, z)
- **Vitesse** et **cap initial**
- **Obstacles cylindriques** (position, rayon, hauteur)
- **Mode de calcul** (virages simplifiés ou réalistes)

### 📊 **Visualisation 3D**

La trajectoire est affichée en 3D avec :
- **Trajectoire principale** (ligne colorée)
- **Position initiale** (point vert)
- **FAF** (point rouge)
- **Aéroport** (triangle bleu)
- **Obstacles** (cylindres semi-transparents)
- **Projections** sur les plans (optionnel)

### 📈 **Graphiques des paramètres**

Affichage temporel de :
- **Altitude** vs temps
- **Vitesse** vs temps  
- **Cap** vs temps
- **Distance au FAF** vs temps

---

## 🔄 **Simulations multiples**

Le système peut générer **plusieurs trajectoires** avec des paramètres aléatoires pour analyser la robustesse :

```python
# Génération de positions aléatoires
for i in range(num_trajectories):
    # Variation aléatoire de la position (+/- 15%)
    random_x = base_x + np.random.uniform(-variation, variation)
    random_y = base_y + np.random.uniform(-variation, variation)
    
    # Calcul de trajectoire pour cette position
    trajectory, params = calculator.calculate_trajectory(aircraft, cylinders)
```

---

## 🎯 **Algorithmes d'optimisation**

### 🔍 **Critères d'optimisation**

Le système optimise la trajectoire selon plusieurs critères :

1. **Distance minimale** : Trajectoire la plus courte
2. **Respect des contraintes** : Pentes, vitesses, rayons de virage
3. **Sécurité** : Évitement d'obstacles avec marges
4. **Confort** : Transitions progressives, virages doux
5. **Réalisme aéronautique** : Procédures d'approche standard

### ⚖️ **Compromis et arbitrages**

Quand plusieurs contraintes sont en conflit :
- **Priorité 1** : Sécurité (évitement d'obstacles)
- **Priorité 2** : Contraintes physiques (pentes maximales)
- **Priorité 3** : Optimisation de la distance
- **Priorité 4** : Confort du vol (transitions douces)

---

## 🛠️ **Configuration et sauvegarde**

### 💾 **Fichier de configuration**

Le système sauvegarde automatiquement la configuration dans `config.json` :

```json
{
    "environment": {
        "size_x": 100.0,
        "size_y": 100.0, 
        "size_z": 10.0,
        "airport": {"x": 5.0, "y": 25.0, "z": 0.0},
        "faf": {"x": 20.0, "y": 25.0, "z": 1.0}
    },
    "cylinders": [
        {"x": 50.0, "y": 50.0, "radius": 2.0, "height": 3.0}
    ],
    "aircraft": {
        "type": "commercial",
        "position": {"x": 70.0, "y": 70.0, "z": 3.0},
        "speed": 250.0,
        "heading": 180.0
    }
}
```

### 🔄 **Persistance des données**

- Configuration automatiquement sauvegardée à la fermeture
- Rechargement automatique au démarrage
- Valeurs par défaut si pas de fichier de configuration

---

## 📝 **Conclusion**

Ce simulateur implémente des algorithmes sophistiqués pour calculer des trajectoires aériennes réalistes. Il combine :

- **Modélisation physique** précise des aéronefs
- **Algorithmes géométriques** pour les trajectoires optimales  
- **Contraintes aéronautiques** réelles (pentes, vitesses, virages)
- **Évitement d'obstacles** automatique
- **Interface intuitive** avec visualisation 3D

Le système est extensible et permet l'ajout facile de nouveaux types d'avions, contraintes ou algorithmes d'optimisation.