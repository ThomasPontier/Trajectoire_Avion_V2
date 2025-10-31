# Guide de Résolution des Problèmes

## ⚠️ Problèmes de Trajectoire

### Version 1.3 : Nouvelle logique de calcul

Depuis la V1.3, **toutes les trajectoires** utilisent le cap initial de l'avion. L'avion vire automatiquement si son cap ne pointe pas vers la cible.

### L'avion ne vire pas du tout

**Cause** : Le cap initial pointe déjà vers le FAF (angle < 5°)

**Solution** : Changez le cap initial dans l'interface
- Essayez 0° (Nord), 90° (Est), 180° (Sud), ou 270° (Ouest)
- La flèche verte vous montre où l'avion pointe

### Message : "Impossible de calculer un virage tangent -> trajectoire directe"

Ce message apparaît uniquement en **mode virages réalistes** (☑️ activé) quand l'algorithme ne peut pas calculer l'interception tangente de l'axe d'approche. Le mode trajectoire directe est alors utilisé.

### Causes possibles et solutions

#### 1. 🎯 L'avion est déjà proche de l'axe d'approche
**Solution** : Positionnez l'avion plus loin de l'axe d'approche
- Essayez avec un avion positionné sur le côté (par exemple X=10 si le FAF est à X=25)
- Augmentez la distance perpendiculaire à l'axe

#### 2. 📐 Le cap initial pointe déjà vers le FAF
**Solution** : Changez le cap initial de l'avion
- Si l'axe d'approche va vers l'Est (90°), essayez un cap à 45° ou 135°
- Plus le cap est différent de l'axe, plus le virage sera visible
- Exemple : Axe à 90°, essayez cap à 180° (Sud) ou 0° (Nord)

#### 3. ⚡ Rayon de virage trop grand
Le rayon de virage dépend de la vitesse : R = V²/(g×tan(φ))

**Solution** :
- Réduisez la vitesse de l'avion (ex: 150 km/h au lieu de 250 km/h)
- Utilisez un avion léger (angle d'inclinaison max plus grand = rayon plus petit)
- Augmentez la taille de l'espace aérien

#### 4. 🗺️ Configuration géométrique difficile
**Solution** : Configuration de test recommandée
```
Environnement:
- Taille: 50 x 50 x 5 km
- Aéroport: X=5, Y=25, Z=0
- FAF: X=20, Y=25, Z=1

Avion:
- Type: Léger
- Position: X=40, Y=10, Z=3
- Vitesse: 180 km/h
- Cap: 270° (Ouest)

Options:
☑️ Virages réalistes activé
```

### Comment vérifier que ça fonctionne

1. ✅ **Flèche verte** : Vérifiez que la flèche de direction de l'avion pointe dans une direction différente de l'axe d'approche
2. ✅ **Message de succès** : Cherchez "✓ Virage calculé:" dans la console
3. ✅ **Trajectoire cyan** : Le début de la trajectoire doit être en cyan (phase de virage)
4. ✅ **Transition** : La trajectoire doit changer de couleur (cyan → vert) au point d'interception

### Exemple de configuration fonctionnelle

```
Cas 1 - Approche de côté:
Aéroport: (5, 25, 0)
FAF: (20, 25, 1) 
Avion: (40, 10, 3) - Cap 270° (Ouest)
→ L'avion vire pour intercepter l'axe qui va d'Ouest en Est

Cas 2 - Approche en diagonale:
Aéroport: (10, 10, 0)
FAF: (30, 30, 1)
Avion: (40, 10, 3) - Cap 0° (Nord)
→ L'avion vire pour intercepter l'axe diagonal

Cas 3 - Approche opposée:
Aéroport: (5, 25, 0)
FAF: (20, 25, 1)
Avion: (10, 25, 3) - Cap 90° (Est)
→ L'avion vire en arc pour rejoindre l'axe par l'arrière
```

## 🔍 Utilisation du zoom

- **Molette de souris** : Zoom avant/arrière (si disponible)
- **Boutons de la barre d'outils** :
  - 🏠 : Réinitialiser la vue
  - 📐 : Zoomer sur une zone (cliquer-glisser)
  - ✋ : Déplacer la vue (pan)
  - 🔄 : Rotation 3D (maintenir clic gauche et bouger la souris)

## 🧭 Convention de cap

- **0°** = Nord (axe Y positif)
- **90°** = Est (axe X positif)
- **180°** = Sud (axe Y négatif)
- **270°** = Ouest (axe X négatif)

La flèche verte sur l'avion montre toujours son cap initial.

## 💡 Conseils pour de meilleurs résultats

1. **Commencez simple** : Utilisez la configuration de test recommandée ci-dessus
2. **Observez la flèche** : Elle doit pointer loin de l'axe d'approche
3. **Vitesse modérée** : 150-200 km/h fonctionne mieux pour les tests
4. **Type léger** : Plus maniable, meilleur pour visualiser les virages
5. **Espace suffisant** : Minimum 40-50 km pour voir les virages complets
