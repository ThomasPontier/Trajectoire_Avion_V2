"""
Module de gestion de l'avion
"""

import numpy as np


class AircraftType:
    """Types d'avions avec leurs spécifications"""
    
    LIGHT = "light"
    COMMERCIAL = "commercial"
    CARGO = "cargo"
    
    SPECIFICATIONS = {
        "light": {
            "name": "Avion Léger",
            "max_climb_slope": 15.0,      # degrés
            "max_descent_slope": -10.0,   # degrés (négatif = descente)
            "typical_speed": 180,          # km/h (vitesse de croisière)
            "approach_speed": 120,         # km/h (vitesse d'approche finale)
            "faf_speed": 140,             # km/h (vitesse cible au FAF)
            "min_speed": 100,             # km/h (vitesse minimale)
            "max_speed": 220,             # km/h (vitesse maximale)
            "max_bank_angle": 30.0,        # degrés d'inclinaison max
        },
        "commercial": {
            "name": "Avion de Ligne",
            "max_climb_slope": 10.0,
            "max_descent_slope": -6.0,
            "typical_speed": 250,
            "approach_speed": 180,
            "faf_speed": 200,
            "min_speed": 160,
            "max_speed": 300,
            "max_bank_angle": 25.0,
        },
        "cargo": {
            "name": "Avion Cargo",
            "max_climb_slope": 8.0,
            "max_descent_slope": -5.0,
            "typical_speed": 220,
            "approach_speed": 160,
            "faf_speed": 180,
            "min_speed": 140,
            "max_speed": 280,
            "max_bank_angle": 20.0,
        }
    }
    
    @staticmethod
    def get_all_types():
        """Retourne la liste de tous les types d'avions"""
        return list(AircraftType.SPECIFICATIONS.keys())
    
    @staticmethod
    def get_specifications(aircraft_type):
        """Retourne les spécifications d'un type d'avion"""
        return AircraftType.SPECIFICATIONS.get(aircraft_type, AircraftType.SPECIFICATIONS["commercial"])


