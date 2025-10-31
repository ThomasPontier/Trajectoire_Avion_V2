# Historique des Versions

## Version 1.3.0 (2025-10-30)

### 🚀 Refonte majeure de la logique de trajectoire

#### 🧭 Trajectoire basée sur le vecteur vitesse
- **AVANT** : La trajectoire était calculée uniquement depuis la position vers le FAF (ligne droite)
- **MAINTENANT** : La trajectoire prend en compte le cap initial de l'avion
- **Impact** : L'avion ne peut plus "téléporter" sa direction, il doit virer physiquement

#### 🔄 Virage initial automatique
- **Nouveau comportement** : Si le cap ne pointe pas vers la cible (angle > 5°), un virage est calculé automatiquement
- **Mode trajectoire directe** : Virage pour pointer vers le FAF + ligne droite
- **Mode virages réalistes** : Virage tangent pour intercepter l'axe d'approche

#### 📐 Physique du vol améliorée
- Calcul du rayon de virage basé sur la vitesse et l'angle d'inclinaison max
- Arc de cercle précis pour le virage
- Respect des contraintes physiques (pas de changement instantané de direction)

#### 🎯 Clarification des deux modes
1. **☐ Virages désactivés** : Virage direct vers le FAF, puis ligne droite
2. **☑️ Virages activés** : Interception tangente de l'axe aéroport-FAF

### 🔧 Modifications techniques
- Ajout de `_calculate_trajectory_with_initial_turn()` dans `trajectory_calculator.py`
- Modification de `calculate_trajectory()` pour utiliser le cap initial
- Détection automatique de l'angle entre cap actuel et direction cible

### 📊 Impact utilisateur
- **Plus réaliste** : L'avion se comporte comme un vrai avion
- **Plus prévisible** : La flèche verte montre clairement où l'avion va virer
- **Configuration importante** : Le cap initial est maintenant crucial pour la trajectoire

---

## Version 1.2.1 (2025-10-30)

### ✨ Nouvelles fonctionnalités

#### 🔍 Navigation 3D améliorée
- **Barre d'outils interactive** ajoutée à la visualisation 3D
  - Zoom avant/arrière avec molette ou boutons
  - Rotation libre de la vue
  - Déplacement (pan) de la vue
  - Réinitialisation de la vue
  - Sauvegarde d'images
- **Axes fixes** : Les dimensions de l'espace aérien restent constantes lors du zoom

#### 🧭 Visualisation du cap initial
- **Flèche de direction** : Une flèche verte partant de l'avion indique son cap initial
- **Aide visuelle** : Indication claire (0°=Nord, 90°=Est, 180°=Sud, 270°=Ouest) dans l'interface
- **Cap modifiable** : L'utilisateur peut facilement modifier le cap initial de l'avion

#### 🎯 Variation de vitesse durant l'approche
- **Décélération progressive** : L'avion ralentit de sa vitesse de croisière à sa vitesse d'approche
- **Profil réaliste** : 
  - Vitesse constante sur les premiers 33% de l'approche
  - Décélération douce (fonction cosinus) sur les 67% restants
- **Rayon de virage dynamique** : Le rayon de virage s'adapte à la vitesse actuelle
- **Affichage des vitesses** : Vitesse initiale et vitesse d'approche affichées dans les résultats

### 🔧 Améliorations techniques
- Optimisation des messages de débogage (moins verbeux, plus informatifs)
- Correction de la gestion des gestionnaires de géométrie tkinter (grid/pack)
- Amélioration de la lisibilité du code

### 📊 Vitesses d'approche par type d'avion
- **Avion Léger** : 180 → 120 km/h
- **Avion Commercial** : 250 → 180 km/h
- **Avion Cargo** : 220 → 160 km/h

---

## Version 1.2.0 (2025-10-29)

### ✨ Virages réalistes
- Calcul de trajectoire avec rayon de courbure minimum
- Interception tangente de l'axe d'approche
- Respect des contraintes physiques (vitesse, angle d'inclinaison)
- Visualisation multi-phases (virage, approche, descente)
- Mode sélectionnable via checkbox

### 📐 Formule de rayon de virage
```
R_min = V² / (g × tan(φ_max))
```

---

## Version 1.1+ (2025-10-28)

### Interface à onglets
- Organisation en 3 onglets (Environnement, Obstacles, Avion)
- Environnement personnalisable (dimensions X, Y, Z)
- Gestion des obstacles cylindriques
- Axe d'approche visualisé
- Sauvegarde persistante (config.json)

---

## Version 1.1 (2025-10-27)

### Types d'avions
- 3 types : Léger, Commercial, Cargo
- Contraintes de pente spécifiques
- Vol en palier optimisé
- Descente au plus tard

---

## Version 1.0 (2025-10-26)

### Version initiale
- Calcul de trajectoire basique
- Visualisation 3D
- Graphiques d'altitude et pente
- Interface simple
