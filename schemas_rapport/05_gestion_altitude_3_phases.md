# GESTION ALTITUDE - Profil Vertical en 3 Phases

```mermaid
graph TB
    subgraph "VUE D'ENSEMBLE"
        START_ALT[Position initiale<br/>z_start altitude élevée]
        END_ALT[FAF<br/>z_faf altitude basse]
        START_ALT -.->|Profil altitude| END_ALT
    end
    
    subgraph "CALCULS PRÉLIMINAIRES"
        CALC1[Différence altitude:<br/>altitude_diff = z_faf - z_start<br/>généralement négatif descente]
        CALC2[Pente maximale avion:<br/>max_descent_slope degrés<br/>spécifique au type avion]
        CALC3[Conversion radians:<br/>max_descent_slope_rad = radians slope]
        CALC4[Distance minimale descente:<br/>min_descent_distance = |Δz| / tan |slope|]
        CALC5[Distance transition:<br/>transition_distance = clip<br/>min_descent × 0.50, 3.0, 12.0 km]
        CALC6[Distance descente totale:<br/>total_descent = min_descent + transition]
        
        CALC1 --> CALC2
        CALC2 --> CALC3
        CALC3 --> CALC4
        CALC4 --> CALC5
        CALC5 --> CALC6
    end
    
    subgraph "RÉPARTITION DISTANCES"
        CALC6 --> CHECK{total_descent<br/>>= distance_horizontale<br/>vers FAF ?}
        
        CHECK -->|OUI<br/>Pas assez d'espace| ADJ1[Ajustement forcé:<br/>level_flight_distance = 0<br/>transition = min 30% distance<br/>descent = reste]
        
        CHECK -->|NON<br/>Espace suffisant| ADJ2[Répartition normale:<br/>level_flight = distance - total_descent<br/>descent = min_descent_distance<br/>transition = calculée]
        
        ADJ1 --> PHASES
        ADJ2 --> PHASES
    end
    
    subgraph "PHASE 1: VOL EN PALIER"
        PHASE1[PHASE 1: VOL EN PALIER]
        
        P1_COND[Condition:<br/>distance_parcourue < level_flight_distance]
        P1_CALC[Calcul altitude:<br/>altitude = altitude_start<br/>constante]
        P1_SLOPE[Pente:<br/>slope = 0°<br/>vol horizontal]
        P1_REASON[Objectif:<br/>• Maintenir altitude sécurité<br/>• Permettre alignement horizontal<br/>• Préparer descente progressive]
        
        PHASE1 --> P1_COND
        P1_COND --> P1_CALC
        P1_CALC --> P1_SLOPE
        P1_SLOPE --> P1_REASON
    end
    
    subgraph "PHASE 2: TRANSITION PROGRESSIVE"
        PHASE2[PHASE 2: TRANSITION]
        
        P2_COND["Condition:<br/>level_flight ≤ distance < level_flight + transition"]
        P2_PROGRESS[Calcul progression:<br/>transition_progress = <br/>distance - level_flight / transition_distance]
        P2_SMOOTH["Application super-smoothstep 7°:<br/>smooth_t = -20t⁷ + 70t⁶ - 84t⁵ + 35t⁴"]
        P2_DROP[Calcul drop transition:<br/>transition_altitude_drop = <br/>transition_distance × tan |max_slope|]
        P2_ALT[Altitude finale:<br/>altitude = altitude_start - smooth_t × drop]
        P2_DERIV["Propriétés mathématiques:<br/>• f(0) = 0, f(1) = 1<br/>• f'(0) = f'(1) = 0 dérivée 1<br/>• f''(0) = f''(1) = 0 dérivée 2<br/>→ Transition imperceptible"]
        
        PHASE2 --> P2_COND
        P2_COND --> P2_PROGRESS
        P2_PROGRESS --> P2_SMOOTH
        P2_SMOOTH --> P2_DROP
        P2_DROP --> P2_ALT
        P2_ALT --> P2_DERIV
    end
    
    subgraph "PHASE 3: DESCENTE LINÉAIRE"
        PHASE3[PHASE 3: DESCENTE LINÉAIRE]
        
        P3_COND[Condition:<br/>distance >= level_flight + transition]
        P3_PROGRESS[Distance dans descente:<br/>descent_progress = <br/>distance - level_flight - transition]
        P3_DROP_TRANS[Drop cumulé transition:<br/>calculé phase 2]
        P3_DROP_DESC[Drop descente linéaire:<br/>descent_altitude_drop = <br/>descent_progress × tan |max_slope|]
        P3_ALT[Altitude finale:<br/>altitude = altitude_start<br/>- drop_transition<br/>- drop_descent]
        P3_SLOPE[Pente constante:<br/>slope = max_descent_slope<br/>pente maximale respectée]
        
        PHASE3 --> P3_COND
        P3_COND --> P3_PROGRESS
        P3_PROGRESS --> P3_DROP_TRANS
        P3_DROP_TRANS --> P3_DROP_DESC
        P3_DROP_DESC --> P3_ALT
        P3_ALT --> P3_SLOPE
    end
    
    PHASES[Application à chaque point trajectoire] --> PHASE1
    PHASES --> PHASE2
    PHASES --> PHASE3
    
    subgraph "PROFIL ALTITUDE RÉSULTANT"
        direction LR
        PROFILE["Graphique altitude = f(distance)<br/>───────────────────────<br/>altitude<br/>│    ════════════  Phase 1: Palier<br/>│               ╲<br/>│                 ╲  Phase 2: Transition<br/>│                  ╲ courbe smooth<br/>│                    ╲____  Phase 3: Descente<br/>│                         ╲___<br/>│                             ╲___<br/>└──────────────────────────────────→ distance<br/>    0     level    level+trans       FAF"]
    end
    
    P1_REASON --> PROFILE
    P2_DERIV --> PROFILE
    P3_SLOPE --> PROFILE
    
    subgraph "VALIDATION ET SÉCURITÉ"
        VALID[Vérifications continues]
        V1[Pente jamais > max_descent_slope<br/>en valeur absolue]
        V2[Altitude finale = z_faf<br/>au point FAF exactement]
        V3[Continuité C² garantie<br/>par super-smoothstep]
        V4[Pas de discontinuité<br/>entre phases]
        
        VALID --> V1
        VALID --> V2
        VALID --> V3
        VALID --> V4
    end
    
    PROFILE --> VALID
    
    %% Styles
    classDef phase1 fill:#e3f2fd,stroke:#2196f3,stroke-width:3px
    classDef phase2 fill:#fff3e0,stroke:#ff9800,stroke-width:3px
    classDef phase3 fill:#fce4ec,stroke:#e91e63,stroke-width:3px
    classDef calcul fill:#f1f8e9,stroke:#8bc34a,stroke-width:2px
    classDef validation fill:#ede7f6,stroke:#673ab7,stroke-width:2px
    classDef profile fill:#fff9c4,stroke:#fbc02d,stroke-width:2px
    
    class PHASE1,P1_COND,P1_CALC,P1_SLOPE,P1_REASON phase1
    class PHASE2,P2_COND,P2_PROGRESS,P2_SMOOTH,P2_DROP,P2_ALT,P2_DERIV phase2
    class PHASE3,P3_COND,P3_PROGRESS,P3_DROP_TRANS,P3_DROP_DESC,P3_ALT,P3_SLOPE phase3
    class CALC1,CALC2,CALC3,CALC4,CALC5,CALC6,CHECK,ADJ1,ADJ2 calcul
    class VALID,V1,V2,V3,V4 validation
    class PROFILE profile
```

