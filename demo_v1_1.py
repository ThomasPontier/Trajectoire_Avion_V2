"""
Script de démonstration automatique - Version 1.1
Teste différents scénarios de vol
"""

import numpy as np
from environment import Environment
from aircraft import Aircraft, AircraftType
from trajectory_calculator import TrajectoryCalculator


def print_separator():
    print("\n" + "="*80 + "\n")


def demo_scenario(name, aircraft_type, position, speed, env):
    """Démontre un scénario de vol"""
    
    print(f"🛩️  SCÉNARIO : {name}")
    print(f"   Type d'avion : {AircraftType.get_specifications(aircraft_type)['name']}")
    print(f"   Position initiale : ({position[0]:.1f}, {position[1]:.1f}, {position[2]:.1f}) km")
    print(f"   Vitesse : {speed} km/h")
    
    # Créer l'avion
    aircraft = Aircraft(position=position, speed=speed, heading=90.0, aircraft_type=aircraft_type)
    
    print(f"   Pente max descente : {aircraft.max_descent_slope:.1f}°")
    
    # Calculer la trajectoire
    calculator = TrajectoryCalculator(env)
    trajectory, params = calculator.calculate_trajectory(aircraft)
    
    # Afficher les résultats
    print(f"\n   📊 RÉSULTATS :")
    print(f"   • Distance totale : {params['distance']:.2f} km")
    print(f"   • Temps de vol : {params['flight_time']*60:.1f} minutes")
    
    if 'level_flight_distance' in params:
        print(f"   • Vol en palier : {params['level_flight_distance']:.2f} km")
        print(f"   • Distance de descente : {params['descent_distance']:.2f} km")
        actual_slope = np.min(params['slope'])
        print(f"   • Pente de descente utilisée : {actual_slope:.2f}°")
        
        # Vérifier la contrainte
        if actual_slope >= aircraft.max_descent_slope:
            print(f"   ✅ Contrainte respectée !")
        else:
            print(f"   ❌ ATTENTION : Contrainte violée !")
    
    print(f"   • Altitude finale : {trajectory[-1, 2]:.3f} km (cible FAF : {env.faf_position[2]:.3f} km)")
    
    return trajectory, params


def main():
    """Programme principal de démonstration"""
    
    print("╔" + "="*78 + "╗")
    print("║" + " "*15 + "DÉMONSTRATION VERSION 1.1 - CONTRAINTE DE PENTE" + " "*15 + "║")
    print("╚" + "="*78 + "╝")
    
    # Créer l'environnement
    env = Environment(size_x=50, size_y=50, size_z=5)
    
    print(f"\n🏢 Aéroport : ({env.airport_position[0]:.1f}, {env.airport_position[1]:.1f}, {env.airport_position[2]:.1f}) km")
    print(f"🎯 Point FAF : ({env.faf_position[0]:.1f}, {env.faf_position[1]:.1f}, {env.faf_position[2]:.1f}) km")
    
    print_separator()
    
    # Scénario 1 : Avion commercial
    demo_scenario(
        "Descente normale - Avion Commercial",
        "commercial",
        np.array([10.0, 10.0, 3.0]),
        250.0,
        env
    )
    
    print_separator()
    
    # Scénario 2 : Avion cargo
    demo_scenario(
        "Descente douce - Avion Cargo",
        "cargo",
        np.array([10.0, 10.0, 3.0]),
        220.0,
        env
    )
    
    print_separator()
    
    # Scénario 3 : Avion léger
    demo_scenario(
        "Descente rapide - Avion Léger",
        "light",
        np.array([10.0, 10.0, 3.0]),
        180.0,
        env
    )
    
    print_separator()
    
    # Scénario 4 : Haute altitude
    demo_scenario(
        "Très haute altitude - Cargo",
        "cargo",
        np.array([0.0, 0.0, 5.0]),
        220.0,
        env
    )
    
    print_separator()
    
    # Scénario 5 : Distance courte
    demo_scenario(
        "Distance courte - Commercial",
        "commercial",
        np.array([35.0, 35.0, 3.0]),
        250.0,
        env
    )
    
    print_separator()
    
    print("\n✅ Démonstration terminée !")
    print("\n💡 Observations clés :")
    print("   1. Plus la pente max est raide, plus le vol en palier est long")
    print("   2. L'avion descend toujours au plus tard possible")
    print("   3. Les contraintes de pente sont respectées")
    print("   4. En cas de distance insuffisante, la pente est ajustée")
    

if __name__ == "__main__":
    main()
