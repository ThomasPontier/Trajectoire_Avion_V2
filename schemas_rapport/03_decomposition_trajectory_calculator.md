# DÉCOMPOSITION FONCTIONNELLE - TrajectoryCalculator

```mermaid
graph TB
    subgraph "NIVEAU 1 - Fonction Principale"
        CALC[calculate_trajectory<br/>aircraft, cylinders<br/>→ trajectory, parameters]
    end
    
    subgraph "NIVEAU 2 - Analyse Géométrique"
        ANALYZE[Analyse Configuration Initiale]
        DIST[Calcul Distances<br/>horizontal_distance<br/>runway_axis_distance]
        ANGLE[Calcul Angle<br/>angle_to_runway<br/>cos_angle]
        INTERCEPT[Calcul Point Interception<br/>_calculate_runway_intercept_point]
    end
    
    subgraph "NIVEAU 2 - Sélection Type Trajectoire"
        DECISION{Type de<br/>Trajectoire?}
        CASE_DIRECT[Cas: Distance minimale<br/>OU pas d'alignement requis]
        CASE_VERT[Cas: Distance horizontale ≈ 0<br/>Au-dessus du FAF]
        CASE_ALIGN[Cas: Alignement piste requis<br/>Avec/Sans obstacles]
    end
    
    subgraph "NIVEAU 3 - Trajectoire Directe"
        SIMPLE[_calculate_simple_trajectory]
        SIMPLE_LINE[Ligne droite]
        SIMPLE_POINTS[Génération points<br/>n = max500, 100/km]
        SIMPLE_PARAMS[Calcul paramètres<br/>_calculate_parameters]
    end
    
    subgraph "NIVEAU 3 - Trajectoire Verticale"
        VERT[_vertical_trajectory]
        VERT_SMOOTH[Fonction smooth<br/>ease-in-out: t²3-2t]
        VERT_POINTS[Génération points<br/>n = max300, Δz×200]
        VERT_PARAMS[Calcul paramètres<br/>vitesse = 10 km/h]
    end
    
    subgraph "NIVEAU 3 - Trajectoire Alignement"
        ALIGN[_build_trajectory_with_runway_alignment]
        
        subgraph "Phase A: Vol Initial"
            PHASE_A[Segment rectiligne<br/>20% distance totale<br/>dans cap actuel]
        end
        
        subgraph "Phase B: Détection Obstacles"
            DETECT[_calculate_avoidance_waypoints]
            CHECK_COLL[Vérification collision<br/>sur trajet direct]
            GEN_WP[Génération waypoints<br/>tangents au cylindre]
            WP_ENTRY[Waypoint entrée<br/>projection - approach_dist]
            WP_EXIT[Waypoint sortie<br/>projection + approach_dist]
        end
        
        subgraph "Phase C: Construction Segments"
            BUILD_SEG[Boucle sur waypoints]
            BEZIER[Courbe Bézier cubique<br/>entre chaque paire]
            BEZIER_P0[P0: waypoint début]
            BEZIER_P1[P1: direction entrée×0.35]
            BEZIER_P2[P2: direction sortie×0.35]
            BEZIER_P3[P3: waypoint fin]
        end
        
        subgraph "Phase D: Gestion Altitude"
            ALT_MANAGE[Gestion 3 phases altitude]
            ALT_LEVEL[Phase 1: Vol palier<br/>altitude constante]
            ALT_TRANS[Phase 2: Transition<br/>super-smoothstep 7°]
            ALT_DESC[Phase 3: Descente linéaire<br/>pente maximale]
        end
        
        ALIGN_PARAMS[Calcul paramètres finaux<br/>_calculate_parameters]
    end
    
    subgraph "NIVEAU 4 - Calcul Paramètres"
        PARAMS[_calculate_parameters<br/>trajectory, speed]
        PARAM_TIME[Temps cumulé<br/>dt = distance/vitesse]
        PARAM_ALT[Altitude à chaque point<br/>z_array]
        PARAM_SLOPE[Pente entre points<br/>arctan Δz/Δdist]
        PARAM_SPEED[Vitesse constante<br/>ou variable]
        PARAM_HEAD[Cap à chaque point<br/>arctan2 Δy/Δx]
        PARAM_TURN[Taux virage<br/>Δheading/Δtime]
    end
    
    subgraph "NIVEAU 4 - Vérification Collision"
        COLLISION[_check_trajectory_collision]
        COLL_LOOP[Boucle sur points]
        COLL_CHECK[_check_collision_with_cylinder<br/>distance_horiz ≤ rayon<br/>ET z ≤ hauteur]
        COLL_RESULT[Liste cylindres en collision<br/>+ index premier point]
    end
    
    %% Flux principal
    CALC --> ANALYZE
    ANALYZE --> DIST
    ANALYZE --> ANGLE
    ANALYZE --> INTERCEPT
    
    ANALYZE --> DECISION
    
    DECISION -->|Simple| CASE_DIRECT
    DECISION -->|Vertical| CASE_VERT
    DECISION -->|Complexe| CASE_ALIGN
    
    CASE_DIRECT --> SIMPLE
    SIMPLE --> SIMPLE_LINE
    SIMPLE_LINE --> SIMPLE_POINTS
    SIMPLE_POINTS --> SIMPLE_PARAMS
    
    CASE_VERT --> VERT
    VERT --> VERT_SMOOTH
    VERT_SMOOTH --> VERT_POINTS
    VERT_POINTS --> VERT_PARAMS
    
    CASE_ALIGN --> ALIGN
    ALIGN --> PHASE_A
    PHASE_A --> DETECT
    
    DETECT --> CHECK_COLL
    CHECK_COLL -->|Collision| GEN_WP
    GEN_WP --> WP_ENTRY
    GEN_WP --> WP_EXIT
    
    WP_ENTRY --> BUILD_SEG
    WP_EXIT --> BUILD_SEG
    CHECK_COLL -->|Pas collision| BUILD_SEG
    
    BUILD_SEG --> BEZIER
    BEZIER --> BEZIER_P0
    BEZIER --> BEZIER_P1
    BEZIER --> BEZIER_P2
    BEZIER --> BEZIER_P3
    
    BEZIER --> ALT_MANAGE
    ALT_MANAGE --> ALT_LEVEL
    ALT_MANAGE --> ALT_TRANS
    ALT_MANAGE --> ALT_DESC
    
    ALT_DESC --> ALIGN_PARAMS
    
    SIMPLE_PARAMS --> PARAMS
    VERT_PARAMS --> PARAMS
    ALIGN_PARAMS --> PARAMS
    
    PARAMS --> PARAM_TIME
    PARAMS --> PARAM_ALT
    PARAMS --> PARAM_SLOPE
    PARAMS --> PARAM_SPEED
    PARAMS --> PARAM_HEAD
    PARAMS --> PARAM_TURN
    
    ALIGN_PARAMS --> COLLISION
    COLLISION --> COLL_LOOP
    COLL_LOOP --> COLL_CHECK
    COLL_CHECK --> COLL_RESULT
    
    %% Styles
    classDef niveau1 fill:#e1f5e1,stroke:#4caf50,stroke-width:3px,font-size:14px
    classDef niveau2 fill:#bbdefb,stroke:#2196f3,stroke-width:2px
    classDef niveau3 fill:#fff9c4,stroke:#fbc02d,stroke-width:2px
    classDef niveau4 fill:#f8bbd0,stroke:#e91e63,stroke-width:1px
    classDef decision fill:#ffccbc,stroke:#ff5722,stroke-width:2px
    classDef phase fill:#e1bee7,stroke:#9c27b0,stroke-width:1px
    
    class CALC niveau1
    class ANALYZE,DIST,ANGLE,INTERCEPT,DECISION,CASE_DIRECT,CASE_VERT,CASE_ALIGN niveau2
    class SIMPLE,VERT,ALIGN,SIMPLE_LINE,SIMPLE_POINTS,SIMPLE_PARAMS,VERT_SMOOTH,VERT_POINTS,VERT_PARAMS niveau3
    class PHASE_A,DETECT,BUILD_SEG,BEZIER,ALT_MANAGE,ALIGN_PARAMS phase
    class PARAMS,COLLISION,PARAM_TIME,PARAM_ALT,PARAM_SLOPE,PARAM_SPEED,PARAM_HEAD,PARAM_TURN,COLL_LOOP,COLL_CHECK,COLL_RESULT,CHECK_COLL,GEN_WP,WP_ENTRY,WP_EXIT,BEZIER_P0,BEZIER_P1,BEZIER_P2,BEZIER_P3,ALT_LEVEL,ALT_TRANS,ALT_DESC niveau4
    class DECISION decision
```