## Détail Mathématique des Phases

### Phase 1: Vol en Palier

**Domaine spatial:**
```
0 ≤ distance_parcourue < level_flight_distance
```

**Fonction altitude:**
```python
altitude(distance) = altitude_start  # Constante
```

**Pente:**
```
slope = 0°
```

**Caractéristiques:**
- Altitude constante maximale
- Permet alignement horizontal sans contrainte verticale
- Durée dépend de l'espace disponible avant descente obligatoire
- Si espace insuffisant: level_flight_distance = 0 (pas de palier)

---

### Phase 2: Transition Progressive

**Domaine spatial:**
```
level_flight_distance ≤ distance < level_flight_distance + transition_distance
```

**Calcul du paramètre de progression:**
```python
transition_progress = (distance_parcourue - level_flight_distance) / transition_distance
# t ∈ [0, 1]
```

**Fonction super-smoothstep (polynôme degré 7):**
```python
smooth_t = -20*t⁷ + 70*t⁶ - 84*t⁵ + 35*t⁴
```

**Propriétés mathématiques:**
- `f(0) = 0` : début transition
- `f(1) = 1` : fin transition
- `f'(0) = 0` : dérivée première nulle au début (pente continue)
- `f'(1) = 0` : dérivée première nulle à la fin (pente continue)
- `f''(0) = 0` : dérivée seconde nulle au début (accélération nulle)
- `f''(1) = 0` : dérivée seconde nulle à la fin (accélération nulle)

