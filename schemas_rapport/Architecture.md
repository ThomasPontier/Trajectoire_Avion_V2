# ARCHITECTURE SYSTÈME - SIMULATEUR TRAJECTOIRE AVION P21

## 1. Vue d'ensemble - Architecture globale

```mermaid
graph LR
    USER[Utilisateur]
    
    subgraph "Simulateur Trajectoire Avion"
        GUI[Interface GUI<br/>FlightSimulatorGUI]
        CALC[Calcul Trajectoire<br/>TrajectoryCalculator]
        ENV[Environnement<br/>Environment]
        AIRCRAFT[Avion<br/>Aircraft]
    end
    
    CONFIG[Fichiers Config<br/>JSON]
    
    USER -->|Interactions| GUI
    GUI -->|Demande calcul| CALC
    GUI -->|Configure| ENV
    GUI -->|Configure| AIRCRAFT
    GUI <-->|Sauvegarde/Charge| CONFIG
    
    CALC -->|Lit| ENV
    CALC -->|Lit| AIRCRAFT
    GUI -->|Affiche résultats| USER
    
    classDef user fill:#e1f5e1,stroke:#4caf50,stroke-width:2px
    classDef module fill:#bbdefb,stroke:#2196f3,stroke-width:2px
    classDef data fill:#fff9c4,stroke:#fbc02d,stroke-width:2px
    
    class USER user
    class GUI,CALC,ENV,AIRCRAFT module
    class CONFIG data
```

**Description** : L'utilisateur interagit avec l'interface GUI qui orchestre l'ensemble du système. Le GUI configure l'environnement et l'avion, puis demande au calculateur de trajectoire de générer le parcours optimal.

---

## 2. Module GUI - Interface utilisateur

```mermaid
graph TB
    USER[Utilisateur]
    
    subgraph "FlightSimulatorGUI main.py"
        WINDOW[Fenêtre Tkinter<br/>Racine application]
        
        subgraph "Panneau Gauche"
            CTRL_AIRCRAFT[Paramètres Avion<br/>Type/Position/Vitesse]
            CTRL_ENV[Paramètres Environnement<br/>Aéroport/FAF/Obstacles]
            CTRL_TRAJ[Mode Trajectoire<br/>Direct/Align/Avoid/Vertical]
            BTN_CALC[Bouton<br/>Calculer Trajectoire]
            BTN_CONFIG[Boutons<br/>Save/Load Config]
        end
        
        subgraph "Panneau Droit"
            VIZ_3D[Visualisation 3D<br/>Matplotlib Canvas]
            PARAMS[Affichage Paramètres<br/>Altitude/Pente/Temps]
        end
    end
    
    USER -->|Saisie paramètres| CTRL_AIRCRAFT
    USER -->|Saisie paramètres| CTRL_ENV
    USER -->|Sélectionne mode| CTRL_TRAJ
    USER -->|Clique| BTN_CALC
    USER -->|Clique| BTN_CONFIG
    
    BTN_CALC -->|Déclenche| CALCUL[Calcul Trajectoire]
    BTN_CONFIG -->|Sauvegarde/Charge| JSON[Fichier JSON]
    
    CALCUL -->|Résultat| VIZ_3D
    CALCUL -->|Résultat| PARAMS
    
    classDef user fill:#e1f5e1,stroke:#4caf50,stroke-width:2px
    classDef gui fill:#bbdefb,stroke:#2196f3,stroke-width:2px
    classDef action fill:#f8bbd0,stroke:#e91e63,stroke-width:2px
    
    class USER user
    class WINDOW,CTRL_AIRCRAFT,CTRL_ENV,CTRL_TRAJ,VIZ_3D,PARAMS gui
    class BTN_CALC,BTN_CONFIG,CALCUL,JSON action
```

**Composants clés** :
- **Panneau Gauche** : Tous les contrôles de saisie des paramètres
- **Panneau Droit** : Visualisation 3D et affichage des résultats
- **Boutons d'action** : Calcul de trajectoire et gestion de configuration

---

## 3. Flux de données - Communication entre modules

```mermaid
sequenceDiagram
    participant U as Utilisateur
    participant G as GUI
    participant E as Environment
    participant A as Aircraft
    participant T as TrajectoryCalculator
    
    U->>G: Configure paramètres avion
    G->>A: Crée/Met à jour Aircraft
    
    U->>G: Configure environnement
    G->>E: Crée/Met à jour Environment
    
    U->>G: Clique "Calculer"
    G->>T: calculate_trajectory(aircraft, environment)
    
    T->>E: Lit positions (aéroport, FAF, obstacles)
    T->>A: Lit spécifications (vitesse, pentes, rayon)
    
    T->>T: Calcul trajectoire horizontale
    T->>T: Application profil vertical
    T->>T: Calcul paramètres (temps, distance, pente)
    
    T-->>G: Retourne (points_3D, params)
    
    G->>G: Affiche trajectoire 3D
    G->>G: Affiche paramètres calculés
    G-->>U: Visualisation résultats
    
    Note over U,T: Cycle de simulation complet
```

**Flux séquentiel** :
1. Configuration initiale par l'utilisateur
2. Création des objets `Aircraft` et `Environment`
3. Déclenchement du calcul
4. Lecture des données par le calculateur
5. Calcul de la trajectoire
6. Retour et affichage des résultats

---

## Légende générale

- **Vert** : Points d'entrée/sortie (utilisateur, résultats)
- **Bleu** : Modules et processus principaux
- **Jaune** : Décisions et données de configuration
- **Rose** : Calculs et opérations critiques

## Description des modules

### Environment
Représente l'espace aérien avec :
- Dimensions de l'espace (size_x, size_y, size_z)
- Position aéroport et FAF
- Liste des obstacles cylindriques

### Aircraft
Modèle de l'avion avec :
- 3 types : Light, Commercial, Cargo
- Spécifications aérodynamiques (pentes max, vitesses, inclinaison)
- État dynamique (position, vitesse, cap)

### TrajectoryCalculator
Cœur du calcul de trajectoire :
- 4 types de trajectoires selon configuration
- Gestion altitude en 3 phases
- Évitement automatique d'obstacles

### GUI
Interface utilisateur complète :
- Configuration interactive des paramètres
- Visualisation 3D temps réel
- Sauvegarde/Chargement configuration