## Détail des Niveaux de Décomposition

### NIVEAU 1 - Point d'Entrée
**`calculate_trajectory(aircraft, cylinders)`**
- Input: objet Aircraft, liste obstacles
- Output: numpy array trajectoire (N×3), dict paramètres
- Fonction principale appelée par l'interface

### NIVEAU 2 - Analyse et Décision
**Analyse géométrique:**
- Calcul distance horizontale avion → FAF
- Calcul angle entre cap actuel et axe piste
- Détermination point interception optimal sur axe piste

**Décision type trajectoire:**
- Simple: distance courte, pas d'alignement
- Verticale: position XY ≈ FAF (descente pure)
- Complexe: alignement piste + évitement obstacles

### NIVEAU 3 - Types de Trajectoires

#### Trajectoire Simple
- Ligne droite start → FAF
- Densité: 100 points/km minimum
- Descente linéaire si altitude différente

#### Trajectoire Verticale
- Cas spécial: avion au-dessus du FAF
- Fonction smooth ease-in-out pour descente douce
- Vitesse réduite: 10 km/h

#### Trajectoire Complexe
Décomposée en 4 phases séquentielles

### NIVEAU 4 - Sous-Fonctions Détaillées

#### Phase A: Vol Initial Rectiligne
- 20% de la distance totale
- Maintien du cap actuel
- Altitude constante