**Calcul altitude:**
```python
transition_altitude_drop = transition_distance * abs(tan(max_descent_slope_rad))
altitude = altitude_start - smooth_t * transition_altitude_drop
```

**Pente instantanée:**
```python
slope = arctan(-d(altitude)/d(distance))
# Variable, progressive, max au milieu
```

**Objectif:**
- Transition douce entre palier (pente 0°) et descente (pente max)
- Aucune discontinuité ressentie par les occupants
- Respect physiologique (pas de changement brusque)

---

### Phase 3: Descente Linéaire

**Domaine spatial:**
```
distance ≥ level_flight_distance + transition_distance
```

**Calcul distance dans phase:**
```python
descent_progress = distance_parcourue - level_flight_distance - transition_distance
```

**Altitude cumulée perdue:**
```python
# Drop phase 2 (déjà calculé)
transition_drop = transition_distance * abs(tan(max_descent_slope_rad))

# Drop phase 3 (linéaire)
descent_drop = descent_progress * abs(tan(max_descent_slope_rad))

# Altitude finale
altitude = altitude_start - transition_drop - descent_drop
```

**Pente:**
```
slope = max_descent_slope  # Constante
```

**Caractéristiques:**
- Pente maximale permise par le type d'avion
- Linéaire, prédictible
- Continue jusqu'au FAF
- Garantit arrivée à z_faf exactement

---

## Exemples Numériques

### Avion Commercial
**Spécifications:**
- `max_descent_slope = -6.0°`
- `altitude_start = 3.0 km`
- `altitude_faf = 0.5 km`
- `distance_horizontale = 40 km`

**Calculs:**
```
altitude_diff = -2.5 km
tan(6°) ≈ 0.1051
min_descent_distance = 2.5 / 0.1051 ≈ 23.8 km
transition_distance = 23.8 × 0.50 = 11.9 km → clip → 11.9 km
total_descent = 23.8 + 11.9 = 35.7 km

distance_horizontale = 40 km > 35.7 km ✓

Répartition:
• Phase 1 (Palier): 0 → 4.3 km (10.75%)
• Phase 2 (Transition): 4.3 → 16.2 km (29.75%)
• Phase 3 (Descente): 16.2 → 40 km (59.5%)
```

### Avion Léger
**Spécifications:**
- `max_descent_slope = -10.0°`
- `altitude_start = 2.5 km`
- `altitude_faf = 0.5 km`
- `distance_horizontale = 25 km`

