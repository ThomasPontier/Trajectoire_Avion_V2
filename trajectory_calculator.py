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
        
        print("\n" + "="*70)
        print("🛩️  CALCUL TRAJECTOIRE AVEC ALIGNEMENT SUR AXE PISTE (Mode virages simplifiés)")
        print("="*70)
        print(f"📍 Position initiale: ({start_pos[0]:.1f}, {start_pos[1]:.1f}, {start_pos[2]:.1f}) km")
        print(f"� Aéroport: ({airport_pos[0]:.1f}, {airport_pos[1]:.1f}, {airport_pos[2]:.1f}) km")
        print(f"�🎯 FAF cible: ({faf_pos[0]:.1f}, {faf_pos[1]:.1f}, {faf_pos[2]:.1f}) km")
        print(f"🧭 Cap initial: {aircraft.heading:.1f}°")
        print(f"⚡ Vitesse: {aircraft.speed:.0f} km/h")
        print(f"✈️  Type: {aircraft.aircraft_type}")
        
        # Calculer l'axe d'approche (FAF → aéroport, direction de l'atterrissage)
        # L'avion doit arriver au FAF en étant orienté VERS l'aéroport
        runway_axis = airport_pos[:2] - faf_pos[:2]
        runway_axis_distance = np.linalg.norm(runway_axis)
        
        if runway_axis_distance < 0.1:
            print("⚠️  Aéroport et FAF trop proches -> trajectoire directe")
            return self._calculate_simple_trajectory(aircraft, start_pos, faf_pos)
        
        runway_direction = runway_axis / runway_axis_distance
        print(f"🛬 Direction d'approche (FAF→Aéroport): ({runway_direction[0]:.3f}, {runway_direction[1]:.3f})")
        
        # Direction actuelle de l'avion
        heading_rad = np.radians(aircraft.heading)
        current_direction = np.array([np.sin(heading_rad), np.cos(heading_rad)])
        
        # Calculer l'angle entre le cap actuel et l'axe de la piste
        cos_angle = np.dot(current_direction, runway_direction)
        angle_to_runway = np.degrees(np.arccos(np.clip(cos_angle, -1.0, 1.0)))
        
        print(f"🔄 Angle entre cap et axe piste: {angle_to_runway:.1f}°")
        
        # Distance horizontale au FAF
        horizontal_distance = np.linalg.norm(faf_pos[:2] - start_pos[:2])
        print(f"📏 Distance horizontale au FAF: {horizontal_distance:.2f} km")
        
        if horizontal_distance < 0.1:
            print("⚠️  Déjà au FAF horizontalement -> trajectoire verticale uniquement")
            return self._vertical_trajectory(aircraft, start_pos, faf_pos)
        
        # Calculer le point d'interception optimal sur l'axe de la piste
        # On vise un point AVANT le FAF pour avoir le temps de s'aligner
        intercept_point = self._calculate_runway_intercept_point(
            start_pos[:2], current_direction, airport_pos[:2], 
            faf_pos[:2], runway_direction, angle_to_runway
        )
        
        print(f"📍 Point d'interception sur axe: ({intercept_point[0]:.1f}, {intercept_point[1]:.1f}) km")
        
        # Construire la trajectoire en 2 phases avec évitement d'obstacles
        return self._build_trajectory_with_runway_alignment(
            aircraft, start_pos, intercept_point, faf_pos, 
            current_direction, runway_direction, cylinders
        )
    
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
        
        # S'assurer qu'on finit exactement au FAF avec une transition d'altitude douce
        if len(trajectory) > 0:
            # Au lieu de forcer brutalement, faire une transition douce sur les derniers points
            n_smooth_points = min(50, len(trajectory) // 10)  # 50 points ou 10% de la trajectoire
            if n_smooth_points > 0 and len(trajectory) >= n_smooth_points:
                for i in range(n_smooth_points):
                    idx = len(trajectory) - n_smooth_points + i
                    if idx >= 0:
                        t = i / (n_smooth_points - 1)
                        # Transition douce vers la position FAF exacte
                        trajectory[idx][:2] = (1 - t) * trajectory[idx][:2] + t * target_pos[:2]
                        trajectory[idx][2] = (1 - t) * trajectory[idx][2] + t * target_pos[2]
            
            # Dernière position exactement au FAF
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
        
        print(f"   📊 Distance perpendiculaire à l'axe: {perp_distance:.2f} km")
        print(f"   📊 Distance jusqu'au FAF sur l'axe: {distance_to_faf_on_axis:.2f} km")
        
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
        
        print(f"\n🔵 Construction de la trajectoire en 2 phases...")
        
        # Distance totale jusqu'au FAF
        total_distance_to_faf = np.linalg.norm(faf_pos[:2] - start_pos[:2])
        
        # Phase 1: Vol initial (15-25% de la distance totale, entre 1 et 5 km)
        initial_flight_ratio = 0.20
        initial_flight_dist = np.clip(total_distance_to_faf * initial_flight_ratio, 1.0, 5.0)
        initial_end_point = start_pos[:2] + current_dir * initial_flight_dist
        
        print(f"   Phase 1: Vol initial {initial_flight_dist:.2f} km dans le cap {aircraft.heading:.0f}°")
        
        # Phase 2: Virage progressif qui se termine DIRECTEMENT au FAF
        # Le virage amènera l'avion parfaitement aligné avec l'axe de piste en arrivant au FAF
        turn_distance = np.linalg.norm(faf_pos[:2] - initial_end_point)
        
        print(f"   Phase 2: Virage progressif sur {turn_distance:.2f} km jusqu'au FAF")
        print(f"   💡 L'avion sera parfaitement aligné avec la piste en arrivant au FAF")
        
        # CALCUL DE LA GESTION D'ALTITUDE avec respect de la pente max
        altitude_start = start_pos[2]
        altitude_end = faf_pos[2]
        altitude_diff = altitude_end - altitude_start
        
        # Pente maximale de descente (en radians, négative)
        max_descent_slope_rad = np.radians(aircraft.max_descent_slope)
        
        # Distance minimale nécessaire pour descendre avec la pente max
        # distance = |altitude_diff| / tan(|slope|)
        min_descent_distance = abs(altitude_diff / np.tan(abs(max_descent_slope_rad)))
        
        # Distance de transition progressive - ULTRA-SMOOTH avec transition très longue
        # 50% de la distance de descente minimum, entre 3 et 12 km pour une transition imperceptible
        transition_distance = max(min(min_descent_distance * 0.50, 12.0), 3.0)
        
        print(f"\n   📐 Gestion altitude:")
        print(f"      Altitude départ: {altitude_start:.2f} km → FAF: {altitude_end:.2f} km (Δ = {altitude_diff:.2f} km)")
        print(f"      Pente max: {aircraft.max_descent_slope:.1f}°")
        print(f"      Distance min descente: {min_descent_distance:.2f} km")
        print(f"      Distance transition: {transition_distance:.2f} km")
        print(f"      Distance totale disponible: {total_distance_to_faf:.2f} km")
        
        # Calculer où commencer la descente (palier puis transition puis descente)
        total_descent_distance = min_descent_distance + transition_distance
        
        if total_descent_distance >= total_distance_to_faf:
            # Pas assez de distance -> transition dès le départ
            level_flight_distance = 0.0
            transition_distance = min(transition_distance, total_distance_to_faf * 0.3)
            descent_distance = total_distance_to_faf - transition_distance
            print(f"      ⚠️  Distance limitée -> Transition dès le départ")
        else:
            # On peut voler en palier avant de descendre
            level_flight_distance = total_distance_to_faf - total_descent_distance
            descent_distance = min_descent_distance
            print(f"      ✓ Vol en palier: {level_flight_distance:.2f} km, puis transition et descente")
        
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
        
        # VALIDATION CRITIQUE: Vérifier qu'aucun point ne traverse les obstacles
        if cylinders:
            print(f"\n   🔍 VALIDATION: Vérification des collisions sur {len(trajectory)} points...")
            has_collision, colliding_indices, first_collision_idx = self._check_trajectory_collision(
                trajectory, cylinders
            )
            
            if has_collision:
                print(f"   ❌ COLLISION DÉTECTÉE avec {len(colliding_indices)} obstacle(s) !")
                print(f"      Premier point de collision: index {first_collision_idx}/{len(trajectory)}")
                print(f"      Position: ({trajectory[first_collision_idx][0]:.2f}, "
                      f"{trajectory[first_collision_idx][1]:.2f}, "
                      f"{trajectory[first_collision_idx][2]:.2f}) km")
                
                # Identifier le cylindre en collision
                for cyl_idx in colliding_indices:
                    cyl = cylinders[cyl_idx]
                    dist = np.sqrt((trajectory[first_collision_idx][0] - cyl['x'])**2 + 
                                 (trajectory[first_collision_idx][1] - cyl['y'])**2)
                    print(f"      Cylindre {cyl_idx}: centre=({cyl['x']:.1f}, {cyl['y']:.1f}), "
                          f"rayon={cyl['radius']:.2f} km, distance={dist:.2f} km")
                
                # Réinitialiser le stockage des tentatives pour cette nouvelle trajectoire
                self.retry_trajectories = []
                self.retry_trajectories_info = []
                
                # RECALCULER avec marges augmentées (tentatives multiples)
                print(f"\n   🔄 RECALCUL avec marges de sécurité augmentées...")
                
                for attempt in range(5):
                    safety_factor = 2.0 + attempt * 0.5  # 2.0, 2.5, 3.0, 3.5, 4.0 km
                    print(f"\n   Tentative {attempt + 1}/5 - Facteur de sécurité: {safety_factor:.1f} km")
                    
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
                    print(f"\n   ⛔ ÉCHEC avec marges normales - AUCUN CONTOURNEMENT POSSIBLE")
                    
                    # Toutes les tentatives avec marges augmentées ont échoué
                    print(f"   � Toutes les tentatives de recalcul ont échoué")
                    print(f"   🚫 AUCUNE TRAJECTOIRE SÛRE TROUVÉE depuis cette position")
                    print(f"   💡 Suggestions:")
                    print(f"      • Déplacer l'avion plus loin des obstacles")
                    print(f"      • Réduire la taille ou le nombre d'obstacles")
                    print(f"      • Changer la position du FAF ou de l'aéroport")
                    
                    # SÉCURITÉ ABSOLUE : ne jamais retourner une trajectoire avec collision
                    return None, {}
            else:
                print(f"   ✅ Aucune collision - Trajectoire VALIDE")
        
        # Calculer le nombre de points du virage (tous les segments sauf le premier)
        n_turn_points = len(trajectory) - len(initial_segment)
        
        print(f"\n   ✅ Trajectoire complète: {len(trajectory)} points")
        print(f"      - Segment 1 (vol initial): {len(initial_segment)} points")
        print(f"      - Segment 2 (virage→FAF): {n_turn_points} points")
        if len(waypoints_2d) > 2:
            print(f"      - Waypoints de contournement: {len(waypoints_2d) - 2}")
        print(f"   ✈️  L'avion est aligné avec la piste en arrivant au FAF")
        print("=" * 70 + "\n")
        
        # Calculer les paramètres
        parameters = self._calculate_parameters(trajectory, aircraft.speed)
        parameters['intercept_point'] = faf_pos[:2]  # Le point d'interception est maintenant le FAF
        parameters['initial_segment_end'] = len(initial_segment)
        parameters['turn_segment_end'] = len(trajectory)  # Le virage se termine au FAF
        parameters['runway_alignment'] = True  # Marqueur pour l'affichage
        parameters['n_points'] = len(trajectory)
        
        return trajectory, parameters
    
    def _calculate_trajectory_along_runway(self, aircraft, start_pos, faf_pos, runway_dir):
        """
        Calcule la trajectoire le long de l'axe piste avec gestion altitude (palier, transition smooth,
        descente à pente max) pour arriver exactement au FAF.
        """
        
        horizontal_distance = np.linalg.norm(faf_pos[:2] - start_pos[:2])
        altitude_diff = faf_pos[2] - start_pos[2]
        
        # Si pas de descente nécessaire
        if altitude_diff >= -0.01:
            n_points = max(100, int(horizontal_distance * 100))
            trajectory = np.zeros((n_points, 3))
            for i in range(n_points):
                t = i / (n_points - 1)
                trajectory[i] = start_pos + t * (faf_pos - start_pos)
            return trajectory
        
        # Descente avec contrainte de pente
        max_descent_slope_rad = np.radians(aircraft.max_descent_slope)
        min_descent_distance = abs(altitude_diff / np.tan(max_descent_slope_rad))
        
        # Distance de transition
        transition_distance = max(min(min_descent_distance * 0.15, 2.0), 0.5)
        
        if horizontal_distance < min_descent_distance + transition_distance:
            level_distance = 0
        else:
            level_distance = horizontal_distance - min_descent_distance - transition_distance
        
        # Construire la trajectoire avec transitions ultra-douces
        n_points = max(500, int(horizontal_distance * 100))
        trajectory = np.zeros((n_points, 3))
        
        # Augmenter la distance de transition pour une descente encore plus douce
        transition_distance = max(min(min_descent_distance * 0.25, 3.0), 1.0)
        
        if horizontal_distance < min_descent_distance + transition_distance:
            level_distance = 0
        else:
            level_distance = horizontal_distance - min_descent_distance - transition_distance
        
        for i in range(n_points):
            t = i / (n_points - 1)
            current_distance = t * horizontal_distance
            
            # Position horizontale le long de l'axe
            trajectory[i, :2] = start_pos[:2] + runway_dir * current_distance
            
            # Altitude avec phases ultra-lissées
            if current_distance < level_distance:
                # Phase 1: Vol en palier
                trajectory[i, 2] = start_pos[2]
            elif current_distance < level_distance + transition_distance:
                # Phase 2: Transition ultra-douce avec smoothstep quintic (dérivées 1 et 2 nulles)
                transition_progress = (current_distance - level_distance) / transition_distance
                # Smoothstep quintic: 6t⁵ - 15t⁴ + 10t³ (variation de pente très progressive)
                smooth_factor = 6 * transition_progress**5 - 15 * transition_progress**4 + 10 * transition_progress**3
                descent_in_transition = transition_distance * abs(np.tan(max_descent_slope_rad))
                trajectory[i, 2] = start_pos[2] - smooth_factor * descent_in_transition
            else:
                # Phase 3: Descente constante
                descent_distance = current_distance - level_distance - transition_distance
                descent_so_far = transition_distance * abs(np.tan(max_descent_slope_rad))
                additional_descent = descent_distance * abs(np.tan(max_descent_slope_rad))
                trajectory[i, 2] = start_pos[2] - descent_so_far - additional_descent
        
        # Finir exactement au FAF avec transition douce d'altitude
        # Lisser les derniers points pour éviter une chute brutale
        n_smooth_end = min(200, len(trajectory) // 5)  # Points pour lissage final
        if n_smooth_end > 0 and len(trajectory) > n_smooth_end:
            target_altitude = faf_pos[2]
            start_smooth_idx = len(trajectory) - n_smooth_end
            start_altitude = trajectory[start_smooth_idx][2]
            
            for i in range(n_smooth_end):
                idx = start_smooth_idx + i
                t = i / (n_smooth_end - 1)
                # Progression douce de l'altitude vers le FAF
                trajectory[idx][2] = start_altitude + t * (target_altitude - start_altitude)
        
        # Finir exactement au FAF
        trajectory[-1] = faf_pos
        
        return trajectory
    
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
    
    def _check_slope_feasibility(self, aircraft, start_pos, target_pos):
        """
        Vérifie si la pente directe vers le FAF respecte la pente max autorisée.
        Calcule l'altitude excédentaire nécessitant des tours en spirale si la pente est trop forte.
        """
        # Distance horizontale directe
        horizontal_distance = np.linalg.norm(target_pos[:2] - start_pos[:2])
        altitude_diff = target_pos[2] - start_pos[2]
        
        if horizontal_distance < 0.01:
            return True, 0.0, 0.0
        
        # Pente nécessaire (en degrés)
        required_slope = np.degrees(np.arctan(altitude_diff / horizontal_distance))
        
        # Vérifier si on dépasse la pente maximale de descente
        max_descent = abs(aircraft.max_descent_slope)  # Valeur positive
        
        if altitude_diff < 0 and abs(required_slope) > max_descent:
            # Calcul de l'altitude excédentaire qui nécessite des tours
            min_descent_distance = abs(altitude_diff) / np.tan(np.radians(max_descent))
            excess_altitude = abs(altitude_diff) - (horizontal_distance * np.tan(np.radians(max_descent)))
            return False, required_slope, excess_altitude
        
        return True, required_slope, 0.0
    
    def _calculate_altitude_reduction_turns(self, aircraft, start_pos, target_pos, excess_altitude, cylinders=None):
        """
        Génère des tours en spirale pour perdre l'altitude excédentaire avec évitement d'obstacles.
        Calcule le nombre de tours nécessaires, trouve un centre sûr, génère la spirale avec transitions
        douces et vérifie les collisions.
        """
        if cylinders is None:
            cylinders = []
            
        print(f"\n🌀 CALCUL DE TOURS POUR RÉDUCTION D'ALTITUDE AVEC ÉVITEMENT")
        print("-" * 60)
        print(f"💡 Altitude excédentaire à perdre: {excess_altitude:.2f} km")
        print(f"🚧 Obstacles à éviter: {len(cylinders)}")
        
        # Paramètres de la spirale avec sécurité renforcée
        turn_radius = aircraft.calculate_min_turn_radius()
        
        # Ajuster le rayon si nécessaire pour éviter les obstacles
        adjusted_radius = self._adjust_turn_radius_for_obstacles(turn_radius, start_pos, cylinders)
        if adjusted_radius != turn_radius:
            print(f"🔄 Rayon de virage ajusté: {turn_radius:.3f} → {adjusted_radius:.3f} km (évitement obstacles)")
            turn_radius = adjusted_radius
        else:
            print(f"🔄 Rayon de virage: {turn_radius:.3f} km")
        
        # Vitesse de descente pendant les tours (conservatrice pour sécurité)
        # Réduire encore plus si obstacles proches
        safety_factor = 0.6 if cylinders else 0.7  # Plus conservateur avec obstacles
        safe_descent_rate = abs(aircraft.max_descent_slope) * safety_factor
        print(f"⬇️  Taux de descente pendant tours: {safe_descent_rate:.1f}° (facteur sécurité: {safety_factor})")
        
        # Calculer le nombre de tours nécessaires
        turn_circumference = 2 * np.pi * turn_radius
        descent_per_turn = turn_circumference * np.tan(np.radians(safe_descent_rate))
        num_turns = excess_altitude / descent_per_turn
        
        # Limiter le nombre de tours pour éviter la spirale infinie
        max_turns = 5.0  # Maximum 5 tours
        if num_turns > max_turns:
            print(f"⚠️  Limitation du nombre de tours: {num_turns:.1f} → {max_turns}")
            num_turns = max_turns
            # Recalculer le taux de descente nécessaire
            required_descent_per_turn = excess_altitude / num_turns
            required_descent_rate = np.degrees(np.arctan(required_descent_per_turn / turn_circumference))
            
            # Vérifier que c'est encore sûr
            max_safe_rate = abs(aircraft.max_descent_slope) * 0.9
            if required_descent_rate > max_safe_rate:
                print(f"⚠️  Taux de descente requis trop élevé: {required_descent_rate:.1f}° > {max_safe_rate:.1f}°")
                # Utiliser le taux maximum et accepter de ne pas perdre toute l'altitude
                safe_descent_rate = max_safe_rate
                achievable_descent = num_turns * turn_circumference * np.tan(np.radians(safe_descent_rate))
                print(f"💡 Altitude réellement perdue dans les tours: {achievable_descent:.2f} km sur {excess_altitude:.2f} km")
            else:
                safe_descent_rate = required_descent_rate
        
        print(f"📐 Périmètre par tour: {turn_circumference:.2f} km")
        print(f"📉 Descente par tour: {turn_circumference * np.tan(np.radians(safe_descent_rate)):.3f} km")
        print(f"🔢 Nombre de tours: {num_turns:.1f}")
        
        # Choisir une position pour la spirale qui évite les obstacles
        spiral_center = self._find_safe_spiral_center(start_pos, target_pos, turn_radius, cylinders)
        
        # Vérifier que la spirale complète évite les obstacles
        spiral_is_safe = self._verify_spiral_clearance(spiral_center, turn_radius, start_pos[2], cylinders)
        if not spiral_is_safe:
            print(f"⚠️  Spirale initiale non sûre, recherche position alternative...")
            spiral_center = self._find_alternative_spiral_center(start_pos, target_pos, turn_radius, cylinders)
        
        print(f"⭕ Centre de spirale final: ({spiral_center[0]:.1f}, {spiral_center[1]:.1f}) km")
        
        # Générer la trajectoire en spirale avec évitement intégré
        spiral_trajectory = self._generate_spiral_trajectory(
            start_pos, spiral_center, turn_radius, num_turns, 
            min(excess_altitude, num_turns * turn_circumference * np.tan(np.radians(safe_descent_rate))),
            safe_descent_rate
        )
        
        # Vérification finale de non-collision
        collision_check = self._check_trajectory_collision(spiral_trajectory, cylinders)
        if collision_check[0]:  # Si collision détectée
            print(f"❌ COLLISION DÉTECTÉE dans la spirale ! Ajustement d'urgence...")
            # Déplacer la spirale plus loin des obstacles
            safe_center = self._emergency_spiral_positioning(start_pos, target_pos, turn_radius, cylinders)
            spiral_trajectory = self._generate_spiral_trajectory(
                start_pos, safe_center, turn_radius * 1.2, num_turns * 0.8, 
                excess_altitude * 0.8, safe_descent_rate
            )
        
        # Position finale après les tours
        final_position = spiral_trajectory[-1].copy()
        altitude_lost = start_pos[2] - final_position[2]
        
        print(f"🎯 Position finale après tours: ({final_position[0]:.1f}, {final_position[1]:.1f}, {final_position[2]:.1f}) km")
        print(f"✅ Altitude perdue: {altitude_lost:.2f} km (objectif: {excess_altitude:.2f} km)")
        
        if altitude_lost < excess_altitude * 0.9:
            print(f"💡 Note: Altitude restante à perdre sera gérée par descente normale vers FAF")
        
        return spiral_trajectory, final_position
    
    def _adjust_turn_radius_for_obstacles(self, base_radius, start_pos, cylinders):
        """
        Augmente le rayon de virage si des obstacles sont proches pour maintenir la distance
        de sécurité. Limite l'augmentation à 50% du rayon de base.
        """
        if not cylinders:
            return base_radius
        
        adjusted_radius = base_radius
        
        for cylinder in cylinders:
            cyl_center = np.array([cylinder['x'], cylinder['y']])
            dist_to_obstacle = np.linalg.norm(start_pos[:2] - cyl_center)
            
            # Si l'obstacle est proche, augmenter le rayon pour maintenir la distance de sécurité
            safety_distance = cylinder['radius'] + 1.5  # 1.5 km de marge
            required_radius = max(base_radius, dist_to_obstacle - safety_distance)
            
            if required_radius > adjusted_radius:
                adjusted_radius = required_radius
        
        # Limiter l'augmentation à 50% du rayon de base
        return min(adjusted_radius, base_radius * 1.5)
    
    def _verify_spiral_clearance(self, center, radius, altitude, cylinders):
        """
        Vérifie que la spirale (cercle de rayon donné centré en 'center') ne traverse aucun
        obstacle en comparant les distances centre-obstacle avec les rayons requis.
        """
        for cylinder in cylinders:
            if altitude <= cylinder['height'] + 0.5:  # Marge verticale
                cyl_center = np.array([cylinder['x'], cylinder['y']])
                dist_center_to_obstacle = np.linalg.norm(center - cyl_center)
                required_clearance = radius + cylinder['radius'] + 0.8  # Marge de sécurité
                
                if dist_center_to_obstacle < required_clearance:
                    return False
        
        return True
    
    def _find_alternative_spiral_center(self, start_pos, target_pos, turn_radius, cylinders):
        """
        Recherche par grille radiale pour trouver le centre de spirale le plus éloigné de tous
        les obstacles (maximise la distance minimale aux obstacles).
        """
        # Calculer le point le plus éloigné de tous les obstacles
        best_center = start_pos[:2] + np.array([turn_radius * 2, 0])  # Position par défaut
        max_min_distance = 0
        
        # Grille de recherche autour de la position de départ
        search_radius = turn_radius * 4
        grid_size = 20
        
        for i in range(grid_size):
            for j in range(grid_size):
                # Position candidate
                angle = (i * 2 * np.pi) / grid_size
                distance = (j + 1) * search_radius / grid_size
                
                candidate = start_pos[:2] + distance * np.array([np.cos(angle), np.sin(angle)])
                
                # Calculer la distance minimum à tous les obstacles
                min_dist_to_obstacles = float('inf')
                for cylinder in cylinders:
                    cyl_center = np.array([cylinder['x'], cylinder['y']])
                    dist = np.linalg.norm(candidate - cyl_center) - cylinder['radius']
                    min_dist_to_obstacles = min(min_dist_to_obstacles, dist)
                
                # Garder la position avec la plus grande distance minimum
                if min_dist_to_obstacles > max_min_distance:
                    max_min_distance = min_dist_to_obstacles
                    best_center = candidate
        
        return best_center
    
    def _emergency_spiral_positioning(self, start_pos, target_pos, turn_radius, cylinders):
        """
        Positionnement d'urgence : teste 16 directions à 3 distances différentes et choisit
        la position la plus éloignée des obstacles.
        """
        # Aller le plus loin possible des obstacles
        if not cylinders:
            return start_pos[:2] + np.array([turn_radius * 3, 0])
        
        # Trouver le point le plus éloigné dans un rayon raisonnable
        max_distance = 0
        best_position = start_pos[:2]
        
        for angle in np.linspace(0, 2*np.pi, 16):
            for dist in [turn_radius * 3, turn_radius * 4, turn_radius * 5]:
                test_pos = start_pos[:2] + dist * np.array([np.cos(angle), np.sin(angle)])
                
                min_dist_to_obstacles = float('inf')
                for cylinder in cylinders:
                    cyl_center = np.array([cylinder['x'], cylinder['y']])
                    dist_to_cyl = np.linalg.norm(test_pos - cyl_center)
                    min_dist_to_obstacles = min(min_dist_to_obstacles, dist_to_cyl)
                
                if min_dist_to_obstacles > max_distance:
                    max_distance = min_dist_to_obstacles
                    best_position = test_pos
        
        return best_position
    
    def _find_safe_spiral_center(self, start_pos, target_pos, turn_radius, cylinders):
        """
        Recherche intelligente du meilleur centre de spirale en testant 4 directions (droite, gauche,
        arrière-droite, arrière-gauche) à distances croissantes. Évalue chaque position avec un score
        de sécurité basé sur les distances aux obstacles et l'orientation vers le FAF.
        """
        print(f"   🔍 Recherche centre de spirale sûr (rayon: {turn_radius:.3f} km)")
        
        # Direction vers le FAF pour orientation
        direction_to_faf = target_pos[:2] - start_pos[:2]
        if np.linalg.norm(direction_to_faf) > 0.01:
            direction_to_faf = direction_to_faf / np.linalg.norm(direction_to_faf)
        else:
            direction_to_faf = np.array([1.0, 0.0])
        
        # Vecteurs perpendiculaires (droite et gauche)
        perp_right = np.array([-direction_to_faf[1], direction_to_faf[0]])
        perp_left = -perp_right
        
        # Marges de sécurité variables selon la distance aux obstacles
        base_safety_margin = 0.8  # Marge de base
        
        # Analyser les obstacles pour déterminer la meilleure stratégie
        if cylinders:
            print(f"   🚧 Analyse de {len(cylinders)} obstacle(s):")
            for i, cyl in enumerate(cylinders):
                dist_to_start = np.linalg.norm(np.array([cyl['x'], cyl['y']]) - start_pos[:2])
                print(f"      Obstacle {i+1}: centre=({cyl['x']:.1f}, {cyl['y']:.1f}), "
                      f"rayon={cyl['radius']:.2f} km, distance={dist_to_start:.2f} km")
        
        # Essayer différentes positions avec analyse fine
        best_center = None
        best_score = -1  # Score de qualité (plus élevé = meilleur)
        
        # Directions à tester (droite, gauche, arrière-droite, arrière-gauche)
        test_directions = [perp_right, perp_left, 
                          (perp_right - direction_to_faf).astype(float), 
                          (perp_left - direction_to_faf).astype(float)]
        
        # Normaliser les directions diagonales
        for i in range(2, len(test_directions)):
            test_directions[i] = test_directions[i] / np.linalg.norm(test_directions[i])
        
        direction_names = ["droite", "gauche", "arrière-droite", "arrière-gauche"]
        
        for dir_idx, test_direction in enumerate(test_directions):
            for distance_factor in [1.2, 1.5, 2.0, 2.5, 3.0]:  # Distances croissantes
                test_center = start_pos[:2] + test_direction * turn_radius * distance_factor
                
                # Calculer le score de cette position
                score = self._evaluate_spiral_center_safety(
                    test_center, turn_radius, cylinders, start_pos, target_pos, base_safety_margin
                )
                
                if score > best_score:
                    best_score = score
                    best_center = test_center
                    print(f"   ⭐ Nouveau meilleur centre: {direction_names[dir_idx]} "
                          f"(distance {distance_factor:.1f}x, score {score:.2f})")
                
                # Si on trouve un score parfait, pas besoin de chercher plus
                if score >= 10.0:
                    break
            
            if best_score >= 10.0:
                break
        
        if best_center is not None:
            print(f"   ✅ Centre optimal trouvé avec score {best_score:.2f}")
            return best_center
        else:
            # Fallback : position par défaut éloignée des obstacles
            default_center = start_pos[:2] + perp_right * turn_radius * 3.0
            print(f"   ⚠️  Aucun centre optimal, utilisation position de secours")
            return default_center
    
    def _evaluate_spiral_center_safety(self, center, turn_radius, cylinders, start_pos, target_pos, base_margin):
        """
        Calcule un score de sécurité (0-10+) pour un centre de spirale : pénalités pour collisions
        avec obstacles, bonus pour distances de sécurité supplémentaires, proximité raisonnable
        au point de départ et orientation favorable vers le FAF.
        """
        score = 10.0  # Score de base
        
        # Vérifier les collisions avec obstacles
        for cylinder in cylinders:
            cyl_center = np.array([cylinder['x'], cylinder['y']])
            cyl_radius = cylinder['radius']
            cyl_height = cylinder['height']
            
            # Distance entre le centre de spirale et l'obstacle
            dist_center_to_obstacle = np.linalg.norm(center - cyl_center)
            
            # Distance minimale requise (rayon spirale + rayon obstacle + marge)
            required_clearance = turn_radius + cyl_radius + base_margin
            
            if dist_center_to_obstacle < required_clearance:
                # Collision ! Score très bas
                overlap = required_clearance - dist_center_to_obstacle
                score -= overlap * 5.0  # Pénalité importante pour collision
            else:
                # Bonus pour distance de sécurité supplémentaire
                extra_clearance = dist_center_to_obstacle - required_clearance
                score += min(extra_clearance * 0.5, 2.0)  # Bonus limité
            
            # Vérifier si l'altitude de vol est compatible
            flight_altitude = start_pos[2]  # Altitude approximative pendant les tours
            if flight_altitude <= cyl_height + 0.3:  # Marge verticale de 300m
                # Obstacle peut affecter la trajectoire verticalement
                vertical_clearance = flight_altitude - cyl_height
                if vertical_clearance < 0.5:  # Moins de 500m de marge
                    score -= (0.5 - vertical_clearance) * 3.0
        
        # Bonus pour proximité raisonnable du point de départ
        dist_to_start = np.linalg.norm(center - start_pos[:2])
        if dist_to_start < turn_radius * 4:  # Pas trop loin
            score += 1.0
        elif dist_to_start > turn_radius * 6:  # Trop loin
            score -= (dist_to_start - turn_radius * 6) * 0.2
        
        # Bonus pour orientation favorable vers le FAF
        to_faf = target_pos[:2] - start_pos[:2]
        to_center = center - start_pos[:2]
        if np.linalg.norm(to_faf) > 0.01 and np.linalg.norm(to_center) > 0.01:
            cos_angle = np.dot(to_faf, to_center) / (np.linalg.norm(to_faf) * np.linalg.norm(to_center))
            if cos_angle < 0:  # Centre dans la direction opposée au FAF (bon pour spirale)
                score += abs(cos_angle) * 1.5
        
        return max(0.0, score)  # Score ne peut pas être négatif
    
    def _generate_spiral_trajectory(self, start_pos, spiral_center, turn_radius, num_turns, total_descent, descent_rate):
        """
        Génère une spirale avec 3 phases (entrée 15%, stable 70%, sortie 15%) et transitions ultra-douces
        (smoothstep quintic) pour éviter les à-coups. Haute densité de points (720/tour) et lissage final.
        """
        # Angle total à parcourir
        total_angle = num_turns * 2 * np.pi
        
        # Nombre de points (très haute densité pour trajectoire ultra-lisse)
        points_per_turn = 720  # 2 points par degré pour maximum de fluidité
        total_points = int(num_turns * points_per_turn)
        total_points = max(200, total_points)  # Minimum 200 points
        
        # Angle initial (de la position de départ vers le centre)
        initial_vec = start_pos[:2] - spiral_center
        initial_angle = np.arctan2(initial_vec[1], initial_vec[0])
        
        # Phases de la spirale pour transitions douces
        entry_phase = 0.15    # 15% pour l'entrée en spirale
        stable_phase = 0.70   # 70% pour la spirale stable
        exit_phase = 0.15     # 15% pour la sortie de spirale
        
        # Générer la trajectoire avec transitions progressives
        trajectory = np.zeros((total_points, 3))
        
        for i in range(total_points):
            # Progression de 0 à 1
            t = i / (total_points - 1)
            
            # Déterminer la phase actuelle
            if t < entry_phase:
                # Phase d'entrée : transition douce vers la spirale
                phase_t = t / entry_phase
                # Fonction de transition smooth (évite les à-coups)
                smooth_factor = self._smooth_transition(phase_t)
                
                # Rayon qui augmente progressivement vers le rayon de virage
                current_radius = turn_radius * smooth_factor
                # Angle avec progression ralentie au début
                angle_progress = smooth_factor * (entry_phase * total_angle)
                
                # Descente ralentie pendant l'entrée (évite pic de chute)
                descent_factor = smooth_factor * 0.5  # Descente réduite pendant l'entrée
                
            elif t < entry_phase + stable_phase:
                # Phase stable : spirale constante
                phase_start = entry_phase
                phase_t = (t - phase_start) / stable_phase
                
                current_radius = turn_radius  # Rayon constant
                angle_progress = entry_phase * total_angle + phase_t * (stable_phase * total_angle)
                
                # Descente constante et progressive
                descent_factor = 0.5 + phase_t * 0.4  # De 50% à 90% du taux normal
                
            else:
                # Phase de sortie : transition douce vers trajectoire normale
                phase_start = entry_phase + stable_phase
                phase_t = (t - phase_start) / exit_phase
                # Fonction de transition inverse pour sortie douce
                smooth_factor = 1.0 - self._smooth_transition(phase_t)
                
                current_radius = turn_radius * (0.7 + 0.3 * smooth_factor)  # Rayon qui se stabilise
                angle_progress = (entry_phase + stable_phase) * total_angle + phase_t * (exit_phase * total_angle)
                
                # Descente qui se stabilise vers la fin
                descent_factor = 0.9 + phase_t * 0.1  # De 90% à 100%
            
            # Angle actuel
            angle = initial_angle + angle_progress
            
            # Position horizontale avec rayon variable pour transitions douces
            x = spiral_center[0] + current_radius * np.cos(angle)
            y = spiral_center[1] + current_radius * np.sin(angle)
            
            # Altitude avec descente progressive et sans à-coups
            # Utilisation d'une fonction smooth pour éviter les pics
            base_descent = t * total_descent
            smooth_descent = base_descent * descent_factor
            
            # Application d'une fonction de lissage supplémentaire
            if i > 0:
                # Éviter les variations trop brusques d'altitude
                prev_altitude = trajectory[i-1, 2]
                target_altitude = start_pos[2] - smooth_descent
                max_altitude_change = 0.01  # Limite la variation d'altitude entre points (10m)
                
                altitude_change = target_altitude - prev_altitude
                if abs(altitude_change) > max_altitude_change:
                    altitude_change = np.sign(altitude_change) * max_altitude_change
                
                z = prev_altitude + altitude_change
            else:
                z = start_pos[2] - smooth_descent
            
            trajectory[i] = [x, y, z]
        
        # Vérification et lissage final pour éviter les discontinuités
        trajectory = self._smooth_trajectory(trajectory)
        
        print(f"   🌀 Spirale générée avec transitions douces: {len(trajectory)} points sur {num_turns:.1f} tours")
        print(f"   📐 Points par tour: {points_per_turn} (haute densité)")
        print(f"   🔄 Phases: entrée {entry_phase*100:.0f}%, stable {stable_phase*100:.0f}%, sortie {exit_phase*100:.0f}%")
        return trajectory
    
    def _smooth_transition(self, t):
        """
        Fonction smoothstep de degré 5 : f(t) = 6t⁵ - 15t⁴ + 10t³
        Garantit dérivées nulles en 0 et 1 pour transitions sans à-coups.
        """
        # Smoothstep de degré 5: f(t) = 6t^5 - 15t^4 + 10t^3
        t = np.clip(t, 0.0, 1.0)
        return 6 * t**5 - 15 * t**4 + 10 * t**3
    
    def _smooth_trajectory(self, trajectory):
        """
        Lissage final de l'altitude par moyenne mobile pondérée (25%-50%-25%) pour éliminer
        les discontinuités résiduelles.
        """
        if len(trajectory) < 3:
            return trajectory
        
        smoothed = trajectory.copy()
        
        # Lissage par moyenne mobile pondérée sur l'altitude uniquement
        for i in range(1, len(trajectory) - 1):
            # Pondération: 25% point précédent, 50% point actuel, 25% point suivant
            smoothed[i, 2] = (0.25 * trajectory[i-1, 2] + 
                             0.50 * trajectory[i, 2] + 
                             0.25 * trajectory[i+1, 2])
        
        return smoothed
    
    def calculate_trajectory_with_automatic_turns(self, aircraft, cylinders=None):
        """
        Détecte si la pente directe est trop forte, génère des tours en spirale pour perdre
        l'altitude excédentaire si nécessaire, puis calcule une trajectoire normale vers le FAF.
        """
        if cylinders is None:
            cylinders = []
            
        start_pos = aircraft.position.copy()
        faf_pos = self.environment.faf_position.copy()
        
        print("\n" + "="*70)
        print("🛩️  CALCUL TRAJECTOIRE AVEC TOURS AUTOMATIQUES POUR PENTE")
        print("="*70)
        
        # Vérifier la faisabilité de la pente directe
        is_feasible, required_slope, excess_altitude = self._check_slope_feasibility(aircraft, start_pos, faf_pos)
        
        print(f"📊 Analyse de pente:")
        print(f"   Position avion: ({start_pos[0]:.1f}, {start_pos[1]:.1f}, {start_pos[2]:.1f}) km")
        print(f"   Position FAF: ({faf_pos[0]:.1f}, {faf_pos[1]:.1f}, {faf_pos[2]:.1f}) km")
        
        # Calculs détaillés pour debug
        horizontal_distance = np.linalg.norm(faf_pos[:2] - start_pos[:2])
        altitude_diff = start_pos[2] - faf_pos[2]
        print(f"   Distance horizontale: {horizontal_distance:.2f} km")
        print(f"   Différence d'altitude: {altitude_diff:.2f} km")
        print(f"   Pente nécessaire: {required_slope:.1f}°")
        print(f"   Pente max autorisée: {abs(aircraft.max_descent_slope):.1f}°")
        print(f"   Altitude excédentaire: {excess_altitude:.2f} km")
        
        if is_feasible:
            print(f"✅ Pente faisable - trajectoire normale")
            return self.calculate_trajectory(aircraft, cylinders)
        
        print(f"❌ Pente trop forte - tours automatiques nécessaires")
        print(f"💡 Altitude excédentaire: {excess_altitude:.2f} km")
        
        # Calculer les tours pour réduire l'altitude
        spiral_trajectory, final_position = self._calculate_altitude_reduction_turns(
            aircraft, start_pos, faf_pos, excess_altitude, cylinders
        )
        
        # Créer un avion virtuel à la position finale des tours
        aircraft_after_turns = Aircraft(
            position=final_position,
            speed=aircraft.speed,
            heading=aircraft.heading,
            aircraft_type=aircraft.aircraft_type
        )
        
        # Calculer la trajectoire finale vers le FAF
        print(f"\n🎯 Calcul trajectoire finale vers FAF...")
        final_trajectory, final_parameters = self.calculate_trajectory(aircraft_after_turns, cylinders)
        
        # Combiner les deux trajectoires
        combined_trajectory = np.vstack([spiral_trajectory, final_trajectory])
        
        # Calculer les paramètres combinés
        combined_parameters = self._calculate_parameters(combined_trajectory, aircraft.speed)
        combined_parameters['has_altitude_turns'] = True
        combined_parameters['spiral_points'] = len(spiral_trajectory)
        combined_parameters['excess_altitude_reduced'] = excess_altitude
        combined_parameters['turns_completed'] = len(spiral_trajectory) / (360 if len(spiral_trajectory) > 360 else len(spiral_trajectory))
        
        print(f"\n✅ TRAJECTOIRE AVEC TOURS AUTOMATIQUES TERMINÉE")
        print(f"   - Tours de réduction d'altitude: {len(spiral_trajectory)} points")
        print(f"   - Trajectoire finale vers FAF: {len(final_trajectory)} points")
        print(f"   - Total: {len(combined_trajectory)} points")
        print("="*70)
        
        return combined_trajectory, combined_parameters
    
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
                print(f"   🚧 Obstacle détecté - création waypoints de contournement")
                print(f"      Distance au segment: {dist_to_segment:.2f} km (rayon+marge: {cyl_radius:.2f} km)")
                
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
                
                print(f"   ↪️  Point entrée: ({entry_point[0]:.1f}, {entry_point[1]:.1f}) - distance au centre: {np.linalg.norm(entry_point - cyl_center):.2f} km")
                print(f"   ↩️  Point sortie: ({exit_point[0]:.1f}, {exit_point[1]:.1f}) - distance au centre: {np.linalg.norm(exit_point - cyl_center):.2f} km")
                print(f"   ✅ Contournement par la {'droite' if side > 0 else 'gauche'}")
        
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
    
    def _calculate_avoidance_point(self, start_pos, target_pos, cylinder, safety_margin=0.5):
        """
        Génère un point de contournement latéral autour d'un obstacle cylindrique.
        Projette le segment sur le cylindre, trouve le point le plus proche, puis crée
        un waypoint à l'extérieur du rayon élargi (rayon + marge). L'altitude est ajustée
        pour rester au-dessus de l'obstacle si nécessaire.
        """
        cyl_center = np.array([cylinder['x'], cylinder['y']])
        cyl_radius = cylinder['radius'] + safety_margin
        
        # Direction du segment start -> target
        direction = target_pos[:2] - start_pos[:2]
        segment_length = np.linalg.norm(direction)
        
        if segment_length < 0.01:
            # Points trop proches, contourner perpendiculairement
            perp = np.array([-1, 1])
            avoidance_2d = cyl_center + perp * cyl_radius
        else:
            direction_unit = direction / segment_length
            
            # Perpendiculaire à la direction
            perp = np.array([-direction_unit[1], direction_unit[0]])
            
            # Vecteur du centre du cylindre vers le segment
            to_start = start_pos[:2] - cyl_center
            projection = np.dot(to_start, direction_unit)
            
            # Point le plus proche sur le segment
            closest_on_segment = start_pos[:2] + direction_unit * np.clip(projection, 0, segment_length)
            
            # Direction du centre vers le point le plus proche
            to_closest = closest_on_segment - cyl_center
            dist_to_closest = np.linalg.norm(to_closest)
            
            if dist_to_closest > 0.01:
                # Contourner dans la direction perpendiculaire la plus proche
                outward = to_closest / dist_to_closest
            else:
                # Si on est pile au centre, utiliser la perpendiculaire
                outward = perp
            
            # Point de contournement : sur le cercle élargi
            avoidance_2d = cyl_center + outward * cyl_radius
        
        # Altitude : moyenne entre start et target, mais au-dessus du cylindre si nécessaire
        avg_altitude = (start_pos[2] + target_pos[2]) / 2
        min_altitude = cylinder['height'] + safety_margin
        avoidance_altitude = max(avg_altitude, min_altitude)
        
        return np.array([avoidance_2d[0], avoidance_2d[1], avoidance_altitude])
