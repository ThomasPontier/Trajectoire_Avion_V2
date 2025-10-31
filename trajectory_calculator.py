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
        avec alignement progressif sur l'axe de la piste.
        
        Stratégie V1.4:
        - Vol initial dans le cap de l'avion
        - Virage progressif pour s'aligner avec l'axe de la piste
        - Suivi de l'axe jusqu'au FAF avec descente
        
        Note: Cette méthode est utilisée quand "Virages réalistes" est DÉSACTIVÉ.
        Elle crée une trajectoire qui s'aligne avec l'axe de la piste (aéroport→FAF).
        
        Args:
            aircraft: Instance de la classe Aircraft
            
        Returns:
            tuple: (trajectory, parameters)
                - trajectory: Array numpy de positions [N x 3]
                - parameters: Dict avec les paramètres au cours du temps
        """
        
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
        
        # Construire la trajectoire en 3 phases
        return self._build_trajectory_with_runway_alignment(
            aircraft, start_pos, intercept_point, faf_pos, 
            current_direction, runway_direction
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
    
    def _calculate_trajectory_with_initial_turn(self, aircraft, start_pos, target_pos, 
                                                current_direction, target_direction):
        """
        Calcule une trajectoire avec un segment initial dans la direction du cap,
        puis un virage pour s'aligner vers le FAF.
        
        Cette méthode crée :
        1. Un segment en ligne droite dans la direction du cap initial
        2. Un arc de cercle pour tourner vers la direction du FAF
        3. Une ligne droite vers le FAF avec gestion de l'altitude
        
        Args:
            aircraft: Instance de la classe Aircraft
            start_pos: Position de départ [x, y, z]
            target_pos: Position cible (FAF) [x, y, z]
            current_direction: Direction actuelle de l'avion (vecteur unitaire 2D)
            target_direction: Direction vers le FAF (vecteur unitaire 2D)
            
        Returns:
            tuple: (trajectory, parameters)
        """
        
        print("\n🔄 CALCUL TRAJECTOIRE AVEC VOL INITIAL PUIS VIRAGE")
        print("-"*70)
        
        # Calculer le rayon de virage
        min_radius = aircraft.calculate_min_turn_radius()
        print(f"📐 Rayon de virage minimum: {min_radius:.3f} km")
        
        # Distance de vol dans la direction initiale avant le virage
        # Proportionnelle à la distance totale (15-25% de la distance au FAF)
        total_distance = np.linalg.norm(target_pos[:2] - start_pos[:2])
        straight_initial_distance = min(max(total_distance * 0.2, 2.0), 10.0)  # Entre 2 et 10 km
        print(f"✈️  Distance vol initial dans le cap {aircraft.heading:.0f}°: {straight_initial_distance:.2f} km")
        
        # Phase 0: Vol en ligne droite dans la direction du cap initial
        print(f"\n🟦 Phase 0: Vol initial dans la direction du cap...")
        initial_straight_end = start_pos[:2] + current_direction * straight_initial_distance
        initial_straight_pos_3d = np.array([initial_straight_end[0], initial_straight_end[1], start_pos[2]])
        
        # Créer le segment initial
        n_initial_points = max(50, int(straight_initial_distance * 50))
        initial_trajectory = np.zeros((n_initial_points, 3))
        for i in range(n_initial_points):
            t = i / (n_initial_points - 1)
            initial_trajectory[i] = start_pos + t * (initial_straight_pos_3d - start_pos)
        
        print(f"   ✓ Segment initial créé: {len(initial_trajectory)} points")
        print(f"   📍 Position fin vol initial: ({initial_straight_end[0]:.1f}, {initial_straight_end[1]:.1f}) km")
        
        # Recalculer la direction vers le FAF depuis la nouvelle position
        new_direction_to_faf = target_pos[:2] - initial_straight_end
        new_direction_to_faf = new_direction_to_faf / np.linalg.norm(new_direction_to_faf)
        
        # Déterminer le sens de virage (gauche = 1, droite = -1)
        cross = current_direction[0] * new_direction_to_faf[1] - current_direction[1] * new_direction_to_faf[0]
        turn_direction = 1 if cross > 0 else -1
        turn_direction_text = "GAUCHE" if turn_direction > 0 else "DROITE"
        print(f"\n↪️  Sens de virage: {turn_direction_text}")
        
        # Calculer l'angle de virage nécessaire
        cos_angle = np.dot(current_direction, new_direction_to_faf)
        turn_angle = np.arccos(np.clip(cos_angle, -1.0, 1.0))
        
        # Si sens horaire, angle négatif
        if turn_direction < 0:
            turn_angle = -turn_angle
        
        print(f"📐 Angle de virage: {np.degrees(turn_angle):.1f}°")
        
        # Centre du cercle de virage (depuis la fin du vol initial)
        perp_direction = np.array([-current_direction[1], current_direction[0]]) * turn_direction
        turn_center = initial_straight_end + perp_direction * min_radius
        print(f"⭕ Centre du cercle: ({turn_center[0]:.1f}, {turn_center[1]:.1f}) km")
        
        # Point final du virage
        vec_to_start = initial_straight_end - turn_center
        cos_a = np.cos(turn_angle)
        sin_a = np.sin(turn_angle)
        rotated_vec = np.array([
            vec_to_start[0] * cos_a - vec_to_start[1] * sin_a,
            vec_to_start[0] * sin_a + vec_to_start[1] * cos_a
        ])
        
        turn_end_point = turn_center + rotated_vec
        print(f"🎯 Point fin de virage: ({turn_end_point[0]:.1f}, {turn_end_point[1]:.1f}) km")
        
        # Phase 1: Arc de virage
        print(f"\n🔵 Phase 1: Création arc de virage...")
        arc_trajectory = self._create_arc_trajectory(
            initial_straight_end, turn_center, turn_angle, min_radius, start_pos[2]
        )
        print(f"   ✓ Arc créé: {len(arc_trajectory)} points")
        
        # Phase 2: Ligne droite vers le FAF avec gestion altitude
        post_turn_pos = np.array([turn_end_point[0], turn_end_point[1], start_pos[2]])
        print(f"\n🔵 Phase 2: Trajectoire droite post-virage vers FAF...")
        print(f"   Position après virage: ({post_turn_pos[0]:.1f}, {post_turn_pos[1]:.1f}, {post_turn_pos[2]:.1f}) km")
        
        # Calculer la trajectoire droite avec contrainte de pente
        altitude_diff = target_pos[2] - post_turn_pos[2]
        print(f"   Différence d'altitude vers FAF: {altitude_diff:.2f} km")
        
        if altitude_diff < 0 and aircraft.max_descent_slope is not None:
            print(f"   ⬇️  Descente avec contrainte de pente (max {aircraft.max_descent_slope:.1f}°)")
            straight_trajectory, _ = self._calculate_trajectory_with_slope_constraint(
                aircraft, post_turn_pos, target_pos
            )
        else:
            print(f"   ➡️  Trajectoire simple vers FAF")
            straight_trajectory, _ = self._calculate_simple_trajectory(
                aircraft, post_turn_pos, target_pos
            )
        
        print(f"   ✓ Segment droit créé: {len(straight_trajectory)} points")
        
        # Combiner les trois segments
        trajectory = np.vstack([initial_trajectory, arc_trajectory, straight_trajectory])
        print(f"\n✅ TRAJECTOIRE TOTALE: {len(trajectory)} points")
        print(f"   - Segment initial: {len(initial_trajectory)} points")
        print(f"   - Arc de virage: {len(arc_trajectory)} points")
        print(f"   - Segment final: {len(straight_trajectory)} points")
        print("=" * 70 + "\n")
        
        # Calculer les paramètres
        parameters = self._calculate_parameters(trajectory, aircraft.speed)
        parameters['turn_radius'] = min_radius
        parameters['turn_angle'] = np.degrees(turn_angle)
        parameters['turn_start_point'] = initial_straight_end  # Nouveau : point de début du virage
        parameters['turn_end_point'] = turn_end_point
        parameters['intercept_point'] = turn_end_point[:2]  # Point 2D pour l'affichage
        parameters['initial_segment_end_index'] = len(initial_trajectory)  # Nouveau : index fin du segment initial
        parameters['turn_segment_end_index'] = len(initial_trajectory) + len(arc_trajectory)  # Nouveau
        parameters['n_points'] = len(trajectory)
        
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
        Calcule le point optimal d'interception sur l'axe de la piste.
        Le point est choisi pour permettre un alignement progressif AVANT le FAF.
        
        Args:
            start_pos: Position actuelle [x, y]
            current_dir: Direction actuelle (vecteur unitaire)
            airport_pos: Position de l'aéroport [x, y]
            faf_pos: Position du FAF [x, y]
            runway_dir: Direction de l'axe piste (vecteur unitaire)
            angle_to_runway: Angle entre cap actuel et axe piste (degrés)
            
        Returns:
            numpy array: Point d'interception [x, y]
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
                                                 faf_pos, current_dir, runway_dir):
        """
        Construit une trajectoire en 3 phases avec alignement progressif sur l'axe de la piste.
        
        Phase 1: Vol initial dans le cap actuel
        Phase 2: Virage progressif pour s'aligner avec l'axe de la piste
        Phase 3: Vol le long de l'axe jusqu'au FAF avec descente
        
        Args:
            aircraft: Instance Aircraft
            start_pos: Position de départ [x, y, z]
            intercept_point: Point d'interception sur l'axe [x, y]
            faf_pos: Position du FAF [x, y, z]
            current_dir: Direction actuelle (vecteur unitaire 2D)
            runway_dir: Direction de l'axe piste (vecteur unitaire 2D)
            
        Returns:
            tuple: (trajectory, parameters)
        """
        
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
        
        # Segment 2: Virage progressif jusqu'au FAF (courbe de Bézier pour un virage smooth)
        # Le virage se termine directement au FAF, avec l'avion aligné sur l'axe de piste
        n_turn = max(150, int(turn_distance * 150))
        turn_segment = np.zeros((n_turn, 3))
        
        # Points de contrôle pour la courbe de Bézier
        P0 = initial_end_point
        P3 = faf_pos[:2]  # Le virage se termine au FAF, pas à un point intermédiaire
        
        # Point de contrôle 1: continuer dans la direction initiale
        P1 = P0 + current_dir * (turn_distance * 0.35)
        
        # Point de contrôle 2: arriver aligné avec l'axe piste au FAF
        P2 = P3 - runway_dir * (turn_distance * 0.35)
        
        # Courbe de Bézier cubique avec gestion de l'altitude
        altitude_start = start_pos[2]
        altitude_end = faf_pos[2]
        altitude_diff = altitude_end - altitude_start
        
        for i in range(n_turn):
            t = i / (n_turn - 1)
            # Position horizontale (Bézier cubique)
            pos_2d = (1-t)**3 * P0 + 3*(1-t)**2*t * P1 + 3*(1-t)*t**2 * P2 + t**3 * P3
            
            # Altitude: descente très progressive avec transition douce (fonction smoothstep)
            # On maintient l'altitude initiale sur 50% du virage, puis descente ultra-lissée
            if t < 0.5:
                altitude = altitude_start
            else:
                # Descente progressive sur les 50% restants avec smoothstep cubique
                # Cette fonction donne une transition très douce avec pente qui varie lentement
                descent_t = (t - 0.5) / 0.5
                # Smoothstep: 3t² - 2t³ (dérivée nulle aux extrémités)
                smooth_t = 3 * descent_t**2 - 2 * descent_t**3
                altitude = altitude_start + smooth_t * altitude_diff
            
            turn_segment[i] = [pos_2d[0], pos_2d[1], altitude]
        
        segments.append(turn_segment)
        
        # Combiner tous les segments
        trajectory = np.vstack(segments)
        
        # S'assurer que le dernier point est exactement au FAF
        trajectory[-1] = faf_pos
        
        print(f"   ✅ Trajectoire complète: {len(trajectory)} points")
        print(f"      - Segment 1 (vol initial): {len(initial_segment)} points")
        print(f"      - Segment 2 (virage→FAF): {len(turn_segment)} points")
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
        Calcule la trajectoire le long de l'axe de la piste avec gestion de l'altitude.
        
        Args:
            aircraft: Instance Aircraft
            start_pos: Position de départ sur l'axe [x, y, z]
            faf_pos: Position du FAF [x, y, z]
            runway_dir: Direction de l'axe piste (vecteur unitaire 2D)
            
        Returns:
            numpy array: Points de la trajectoire [N x 3]
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
        
        # Finir exactement au FAF
        trajectory[-1] = faf_pos
        
        return trajectory
    
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
        
        # Calculer l'angle de cap (heading) dans le plan XY (en degrés)
        # 0° = Nord (axe Y+), 90° = Est (axe X+), sens horaire
        heading_array = np.zeros(n_points)
        for i in range(1, n_points):
            dx = trajectory[i, 0] - trajectory[i-1, 0]  # Variation en X
            dy = trajectory[i, 1] - trajectory[i-1, 1]  # Variation en Y
            if dx != 0 or dy != 0:
                # atan2(dx, dy) donne l'angle par rapport au Nord
                heading_array[i] = np.degrees(np.arctan2(dx, dy))
                # Normaliser entre 0 et 360
                if heading_array[i] < 0:
                    heading_array[i] += 360
        
        heading_array[0] = heading_array[1] if n_points > 1 else 0
        
        # Calculer le taux de virage (variation de cap en degrés par seconde)
        turn_rate_array = np.zeros(n_points)
        for i in range(1, n_points):
            if time_array[i] - time_array[i-1] > 0:
                # Différence d'angle (gestion du passage 0°/360°)
                delta_heading = heading_array[i] - heading_array[i-1]
                # Correction pour le passage 0°/360°
                if delta_heading > 180:
                    delta_heading -= 360
                elif delta_heading < -180:
                    delta_heading += 360
                
                delta_time = time_array[i] - time_array[i-1]
                turn_rate_array[i] = delta_heading / delta_time  # degrés/seconde
        
        turn_rate_array[0] = turn_rate_array[1] if n_points > 1 else 0
        
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
        Calcule les paramètres de la trajectoire avec profil de vitesse variable.
        
        Args:
            trajectory: Array numpy de positions [N x 3]
            initial_speed: Vitesse initiale en km/h
            arc_length: Nombre de points dans l'arc de virage (vitesse constante)
            speed_profile: Array des vitesses pour la phase d'approche [N]
            
        Returns:
            dict: Paramètres au cours du temps
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
        
        # Calculer l'angle de cap (heading) dans le plan XY (en degrés)
        heading_array = np.zeros(n_points)
        for i in range(1, n_points):
            dx = trajectory[i, 0] - trajectory[i-1, 0]
            dy = trajectory[i, 1] - trajectory[i-1, 1]
            if dx != 0 or dy != 0:
                heading_array[i] = np.degrees(np.arctan2(dx, dy))
                if heading_array[i] < 0:
                    heading_array[i] += 360
        
        heading_array[0] = heading_array[1] if n_points > 1 else 0
        
        # Calculer le taux de virage (variation de cap en degrés par seconde)
        turn_rate_array = np.zeros(n_points)
        for i in range(1, n_points):
            if time_array[i] - time_array[i-1] > 0:
                delta_heading = heading_array[i] - heading_array[i-1]
                if delta_heading > 180:
                    delta_heading -= 360
                elif delta_heading < -180:
                    delta_heading += 360
                
                delta_time = time_array[i] - time_array[i-1]
                turn_rate_array[i] = delta_heading / delta_time
        
        turn_rate_array[0] = turn_rate_array[1] if n_points > 1 else 0
        
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
    
    def calculate_trajectory_with_turn(self, aircraft):
        """
        Calcule une trajectoire réaliste avec virage pour rejoindre l'axe d'approche.
        
        Stratégie:
        1. Calculer le rayon de virage minimum
        2. Déterminer le point d'interception tangent à l'axe d'approche
        3. Créer un arc de cercle pour rejoindre l'axe
        4. Suivre l'axe jusqu'au FAF avec gestion de l'altitude
        
        Args:
            aircraft: Instance de la classe Aircraft
            
        Returns:
            tuple: (trajectory, parameters)
        """
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
            
            return self.calculate_trajectory(aircraft)
        
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
        Calcule le point d'interception tangent à l'axe d'approche.
        
        Utilise la géométrie des cercles tangents à une droite.
        
        Returns:
            tuple: (intercept_point, turn_center, turn_angle) ou (None, None, None) si impossible
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
        Crée les points d'un arc de cercle.
        
        Args:
            start_pos: Position de départ [x, y]
            center: Centre du cercle [x, y]
            angle: Angle de rotation (radians, peut être négatif)
            radius: Rayon du cercle
            altitude: Altitude constante pendant le virage
            
        Returns:
            numpy array: Points de l'arc [N x 3]
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
        Calcule la trajectoire d'approche avec descente progressive ET décélération.
        
        Args:
            aircraft: Instance Aircraft
            start_pos: Position de départ [x, y, z]
            target_pos: Position cible (FAF) [x, y, z]
            direction: Direction de l'axe d'approche (vecteur unitaire XY)
            target_speed: Vitesse cible à atteindre au FAF (km/h)
            
        Returns:
            tuple: (trajectory [N x 3], speed_profile [N])
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
    
    def _calculate_approach_with_descent(self, aircraft, start_pos, target_pos, direction):
        """
        Calcule la trajectoire d'approche avec descente progressive.
        
        Args:
            aircraft: Instance Aircraft
            start_pos: Position de départ [x, y, z]
            target_pos: Position cible (FAF) [x, y, z]
            direction: Direction de l'axe d'approche (vecteur unitaire XY)
            
        Returns:
            numpy array: Points de la trajectoire [N x 3]
        """
        # Distance horizontale
        horizontal_distance = np.linalg.norm(target_pos[:2] - start_pos[:2])
        altitude_diff = target_pos[2] - start_pos[2]
        
        # Si pas de descente nécessaire ou montée
        if altitude_diff >= 0:
            # Ligne droite simple
            n_points = max(int(horizontal_distance * 50), 50)
            t_values = np.linspace(0, 1, n_points)
            
            trajectory = np.zeros((n_points, 3))
            for i, t in enumerate(t_values):
                trajectory[i] = start_pos + t * (target_pos - start_pos)
            
            return trajectory
        
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
        
        return trajectory
    
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