**Calculs:**
```
altitude_diff = -2.0 km
tan(10°) ≈ 0.1763
min_descent_distance = 2.0 / 0.1763 ≈ 11.3 km
transition_distance = 11.3 × 0.50 = 5.65 km
total_descent = 11.3 + 5.65 = 16.95 km

distance_horizontale = 25 km > 16.95 km ✓

Répartition:
• Phase 1 (Palier): 0 → 8.05 km (32.2%)
• Phase 2 (Transition): 8.05 → 13.7 km (22.6%)
• Phase 3 (Descente): 13.7 → 25 km (45.2%)
```

### Cas Critique: Espace Insuffisant
**Configuration:**
- `altitude_diff = -3.0 km`
- `max_descent_slope = -5.0°`
- `distance_horizontale = 25 km`

**Calculs:**
```
tan(5°) ≈ 0.0875
min_descent_distance = 3.0 / 0.0875 ≈ 34.3 km
transition_distance = 34.3 × 0.50 = 17.15 km → clip → 12.0 km (max)
total_descent = 34.3 + 12.0 = 46.3 km

distance_horizontale = 25 km < 46.3 km ✗

Ajustement forcé:
level_flight_distance = 0 km (pas de palier)
transition_distance = 25 × 0.30 = 7.5 km
descent_distance = 25 - 7.5 = 17.5 km

Répartition:
• Phase 1 (Palier): AUCUNE
• Phase 2 (Transition): 0 → 7.5 km (30%)
• Phase 3 (Descente): 7.5 → 25 km (70%)
```

## Graphiques de Profil

### Profil Normal
```
Altitude (km)
3.0 ┤──────────────╮
    │              │
2.5 ┤              │  Phase 1
    │              │  Palier
2.0 ┤              ╰─╮
    │                 ╲ Phase 2
1.5 ┤                  ╲ Transition
    │                   ╲
1.0 ┤                    ╲___
    │                        ╲___ Phase 3
0.5 ┤                            ╲___ Descente
    │                                ╲___
0.0 ┴────────────────────────────────────┤
    0        10       20       30       40 km
```

### Profil Espace Contraint
```
Altitude (km)
3.0 ┤╮
    │ ╲
2.5 │  ╲  Phase 2
    │   ╲ Transition
2.0 │    ╲ (courte)
    │     ╲
1.5 │      ╲___
    │          ╲___ Phase 3
1.0 │              ╲___ Descente
    │                  ╲___ (longue)
0.5 │                      ╲___
    │                          ╲___
0.0 ┴──────────────────────────────┤
    0         10        20        25 km
```

## Avantages de l'Approche 3 Phases

### Technique
1. **Continuité C²**: Dérivées 1 et 2 nulles aux jonctions
2. **Prédictibilité**: Comportement déterministe
3. **Sécurité**: Respect strict des limites aérodynamiques

### Opérationnel
1. **Confort**: Pas de changement brusque de pente
2. **Contrôlabilité**: Phases distinctes et compréhensibles
3. **Adaptabilité**: Ajustement automatique selon contraintes

### Réglementaire
1. **Conformité**: Respect pentes maximales certifiées
2. **Traçabilité**: Profil documenté et vérifiable
3. **Répétabilité**: Résultats identiques pour mêmes conditions

## Formules de Référence

**Distance minimale descente:**
```
d_min = |Δz| / tan(|slope_max|)
```

**Drop altitude transition:**
```
drop_trans = d_trans × tan(|slope_max|)
```

**Drop altitude descente:**
```
drop_desc = d_desc × tan(|slope_max|)
```

**Super-smoothstep:**
```
f(t) = -20t⁷ + 70t⁶ - 84t⁵ + 35t⁴
```

**Altitude au point distance d:**
```
if d < d_level:
    z = z_start
elif d < d_level + d_trans:
    t = (d - d_level) / d_trans
    z = z_start - f(t) × drop_trans
else:
    z = z_start - drop_trans - (d - d_level - d_trans) × tan(|slope|)
```
