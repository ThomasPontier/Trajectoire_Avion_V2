# GESTION ALTITUDE - Profil Vertical en 3 Phases (Version Compacte)

## 1. Schéma Global - Vue d'Ensemble

```mermaid
graph LR
    START[Départ<br/>z_start]
    
    CALC[Calculs<br/>Préliminaires]
    
    P1[Phase 1<br/>VOL PALIER<br/>altitude constante]
    P2[Phase 2<br/>TRANSITION<br/>super-smoothstep]
    P3[Phase 3<br/>DESCENTE<br/>pente constante]
    
    END[FAF<br/>z_faf]
    
    START --> CALC
    CALC --> P1
    P1 --> P2
    P2 --> P3
    P3 --> END
    
    classDef phase1 fill:#e3f2fd,stroke:#2196f3,stroke-width:3px
    classDef phase2 fill:#fff3e0,stroke:#ff9800,stroke-width:3px
    classDef phase3 fill:#fce4ec,stroke:#e91e63,stroke-width:3px
    classDef calcul fill:#f1f8e9,stroke:#8bc34a,stroke-width:2px
    
    class P1 phase1
    class P2 phase2
    class P3 phase3
    class CALC calcul
```

**Profil Altitude Résultant:**
```
altitude
│    ═══════  Phase 1
│           ╲
│            ╲ Phase 2
│             ╲___
│                 ╲___ Phase 3
│                     ╲___
└────────────────────────→ distance
```

---

## 2. Schéma Détaillé - Calculs Préliminaires

```mermaid
graph LR
    START[Données initiales:<br/>z_start, z_faf<br/>distance_horizontale<br/>max_descent_slope]
    
    CALC1[Différence altitude<br/>Δz = z_faf - z_start]
    CALC2[Distance minimale<br/>d_min = abs Δz / tan slope]
    CALC3[Distance transition<br/>d_trans = clip d_min×0.50, 3.0, 12.0]
    
    START --> CALC1
    CALC1 --> CALC2
    CALC2 --> CALC3
    
    classDef calcul fill:#f1f8e9,stroke:#8bc34a,stroke-width:2px
    class START,CALC1,CALC2,CALC3 calcul
```

```mermaid
graph LR
    CALC4[Distance totale descente<br/>d_total = d_min + d_trans]
    
    CHECK{d_total >=<br/>distance_horizontale?}
    
    ADJ_OUI[Ajustement forcé<br/>d_palier = 0<br/>d_trans = 30% distance<br/>d_desc = 70% distance]
    
    ADJ_NON[Répartition normale<br/>d_palier = distance - d_total<br/>d_trans = calculée<br/>d_desc = d_min]
    
    CALC4 --> CHECK
    CHECK -->|OUI<br/>Espace insuffisant| ADJ_OUI
    CHECK -->|NON<br/>Espace suffisant| ADJ_NON
    
    classDef calcul fill:#f1f8e9,stroke:#8bc34a,stroke-width:2px
    class CALC4,ADJ_OUI,ADJ_NON calcul
```

---

## 3. Schéma Détaillé - Phase 1 (Vol en Palier)

```mermaid
graph LR
    P1_START[PHASE 1: VOL EN PALIER]
    
    P1_DOMAIN[Domaine spatial<br/>0 ≤ distance < d_palier]
    
    P1_CALC[Calcul altitude<br/>z distance = z_start]
    
    P1_SLOPE[Pente<br/>slope = 0°]
    
    P1_OBJ[Objectifs:<br/>• Maintenir altitude sécurité<br/>• Alignement horizontal<br/>• Préparer descente]
    
    P1_START --> P1_DOMAIN
    P1_DOMAIN --> P1_CALC
    P1_CALC --> P1_SLOPE
    P1_SLOPE --> P1_OBJ
    
    classDef phase1 fill:#e3f2fd,stroke:#2196f3,stroke-width:3px
    class P1_START,P1_DOMAIN,P1_CALC,P1_SLOPE,P1_OBJ phase1
```

**Formules Phase 1:**
```
Domaine: 0 ≤ d < d_palier
Altitude: z(d) = z_start (constante)
Pente: slope = 0°
```

---

## 4. Schéma Détaillé - Phase 2 (Transition)

```mermaid
graph LR
    P2_START[PHASE 2: TRANSITION PROGRESSIVE]
    P2_DOMAIN[Domaine spatial<br/>d_palier ≤ distance < d_palier + d_trans]
    P2_PROGRESS[Paramètre progression<br/>t = distance - d_palier / d_trans]
    P2_SMOOTH[Super-smoothstep degré 7<br/>smooth_t = -20t⁷ + 70t⁶ - 84t⁵ + 35t⁴]
    
    P2_START --> P2_DOMAIN
    P2_DOMAIN --> P2_PROGRESS
    P2_PROGRESS --> P2_SMOOTH
    
    classDef phase2 fill:#fff3e0,stroke:#ff9800,stroke-width:3px
    class P2_START,P2_DOMAIN,P2_PROGRESS,P2_SMOOTH phase2
```

