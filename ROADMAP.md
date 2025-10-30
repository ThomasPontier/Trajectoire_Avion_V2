# Feuille de Route - Développement Itératif
## Simulateur de Trajectoire d'Avion - Projet P21

---

## ✅ Version 1.0 - BASE (ACTUELLE)

### Fonctionnalités Implémentées
- [x] Environnement 3D (cube 50x50x5 km)
- [x] Aéroport et point FAF positionnés
- [x] Interface utilisateur pour paramétrer l'avion
- [x] Visualisation 3D de l'espace aérien
- [x] Calcul de trajectoire simple (ligne droite)
- [x] Graphiques de paramètres :
  - Altitude au cours du temps
  - Pente au cours du temps
  - Vitesse au cours du temps

### Comment utiliser
1. Lancer : `python main.py` ou double-cliquer sur `lancer_simulateur.bat`
2. Paramétrer la position, altitude, vitesse, cap
3. Cliquer sur "Valider Position"
4. Cliquer sur "Lancer Simulation"
5. Observer la trajectoire 3D et les graphiques

---

## 🔄 Version 1.1 - CONTRAINTE DE PENTE MAXIMALE

### Objectif
Implémenter une contrainte de pente maximale en fonction du type d'avion.

### Modifications à apporter

#### 1. Fichier `aircraft.py`
```python
# Ajouter des types d'avions prédéfinis
class AircraftType:
    LIGHT = "light"          # Avion léger
    COMMERCIAL = "commercial" # Avion de ligne
    CARGO = "cargo"          # Avion cargo
    
    SPECIFICATIONS = {
        "light": {
            "max_climb_slope": 15.0,    # degrés
            "max_descent_slope": -10.0,  # degrés
            "typical_speed": 180,        # km/h
        },
        "commercial": {
            "max_climb_slope": 10.0,
            "max_descent_slope": -6.0,
            "typical_speed": 250,
        },
        "cargo": {
            "max_climb_slope": 8.0,
            "max_descent_slope": -5.0,
            "typical_speed": 220,
        }
    }

# Modifier la classe Aircraft
class Aircraft:
    def __init__(self, position, speed, heading=0.0, aircraft_type="commercial"):
        self.aircraft_type = aircraft_type
        self.specs = AircraftType.SPECIFICATIONS[aircraft_type]
        self.max_climb_slope = self.specs["max_climb_slope"]
        self.max_descent_slope = self.specs["max_descent_slope"]
```

#### 2. Fichier `trajectory_calculator.py`
```python
def calculate_trajectory_with_slope_constraint(self, aircraft):
    """
    Calcule la trajectoire en respectant les contraintes de pente
    
    Algorithme:
    1. Calculer la trajectoire directe idéale
    2. Vérifier les pentes à chaque segment
    3. Si pente > max : ajuster en ajoutant des paliers
    4. Recalculer la trajectoire optimisée
    """
    # À implémenter
```

#### 3. Fichier `main.py`
```python
# Ajouter un menu déroulant pour le type d'avion
ttk.Label(control_frame, text="Type d'avion:").grid(...)
self.aircraft_type_var = tk.StringVar(value="commercial")
aircraft_combo = ttk.Combobox(control_frame, 
                              textvariable=self.aircraft_type_var,
                              values=["light", "commercial", "cargo"])
aircraft_combo.grid(...)

# Afficher les contraintes actuelles
ttk.Label(control_frame, text="Pente max montée: X°").grid(...)
ttk.Label(control_frame, text="Pente max descente: X°").grid(...)
```

### Tests à effectuer
- [ ] Trajectoire avec pente forte → doit ajuster automatiquement
- [ ] Avion léger vs cargo → pentes différentes
- [ ] Graphique de pente → rester dans les limites

---

## 🔄 Version 1.2 - RAYON DE VIRAGE MINIMAL

### Objectif
Implémenter un rayon de virage minimal basé sur le type d'avion et la vitesse.

### Concepts à implémenter

#### Physique du virage
```
Rayon de virage = V² / (g × tan(angle_inclinaison))

Où:
- V = vitesse (m/s)
- g = 9.81 m/s²
- angle_inclinaison = typiquement 25° pour avion commercial
```

#### Modifications à apporter

