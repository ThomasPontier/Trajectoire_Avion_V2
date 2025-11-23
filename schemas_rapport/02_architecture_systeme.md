# ARCHITECTURE SYSTÈME - SIMULATEUR TRAJECTOIRE AVION P21

```mermaid
graph TB
    subgraph "NIVEAU 0 - Système Global"
        SYS[Simulateur Trajectoire Avion P21<br/>Interface + Calcul + Visualisation]
    end
    
    subgraph "NIVEAU 1 - Modules Principaux"
        GUI[FlightSimulatorGUI<br/>Interface Tkinter]
        ENV[Environment<br/>Espace aérien]
        AIRCRAFT[Aircraft<br/>Modèle avion]
        TRAJ[TrajectoryCalculator<br/>Calcul trajectoire]
    end
    
    subgraph "NIVEAU 2 - Composants GUI"
        GUI_CTRL[Panneau Contrôle<br/>Paramètres simulation]
        GUI_VIZ[Visualisation 3D<br/>Matplotlib]
        GUI_PARAMS[Affichage Paramètres<br/>Altitude/Pente/Vitesse]
        GUI_CONFIG[Gestion Config<br/>Sauvegarde/Chargement JSON]
    end
    
    subgraph "NIVEAU 2 - Composants Environment"
        ENV_SPACE[Espace Aérien<br/>Dimensions XYZ]
        ENV_AIRPORT[Position Aéroport<br/>Point d'atterrissage]
        ENV_FAF[Point FAF<br/>Final Approach Fix]
        ENV_OBS[Obstacles<br/>Cylindres]
    end
    
    subgraph "NIVEAU 2 - Composants Aircraft"
        AC_TYPE[Type Avion<br/>Light/Commercial/Cargo]
        AC_POS[État Dynamique<br/>Position/Vitesse/Cap]
        AC_SPECS[Spécifications<br/>Pentes/Vitesses/Inclinaison]
        AC_CALC[Calculs Aérodynamiques<br/>Rayon virage min]
    end
    
    subgraph "NIVEAU 2 - Composants TrajectoryCalculator"
        TRAJ_MAIN[calculate_trajectory()<br/>Point d'entrée principal]
        TRAJ_DIRECT[Trajectoire Directe<br/>Ligne droite]
        TRAJ_ALIGN[Trajectoire Alignement<br/>Bézier + Piste]
        TRAJ_AVOID[Évitement Obstacles<br/>Waypoints tangents]
        TRAJ_VERT[Descente Verticale<br/>Cas spécial]
        TRAJ_ALT[Gestion Altitude<br/>3 phases]
        TRAJ_PARAMS[Calcul Paramètres<br/>Temps/Pente/Virage]
    end
    
    %% Relations Niveau 0-1
    SYS --> GUI
    SYS --> ENV
    SYS --> AIRCRAFT
    SYS --> TRAJ
    
    %% Relations GUI
    GUI --> GUI_CTRL
    GUI --> GUI_VIZ
    GUI --> GUI_PARAMS
    GUI --> GUI_CONFIG
    
    GUI_CTRL -.->|configure| ENV
    GUI_CTRL -.->|configure| AIRCRAFT
    GUI_CTRL -->|demande calcul| TRAJ
    
    %% Relations Environment
    ENV --> ENV_SPACE
    ENV --> ENV_AIRPORT
    ENV --> ENV_FAF
    ENV --> ENV_OBS
    
    %% Relations Aircraft
    AIRCRAFT --> AC_TYPE
    AIRCRAFT --> AC_POS
    AIRCRAFT --> AC_SPECS
    AIRCRAFT --> AC_CALC
    
    %% Relations TrajectoryCalculator
    TRAJ --> TRAJ_MAIN
    TRAJ_MAIN --> TRAJ_DIRECT
    TRAJ_MAIN --> TRAJ_ALIGN
    TRAJ_MAIN --> TRAJ_AVOID
    TRAJ_MAIN --> TRAJ_VERT
    TRAJ_ALIGN --> TRAJ_ALT
    TRAJ_AVOID --> TRAJ_ALT
    TRAJ_MAIN --> TRAJ_PARAMS
    
    %% Relations transverses
    TRAJ -.->|utilise| ENV
    TRAJ -.->|utilise| AIRCRAFT
    GUI_VIZ -.->|affiche| ENV
    GUI_VIZ -.->|affiche| AIRCRAFT
    GUI_VIZ -.->|affiche| TRAJ
    
    %% Styles
    classDef niveau0 fill:#e1f5e1,stroke:#4caf50,stroke-width:3px
    classDef niveau1 fill:#bbdefb,stroke:#2196f3,stroke-width:2px
    classDef niveau2 fill:#fff9c4,stroke:#fbc02d,stroke-width:1px
    classDef calcul fill:#f8bbd0,stroke:#e91e63,stroke-width:2px
    
    class SYS niveau0
    class GUI,ENV,AIRCRAFT,TRAJ niveau1
    class GUI_CTRL,GUI_VIZ,GUI_PARAMS,GUI_CONFIG,ENV_SPACE,ENV_AIRPORT,ENV_FAF,ENV_OBS,AC_TYPE,AC_POS,AC_SPECS,AC_CALC niveau2
    class TRAJ_MAIN,TRAJ_DIRECT,TRAJ_ALIGN,TRAJ_AVOID,TRAJ_VERT,TRAJ_ALT,TRAJ_PARAMS calcul
```

## Légende

- **Niveau 0** (Vert) : Système global
- **Niveau 1** (Bleu) : Modules principaux indépendants
- **Niveau 2** (Jaune) : Composants et sous-fonctions
- **Calcul** (Rose) : Fonctions de calcul de trajectoire
- **Flèches pleines** : Décomposition hiérarchique
- **Flèches pointillées** : Utilisation/Dépendance

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