```mermaid
graph LR
    P2_DROP[Drop altitude transition<br/>drop_trans = d_trans × tan abs slope]
    P2_ALT[Altitude finale<br/>z = z_start - smooth_t × drop_trans]
    P2_PROP[Propriétés C²:<br/>f 0 = 0, f 1 = 1<br/>f' 0 = f' 1 = 0<br/>f'' 0 = f'' 1 = 0]
    
    P2_DROP --> P2_ALT
    P2_ALT --> P2_PROP
    
    classDef phase2 fill:#fff3e0,stroke:#ff9800,stroke-width:3px
    class P2_DROP,P2_ALT,P2_PROP phase2
```

**Formules Phase 2:**
```
Domaine: d_palier ≤ d < d_palier + d_trans
Paramètre: t = (d - d_palier) / d_trans ∈ [0, 1]
Super-smoothstep: f(t) = -20t⁷ + 70t⁶ - 84t⁵ + 35t⁴
Drop: drop_trans = d_trans × tan(|slope_max|)
Altitude: z(d) = z_start - f(t) × drop_trans
```

---

## 5. Schéma Détaillé - Phase 3 (Descente)

```mermaid
graph LR
    P3_START[PHASE 3: DESCENTE LINÉAIRE]
    P3_DOMAIN[Domaine spatial<br/>distance >= d_palier + d_trans]
    P3_PROGRESS[Distance dans descente<br/>d_desc = distance - d_palier - d_trans]
    P3_DROP_T[Drop cumulé transition<br/>calculé en phase 2]
    
    P3_START --> P3_DOMAIN
    P3_DOMAIN --> P3_PROGRESS
    P3_PROGRESS --> P3_DROP_T
    
    classDef phase3 fill:#fce4ec,stroke:#e91e63,stroke-width:3px
    class P3_START,P3_DOMAIN,P3_PROGRESS,P3_DROP_T phase3
```

```mermaid
graph LR
    P3_DROP_D[Drop descente linéaire<br/>drop_desc = d_desc × tan abs slope]
    P3_ALT[Altitude finale<br/>z = z_start - drop_trans - drop_desc]
    P3_SLOPE[Pente constante<br/>slope = max_descent_slope]
    
    P3_DROP_D --> P3_ALT
    P3_ALT --> P3_SLOPE
    
    classDef phase3 fill:#fce4ec,stroke:#e91e63,stroke-width:3px
    class P3_DROP_D,P3_ALT,P3_SLOPE phase3
```

**Formules Phase 3:**
```
Domaine: d ≥ d_palier + d_trans
Distance parcourue: d_desc = d - d_palier - d_trans
Drop transition: drop_trans (déjà calculé)
Drop descente: drop_desc = d_desc × tan(|slope_max|)
Altitude: z(d) = z_start - drop_trans - drop_desc
Pente: slope = max_descent_slope (constante)
```

---

## 6. Schéma Détaillé - Validation et Sécurité

```mermaid
graph TB
    VALID[Vérifications continues<br/>tout au long de la trajectoire]
    
    V1[Pente respectée<br/>abs slope ≤ max_descent_slope]
    V2[Altitude finale exacte<br/>z FAF = z_faf]
    V3[Continuité C²<br/>dérivées 1 et 2 continues]
    V4[Pas de discontinuité<br/>entre phases]
    
    RESULT[Profil altitude sûr<br/>et confortable]
    
    VALID --> V1
    VALID --> V2
    VALID --> V3
    VALID --> V4
    
    V1 --> RESULT
    V2 --> RESULT
    V3 --> RESULT
    V4 --> RESULT
    
    classDef validation fill:#ede7f6,stroke:#673ab7,stroke-width:2px
    class VALID,V1,V2,V3,V4,RESULT validation
```

---

## Résumé des Formules Clés

| Phase | Domaine | Formule Altitude |
|-------|---------|------------------|
| **Phase 1** | `0 ≤ d < d_palier` | `z = z_start` |
| **Phase 2** | `d_palier ≤ d < d_palier + d_trans` | `z = z_start - f(t) × drop_trans`<br/>où `t = (d - d_palier) / d_trans`<br/>et `f(t) = -20t⁷ + 70t⁶ - 84t⁵ + 35t⁴` |
| **Phase 3** | `d ≥ d_palier + d_trans` | `z = z_start - drop_trans - drop_desc`<br/>où `drop_desc = (d - d_palier - d_trans) × tan(\|slope\|)` |

**Calculs préliminaires:**
- `d_min = |Δz| / tan(|slope_max|)`
- `d_trans = clip(d_min × 0.50, 3.0, 12.0)`
- `d_total = d_min + d_trans`
- Si `d_total < distance_horizontale`: `d_palier = distance - d_total`
- Sinon: ajustement forcé avec `d_palier = 0`

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
transition_distance = 23.8 × 0.50 = 11.9 km
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

---
