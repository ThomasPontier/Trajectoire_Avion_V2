"""
Module de calcul de trajectoire optimale
"""

import numpy as np


class TrajectoryCalculator:
    """
    Classe pour calculer la trajectoire optimale vers le point FAF
    """
    
    def __init__(self, environment):
        """
        Initialise le calculateur de trajectoire
        
        Args:
            environment: Instance de la classe Environment
        """
        self.environment = environment
        
    def calculate_trajectory(self, aircraft):
        """
        Calcule la trajectoire optimale de l'avion vers le point FAF
        avec respect de la contrainte de pente maximale.
        
        Stratégie V1.1:
        - Vol en palier le plus longtemps possible
        - Descente au plus tard en respectant la pente max
        - Ligne droite horizontale vers le FAF
        
        Args:
            aircraft: Instance de la classe Aircraft
            
        Returns:
            tuple: (trajectory, parameters)
                - trajectory: Array numpy de positions [N x 3]
                - parameters: Dict avec les paramètres au cours du temps
        """
        
        start_pos = aircraft.position.copy()
        target_pos = self.environment.faf_position.copy()
        
        # Calculer la distance horizontale totale
        horizontal_distance = np.linalg.norm(target_pos[:2] - start_pos[:2])
        
        if horizontal_distance < 0.1:  # Si déjà au FAF horizontalement
            return self._vertical_trajectory(aircraft, start_pos, target_pos)
        
        # Différence d'altitude
        altitude_diff = target_pos[2] - start_pos[2]
        
        # Si on doit descendre et qu'on a une contrainte de pente
        if altitude_diff < 0 and aircraft.max_descent_slope is not None:
            return self._calculate_trajectory_with_slope_constraint(aircraft, start_pos, target_pos)
        else:
            # Trajectoire simple (ligne droite)
            return self._calculate_simple_trajectory(aircraft, start_pos, target_pos)
    
    def _calculate_trajectory_with_slope_constraint(self, aircraft, start_pos, target_pos):
        """
        Calcule une trajectoire avec vol en palier puis descente respectant la pente max.
        Utilise une transition progressive (smooth) entre les phases.
        
        Logique:
        1. Calculer la distance minimale nécessaire pour descendre avec la pente max
        2. Voler en palier jusqu'au point de début de transition
        3. Phase de transition progressive (courbe lisse)
        4. Descendre avec la pente maximale jusqu'au FAF
        
        Args:
            aircraft: Instance de la classe Aircraft
            start_pos: Position de départ [x, y, z]
            target_pos: Position cible (FAF) [x, y, z]
            
        Returns:
            tuple: (trajectory, parameters)
        """
        
        # Distance horizontale totale
        horizontal_distance = np.linalg.norm(target_pos[:2] - start_pos[:2])
        
        # Différence d'altitude (négative si descente)
        altitude_diff = target_pos[2] - start_pos[2]
        
        # Pente maximale de descente (en radians, valeur négative)
        max_descent_slope_rad = np.radians(aircraft.max_descent_slope)
        
        # Distance minimale nécessaire pour la descente avec la pente max
        # distance = altitude_diff / tan(slope)
        min_descent_distance = abs(altitude_diff / np.tan(max_descent_slope_rad))
        
        # Distance de transition (smooth) - environ 10% de la distance de descente ou 2 km min
        transition_distance = max(min(min_descent_distance * 0.15, 3.0), 1.0)
        
        # Vecteur de direction horizontal normalisé
        horizontal_direction = target_pos[:2] - start_pos[:2]
        horizontal_direction = horizontal_direction / np.linalg.norm(horizontal_direction)
        
        # Calculer les phases
        if min_descent_distance + transition_distance >= horizontal_distance:
            # Pas assez de distance: transition dès le départ
            level_flight_distance = 0.0
            transition_distance = min(transition_distance, horizontal_distance * 0.3)
            descent_distance = horizontal_distance - transition_distance
        else:
            # On peut voler en palier avant la transition
            level_flight_distance = horizontal_distance - min_descent_distance - transition_distance
            descent_distance = min_descent_distance
        
        # Nombre de points pour une trajectoire lisse (minimum 500 points, ou 1 point tous les 100m)
        min_points = 500
        points_per_km = 100  # 100 points par km pour un tracé très lisse
        n_points = max(min_points, int(horizontal_distance * points_per_km))
        
        # Calculer les indices pour chaque phase
        if horizontal_distance > 0:
            n_level = int(n_points * level_flight_distance / horizontal_distance)
            n_transition = int(n_points * transition_distance / horizontal_distance)
            n_descent = n_points - n_level - n_transition
        else:
            n_level = 0
            n_transition = 0
            n_descent = n_points
        
        # Créer la trajectoire avec les 3 phases
        trajectory = []
        current_distance = 0.0
        
        # Phase 1: Vol en palier
        if n_level > 0:
            for i in range(n_level):
                t = i / max(n_level - 1, 1)
                d = t * level_flight_distance
                pos = start_pos.copy()
                pos[:2] = start_pos[:2] + horizontal_direction * d
                pos[2] = start_pos[2]  # Altitude constante
                trajectory.append(pos)
                current_distance = d
        
        # Phase 2: Transition progressive (courbe smooth avec fonction cosinus)
        if n_transition > 0:
            for i in range(n_transition):
                t = i / max(n_transition - 1, 1)
                
                # Utiliser une fonction cosinus pour une transition douce
                # smooth_factor varie de 0 à 1 avec une courbe en S
                smooth_factor = (1 - np.cos(t * np.pi)) / 2
                
                # Distance horizontale
                d = level_flight_distance + t * transition_distance
                
                # Altitude avec transition progressive
                # De l'altitude de palier à l'altitude de début de descente linéaire
                z_start = start_pos[2]
                z_transition_end = start_pos[2] - (transition_distance * abs(np.tan(max_descent_slope_rad)))
                
                pos = start_pos.copy()
                pos[:2] = start_pos[:2] + horizontal_direction * d
                pos[2] = z_start + smooth_factor * (z_transition_end - z_start)
                trajectory.append(pos)
                current_distance = d
        
        # Phase 3: Descente linéaire
        if n_descent > 0:
            descent_start_distance = level_flight_distance + transition_distance
            descent_start_altitude = trajectory[-1][2] if len(trajectory) > 0 else start_pos[2]
            
            for i in range(n_descent):
                t = i / max(n_descent - 1, 1)
                d = descent_start_distance + t * descent_distance
                
                # Calcul de l'altitude pour atteindre exactement le FAF
                remaining_altitude = target_pos[2] - descent_start_altitude
                
                pos = start_pos.copy()
                pos[:2] = start_pos[:2] + horizontal_direction * d
                pos[2] = descent_start_altitude + t * remaining_altitude
                trajectory.append(pos)
        
        # S'assurer qu'on finit exactement au FAF
        if len(trajectory) > 0:
            trajectory[-1] = target_pos.copy()
        
        trajectory = np.array(trajectory)
        
        # Calculer les paramètres
        parameters = self._calculate_parameters(trajectory, aircraft.speed)
        parameters['level_flight_distance'] = level_flight_distance
        parameters['transition_distance'] = transition_distance
        parameters['descent_distance'] = descent_distance
        parameters['descent_start_index'] = n_level
        parameters['transition_end_index'] = n_level + n_transition
        parameters['n_points'] = n_points
        
        return trajectory, parameters
    
    def _calculate_simple_trajectory(self, aircraft, start_pos, target_pos):
        """
        Calcule une trajectoire simple en ligne droite (sans contrainte de pente)
        avec un nombre élevé de points pour un tracé lisse
        
        Args:
            aircraft: Instance de la classe Aircraft
            start_pos: Position de départ
            target_pos: Position cible
            
        Returns:
            tuple: (trajectory, parameters)
        """
        
        distance_vector = target_pos - start_pos
        distance = np.linalg.norm(distance_vector)
        
        # Nombre de points élevé pour trajectoire lisse (min 500 ou 100 points/km)
        min_points = 500
        points_per_km = 100
        n_points = max(min_points, int(distance * points_per_km))
        
        trajectory = np.zeros((n_points, 3))
        for i in range(n_points):
            t = i / (n_points - 1)
            trajectory[i] = start_pos + t * distance_vector
        
        parameters = self._calculate_parameters(trajectory, aircraft.speed)
        parameters['n_points'] = n_points
        
        return trajectory, parameters
    
    def _vertical_trajectory(self, aircraft, start_pos, target_pos):
        """
        Trajectoire purement verticale (déjà au-dessus du FAF)
        avec transition progressive
        
        Args:
            aircraft: Instance de la classe Aircraft
            start_pos: Position de départ
            target_pos: Position cible
            
        Returns:
            tuple: (trajectory, parameters)
        """
        
        altitude_diff = abs(target_pos[2] - start_pos[2])
        
        # Temps estimé pour la manœuvre verticale (vitesse réduite)
        vertical_speed = 10.0  # km/h pour la descente verticale
        
        # Nombre de points élevé pour une descente lisse
        n_points = max(300, int(altitude_diff * 200))
        
        trajectory = np.zeros((n_points, 3))
        
        # Utiliser une courbe smooth pour la descente verticale
        for i in range(n_points):
            t = i / (n_points - 1)
            # Fonction smooth (ease-in-out)
            smooth_t = t * t * (3.0 - 2.0 * t)
            trajectory[i] = start_pos + smooth_t * (target_pos - start_pos)
        
        parameters = self._calculate_parameters(trajectory, vertical_speed)
        parameters['n_points'] = n_points
        
        return trajectory, parameters
    
    def _calculate_parameters(self, trajectory, speed):
        """
        Calcule les paramètres de vol à partir d'une trajectoire
        
        Args:
            trajectory: Array numpy de positions [N x 3]
            speed: Vitesse de l'avion en km/h
            
        Returns:
            dict: Paramètres au cours du temps
        """
        
        n_points = len(trajectory)
        
        # Calculer les distances parcourues
        distances = np.zeros(n_points)
        for i in range(1, n_points):
            distances[i] = distances[i-1] + np.linalg.norm(trajectory[i] - trajectory[i-1])
        
        # Temps (en secondes)
        total_distance = distances[-1]
        if total_distance > 0:
            flight_time_hours = total_distance / speed
            time_array = np.linspace(0, flight_time_hours * 3600, n_points)
        else:
            time_array = np.zeros(n_points)
        
        # Altitude
        altitude_array = trajectory[:, 2]
        
        # Vitesse (constante)
        speed_array = np.full(n_points, speed)
        
        # Calculer la pente (en degrés)
        slope_array = np.zeros(n_points)
        for i in range(1, n_points):
            dz = trajectory[i, 2] - trajectory[i-1, 2]
            dx = np.linalg.norm(trajectory[i, :2] - trajectory[i-1, :2])
            if dx > 0:
                slope_array[i] = np.degrees(np.arctan(dz / dx))
            elif dz != 0:
                slope_array[i] = 90.0 if dz > 0 else -90.0
        
        slope_array[0] = slope_array[1] if n_points > 1 else 0
        
        return {
            'time': time_array,
            'altitude': altitude_array,
            'slope': slope_array,
            'speed': speed_array,
            'distance': total_distance,
            'flight_time': flight_time_hours if total_distance > 0 else 0
        }
    
    def calculate_trajectory_with_constraints(self, aircraft, max_slope=None, min_turn_radius=None):
        """
        Calcule la trajectoire avec des contraintes (pour versions futures)
        
        Args:
            aircraft: Instance de la classe Aircraft
            max_slope: Pente maximale en degrés (optionnel)
            min_turn_radius: Rayon de virage minimal en km (optionnel)
            
        Returns:
            tuple: (trajectory, parameters)
        """
        # TODO: Implémenter dans les versions futures
        # Pour l'instant, on utilise la trajectoire simple
        return self.calculate_trajectory(aircraft)