#### Phase B: Détection et Évitement
**Algorithme waypoints:**
1. Projection centre cylindre sur trajet
2. Si distance < rayon → génération waypoints
3. WP_entrée = projection - approach_distance
4. WP_sortie = projection + approach_distance
5. Décalage perpendiculaire = rayon + marge

#### Phase C: Construction Segments Bézier
**Pour chaque paire de waypoints:**
- P0: position départ segment
- P1: P0 + direction_entrée × 0.35 × distance
- P2: P3 - direction_sortie × 0.35 × distance  
- P3: position fin segment
- Interpolation cubique: P(t) = (1-t)³P₀ + 3(1-t)²tP₁ + 3(1-t)t²P₂ + t³P₃

#### Phase D: Gestion Altitude 3 Phases
1. **Palier** (0 → distance_palier):
   - Altitude = altitude_départ

2. **Transition** (distance_palier → distance_palier + transition):
   - Super-smoothstep 7ème degré: -20t⁷ + 70t⁶ - 84t⁵ + 35t⁴
   - Dérivées 1 et 2 nulles aux bornes
   - Transition imperceptible

3. **Descente** (après transition → FAF):
   - Pente = max_descent_slope (constante)
   - Linéaire jusqu'au FAF

#### Calcul Paramètres
**Pour chaque point de trajectoire:**
- **Temps**: somme cumulative Δdistance/vitesse
- **Altitude**: valeur Z du point
- **Pente**: arctan(Δz / distance_horizontale)
- **Vitesse**: constante (sauf cas vertical)
- **Cap**: arctan2(Δy, Δx) en degrés
- **Taux virage**: (cap[i] - cap[i-1]) / Δt

#### Vérification Collision
- Parcours de tous les points trajectoire
- Test pour chaque cylindre:
  - Distance horizontale ≤ rayon
  - ET altitude ≤ hauteur
- Retour: liste cylindres en collision + index

## Complexité et Performance

| Fonction | Complexité | Points générés |
|----------|-----------|----------------|
| Simple | O(n) | 500 - 10000 |
| Verticale | O(n) | 300 - 2000 |
| Complexe | O(n×m×k) | 5000 - 50000 |

*n = points trajectoire, m = waypoints, k = obstacles*

## Formules Clés

**Distance minimale descente:**
```
d_min = |Δz| / tan(|max_descent_slope|)
```

**Bézier cubique:**
```
P(t) = (1-t)³P₀ + 3(1-t)²tP₁ + 3(1-t)t²P₂ + t³P₃
```

**Super-smoothstep:**
```
f(t) = -20t⁷ + 70t⁶ - 84t⁵ + 35t⁴
```

**Décalage perpendiculaire:**
```
perp = [-direction_y, direction_x]
waypoint = point_base + side × perp × (rayon + marge)
```
