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
        
    def calculate_trajectory(self, aircraft, cylinders=None):
        """
        Calcule la trajectoire optimale vers le FAF avec courbes de Bézier.
        Mode principal : vol initial dans le cap, virage progressif avec courbes de Bézier pour s'aligner,
        descente progressive et évitement automatique des obstacles.
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
        
        # Construire la trajectoire avec courbes de Bézier et évitement d'obstacles
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
            avoidance_waypoints = self._calculate_avoidance_waypoints(
                initial_end_point, faf_pos[:2], cylinders, start_pos[2]
            )
            waypoints_2d.extend(avoidance_waypoints)
        
        waypoints_2d.append(faf_pos[:2])
        
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
                
                dist_entry = np.linalg.norm(entry_point - cyl_center)
                dist_exit = np.linalg.norm(exit_point - cyl_center)
                min_safe_distance = cylinder['radius'] + safety_margin
                if dist_entry < min_safe_distance:
                    entry_point = cyl_center + (entry_point - cyl_center) / dist_entry * min_safe_distance
                if dist_exit < min_safe_distance:
                    exit_point = cyl_center + (exit_point - cyl_center) / dist_exit * min_safe_distance
                
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
    
