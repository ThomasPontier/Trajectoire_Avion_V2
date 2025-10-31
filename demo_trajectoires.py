"""
Démonstration des capacités du simulateur
Virages + Variation d'altitude
"""

from environment import Environment
from aircraft import Aircraft
from trajectory_calculator import TrajectoryCalculator
import numpy as np

def print_phase_analysis(trajectory, params):
    """Analyse les différentes phases de la trajectoire"""
    print(f"\n   📊 Analyse détaillée :")
    print(f"   └─ Points totaux : {len(trajectory)}")
    
    if 'turn_angle' in params:
        print(f"   └─ 🔄 Phase virage : angle {params['turn_angle']:.1f}°, rayon {params['turn_radius']:.3f} km")
    
    if 'level_flight_distance' in params:
        print(f"   └─ 🛫 Phase palier : {params['level_flight_distance']:.2f} km")
        print(f"   └─ 🛬 Phase descente : {params['descent_distance']:.2f} km")
    
    # Analyser les variations d'altitude
    altitudes = trajectory[:, 2]
    alt_min, alt_max = np.min(altitudes), np.max(altitudes)
    alt_diff = alt_max - alt_min
    
    print(f"   └─ 📏 Altitude : {alt_max:.2f} → {alt_min:.2f} km (Δ={alt_diff:.2f} km)")
    
    # Analyser les virages dans le plan horizontal
    if len(trajectory) > 10:
        # Calculer la direction initiale et finale
        start_dir = trajectory[10, :2] - trajectory[0, :2]
        end_dir = trajectory[-1, :2] - trajectory[-10, :2]
        start_dir = start_dir / np.linalg.norm(start_dir)
        end_dir = end_dir / np.linalg.norm(end_dir)
        
        # Angle entre directions
        cos_angle = np.dot(start_dir, end_dir)
        angle = np.degrees(np.arccos(np.clip(cos_angle, -1, 1)))
        
        print(f"   └─ 🧭 Changement direction : {angle:.1f}°")

print("=" * 70)
print("🛩️  DÉMONSTRATION : VIRAGES + VARIATION D'ALTITUDE")
print("=" * 70)

# Configuration de l'environnement
env = Environment(size_x=50, size_y=50, size_z=5)
env.airport_position = np.array([5, 25, 0])
env.faf_position = np.array([20, 25, 1])

calc = TrajectoryCalculator(env)

# ==================== SCÉNARIO 1 ====================
print("\n" + "─" * 70)
print("📋 SCÉNARIO 1 : Virage à droite + Descente modérée")
print("─" * 70)
print("Configuration :")
print("   • Position : (40, 10, 3) - En haut à droite")
print("   • Cap : 180° (Sud) - Pointe vers le bas")
print("   • Altitude : 3 km → 1 km (descente de 2 km)")
print("   • FAF à : (20, 25, 1)")

aircraft1 = Aircraft(
    position=np.array([40, 10, 3]),
    speed=180,
    heading=180,
    aircraft_type="light"
)

trajectory1, params1 = calc.calculate_trajectory(aircraft1)
print(f"\n✓ Trajectoire calculée avec succès")
print_phase_analysis(trajectory1, params1)

# ==================== SCÉNARIO 2 ====================
print("\n" + "─" * 70)
print("📋 SCÉNARIO 2 : Demi-tour complet + Grande descente")
print("─" * 70)
print("Configuration :")
print("   • Position : (25, 40, 5) - En haut au centre")
print("   • Cap : 0° (Nord) - Pointe vers le haut")
print("   • Altitude : 5 km → 1 km (descente de 4 km)")
print("   • FAF à : (20, 25, 1)")

aircraft2 = Aircraft(
    position=np.array([25, 40, 5]),
    speed=180,
    heading=0,
    aircraft_type="light"
)

trajectory2, params2 = calc.calculate_trajectory(aircraft2)
print(f"\n✓ Trajectoire calculée avec succès")
print_phase_analysis(trajectory2, params2)

