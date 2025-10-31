# 📋 Configurations d'Exemple

Ce fichier contient des configurations testées et fonctionnelles pour le simulateur.

## 🎯 Configuration Recommandée par Défaut

**Objectif** : Démonstration simple avec virage visible

```json
{
    "environment": {
        "size_x": 50.0,
        "size_y": 50.0,
        "size_z": 5.0,
        "airport": {
            "x": 5.0,
            "y": 25.0,
            "z": 0.0
        },
        "faf": {
            "x": 20.0,
            "y": 25.0,
            "z": 1.0
        }
    },
    "aircraft": {
        "type": "light",
        "position": {
            "x": 40.0,
            "y": 10.0,
            "z": 3.0
        },
        "speed": 180.0,
        "heading": 270.0
    }
}
```

**Résultat attendu** : Virage à gauche + descente progressive

---

## 🔄 Configuration : Demi-Tour Spectaculaire

**Objectif** : Virage de 180° (demi-cercle complet)

```json
{
    "environment": {
        "size_x": 50.0,
        "size_y": 50.0,
        "size_z": 5.0,
        "airport": {
            "x": 5.0,
            "y": 25.0,
            "z": 0.0
        },
        "faf": {
            "x": 20.0,
            "y": 25.0,
            "z": 1.0
        }
    },
    "aircraft": {
        "type": "light",
        "position": {
            "x": 25.0,
            "y": 40.0,
            "z": 4.0
        },
        "speed": 180.0,
        "heading": 0.0
    }
}
```

**Résultat** : L'avion pointe Nord (0°), doit aller vers le Sud-Ouest → Demi-tour !

---

## ✈️ Configuration : Approche Directe

**Objectif** : Pas de virage, descente uniquement

```json
{
    "environment": {
        "size_x": 50.0,
        "size_y": 50.0,
        "size_z": 5.0,
        "airport": {
            "x": 5.0,
            "y": 25.0,
            "z": 0.0
        },
        "faf": {
            "x": 20.0,
            "y": 25.0,
            "z": 1.0
        }
    },
    "aircraft": {
        "type": "light",
        "position": {
            "x": 30.0,
            "y": 25.0,
            "z": 3.0
        },
        "speed": 180.0,
        "heading": 270.0
    }
}
```

**Résultat** : Ligne droite avec descente progressive (pas de virage)

---

## 🛫 Configuration : Approche Cargo Lourd

**Objectif** : Grand rayon de virage (avion cargo, haute vitesse)

```json
{
    "environment": {
        "size_x": 50.0,
        "size_y": 50.0,
        "size_z": 5.0,
        "airport": {
            "x": 5.0,
            "y": 25.0,
            "z": 0.0
        },
        "faf": {
            "x": 20.0,
            "y": 25.0,
            "z": 1.0
        }
    },
    "aircraft": {
        "type": "cargo",
        "position": {
            "x": 40.0,
            "y": 35.0,
            "z": 4.0
        },
        "speed": 220.0,
        "heading": 45.0
    }
}
```

**Résultat** : Grand arc de cercle (rayon > 0.8 km), descente douce

---

## 🌟 Configuration : Mode Virages Réalistes

**Objectif** : Interception tangente de l'axe d'approche

```json
{
    "environment": {
        "size_x": 50.0,
        "size_y": 50.0,
        "size_z": 5.0,
        "airport": {
            "x": 5.0,
            "y": 25.0,
            "z": 0.0
        },
        "faf": {
            "x": 20.0,
            "y": 25.0,
            "z": 1.0
        }
    },
    "aircraft": {
        "type": "commercial",
        "position": {
            "x": 35.0,
            "y": 10.0,
            "z": 3.0
        },
        "speed": 250.0,
        "heading": 225.0
    }
}
```

**Résultat** : ☑️ Activer "Virages réalistes" → Interception tangente de l'axe

---

## 🚧 Configuration : Avec Obstacles

**Objectif** : Environnement avec zones interdites

