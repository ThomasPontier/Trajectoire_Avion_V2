# DÉCOMPOSITION FONCTIONNELLE - TrajectoryCalculator

## SCHÉMA 1 - Vue d'Ensemble

```mermaid
graph TB
    CALC[calculate_trajectory<br/>Point d'entrée principal]
    
    ANALYZE[ÉTAPE 1<br/>Analyse Géométrique<br/>Voir Schéma 2]
    
    DECISION{ÉTAPE 2<br/>Sélection Type<br/>Trajectoire}
    
    SIMPLE[Type SIMPLE<br/>Trajectoire Directe<br/>Voir Schéma 3]
    
    VERT[Type VERTICAL<br/>Descente Pure<br/>Voir Schéma 4]
    
    ALIGN[Type COMPLEXE<br/>Alignement Piste<br/>Voir Schéma 5]
    
    PARAMS[ÉTAPE 3<br/>Calcul Paramètres<br/>Voir Schéma 6]
    
    OUTPUT[Sortie:<br/>Trajectoire + Paramètres]
    
    CALC --> ANALYZE
    ANALYZE --> DECISION
    DECISION -->|Distance courte| SIMPLE
    DECISION -->|Au-dessus FAF| VERT
    DECISION -->|Alignement requis| ALIGN
    
    SIMPLE --> PARAMS
    VERT --> PARAMS
    ALIGN --> PARAMS
    
    PARAMS --> OUTPUT
    
    classDef main fill:#e1f5e1,stroke:#4caf50,stroke-width:3px
    classDef process fill:#bbdefb,stroke:#2196f3,stroke-width:2px
    classDef decision fill:#ffccbc,stroke:#ff5722,stroke-width:2px
    classDef type fill:#fff9c4,stroke:#fbc02d,stroke-width:2px
    
    class CALC,OUTPUT main
    class ANALYZE,PARAMS process
    class DECISION decision
    class SIMPLE,VERT,ALIGN type
```

**Légende:**
- **Vert**: Point d'entrée/sortie
- **Bleu**: Étapes de traitement
- **Orange**: Point de décision
- **Jaune**: Types de trajectoires

---

## SCHÉMA 2 - Analyse Géométrique Initiale

```mermaid
graph TB
    INPUT[Entrées:<br/>Aircraft position<br/>Cylinders obstacles]
    
    DIST[Calcul Distance<br/>Horizontale<br/>avion → FAF]
    
    RUNWAY[Calcul Distance<br/>à l'Axe Piste<br/>runway_axis_distance]
    
    ANGLE[Calcul Angle<br/>Cap actuel vs<br/>Axe piste]
    
    INTERCEPT[Point Interception<br/>Optimal sur<br/>Axe Piste]
    
    CRITERIA{Évaluation<br/>Critères}
    
    OUTPUT[Vers Décision<br/>Type Trajectoire]
    
    INPUT --> DIST
    INPUT --> RUNWAY
    INPUT --> ANGLE
    
    DIST --> INTERCEPT
    ANGLE --> INTERCEPT
    RUNWAY --> INTERCEPT
    
    INTERCEPT --> CRITERIA
    
    CRITERIA -->|horizontal_distance| OUTPUT
    CRITERIA -->|angle_to_runway| OUTPUT
    CRITERIA -->|runway_axis_distance| OUTPUT
    CRITERIA -->|cos_angle| OUTPUT
    
    classDef input fill:#e1f5e1,stroke:#4caf50,stroke-width:2px
    classDef calc fill:#bbdefb,stroke:#2196f3,stroke-width:2px
    classDef decision fill:#ffccbc,stroke:#ff5722,stroke-width:2px
    
    class INPUT,OUTPUT input
    class DIST,RUNWAY,ANGLE,INTERCEPT calc
    class CRITERIA decision
```

**Formules utilisées:**
- Distance horizontale: `√[(x_faf - x_avion)² + (y_faf - y_avion)²]`
- Angle: `arctan2(Δy, Δx)`
- Distance axe: produit scalaire perpendiculaire

---

## SCHÉMA 3 - Trajectoire Simple (Directe)

