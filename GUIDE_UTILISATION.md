# 🛩️ Guide d'Utilisation - Trajectoires Avec Virages et Variation d'Altitude

## 🎯 Capacités du Simulateur

Votre simulateur calcule des trajectoires réalistes où l'avion peut :
- **Virer** pour changer d'orientation (gauche ou droite)
- **Monter ou descendre** en respectant les pentes maximales
- **Combiner les deux** : virage + changement d'altitude simultanés ou séquentiels

## 📐 Comment ça fonctionne ?

### Phase 1 : Virage Initial (si nécessaire)
```
Position initiale : (40, 10, 3 km)
Cap : 0° (Nord)
Cible : FAF à (20, 25, 1 km) → Direction : Sud-Ouest

Calcul :
1. Angle entre cap et direction FAF : ~60°
2. Rayon de virage : R = V²/(g×tan(φ)) ≈ 0.44 km
3. Arc de cercle de 60° à altitude constante (3 km)
```

**Résultat** : Trajectoire courbe (cyan) jusqu'à pointer vers le FAF

### Phase 2 : Vol en Palier
```
Après le virage :
- L'avion pointe maintenant vers le FAF
- Il maintient l'altitude (3 km)
- Vol en ligne droite
```

**Résultat** : Ligne droite (verte) en palier

### Phase 3 : Descente Progressive
```
Distance restante : 15 km
Altitude à perdre : 3 - 1 = 2 km
Pente max : -10° (avion léger)

Calcul :
- Distance minimale descente : 2/tan(10°) ≈ 11.3 km
- Distance en palier : 15 - 11.3 = 3.7 km
- Descente : derniers 11.3 km
```

**Résultat** : Descente progressive (orange) jusqu'au FAF

## 🎮 Guide Pratique d'Utilisation

### Configuration de Test Recommandée

#### Test 1 : Virage à Droite avec Descente
```
Environnement :
├─ Taille : 50 × 50 × 5 km
├─ Aéroport : (5, 25, 0)
└─ FAF : (20, 25, 1)

Avion :
├─ Type : Léger
├─ Position : (40, 10, 3)  ← En haut à droite
├─ Cap : 180° (Sud)        ← Pointe vers le bas
├─ Vitesse : 180 km/h
└─ Altitude : 3 km

☐ Virages réalistes : DÉSACTIVÉ

Résultat attendu :
🔵 Virage de ~45° vers la gauche (arc cyan)
🟢 Vol en palier vers le FAF (ligne verte)
🟠 Descente de 3→1 km (ligne orange)
```

#### Test 2 : Demi-Tour avec Descente
```
Avion :
├─ Position : (25, 40, 4)  ← En haut au centre
├─ Cap : 0° (Nord)         ← Pointe vers le haut
├─ Altitude : 4 km
└─ Autres : identiques

Résultat attendu :
🔵 Virage de 180° (demi-cercle cyan)
🟢 Vol en palier (ligne verte)
🟠 Descente de 4→1 km (ligne orange)
```

#### Test 3 : Approche Latérale
```
Avion :
├─ Position : (45, 25, 2)  ← À droite sur la ligne
├─ Cap : 270° (Ouest)      ← Pointe vers la gauche
├─ Altitude : 2 km

Résultat attendu :
🟢 Ligne droite (déjà aligné)
🟠 Descente progressive de 2→1 km
```

## 🔍 Visualisation dans le Simulateur

### Éléments à Observer

1. **Flèche verte sur l'avion** 
   - Indique le cap initial
   - Permet de prévoir le sens du virage

2. **Trajectoire colorée**
   - 🔵 **Cyan** : Phase de virage (altitude constante)
   - 🟢 **Vert** : Approche en palier (direction fixe, altitude constante)
   - 🟠 **Orange** : Descente finale (vers le FAF)

3. **Points de repère**
   - 🟥 Carré rouge : Aéroport
   - 🔷 Triangle bleu : FAF
   - 🟢 Point vert : Position initiale avion
   - ⬥ Losange bleu : Point d'interception (si virages réalistes)

4. **Axe d'approche**
   - Ligne pointillée noire : Aéroport → FAF (prolongée)
   - Sert de référence pour l'alignement

## 📊 Informations de Simulation