# ==================== SCÉNARIO 3 ====================
print("\n" + "─" * 70)
print("📋 SCÉNARIO 3 : Virage à gauche + Montée")
print("─" * 70)
print("Configuration :")
print("   • Position : (30, 15, 0.5) - Bas, à droite")
print("   • Cap : 90° (Est) - Pointe vers la droite")
print("   • Altitude : 0.5 km → 1 km (montée de 0.5 km)")
print("   • FAF à : (20, 25, 1)")

aircraft3 = Aircraft(
    position=np.array([30, 15, 0.5]),
    speed=180,
    heading=90,
    aircraft_type="light"
)

trajectory3, params3 = calc.calculate_trajectory(aircraft3)
print(f"\n✓ Trajectoire calculée avec succès")
print_phase_analysis(trajectory3, params3)

# ==================== SCÉNARIO 4 ====================
print("\n" + "─" * 70)
print("📋 SCÉNARIO 4 : Virage serré (haute vitesse) + Descente rapide")
print("─" * 70)
print("Configuration :")
print("   • Position : (40, 35, 4) - En haut à droite")
print("   • Cap : 45° (Nord-Est) - Oblique")
print("   • Vitesse : 250 km/h (avion commercial)")
print("   • Altitude : 4 km → 1 km (descente de 3 km)")

aircraft4 = Aircraft(
    position=np.array([40, 35, 4]),
    speed=250,
    heading=45,
    aircraft_type="commercial"  # Rayon de virage plus grand
)

trajectory4, params4 = calc.calculate_trajectory(aircraft4)
print(f"\n✓ Trajectoire calculée avec succès")
print_phase_analysis(trajectory4, params4)

# ==================== SCÉNARIO 5 ====================
print("\n" + "─" * 70)
print("📋 SCÉNARIO 5 : Pas de virage, descente seulement")
print("─" * 70)
print("Configuration :")
print("   • Position : (25, 25, 3) - Aligné sur l'axe")
print("   • Cap : 270° (Ouest) - Pointe vers le FAF")
print("   • Altitude : 3 km → 1 km (descente de 2 km)")

aircraft5 = Aircraft(
    position=np.array([25, 25, 3]),
    speed=180,
    heading=270,
    aircraft_type="light"
)

trajectory5, params5 = calc.calculate_trajectory(aircraft5)
print(f"\n✓ Trajectoire calculée avec succès")
print_phase_analysis(trajectory5, params5)

# ==================== RÉSUMÉ ====================
print("\n" + "=" * 70)
print("📊 RÉSUMÉ DES CAPACITÉS")
print("=" * 70)
print("\n✅ Le simulateur peut gérer :")
print("   • Virages de 0° à 180° (y compris demi-tours)")
print("   • Descentes progressives (respect pente max)")
print("   • Montées légères")
print("   • Combinaisons virage + altitude simultanées")
print("   • Différents types d'avions (rayons de virage différents)")
print("   • Vitesses variables (impact sur rayon de virage)")
print("\n✅ Phases de vol identifiées :")
print("   🔵 Phase virage : altitude constante, changement direction")
print("   🟢 Phase palier : direction constante, altitude constante")
print("   🟠 Phase descente : direction constante, altitude variable")
print("\n✅ Contraintes respectées :")
print("   • Rayon de virage minimum (physique)")
print("   • Pente maximale de descente (type d'avion)")
print("   • Continuité de la trajectoire (pas de sauts)")

print("\n" + "=" * 70)
print("🎉 Démonstration terminée !")
print("=" * 70)
print("\n💡 Conseil : Lancez main.py pour visualiser en 3D avec zoom !")
print("   - Utilisez la barre d'outils pour zoomer et pivoter")
print("   - La flèche verte montre le cap initial")
print("   - Les couleurs indiquent les phases (cyan/vert/orange)")