```mermaid
graph TB
    START[Position Avion<br/>x, y, z]
    
    FAF[Position FAF<br/>x_faf, y_faf, z_faf]
    
    LINE[Calcul Ligne Droite<br/>Interpolation linéaire<br/>start → FAF]
    
    DENSITY[Calcul Nombre Points<br/>n = max500, 100/km<br/>Densité adaptative]
    
    POINTS[Génération Points<br/>x = xi + t·Δx<br/>y = yi + t·Δy<br/>z = zi + t·Δz]
    
    PARAMS[Calcul Paramètres<br/>temps, altitude,<br/>pente, cap]
    
    OUTPUT[Trajectoire Simple<br/>Array Nx3 + Params]
    
    START --> LINE
    FAF --> LINE
    LINE --> DENSITY
    DENSITY --> POINTS
    POINTS --> PARAMS
    PARAMS --> OUTPUT
    
    classDef position fill:#e1f5e1,stroke:#4caf50,stroke-width:2px
    classDef calc fill:#bbdefb,stroke:#2196f3,stroke-width:2px
    classDef output fill:#fff9c4,stroke:#fbc02d,stroke-width:2px
    
    class START,FAF position
    class LINE,DENSITY,POINTS,PARAMS calc
    class OUTPUT output
```

**Caractéristiques:**
- Type: Ligne droite
- Points: 500 à 10 000
- Complexité: O(n)
- Cas d'usage: Distance < seuil OU pas d'alignement requis

---

## SCHÉMA 4 - Trajectoire Verticale (Descente Pure)

```mermaid
graph TB
    CHECK[Vérification<br/>Position XY ≈ FAF<br/>distance_horiz < seuil]
    
    ALTITUDE[Différence Altitude<br/>Δz = z_avion - z_faf]
    
    SMOOTH[Fonction Smoothstep<br/>Ease-in-out<br/>f = t² · 3 - 2·t]
    
    DENSITY[Nombre Points<br/>n = min300, Δz×200<br/>Densité variable]
    
    GENERATE[Génération Points<br/>x = constant<br/>y = constant<br/>z = z_start - Δz·f]
    
    PARAMS[Paramètres Spéciaux<br/>Vitesse = 10 km/h<br/>Descente douce]
    
    OUTPUT[Trajectoire Verticale<br/>300-2000 points]
    
    CHECK --> ALTITUDE
    ALTITUDE --> SMOOTH
    SMOOTH --> DENSITY
    DENSITY --> GENERATE
    GENERATE --> PARAMS
    PARAMS --> OUTPUT
    
    classDef check fill:#ffccbc,stroke:#ff5722,stroke-width:2px
    classDef calc fill:#bbdefb,stroke:#2196f3,stroke-width:2px
    classDef output fill:#fff9c4,stroke:#fbc02d,stroke-width:2px
    
    class CHECK check
    class ALTITUDE,SMOOTH,DENSITY,GENERATE,PARAMS calc
    class OUTPUT output
```

**Formule Smoothstep:**
```
f(t) = t² · (3 - 2·t)
où t ∈ [0, 1]
Dérivées nulles en t=0 et t=1
```

---

## SCHÉMA 5 - Trajectoire Complexe - Vue d'Ensemble

```mermaid
graph TB
    START[Début Trajectoire Complexe]
    
    PHASE_A[PHASE A<br/>Vol Initial Rectiligne<br/>20% distance<br/>Voir Schéma 5A]
    
    PHASE_B[PHASE B<br/>Courbes Bézier + Évitement<br/>Construction point par point<br/>XY Bézier + Z 3-phases<br/>Voir Schéma 5B]
    
    VERIFY[Vérification<br/>Collision Finale<br/>Voir Schéma 5C]
    
    OUTPUT[Trajectoire 3D Complète<br/>Array Nx3 xyz]
    
    START --> PHASE_A
    PHASE_A --> PHASE_B
    PHASE_B --> VERIFY
    VERIFY --> OUTPUT
    
    classDef main fill:#e1f5e1,stroke:#4caf50,stroke-width:3px
    classDef phase fill:#bbdefb,stroke:#2196f3,stroke-width:2px
    classDef verify fill:#ffccbc,stroke:#ff5722,stroke-width:2px
    classDef output fill:#fff9c4,stroke:#fbc02d,stroke-width:2px
    
    class START main
    class PHASE_A,PHASE_B phase
    class VERIFY verify
    class OUTPUT output
```

**Note critique sur le calcul :**

La trajectoire est construite **point par point** dans une boucle unique où :
- **Coordonnées XY** : Calculées via courbes de Bézier cubiques
- **Coordonnée Z** : Calculée via profil 3 phases (palier/transition/descente)
- **Assignation** : `[x, y, z]` simultanée pour chaque point

**Il n'y a PAS de séparation temporelle** :
- ❌ Pas de trajectoire XY générée d'abord
- ❌ Pas de fusion ultérieure avec Z
- ✅ Calcul et assemblage **simultanés** dans la même itération

**Indépendance algorithmique** (pas temporelle) :
- La formule XY (Bézier) ne dépend pas de Z
- La formule Z (3 phases) ne dépend que de la distance 2D cumulée
- Les deux logiques s'exécutent **en parallèle** dans le code