Après le calcul, un message affiche :
```
✅ Simulation terminée!

📊 Distance totale: 32.45 km
⏱️  Temps de vol: 10.8 minutes
📍 Points de trajectoire: 2091

✈️  Vitesse initiale: 180.0 km/h
🎯 Vitesse d'approche: 120.0 km/h

🔄 Rayon de virage: 0.441 km
🎯 Angle de virage: 180.0°

🛫 Vol en palier: 15.2 km
🛬 Distance de descente: 11.3 km
📐 Pente de descente: -10.0° (max: -10.0°)
```

## 🎛️ Deux Modes de Calcul

### Mode 1 : Trajectoire Directe (☐ Virages désactivés)

**Logique :**
```
1. Virage pour pointer vers le FAF
2. Ligne droite jusqu'au FAF
3. Gestion altitude : palier → descente
```

**Avantages :**
- ✅ Simple et prévisible
- ✅ Fonctionne toujours
- ✅ Trajets plus courts

**Utilisation :** Route directe, approche simple

### Mode 2 : Interception Axe (☑️ Virages réalistes)

**Logique :**
```
1. Virage TANGENT pour intercepter l'axe Aéroport→FAF
2. Suivi de l'axe d'approche
3. Descente alignée sur l'axe
```

**Avantages :**
- ✅ Plus réaliste (procédure IFR)
- ✅ Alignement parfait avec la piste
- ✅ Approche stabilisée

**Inconvénient :**
- ⚠️ Peut échouer si géométrie impossible (→ fallback mode 1)

**Utilisation :** Approche IFR standard, alignement piste

## 🧮 Formules Utilisées

### Rayon de Virage
```python
R = V² / (g × tan(φ_max))

Exemple (avion léger, 180 km/h, φ=30°) :
R = (50 m/s)² / (9.81 × tan(30°))
R = 2500 / 5.66
R ≈ 441 mètres = 0.44 km
```

### Distance de Descente
```python
d = Δh / tan(pente_max)

Exemple (descente de 2 km, pente -10°) :
d = 2000 m / tan(10°)
d = 2000 / 0.176
d ≈ 11,300 mètres = 11.3 km
```

### Angle de Virage
```python
θ = arccos(cap_initial · direction_FAF)

Exemple (cap Nord 0°, FAF au Sud 180°) :
θ = arccos(cos(180°))
θ = 180°  → Demi-tour complet
```

## 💡 Conseils d'Utilisation

### Pour Voir un Virage Spectaculaire
```
✓ Positionnez l'avion loin du FAF (40+ km)
✓ Choisissez un cap perpendiculaire ou opposé
✓ Utilisez un avion léger (rayon de virage plus petit)
✓ Réduisez la vitesse (150-180 km/h)
```

### Pour Optimiser la Trajectoire
```
✓ Cap initial proche de la direction FAF
✓ Altitude initiale ≈ altitude FAF + 2 km
✓ Vitesse adaptée au type d'avion
```

### Pour Tester les Limites
```
✓ Cap opposé au FAF (180°) → Demi-tour
✓ Altitude très élevée (4-5 km) → Descente longue
✓ Vitesse élevée (250+ km/h) → Grand rayon de virage
```

## 🔬 Expériences Intéressantes

### Expérience 1 : Impact de la Vitesse sur le Rayon
```
Configuration identique, vitesses différentes :
- 150 km/h → R = 0.31 km (virage serré)
- 200 km/h → R = 0.55 km (virage moyen)
- 250 km/h → R = 0.86 km (virage large)
```

### Expérience 2 : Type d'Avion
```
Même vitesse (200 km/h), types différents :
- Léger (φ=30°)      → R = 0.55 km
- Commercial (φ=25°) → R = 0.64 km
- Cargo (φ=20°)      → R = 0.84 km
```

### Expérience 3 : Angle de Virage
```
Position fixe, caps différents :
- Cap 270° → Angle 0° (aligné)
- Cap 0°   → Angle 90° (perpendiculaire)
- Cap 90°  → Angle 180° (opposé)
```

## 🎯 Résumé

Votre simulateur combine :
- **Virages réalistes** : basés sur la physique (vitesse, inclinaison)
- **Gestion d'altitude** : palier + descente progressive
- **Deux modes** : direct ou interception axe
- **Visualisation 3D** : avec zoom, rotation, couleurs par phase

**C'est un outil complet et réaliste pour étudier les trajectoires d'approche ! 🛩️**
