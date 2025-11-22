"""
Module de calcul de trajectoire optimale
"""

import numpy as np
from aircraft import Aircraft


class TrajectoryCalculator:
    """
    Classe pour calculer la trajectoire optimale vers le point FAF
    """
    
    def __init__(self, environment):
        """Initialise le calculateur avec l'environnement (aéroport, FAF, obstacles)."""
        self.environment = environment
        self.retry_trajectories = []  # Stockage des trajectoires de tentatives
        self.retry_trajectories_info = []  # Informations sur chaque tentative
        
    def calculate_trajectory(self, aircraft, cylinders=None):
        """
        Calcule la trajectoire optimale vers le FAF avec alignement progressif sur l'axe de la piste.
        Mode virages simplifiés : vol initial dans le cap, virage pour s'aligner, suivi de l'axe avec
        descente et évitement automatique des obstacles.
        """
        
        if cylinders is None:
            cylinders = []
        
        start_pos = aircraft.position.copy()
        faf_pos = self.environment.faf_position.copy()
        airport_pos = self.environment.airport_position.copy()
        
        runway_axis = airport_pos[:2] - faf_pos[:2]
        runway_axis_distance = np.linalg.norm(runway_axis)
        
        if runway_axis_distance < 0.1:
            return self._calculate_simple_trajectory(aircraft, start_pos, faf_pos)
        
        runway_direction = runway_axis / runway_axis_distance
        
        # Direction actuelle de l'avion
        heading_rad = np.radians(aircraft.heading)
        current_direction = np.array([np.sin(heading_rad), np.cos(heading_rad)])
        
        cos_angle = np.dot(current_direction, runway_direction)
        angle_to_runway = np.degrees(np.arccos(np.clip(cos_angle, -1.0, 1.0)))
        
        horizontal_distance = np.linalg.norm(faf_pos[:2] - start_pos[:2])
        if horizontal_distance < 0.1:
            return self._vertical_trajectory(aircraft, start_pos, faf_pos)
        
        intercept_point = self._calculate_runway_intercept_point(
            start_pos[:2], current_direction, airport_pos[:2], 
            faf_pos[:2], runway_direction, angle_to_runway
        )
        
        # Construire la trajectoire en 2 phases avec évitement d'obstacles
        return self._build_trajectory_with_runway_alignment(
            aircraft, start_pos, intercept_point, faf_pos, 
            current_direction, runway_direction, cylinders
        )
    
    
    def _calculate_simple_trajectory(self, aircraft, start_pos, target_pos):
        """
        Trajectoire directe en ligne droite avec haute densité de points pour un tracé lisse.
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
    
    def _calculate_runway_intercept_point(self, start_pos, current_dir, airport_pos, 
                                          faf_pos, runway_dir, angle_to_runway):
        """
        Calcule le point d'interception optimal sur l'axe piste en projetant la position actuelle
        et en ajustant selon l'angle et la distance pour un alignement progressif avant le FAF.
        """
        
        # Projection orthogonale de la position actuelle sur l'axe de la piste
        vec_to_aircraft = start_pos - airport_pos
        projection_dist = np.dot(vec_to_aircraft, runway_dir)
        closest_point = airport_pos + projection_dist * runway_dir
        
        # Distance perpendiculaire à l'axe
        perp_distance = np.linalg.norm(start_pos - closest_point)
        
        # Distance le long de l'axe jusqu'au FAF
        runway_length = np.linalg.norm(faf_pos - airport_pos)
        distance_to_faf_on_axis = runway_length - projection_dist
        
        # Calculer la distance nécessaire pour s'aligner progressivement
        # Plus l'angle est grand, plus on a besoin de distance
        alignment_distance = max(perp_distance * 2, angle_to_runway * 0.1, 3.0)
        
        # Le point d'interception doit être JUSTE AVANT le FAF
        # On veut que l'avion soit aligné en arrivant au FAF
        # Donc on positionne l'interception à FAF - petite marge de sécurité
        safety_margin = 0.5  # 500m avant le FAF pour être bien aligné
        target_projection = runway_length - safety_margin
        
        # Mais si on est trop loin, on prend un point intermédiaire
        # pour permettre un alignement plus progressif
        if projection_dist < runway_length * 0.3:
            # Si on est loin en arrière, on vise 80-95% du chemin
            target_projection = min(
                projection_dist + alignment_distance,
                runway_length * 0.95
            )
        
        intercept_point = airport_pos + target_projection * runway_dir
        
        return intercept_point
    
    def _build_trajectory_with_runway_alignment(self, aircraft, start_pos, intercept_point, 
                                                 faf_pos, current_dir, runway_dir, cylinders=None):
        """
        Construit une trajectoire en 2 phases : vol initial dans le cap puis virage progressif
        jusqu'au FAF avec alignement sur l'axe piste, gestion altitude/pente et évitement d'obstacles.
        """
        
        if cylinders is None:
            cylinders = []
        
        total_distance_to_faf = np.linalg.norm(faf_pos[:2] - start_pos[:2])
        initial_flight_dist = np.clip(total_distance_to_faf * 0.20, 1.0, 5.0)
        initial_end_point = start_pos[:2] + current_dir * initial_flight_dist
        
        altitude_start, altitude_end = start_pos[2], faf_pos[2]
        altitude_diff = altitude_end - altitude_start
        max_descent_slope_rad = np.radians(aircraft.max_descent_slope)
        min_descent_distance = abs(altitude_diff / np.tan(abs(max_descent_slope_rad)))
        transition_distance = max(min(min_descent_distance * 0.50, 12.0), 3.0)
        total_descent_distance = min_descent_distance + transition_distance
        
        if total_descent_distance >= total_distance_to_faf:
            level_flight_distance = 0.0
            transition_distance = min(transition_distance, total_distance_to_faf * 0.3)
            descent_distance = total_distance_to_faf - transition_distance
        else:
            level_flight_distance = total_distance_to_faf - total_descent_distance
            descent_distance = min_descent_distance
        
        # Construire les segments
        segments = []
        
        # Segment 1: Vol initial en ligne droite
        n_initial = max(50, int(initial_flight_dist * 100))
        initial_segment = np.zeros((n_initial, 3))
        for i in range(n_initial):
            t = i / (n_initial - 1)
            pos_2d = start_pos[:2] + t * initial_flight_dist * current_dir
            initial_segment[i] = [pos_2d[0], pos_2d[1], start_pos[2]]
        
        segments.append(initial_segment)
        
        # Segment 2: Virage progressif jusqu'au FAF avec évitement d'obstacles
        # Détecter les obstacles sur le trajet et créer des waypoints de contournement
        waypoints_2d = [initial_end_point]
        
        if cylinders:
            # Calculer les waypoints de contournement
            avoidance_waypoints = self._calculate_avoidance_waypoints(
                initial_end_point, faf_pos[:2], cylinders, start_pos[2]
            )
            waypoints_2d.extend(avoidance_waypoints)
        
        waypoints_2d.append(faf_pos[:2])
        
        print(f"   🛤️  Trajectoire avec {len(waypoints_2d)} points de passage")
        
        # Construire des courbes de Bézier entre chaque paire de waypoints
        altitude_start = start_pos[2]
        altitude_end = faf_pos[2]
        
        for wp_idx in range(len(waypoints_2d) - 1):
            wp_start = waypoints_2d[wp_idx]
            wp_end = waypoints_2d[wp_idx + 1]
            
            segment_distance = np.linalg.norm(wp_end - wp_start)
            n_segment = max(100, int(segment_distance * 150))
            
            # Direction entre waypoints
            seg_dir = (wp_end - wp_start) / segment_distance if segment_distance > 0.01 else np.array([1, 0])
            
            # Points de contrôle pour cette section
            P0_seg = wp_start
            P3_seg = wp_end
            
            # Si c'est le premier segment, utiliser la direction initiale
            if wp_idx == 0:
                P1_seg = P0_seg + current_dir * (segment_distance * 0.35)
            else:
                # Direction du segment précédent pour continuité tangente
                prev_dir = (wp_start - waypoints_2d[wp_idx - 1])
                if np.linalg.norm(prev_dir) > 0.01:
                    prev_dir = prev_dir / np.linalg.norm(prev_dir)
                else:
                    prev_dir = seg_dir
                P1_seg = P0_seg + prev_dir * (segment_distance * 0.35)
            
            # Si c'est le dernier segment, utiliser la direction finale (runway)
            if wp_idx == len(waypoints_2d) - 2:
                P2_seg = P3_seg - runway_dir * (segment_distance * 0.35)
            else:
                # Direction vers le prochain waypoint pour continuité
                next_dir = (waypoints_2d[wp_idx + 2] - wp_end)
                if np.linalg.norm(next_dir) > 0.01:
                    next_dir = next_dir / np.linalg.norm(next_dir)
                else:
                    next_dir = seg_dir
                P2_seg = P3_seg - next_dir * (segment_distance * 0.35)
            
            # Courbe de Bézier pour ce segment
            segment_array = np.zeros((n_segment, 3))
            total_distance = np.linalg.norm(faf_pos[:2] - initial_end_point)
            dist_so_far = sum([np.linalg.norm(waypoints_2d[i+1] - waypoints_2d[i]) 
                              for i in range(wp_idx)])
            
            for i in range(n_segment):
                t_local = i / (n_segment - 1)
                # Position 2D avec Bézier cubique
                pos_2d = ((1-t_local)**3 * P0_seg + 
                         3*(1-t_local)**2*t_local * P1_seg + 
                         3*(1-t_local)*t_local**2 * P2_seg + 
                         t_local**3 * P3_seg)
                
                # ALTITUDE avec respect de la pente maximale
                # Distance parcourue depuis le début du virage (après vol initial)
                current_distance = dist_so_far + t_local * segment_distance
                
                if current_distance < level_flight_distance:
                    # Phase 1: Vol en palier
                    altitude = altitude_start
                    
                elif current_distance < level_flight_distance + transition_distance:
                    # Phase 2: Transition ULTRA-progressive avec super-smoothstep (septième degré)
                    transition_progress = (current_distance - level_flight_distance) / transition_distance
                    
                    # Super-smoothstep (7ème degré) : dérivées 1ère ET 2ème nulles aux extrémités
                    # f(t) = -20t^7 + 70t^6 - 84t^5 + 35t^4
                    # Cette fonction garantit une transition IMPERCEPTIBLE
                    t = transition_progress
                    smooth_t = -20*t**7 + 70*t**6 - 84*t**5 + 35*t**4
                    
                    # Altitude descend progressivement pendant la transition
                    transition_altitude_drop = (transition_distance * abs(np.tan(max_descent_slope_rad)))
                    altitude = altitude_start - smooth_t * transition_altitude_drop
                    
                else:
                    # Phase 3: Descente linéaire avec pente maximale
                    descent_progress = current_distance - level_flight_distance - transition_distance
                    transition_altitude_drop = (transition_distance * abs(np.tan(max_descent_slope_rad)))
                    descent_altitude_drop = descent_progress * abs(np.tan(max_descent_slope_rad))
                    
                    altitude = altitude_start - transition_altitude_drop - descent_altitude_drop
                    
                    # S'assurer qu'on ne descend pas en dessous du FAF
                    altitude = max(altitude, altitude_end)
                
                segment_array[i] = [pos_2d[0], pos_2d[1], altitude]
            
            segments.append(segment_array)
        
        # Combiner tous les segments
        trajectory = np.vstack(segments)
        
        # S'assurer que le dernier point est exactement au FAF avec transition douce
        # Faire une transition douce sur les derniers points vers le FAF
        n_smooth_final = min(100, len(trajectory) // 20)  # Points pour transition finale
        if n_smooth_final > 0:
            for i in range(n_smooth_final):
                idx = len(trajectory) - n_smooth_final + i
                if idx >= 0:
                    t = i / (n_smooth_final - 1)
                    # Transition progressive vers FAF en position ET en altitude
                    trajectory[idx][:2] = (1 - t) * trajectory[idx][:2] + t * faf_pos[:2]
                    trajectory[idx][2] = (1 - t) * trajectory[idx][2] + t * faf_pos[2]
        
        # Dernière position exactement au FAF
        trajectory[-1] = faf_pos
        
        if cylinders:
            has_collision, colliding_indices, first_collision_idx = self._check_trajectory_collision(trajectory, cylinders)
            
            if has_collision:
                self.retry_trajectories = []
                self.retry_trajectories_info = []
                
                for attempt in range(5):
                    safety_factor = 2.0 + attempt * 0.5
                    
                    # Recalculer les waypoints avec marge augmentée
                    waypoints_2d_retry = [initial_end_point]
                    avoidance_waypoints_retry = self._calculate_avoidance_waypoints_with_margin(
                        initial_end_point, faf_pos[:2], cylinders, start_pos[2], safety_factor
                    )
                    waypoints_2d_retry.extend(avoidance_waypoints_retry)
                    waypoints_2d_retry.append(faf_pos[:2])
                    
                    # Reconstruire la trajectoire avec ces nouveaux waypoints
                    segments_retry = [initial_segment]
                    
                    for wp_idx in range(len(waypoints_2d_retry) - 1):
                        wp_start = waypoints_2d_retry[wp_idx]
                        wp_end = waypoints_2d_retry[wp_idx + 1]
                        
                        segment_distance = np.linalg.norm(wp_end - wp_start)
                        n_segment = max(100, int(segment_distance * 150))
                        
                        seg_dir = (wp_end - wp_start) / segment_distance if segment_distance > 0.01 else np.array([1, 0])
                        
                        P0_seg = wp_start
                        P3_seg = wp_end
                        
                        if wp_idx == 0:
                            P1_seg = P0_seg + current_dir * (segment_distance * 0.35)
                        else:
                            prev_dir = (wp_start - waypoints_2d_retry[wp_idx - 1])
                            if np.linalg.norm(prev_dir) > 0.01:
                                prev_dir = prev_dir / np.linalg.norm(prev_dir)
                            else:
                                prev_dir = seg_dir
                            P1_seg = P0_seg + prev_dir * (segment_distance * 0.35)
                        
                        if wp_idx == len(waypoints_2d_retry) - 2:
                            P2_seg = P3_seg - runway_dir * (segment_distance * 0.35)
                        else:
                            next_dir = (waypoints_2d_retry[wp_idx + 2] - wp_end)
                            if np.linalg.norm(next_dir) > 0.01:
                                next_dir = next_dir / np.linalg.norm(next_dir)
                            else:
                                next_dir = seg_dir
                            P2_seg = P3_seg - next_dir * (segment_distance * 0.35)
                        
                        segment_array = np.zeros((n_segment, 3))
                        total_distance = np.linalg.norm(faf_pos[:2] - initial_end_point)
                        dist_so_far = sum([np.linalg.norm(waypoints_2d_retry[i+1] - waypoints_2d_retry[i]) 
                                          for i in range(wp_idx)])
                        
                        for i in range(n_segment):
                            t_local = i / (n_segment - 1)
                            pos_2d = ((1-t_local)**3 * P0_seg + 
                                     3*(1-t_local)**2*t_local * P1_seg + 
                                     3*(1-t_local)*t_local**2 * P2_seg + 
                                     t_local**3 * P3_seg)
                            
                            # ALTITUDE avec respect de la pente maximale (même logique que trajectoire principale)
                            current_distance = dist_so_far + t_local * segment_distance
                            
                            if current_distance < level_flight_distance:
                                altitude = altitude_start
                            elif current_distance < level_flight_distance + transition_distance:
                                transition_progress = (current_distance - level_flight_distance) / transition_distance
                                # Super-smoothstep (7ème degré) pour transition ultra-douce
                                t = transition_progress
                                smooth_t = -20*t**7 + 70*t**6 - 84*t**5 + 35*t**4
                                transition_altitude_drop = (transition_distance * abs(np.tan(max_descent_slope_rad)))
                                altitude = altitude_start - smooth_t * transition_altitude_drop
                            else:
                                descent_progress = current_distance - level_flight_distance - transition_distance
                                transition_altitude_drop = (transition_distance * abs(np.tan(max_descent_slope_rad)))
                                descent_altitude_drop = descent_progress * abs(np.tan(max_descent_slope_rad))
                                altitude = altitude_start - transition_altitude_drop - descent_altitude_drop
                                altitude = max(altitude, altitude_end)
                            
                            segment_array[i] = [pos_2d[0], pos_2d[1], altitude]
                        
                        segments_retry.append(segment_array)
                    
                    trajectory_retry = np.vstack(segments_retry)
                    trajectory_retry[-1] = faf_pos
                    
                    # Vérifier cette nouvelle trajectoire
                    has_collision_retry, _, _ = self._check_trajectory_collision(trajectory_retry, cylinders)
                    
                    # Stocker cette tentative de trajectoire pour visualisation
                    self.retry_trajectories.append(trajectory_retry.copy())
                    self.retry_trajectories_info.append({
                        'attempt_number': attempt + 1,
                        'safety_factor': safety_factor,
                        'has_collision': has_collision_retry,
                        'num_points': len(trajectory_retry)
                    })
                    
                    if not has_collision_retry:
                        print(f"   ✅ Trajectoire VALIDE trouvée (tentative {attempt + 1})")
                        trajectory = trajectory_retry
                        waypoints_2d = waypoints_2d_retry
                        break
                    else:
                        print(f"   ⚠️  Collision persistante (tentative {attempt + 1})")
                
                else:
                    print(f"   ❌ Aucune trajectoire sûre trouvée après toutes les tentatives")
                    return None, {}
        
        n_turn_points = len(trajectory) - len(initial_segment)
        
        parameters = self._calculate_parameters(trajectory, aircraft.speed)
        parameters['intercept_point'] = faf_pos[:2]  # Le point d'interception est maintenant le FAF
        parameters['initial_segment_end'] = len(initial_segment)
        parameters['turn_segment_end'] = len(trajectory)  # Le virage se termine au FAF
        parameters['runway_alignment'] = True  # Marqueur pour l'affichage
        parameters['n_points'] = len(trajectory)
        
        return trajectory, parameters
    
    
    def _calculate_parameters(self, trajectory, speed):
        """
        Calcule les paramètres de vol (temps, altitude, pente, cap, taux de virage) à partir
        de la trajectoire et de la vitesse.
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
        
        # Calculer la pente (en degrés) - vectorisé
        slope_array = np.zeros(n_points)
        if n_points > 1:
            dz = np.diff(trajectory[:, 2])  # Différences d'altitude
            dx = np.linalg.norm(np.diff(trajectory[:, :2], axis=0), axis=1)  # Distances horizontales
            slope_array[1:] = np.where(dx > 0, np.degrees(np.arctan(dz / dx)), 
                                       np.where(dz != 0, np.where(dz > 0, 90.0, -90.0), 0.0))
            slope_array[0] = slope_array[1]
        
        # Calculer l'angle de cap (heading) - vectorisé
        heading_array = np.zeros(n_points)
        if n_points > 1:
            dxy = np.diff(trajectory[:, :2], axis=0)  # Variations [dx, dy]
            heading_array[1:] = np.degrees(np.arctan2(dxy[:, 0], dxy[:, 1]))  # atan2(dx, dy)
            heading_array[1:] = np.where(heading_array[1:] < 0, heading_array[1:] + 360, heading_array[1:])
            heading_array[0] = heading_array[1]
        
        # Calculer le taux de virage - vectorisé
        turn_rate_array = np.zeros(n_points)
        if n_points > 1:
            delta_time = np.diff(time_array)
            delta_heading = np.diff(heading_array)
            # Gestion passage 0°/360°
            delta_heading = np.where(delta_heading > 180, delta_heading - 360, delta_heading)
            delta_heading = np.where(delta_heading < -180, delta_heading + 360, delta_heading)
            turn_rate_array[1:] = np.where(delta_time > 0, delta_heading / delta_time, 0.0)
            turn_rate_array[0] = turn_rate_array[1]
        
        return {
            'time': time_array,
            'altitude': altitude_array,
            'slope': slope_array,
            'speed': speed_array,
            'heading': heading_array,
            'turn_rate': turn_rate_array,
            'distance': total_distance,
            'flight_time': flight_time_hours if total_distance > 0 else 0
        }
    
    def _calculate_parameters_with_speed_profile(self, trajectory, initial_speed, arc_length, speed_profile):
        """
        Calcule les paramètres avec profil de vitesse variable : vitesse constante pendant le virage,
        puis vitesse variable en approche (décélération progressive).
        """
        
        n_points = len(trajectory)
        
        # Créer le profil de vitesse complet
        full_speed_profile = np.zeros(n_points)
        # Phase de virage: vitesse constante
        full_speed_profile[:arc_length] = initial_speed
        # Phase d'approche: vitesse variable
        full_speed_profile[arc_length:] = speed_profile
        
        # Calculer les distances et temps avec vitesse variable
        distances = np.zeros(n_points)
        time_array = np.zeros(n_points)
        
        for i in range(1, n_points):
            segment_distance = np.linalg.norm(trajectory[i] - trajectory[i-1])
            distances[i] = distances[i-1] + segment_distance
            
            # Vitesse moyenne sur ce segment
            avg_speed = (full_speed_profile[i] + full_speed_profile[i-1]) / 2
            if avg_speed > 0:
                segment_time = segment_distance / avg_speed  # temps en heures
                time_array[i] = time_array[i-1] + segment_time * 3600  # conversion en secondes
        
        # Altitude
        altitude_array = trajectory[:, 2]
        
        # Calculer la pente (en degrés) - vectorisé
        slope_array = np.zeros(n_points)
        if n_points > 1:
            dz = np.diff(trajectory[:, 2])
            dx = np.linalg.norm(np.diff(trajectory[:, :2], axis=0), axis=1)
            slope_array[1:] = np.where(dx > 0, np.degrees(np.arctan(dz / dx)),
                                       np.where(dz != 0, np.where(dz > 0, 90.0, -90.0), 0.0))
            slope_array[0] = slope_array[1]
        
        # Calculer l'angle de cap (heading) - vectorisé
        heading_array = np.zeros(n_points)
        if n_points > 1:
            dxy = np.diff(trajectory[:, :2], axis=0)
            heading_array[1:] = np.degrees(np.arctan2(dxy[:, 0], dxy[:, 1]))
            heading_array[1:] = np.where(heading_array[1:] < 0, heading_array[1:] + 360, heading_array[1:])
            heading_array[0] = heading_array[1]
        
        # Calculer le taux de virage - vectorisé
        turn_rate_array = np.zeros(n_points)
        if n_points > 1:
            delta_time = np.diff(time_array)
            delta_heading = np.diff(heading_array)
            delta_heading = np.where(delta_heading > 180, delta_heading - 360, delta_heading)
            delta_heading = np.where(delta_heading < -180, delta_heading + 360, delta_heading)
            turn_rate_array[1:] = np.where(delta_time > 0, delta_heading / delta_time, 0.0)
            turn_rate_array[0] = turn_rate_array[1]
        
        total_distance = distances[-1]
        flight_time_hours = time_array[-1] / 3600 if time_array[-1] > 0 else 0
        
        return {
            'time': time_array,
            'altitude': altitude_array,
            'slope': slope_array,
            'speed': full_speed_profile,
            'heading': heading_array,
            'turn_rate': turn_rate_array,
            'distance': total_distance,
            'flight_time': flight_time_hours,
            'n_points': n_points
        }
    
    def calculate_trajectory_with_turn(self, aircraft, cylinders=None):
        """
        Mode virages réalistes : calcule trajectoire avec arc de virage tangent à l'axe d'approche,
        suivi de l'axe jusqu'au FAF avec descente et décélération progressives.
        """
        
        if cylinders is None:
            cylinders = []
        start_pos = aircraft.position.copy()
        faf_pos = self.environment.faf_position.copy()
        airport_pos = self.environment.airport_position.copy()
        
        # Calculer le rayon de virage minimum
        min_radius = aircraft.calculate_min_turn_radius()
        
        # Axe d'approche: vecteur de l'aéroport vers le FAF (projeté sur XY)
        approach_direction = faf_pos[:2] - airport_pos[:2]
        approach_direction = approach_direction / np.linalg.norm(approach_direction)
        
        # Cap actuel de l'avion (en vecteur unitaire XY)
        heading_rad = np.radians(aircraft.heading)
        current_direction = np.array([np.sin(heading_rad), np.cos(heading_rad)])
        
        # Calculer le point d'interception tangent à l'axe d'approche
        intercept_point, turn_center, turn_angle = self._calculate_tangent_intercept(
            start_pos[:2], current_direction, approach_direction, 
            airport_pos[:2], faf_pos[:2], min_radius
        )
        
        if intercept_point is None:
            # Si impossible de calculer un virage tangent, utiliser la méthode classique
            print("⚠️  Mode virages réalistes : Interception tangente impossible")
            print(f"   → Fallback sur trajectoire directe (virage vers FAF)")
            print(f"   Position: {start_pos[:2]}, Cap: {aircraft.heading}°, Rayon: {min_radius:.2f} km")
            
            # Calculer la distance perpendiculaire à l'axe
            vec_to_aircraft = start_pos[:2] - airport_pos[:2]
            perp_distance = abs(np.dot(vec_to_aircraft, np.array([-approach_direction[1], approach_direction[0]])))
            print(f"   Distance perpendiculaire à l'axe: {perp_distance:.2f} km (rayon: {min_radius:.2f} km)")
            print(f"   💡 Pour voir l'interception tangente: rapprochez l'avion de l'axe ou décrochez 'Virages réalistes'")
            
            # IMPORTANT: Passer les cylindres lors du fallback !
            return self.calculate_trajectory(aircraft, cylinders)
        
        # Succès ! Calculer la distance perpendiculaire pour info
        vec_to_aircraft = start_pos[:2] - airport_pos[:2]
        perp_distance = abs(np.dot(vec_to_aircraft, np.array([-approach_direction[1], approach_direction[0]])))
        
        print(f"✓ Mode virages réalistes : Interception tangente réussie !")
        print(f"   Virage: angle={np.degrees(turn_angle):.1f}°, rayon={min_radius:.3f} km")
        print(f"   Point d'interception: ({intercept_point[0]:.1f}, {intercept_point[1]:.1f}) km")
        print(f"   Distance perpendiculaire: {perp_distance:.2f} km ≤ rayon de virage ✓")
        
        # Construire la trajectoire en 3 phases:
        # 1. Arc de virage jusqu'à l'axe d'approche
        # 2. Ligne droite sur l'axe jusqu'au début de descente
        # 3. Descente jusqu'au FAF
        
        trajectory_segments = []
        
        # Phase 1: Arc de virage
        arc_trajectory = self._create_arc_trajectory(
            start_pos[:2], turn_center, turn_angle, min_radius, 
            start_pos[2]  # Altitude constante pendant le virage
        )
        trajectory_segments.append(arc_trajectory)
        
        # Phase 2 & 3: Ligne droite avec descente et décélération
        # Position après le virage
        post_turn_pos = np.array([intercept_point[0], intercept_point[1], start_pos[2]])
        
        # Vitesse d'approche finale
        approach_speed = aircraft.get_approach_speed()
        
        # Calculer la trajectoire de l'intercept au FAF avec gestion altitude et vitesse
        approach_trajectory, speed_profile = self._calculate_approach_with_descent_and_speed(
            aircraft, post_turn_pos, faf_pos, approach_direction, approach_speed
        )
        trajectory_segments.append(approach_trajectory)
        
        # Combiner les segments
        trajectory = np.vstack(trajectory_segments)
        
        # Calculer les paramètres avec profil de vitesse
        parameters = self._calculate_parameters_with_speed_profile(
            trajectory, aircraft.speed, len(arc_trajectory), speed_profile
        )
        parameters['turn_radius'] = min_radius
        parameters['intercept_point'] = intercept_point
        parameters['turn_angle'] = np.degrees(turn_angle)
        parameters['initial_speed'] = aircraft.speed
        parameters['approach_speed'] = approach_speed
        
        return trajectory, parameters
    
    def _calculate_tangent_intercept(self, start_pos, current_dir, approach_dir, 
                                     airport_pos, faf_pos, radius):
        """
        Calcule le point d'interception tangent à l'axe d'approche en utilisant la géométrie
        des cercles tangents : résout l'équation quadratique pour trouver où le cercle de virage
        touche l'axe d'approche.
        """
        
        # Déterminer le sens de virage (gauche ou droite)
        # Produit vectoriel pour savoir de quel côté tourner
        cross = current_dir[0] * approach_dir[1] - current_dir[1] * approach_dir[0]
        turn_direction = 1 if cross > 0 else -1  # 1 = gauche, -1 = droite
        
        # Vecteur perpendiculaire au cap actuel
        perp_current = np.array([-current_dir[1], current_dir[0]]) * turn_direction
        
        # Centre du cercle de virage
        turn_center = start_pos + perp_current * radius
        
        # Vecteur perpendiculaire à l'axe d'approche (même sens de rotation)
        perp_approach = np.array([-approach_dir[1], approach_dir[0]]) * turn_direction
        
        # Le point de tangence est à distance 'radius' de l'axe d'approche
        # On cherche le point sur l'axe d'approche tel que la distance au centre = radius
        
        # Équation de l'axe d'approche: P = airport_pos + t * approach_dir
        # Distance du centre au point: |turn_center - P| = radius
        
        # Résolution: trouver t tel que |turn_center - (airport_pos + t * approach_dir)| = radius
        # C'est une équation quadratique
        
        vec_to_center = turn_center - airport_pos
        
        a = np.dot(approach_dir, approach_dir)  # = 1 (vecteur unitaire)
        b = -2 * np.dot(vec_to_center, approach_dir)
        c = np.dot(vec_to_center, vec_to_center) - radius ** 2
        
        discriminant = b**2 - 4*a*c
        
        if discriminant < 0:
            return None, None, None  # Pas de solution (cercle trop loin de l'axe)
        
        # Deux solutions possibles
        t1 = (-b + np.sqrt(discriminant)) / (2*a)
        t2 = (-b - np.sqrt(discriminant)) / (2*a)
        
        # Choisir le point le plus proche du FAF (t plus grand si approche pointe vers FAF)
        point1 = airport_pos + t1 * approach_dir
        point2 = airport_pos + t2 * approach_dir
        
        # Vérifier quel point est entre l'aéroport et au-delà du FAF
        # On veut intercepter l'axe avant le FAF
        dist1_to_faf = np.linalg.norm(point1 - faf_pos)
        dist2_to_faf = np.linalg.norm(point2 - faf_pos)
        
        # Choisir le point qui est du bon côté (avant le FAF mais sur l'axe prolongé)
        if t1 > 0 and dist1_to_faf < np.linalg.norm(faf_pos - airport_pos) * 1.5:
            intercept_point = point1
            t_chosen = t1
        elif t2 > 0 and dist2_to_faf < np.linalg.norm(faf_pos - airport_pos) * 1.5:
            intercept_point = point2
            t_chosen = t2
        else:
            # Prendre le plus proche
            intercept_point = point1 if dist1_to_faf < dist2_to_faf else point2
            t_chosen = t1 if dist1_to_faf < dist2_to_faf else t2
        
        # Calculer l'angle de virage
        vec_start = start_pos - turn_center
        vec_end = intercept_point - turn_center
        
        # Angle entre les deux vecteurs
        cos_angle = np.dot(vec_start, vec_end) / (np.linalg.norm(vec_start) * np.linalg.norm(vec_end))
        cos_angle = np.clip(cos_angle, -1.0, 1.0)
        turn_angle = np.arccos(cos_angle)
        
        # Vérifier le sens avec le produit vectoriel
        cross_check = vec_start[0] * vec_end[1] - vec_start[1] * vec_end[0]
        if cross_check * turn_direction < 0:
            turn_angle = -turn_angle
        
        return intercept_point, turn_center, turn_angle
    
    def _create_arc_trajectory(self, start_pos, center, angle, radius, altitude):
        """
        Génère les points d'un arc de cercle pour le virage (altitude constante pendant le virage).
        Densité d'environ 1 point tous les 2 degrés.
        """
        # Nombre de points en fonction de l'angle (environ 1 point tous les 2 degrés)
        n_points = max(int(abs(np.degrees(angle)) / 2), 10)
        
        # Angle initial
        vec_to_start = start_pos - center
        angle_start = np.arctan2(vec_to_start[1], vec_to_start[0])
        
        # Générer les angles
        angles = np.linspace(angle_start, angle_start + angle, n_points)
        
        # Générer les points de l'arc
        arc_points = np.zeros((n_points, 3))
        arc_points[:, 0] = center[0] + radius * np.cos(angles)
        arc_points[:, 1] = center[1] + radius * np.sin(angles)
        arc_points[:, 2] = altitude  # Altitude constante
        
        return arc_points
    
    def _calculate_approach_with_descent_and_speed(self, aircraft, start_pos, target_pos, direction, target_speed):
        """
        Trajectoire d'approche avec descente progressive (palier, transition, descente linéaire)
        ET décélération simultanée de la vitesse initiale vers la vitesse d'approche.
        """
        # Distance horizontale
        horizontal_distance = np.linalg.norm(target_pos[:2] - start_pos[:2])
        altitude_diff = target_pos[2] - start_pos[2]
        
        # Vitesse initiale pour cette phase (vitesse actuelle de l'avion)
        initial_speed = aircraft.speed
        
        # Si pas de descente nécessaire ou montée
        if altitude_diff >= 0:
            # Ligne droite simple avec décélération
            n_points = max(int(horizontal_distance * 50), 50)
            t_values = np.linspace(0, 1, n_points)
            
            trajectory = np.zeros((n_points, 3))
            speed_profile = np.zeros(n_points)
            
            for i, t in enumerate(t_values):
                trajectory[i] = start_pos + t * (target_pos - start_pos)
                # Décélération progressive (linéaire)
                speed_profile[i] = initial_speed + t * (target_speed - initial_speed)
            
            return trajectory, speed_profile
        
        # Descente nécessaire
        max_descent_slope_rad = np.radians(aircraft.max_descent_slope)
        min_descent_distance = abs(altitude_diff / np.tan(max_descent_slope_rad))
        
        # Distance de transition
        transition_distance = max(min(min_descent_distance * 0.15, 3.0), 1.0)
        
        if horizontal_distance < min_descent_distance:
            # Pas assez de distance, descente immédiate
            level_distance = 0
        else:
            # Vol en palier puis descente
            level_distance = horizontal_distance - min_descent_distance - transition_distance
            level_distance = max(0, level_distance)
        
        # Construire la trajectoire avec ultra-haute densité de points
        total_points = max(500, int(horizontal_distance * 100))
        t_values = np.linspace(0, 1, total_points)
        
        trajectory = np.zeros((total_points, 3))
        speed_profile = np.zeros(total_points)
        
        # Distance à partir de laquelle on commence à décélérer (2/3 du parcours)
        decel_start_distance = horizontal_distance * 0.33
        
        for i, t in enumerate(t_values):
            # Position horizontale (interpolation linéaire)
            current_distance = t * horizontal_distance
            trajectory[i, :2] = start_pos[:2] + direction * current_distance
            
            # Altitude (avec phases)
            if current_distance < level_distance:
                # Phase de palier
                trajectory[i, 2] = start_pos[2]
            elif current_distance < level_distance + transition_distance:
                # Phase de transition progressive (cosinus)
                transition_progress = (current_distance - level_distance) / transition_distance
                smooth_factor = (1 - np.cos(transition_progress * np.pi)) / 2
                trajectory[i, 2] = start_pos[2] + smooth_factor * altitude_diff * (transition_distance / min_descent_distance)
            else:
                # Phase de descente linéaire
                descent_distance = current_distance - level_distance - transition_distance
                trajectory[i, 2] = start_pos[2] + altitude_diff * ((transition_distance + descent_distance) / min_descent_distance)
            
            # Profil de vitesse (décélération progressive)
            if current_distance < decel_start_distance:
                # Vitesse constante
                speed_profile[i] = initial_speed
            else:
                # Décélération progressive (utilise une fonction smooth)
                decel_progress = (current_distance - decel_start_distance) / (horizontal_distance - decel_start_distance)
                # Décélération smooth (cosinus)
                smooth_decel = (1 + np.cos((1 - decel_progress) * np.pi)) / 2
                speed_profile[i] = target_speed + smooth_decel * (initial_speed - target_speed)
        
        return trajectory, speed_profile
    
    def _calculate_avoidance_waypoints(self, start_2d, end_2d, cylinders, altitude):
        """
        Détecte les obstacles sur le segment et génère des waypoints de contournement tangents
        (approche latérale en longeant le périmètre) pour chaque obstacle traversé.
        """
        waypoints = []
        safety_margin = 0.5  # Marge de sécurité réduite pour longer le cylindre
        
        # Direction du trajet
        traj_vec = end_2d - start_2d
        traj_dist = np.linalg.norm(traj_vec)
        
        if traj_dist < 0.01:
            return waypoints
        
        traj_dir = traj_vec / traj_dist
        
        for cylinder in cylinders:
            if altitude > cylinder['height'] + 0.5:  # Marge aussi sur l'altitude
                continue  # Pas de collision possible si on vole au-dessus
            
            cyl_center = np.array([cylinder['x'], cylinder['y']])
            cyl_radius = cylinder['radius'] + safety_margin
            
            # Vérifier si le segment traverse le cylindre
            # Projeter le centre du cylindre sur la ligne start-end
            to_cyl = cyl_center - start_2d
            proj_length = np.dot(to_cyl, traj_dir)
            
            # Si la projection est hors du segment, pas de collision
            if proj_length < 0 or proj_length > traj_dist:
                continue
            
            # Point le plus proche sur le segment
            closest_point = start_2d + proj_length * traj_dir
            dist_to_segment = np.linalg.norm(cyl_center - closest_point)
            
            # Si le cylindre est trop proche, créer des waypoints de contournement
            if dist_to_segment < cyl_radius:
                
                # Vecteur perpendiculaire à la trajectoire
                perp = np.array([-traj_dir[1], traj_dir[0]])
                
                # Déterminer le côté de contournement optimal
                # On choisit le côté qui minimise la déviation
                vec_to_cyl = cyl_center - start_2d
                cross_product = vec_to_cyl[0] * traj_dir[1] - vec_to_cyl[1] * traj_dir[0]
                side = 1 if cross_product > 0 else -1
                
                # Calculer la distance avant/après le cylindre pour placer les waypoints
                # Approche tangente : distance réduite pour longer le cylindre
                approach_distance = max(cyl_radius * 0.8, 1.0)  # Distance d'approche réduite
                
                # Points d'entrée et de sortie sur la trajectoire directe
                entry_pos_on_traj = proj_length - approach_distance
                exit_pos_on_traj = proj_length + approach_distance
                
                # S'assurer qu'on reste dans le segment
                entry_pos_on_traj = max(0, entry_pos_on_traj)
                exit_pos_on_traj = min(traj_dist, exit_pos_on_traj)
                
                # Points de base sur la trajectoire
                entry_base = start_2d + entry_pos_on_traj * traj_dir
                exit_base = start_2d + exit_pos_on_traj * traj_dir
                
                # Décaler perpendiculairement pour contourner
                # Décalage juste suffisant pour éviter le cylindre (on longe le périmètre)
                offset_distance = (cylinder['radius'] - dist_to_segment) + safety_margin  # On compense la distance manquante + marge
                
                entry_point = entry_base + side * perp * offset_distance
                exit_point = exit_base + side * perp * offset_distance
                
                # Vérifier que les points ne sont pas DANS le cylindre
                dist_entry = np.linalg.norm(entry_point - cyl_center)
                dist_exit = np.linalg.norm(exit_point - cyl_center)
                
                # Si trop proche, pousser au rayon + marge minimale
                min_safe_distance = cylinder['radius'] + safety_margin
                if dist_entry < min_safe_distance:
                    entry_point = cyl_center + (entry_point - cyl_center) / dist_entry * min_safe_distance
                if dist_exit < min_safe_distance:
                    exit_point = cyl_center + (exit_point - cyl_center) / dist_exit * min_safe_distance
                
                waypoints.append(entry_point)
                waypoints.append(exit_point)
                
               
        return waypoints
    
    def _calculate_avoidance_waypoints_with_margin(self, start_2d, end_2d, cylinders, altitude, safety_factor):
        """
        Similaire à _calculate_avoidance_waypoints mais avec marge de sécurité personnalisée
        (utilisé pour recalculs avec marges augmentées en cas de collision).
        """
        waypoints = []
        
        # Direction du trajet
        traj_vec = end_2d - start_2d
        traj_dist = np.linalg.norm(traj_vec)
        
        if traj_dist < 0.01:
            return waypoints
        
        traj_dir = traj_vec / traj_dist
        
        for cylinder in cylinders:
            if altitude > cylinder['height'] + 0.5:
                continue
            
            cyl_center = np.array([cylinder['x'], cylinder['y']])
            cyl_radius = cylinder['radius'] + safety_factor
            
            # Projeter le centre du cylindre sur la ligne start-end
            to_cyl = cyl_center - start_2d
            proj_length = np.dot(to_cyl, traj_dir)
            
            if proj_length < 0 or proj_length > traj_dist:
                continue
            
            closest_point = start_2d + proj_length * traj_dir
            dist_to_segment = np.linalg.norm(cyl_center - closest_point)
            
            if dist_to_segment < cyl_radius:
                # Vecteur perpendiculaire
                perp = np.array([-traj_dir[1], traj_dir[0]])
                
                # Côté optimal
                vec_to_cyl = cyl_center - start_2d
                cross_product = vec_to_cyl[0] * traj_dir[1] - vec_to_cyl[1] * traj_dir[0]
                side = 1 if cross_product > 0 else -1
                
                # Distance d'approche avec safety_factor (pour les recalculs)
                approach_distance = max(cyl_radius * 0.8, safety_factor * 0.5)
                
                # Points d'entrée/sortie
                entry_pos_on_traj = max(0, proj_length - approach_distance)
                exit_pos_on_traj = min(traj_dist, proj_length + approach_distance)
                
                entry_base = start_2d + entry_pos_on_traj * traj_dir
                exit_base = start_2d + exit_pos_on_traj * traj_dir
                
                # Décalage : on compense la distance manquante + safety_factor
                offset_distance = (cylinder['radius'] - dist_to_segment) + safety_factor
                
                entry_point = entry_base + side * perp * offset_distance
                exit_point = exit_base + side * perp * offset_distance
                
                # Validation : s'assurer qu'on est au moins à rayon + safety_factor
                dist_entry = np.linalg.norm(entry_point - cyl_center)
                dist_exit = np.linalg.norm(exit_point - cyl_center)
                
                min_safe_dist = cylinder['radius'] + safety_factor
                if dist_entry < min_safe_dist:
                    entry_point = cyl_center + (entry_point - cyl_center) / dist_entry * min_safe_dist
                if dist_exit < min_safe_dist:
                    exit_point = cyl_center + (exit_point - cyl_center) / dist_exit * min_safe_dist
                
                waypoints.append(entry_point)
                waypoints.append(exit_point)
        
        return waypoints
    
    def _check_collision_with_cylinder(self, point, cylinder):
        """
        Teste si un point 3D est à l'intérieur d'un cylindre (distance horizontale ≤ rayon ET altitude ≤ hauteur).
        """
        # Distance horizontale au centre du cylindre
        dx = point[0] - cylinder['x']
        dy = point[1] - cylinder['y']
        horizontal_dist = np.sqrt(dx**2 + dy**2)
        
        # Vérifier si dans le rayon et sous la hauteur
        return (horizontal_dist <= cylinder['radius'] and 
                0 <= point[2] <= cylinder['height'])
    
    def _check_trajectory_collision(self, trajectory, cylinders):
        """
        Parcourt toute la trajectoire et détecte les collisions avec les cylindres.
        Retourne la liste des cylindres en collision et l'index du premier point de collision.
        """
        if not cylinders:
            return False, [], -1
        
        colliding_cylinders = []
        first_collision_idx = -1
        
        for i, point in enumerate(trajectory):
            for cyl_idx, cylinder in enumerate(cylinders):
                if self._check_collision_with_cylinder(point, cylinder):
                    if cyl_idx not in colliding_cylinders:
                        colliding_cylinders.append(cyl_idx)
                    if first_collision_idx == -1:
                        first_collision_idx = i
        
        return len(colliding_cylinders) > 0, colliding_cylinders, first_collision_idx
    