**Détails des phases:**
- **Phase A**: 20% distance en ligne droite (altitude constante)
- **Phase B**: Détection obstacles + Construction courbes Bézier avec profil d'altitude intégré
- **Vérification**: Collision finale sur trajectoire 3D complète

---

## SCHÉMA 5A - Phase A: Vol Initial Rectiligne

```mermaid
graph TB
    POS[Position Actuelle xyz]
    CAP[Cap Actuel heading]
    DIST[Distance Phase A 20pct]
    CALC[Calcul Point Final]
    GEN[Génération Segment]
    OUTPUT[Segment Phase A]
    
    POS --> CALC
    CAP --> CALC
    DIST --> CALC
    CALC --> GEN
    GEN --> OUTPUT
    
    classDef input fill:#e1f5e1,stroke:#4caf50,stroke-width:2px
    classDef calc fill:#bbdefb,stroke:#2196f3,stroke-width:2px
    classDef output fill:#fff9c4,stroke:#fbc02d,stroke-width:2px
    
    class POS,CAP,DIST input
    class CALC,GEN calc
    class OUTPUT output
```

**Calculs:**
```
distance_phase_a = max(200m, 20% × distance_totale)
x' = x + distance × cos(heading)
y' = y + distance × sin(heading)
z' = z (altitude maintenue)
```

**Objectif**: Laisser l'avion voler dans sa direction actuelle avant de commencer les manœuvres d'alignement

---

## SCHÉMA 5B - Phase B: Évitement Obstacles et Construction Bézier

```mermaid
graph TB
    TRAJ[Trajet Direct]
    LOOP[Boucle Cylindres]
    PROJ[Projection Centre]
    CHECK{Distance Rayon?}
    NO_WP[Pas de Waypoint]
    CALC_WP[Calcul Waypoints]
    LIST[Liste Waypoints]
    BEZIER[Courbes Bézier]
    CURVE[Interpolation]
    OUTPUT[Trajectoire XY]
    
    TRAJ --> LOOP
    LOOP --> PROJ
    PROJ --> CHECK
    CHECK -->|Non| NO_WP
    CHECK -->|Oui| CALC_WP
    CALC_WP --> LIST
    NO_WP --> LIST
    LIST --> BEZIER
    BEZIER --> CURVE
    CURVE --> OUTPUT
    
    classDef calc fill:#bbdefb,stroke:#2196f3,stroke-width:2px
    classDef decision fill:#ffccbc,stroke:#ff5722,stroke-width:2px
    classDef waypoint fill:#e1bee7,stroke:#9c27b0,stroke-width:2px
    classDef bezier fill:#c5e1a5,stroke:#7cb342,stroke-width:2px
    
    class TRAJ,LOOP,PROJ,CALC_WP calc
    class CHECK decision
    class LIST waypoint
    class BEZIER,CURVE,OUTPUT bezier
```

**Formules Waypoints:**
```
perpendiculaire = [-dir_y, dir_x]
décalage = (rayon + marge_sécurité)
WP_entrée = projection - approach × direction + side × perp × décalage
WP_sortie = projection + approach × direction + side × perp × décalage
```

**Formule Bézier Cubique:**
```
P(t) = (1-t)³·P₀ + 3(1-t)²·t·P₁ + 3(1-t)·t²·P₂ + t³·P₃
Points contrôle:
  P₁ = P₀ + 0.35 × distance × direction
  P₂ = P₃ - 0.35 × distance × direction
Échantillonnage: 100-200 points par segment
```

---

## SCHÉMA 5C - Vérification Collision Finale

```mermaid
graph TB
    TRAJ[Trajectoire 3D]
    LOOP_PT[Boucle Points]
    LOOP_CYL[Boucle Cylindres]
    DIST_H[Distance Horizontale]
    CHECK_H{dist rayon?}
    CHECK_Z{z hauteur?}
    COLLISION[COLLISION]
    NO_COLL[Pas collision]
    REPORT[Rapport]
    
    TRAJ --> LOOP_PT
    LOOP_PT --> LOOP_CYL
    LOOP_CYL --> DIST_H
    DIST_H --> CHECK_H
    CHECK_H -->|Non| NO_COLL
    CHECK_H -->|Oui| CHECK_Z
    CHECK_Z -->|Non| NO_COLL
    CHECK_Z -->|Oui| COLLISION
    COLLISION --> REPORT
    NO_COLL --> LOOP_PT
    
    classDef calc fill:#bbdefb,stroke:#2196f3,stroke-width:2px
    classDef decision fill:#ffccbc,stroke:#ff5722,stroke-width:2px
    classDef alert fill:#f8bbd0,stroke:#e91e63,stroke-width:2px
    
    class LOOP_PT,LOOP_CYL,DIST_H calc
    class CHECK_H,CHECK_Z decision
    class COLLISION,REPORT alert
```