##### 1. Fichier `aircraft.py`
```python
SPECIFICATIONS = {
    "commercial": {
        # ... existing specs ...
        "max_bank_angle": 25.0,  # degrés d'inclinaison max
        "typical_turn_rate": 3.0, # degrés par seconde
    }
}

class Aircraft:
    def calculate_min_turn_radius(self):
        """Calcule le rayon de virage minimal basé sur la vitesse"""
        v_ms = self.speed / 3.6  # Conversion km/h → m/s
        g = 9.81
        bank_angle_rad = np.radians(self.specs["max_bank_angle"])
        radius_m = (v_ms ** 2) / (g * np.tan(bank_angle_rad))
        return radius_m / 1000.0  # Retour en km
```

##### 2. Fichier `trajectory_calculator.py`
```python
def calculate_trajectory_with_turns(self, aircraft):
    """
    Calcule une trajectoire avec virages réalistes
    
    Algorithme:
    1. Calculer la direction vers le FAF
    2. Si changement de cap > seuil :
       - Calculer un arc de cercle avec rayon minimal
       - Insérer des waypoints sur l'arc
    3. Connecter les segments avec des virages lisses
    4. Vérifier que tous les rayons ≥ rayon minimal
    """
```

##### 3. Visualisation améliorée
```python
# Dans main.py
# Afficher le rayon de virage actuel
# Dessiner l'arc de virage prévu en pointillés
# Colorer la trajectoire selon l'intensité du virage
```

### Tests à effectuer
- [ ] Cap initial opposé au FAF → virage nécessaire
- [ ] Haute vitesse → rayon de virage plus grand
- [ ] Visualisation des arcs de virage

---

## 🚀 Version 2.0 - OPTIMISATION AVANCÉE

### Fonctionnalités futures
- **Multi-critères d'optimisation**
  - Temps de vol minimal
  - Consommation de carburant
  - Confort passagers (accélérations limitées)
  
- **Zones d'exclusion**
  - Zones interdites de vol
  - Obstacles à éviter
  - Couloirs aériens obligatoires

- **Conditions météorologiques**
  - Vent (vitesse et direction)
  - Turbulences
  - Adaptation de la trajectoire

- **Procédures d'approche réelles**
  - STAR (Standard Terminal Arrival Route)
  - Patterns d'attente
  - Go-around procedures

---

## 📊 Métriques de Performance

### À implémenter
- Temps de vol total
- Distance parcourue
- Consommation carburant estimée
- Nombre de virages
- Pente moyenne/maximale
- Confort (g-forces)

### Tableau de bord
Créer un panel récapitulatif avec toutes les métriques après simulation.

---

## 🧪 Tests et Validation

### Scénarios de test
1. **Scénario 1**: Avion proche du FAF, altitude correcte
   - Trajectoire attendue : quasi-directe
   
2. **Scénario 2**: Avion loin du FAF, altitude trop haute
   - Trajectoire attendue : approche avec descente progressive
   
3. **Scénario 3**: Avion mal orienté
   - Trajectoire attendue : virage puis approche
   
4. **Scénario 4**: Avion à très basse altitude
   - Trajectoire attendue : montée puis descente vers FAF

### Validation
- Vérifier que toutes les contraintes sont respectées
- Comparer avec des procédures aériennes réelles
- Validation par un expert en navigation aérienne

---

## 📝 Notes de Développement

### Structure du code
Le projet est modulaire :
- `environment.py` : Gère l'espace aérien
- `aircraft.py` : Représente l'avion et ses caractéristiques
- `trajectory_calculator.py` : Logique de calcul de trajectoire
- `main.py` : Interface utilisateur et orchestration

### Bonnes pratiques
- Commenter le code
- Ajouter des docstrings
- Tests unitaires pour chaque module
- Git pour le versionnement

### Ressources utiles
- Documentation OACI sur les procédures d'approche
- Physique du vol
- Algorithmes de pathfinding (A*, RRT)

---

## 🎯 Prochaine Étape Immédiate

**Pour passer à la v1.1**, commencer par :
1. Implémenter les types d'avions dans `aircraft.py`
2. Ajouter le sélecteur de type dans l'interface
3. Modifier le calculateur pour vérifier les pentes
4. Tester avec différents scénarios

**Temps estimé** : 2-3 heures de développement

---

## 💡 Améliorations UX futures

- Presets de positions de départ
- Sauvegarde/chargement de scénarios
- Export des données en CSV
- Animation de la trajectoire en temps réel
- Vue cockpit (première personne)
- Comparaison de plusieurs trajectoires

---

**Dernière mise à jour** : 30 octobre 2025
**Version actuelle** : 1.0