```json
{
    "environment": {
        "size_x": 50.0,
        "size_y": 50.0,
        "size_z": 5.0,
        "airport": {
            "x": 5.0,
            "y": 25.0,
            "z": 0.0
        },
        "faf": {
            "x": 20.0,
            "y": 25.0,
            "z": 1.0
        }
    },
    "cylinders": [
        {
            "x": 30.0,
            "y": 20.0,
            "radius": 3.0,
            "height": 4.0
        },
        {
            "x": 35.0,
            "y": 28.0,
            "radius": 2.0,
            "height": 3.5
        }
    ],
    "aircraft": {
        "type": "light",
        "position": {
            "x": 45.0,
            "y": 15.0,
            "z": 3.5
        },
        "speed": 180.0,
        "heading": 270.0
    }
}
```

**Note** : L'évitement d'obstacles n'est pas encore implémenté (V1.4+)

---

## ⚠️ Erreurs Courantes à Éviter

### ❌ Configuration Aberrante (Exemple à NE PAS utiliser)

```json
{
    "environment": {
        "size_x": 300.0,
        "size_y": 300.0,
        "airport": {
            "x": 300.0,
            "y": 300.0
        },
        "faf": {
            "x": 290.0,
            "y": 296.0
        }
    },
    "aircraft": {
        "position": {
            "x": 200.0,
            "y": 20.0
        }
    }
}
```

**Problèmes** :
- Espace trop grand (300 km !)
- Aéroport hors limites (300, 300)
- FAF très proche de l'aéroport (10 km)
- Avion très éloigné (>280 km)
- Cercle de virage trop petit pour atteindre l'axe

### ✅ Correction

```json
{
    "environment": {
        "size_x": 50.0,        // Taille raisonnable
        "size_y": 50.0,
        "airport": {
            "x": 5.0,          // Coin gauche
            "y": 25.0          // Centre vertical
        },
        "faf": {
            "x": 20.0,         // 15 km avant aéroport
            "y": 25.0          // Aligné
        }
    },
    "aircraft": {
        "position": {
            "x": 40.0,         // Dans l'espace
            "y": 10.0          // Distance raisonnable
        }
    }
}
```

---

## 📐 Règles pour une Bonne Configuration

### Taille de l'Espace
```
Recommandé : 40-60 km (taille_x et taille_y)
Minimum : 20 km
Maximum pratique : 100 km
```

### Position Aéroport
```
Recommandé : 10-20% du bord (ex: x=5 si taille=50)
À éviter : Coller aux bords (x=0) ou hors limites (x > taille)
```

### Position FAF
```
Recommandé : 10-20 km avant l'aéroport
Altitude : 0.5-2.0 km
Alignement : Même axe Y que l'aéroport (approche droite)
```

### Position Avion Initial
```
Distance au FAF : 15-40 km
Altitude : 2-5 km (pour avoir de la marge de descente)
Cap : Varié (0-360°) pour tester différents virages
```

### Vitesses
```
Avion léger : 150-200 km/h
Avion commercial : 200-270 km/h
Cargo : 180-240 km/h
```

---

## 🎮 Comment Utiliser Ces Configurations

### Méthode 1 : Copier dans config.json
```bash
# Sauvegardez l'actuel
cp config.json config.json.backup

# Copiez la configuration souhaitée
# Remplacez le contenu de config.json

# Lancez l'application
python main.py
```

### Méthode 2 : Via l'Interface
```
1. Lancez main.py
2. Onglet "Environnement" : Entrez les valeurs
3. Cliquez "Appliquer Configuration"
4. Onglet "Avion" : Positionnez l'avion
5. Cliquez "Valider Position Avion"
6. Cliquez "Lancer Simulation"
```

### Méthode 3 : Réinitialisation
```
1. Supprimez config.json
2. Relancez main.py
3. Configuration par défaut rechargée
```

---

## 📚 Références

- **Guide Complet** : `GUIDE_UTILISATION.md`
- **Dépannage** : `TROUBLESHOOTING.md`
- **Changelog** : `CHANGELOG.md`
- **Tests** : `python demo_trajectoires.py`

---

**Version** : 1.3.0  
**Date** : 30 octobre 2025