**Conditions collision:**
```
distance_horizontale = √[(x_point - x_centre)² + (y_point - y_centre)²]
collision = (distance_horizontale ≤ rayon) ET (z_point ≤ hauteur_cylindre)
```

---

## GESTION DE L'ALTITUDE - Traitement Parallèle

### Principe Général

L'altitude est calculée **indépendamment** de la trajectoire XY et appliquée sur tous les points de la trajectoire finale.

```mermaid
graph TB
    XY[Trajectoire XY]
    PARAMS[Paramètres z]
    PROFIL[Profil Altitude]
    APPLY[Application z]
    TRAJ_3D[Trajectoire 3D]
    
    XY --> APPLY
    PARAMS --> PROFIL
    PROFIL --> APPLY
    APPLY --> TRAJ_3D
    
    classDef input fill:#e1f5e1,stroke:#4caf50,stroke-width:2px
    classDef calc fill:#bbdefb,stroke:#2196f3,stroke-width:2px
    classDef output fill:#fff9c4,stroke:#fbc02d,stroke-width:2px
    
    class XY,PARAMS input
    class PROFIL,APPLY calc
    class TRAJ_3D output
```

### Profil Altitude Tri-Phases

```mermaid
graph LR
    P1[PHASE 1 Palier]
    P2[PHASE 2 Transition]
    P3[PHASE 3 Descente]
    
    P1 --> P2
    P2 --> P3
    
    classDef phase fill:#e1bee7,stroke:#9c27b0,stroke-width:2px
    class P1,P2,P3 phase
```

**PHASE 1 - Palier:**
- Distance: `0 → distance_palier`
- Altitude: `z = z_départ` (constant)

**PHASE 2 - Transition:**
- Fonction: Super-smoothstep ordre 7
- Formule: `f(t) = -20t⁷ + 70t⁶ - 84t⁵ + 35t⁴`
- Application: `z = z_start - Δz × f(t)`
- Propriétés: Dérivées 1ère et 2ème nulles aux extrémités

**PHASE 3 - Descente:**
- Pente: Maximale autorisée
- Mode: Linéaire jusqu'au FAF

**Avantages de cette approche:**
- Séparation des préoccupations (XY vs Z)
- Profil d'altitude indépendant des obstacles horizontaux
- Facilite les modifications ultérieures
- Performance optimisée (calcul vectoriel)

---

## SCHÉMA 6 - Calcul Paramètres Trajectoire

```mermaid
graph TB
    TRAJ[Trajectoire 3D]
    SPEED[Vitesse]
    TIME[Temps]
    ALT[Altitude]
    SLOPE[Pente]
    HEAD[Cap]
    TURN[Virage]
    DICT[Dictionnaire]
    OUTPUT[Paramètres]
    
    TRAJ --> TIME
    SPEED --> TIME
    TRAJ --> ALT
    TRAJ --> SLOPE
    TRAJ --> HEAD
    HEAD --> TURN
    TIME --> TURN
    TIME --> DICT
    ALT --> DICT
    SLOPE --> DICT
    HEAD --> DICT
    TURN --> DICT
    SPEED --> DICT
    DICT --> OUTPUT
    
    classDef input fill:#e1f5e1,stroke:#4caf50,stroke-width:2px
    classDef calc fill:#bbdefb,stroke:#2196f3,stroke-width:2px
    classDef output fill:#fff9c4,stroke:#fbc02d,stroke-width:2px
    
    class TRAJ,SPEED input
    class TIME,ALT,SLOPE,HEAD,TURN,DICT calc
    class OUTPUT output
```

**Note:** L'altitude utilisée provient du profil calculé en parallèle

**Dictionnaire de sortie:**
```python
{
    'time': array,         # temps cumulé [s]
    'altitude': array,     # altitude [m]
    'slope': array,        # pente [deg]
    'speed': constant,     # vitesse [km/h]
    'heading': array,      # cap [deg]
    'turn_rate': array     # taux virage [deg/s]
}
```

---

## Complexité et Performance

| Fonction | Complexité | Points générés |
|----------|-----------|----------------|
| Simple | O(n) | 500 - 10000 |
| Verticale | O(n) | 300 - 2000 |
| Complexe | O(n×m×k) | 5000 - 50000 |

*n = points trajectoire, m = waypoints, k = obstacles*

---

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