class Aircraft:
    """
    Classe représentant un avion avec ses paramètres de vol
    """
    
    def __init__(self, position, speed, heading=0.0, aircraft_type="commercial"):
        """
        Initialise l'avion
        
        Args:
            position: Position initiale [x, y, z] en km
            speed: Vitesse en km/h
            heading: Cap initial en degrés (0° = Nord, 90° = Est)
            aircraft_type: Type d'avion ("light", "commercial", "cargo")
        """
        self.position = np.array(position, dtype=float)
        self.speed = speed  # km/h
        self.heading = heading  # degrés
        self.aircraft_type = aircraft_type
        
        # Récupérer les spécifications du type d'avion
        self.specs = AircraftType.get_specifications(aircraft_type)
        self.max_climb_slope = self.specs["max_climb_slope"]
        self.max_descent_slope = self.specs["max_descent_slope"]
        self.max_bank_angle = self.specs["max_bank_angle"]
        
    def get_velocity_vector(self):
        """
        Calcule le vecteur vitesse basé sur le cap et la vitesse
        
        Returns:
            Vecteur numpy [vx, vy, vz]
        """
        # Convertir le cap en radians
        heading_rad = np.radians(self.heading)
        
        # Calculer les composantes de vitesse (dans le plan horizontal)
        vx = self.speed * np.sin(heading_rad)
        vy = self.speed * np.cos(heading_rad)
        vz = 0.0  # Composante verticale initialement nulle
        
        return np.array([vx, vy, vz])
    
    def get_state(self):
        """
        Retourne l'état actuel de l'avion
        
        Returns:
            dict: Dictionnaire avec les paramètres de l'avion
        """
        return {
            'position': self.position.copy(),
            'speed': self.speed,
            'heading': self.heading,
            'altitude': self.position[2],
            'type': self.aircraft_type,
            'max_climb_slope': self.max_climb_slope,
            'max_descent_slope': self.max_descent_slope
        }
    
    def calculate_min_turn_radius(self, speed=None):
        """
        Calcule le rayon de virage minimal basé sur la vitesse
        
        Args:
            speed: Vitesse en km/h (si None, utilise la vitesse actuelle de l'avion)
        
        Returns:
            float: Rayon minimal en km
        """
        if speed is None:
            speed = self.speed
            
        v_ms = speed / 3.6  # Conversion km/h → m/s
        g = 9.81
        bank_angle_rad = np.radians(self.max_bank_angle)
        radius_m = (v_ms ** 2) / (g * np.tan(bank_angle_rad))
        return radius_m / 1000.0  # Retour en km
    
    def get_approach_speed(self):
        """
        Retourne la vitesse d'approche finale pour ce type d'avion
        
        Returns:
            float: Vitesse d'approche en km/h
        """
        return self.specs.get("approach_speed", self.speed * 0.7)
    
    def get_faf_speed(self):
        """
        Retourne la vitesse cible au FAF pour ce type d'avion
        
        Returns:
            float: Vitesse cible au FAF en km/h
        """
        return self.specs.get("faf_speed", self.speed * 0.8)
    
    def get_speed_limits(self):
        """
        Retourne les limites de vitesse pour ce type d'avion
        
        Returns:
            tuple: (min_speed, max_speed) en km/h
        """
        min_speed = self.specs.get("min_speed", self.speed * 0.6)
        max_speed = self.specs.get("max_speed", self.speed * 1.2)
        return min_speed, max_speed
    
    def is_speed_valid(self, speed):
        """
        Vérifie si une vitesse donnée est valide pour ce type d'avion
        
        Args:
            speed: Vitesse à vérifier en km/h
            
        Returns:
            bool: True si la vitesse est valide
        """
        min_speed, max_speed = self.get_speed_limits()
        return min_speed <= speed <= max_speed
    
    def calculate_speed_profile(self, trajectory_points, target_faf_speed=None):
        """
        Calcule un profil de vitesse réaliste pour une trajectoire donnée
        
        Args:
            trajectory_points: Nombre de points dans la trajectoire
            target_faf_speed: Vitesse cible au FAF (si None, utilise get_faf_speed())
            
        Returns:
            numpy.array: Profil de vitesse pour chaque point de la trajectoire
        """
        if target_faf_speed is None:
            target_faf_speed = self.get_faf_speed()
        
        # Créer un profil de vitesse progressif
        speed_profile = np.zeros(trajectory_points)
        
        if trajectory_points <= 1:
            speed_profile[0] = self.speed
            return speed_profile
        
        # Phase initiale : maintenir la vitesse actuelle (30% du trajet)
        cruise_phase = int(trajectory_points * 0.3)
        
        # Phase de transition : réduction progressive de vitesse (50% du trajet)
        transition_phase = int(trajectory_points * 0.5)
        
        # Phase finale : vitesse constante au FAF (20% du trajet)
        final_phase = trajectory_points - cruise_phase - transition_phase
        
        # Remplir le profil
        # Phase de croisière
        speed_profile[:cruise_phase] = self.speed
        
        # Phase de transition (réduction linéaire)
        if transition_phase > 0:
            transition_speeds = np.linspace(self.speed, target_faf_speed, transition_phase)
            speed_profile[cruise_phase:cruise_phase + transition_phase] = transition_speeds
        
        # Phase finale (vitesse FAF)
        if final_phase > 0:
            speed_profile[cruise_phase + transition_phase:] = target_faf_speed
        
        return speed_profile
    
    def __str__(self):
        """Représentation textuelle de l'avion"""
        return (f"{self.specs['name']} at ({self.position[0]:.2f}, {self.position[1]:.2f}, "
                f"{self.position[2]:.2f}) km, "
                f"Speed: {self.speed:.1f} km/h, Heading: {self.heading:.1f}°")
