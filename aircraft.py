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
            "min_speed": 100,             # km/h (vitesse minimale)
            "max_speed": 220,             # km/h (vitesse maximale)
            "max_bank_angle": 30.0,        # degrés d'inclinaison max
        },
        "commercial": {
            "name": "Avion de Ligne",
            "max_climb_slope": 10.0,
            "max_descent_slope": -6.0,
            "typical_speed": 250,
            "min_speed": 160,
            "max_speed": 300,
            "max_bank_angle": 25.0,
        },
        "cargo": {
            "name": "Avion Cargo",
            "max_climb_slope": 8.0,
            "max_descent_slope": -5.0,
            "typical_speed": 220,
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
    
    def __init__(self, position, speed, heading=0.0, aircraft_type="commercial", 
                 max_climb_slope=None, max_descent_slope=None):
        """
        Initialise l'avion
        
        Args:
            position: Position initiale [x, y, z] en km
            speed: Vitesse en km/h
            heading: Cap initial en degrés (0° = Nord, 90° = Est)
            aircraft_type: Type d'avion ("light", "commercial", "cargo")
            max_climb_slope: Pente maximale de montée en degrés (optionnel, sinon utilise celle du type)
            max_descent_slope: Pente maximale de descente en degrés (optionnel, sinon utilise celle du type)
        """
        self.position = np.array(position, dtype=float)
        self.speed = speed  # km/h
        self.heading = heading  # degrés
        self.aircraft_type = aircraft_type
        
        # Récupérer les spécifications du type d'avion
        self.specs = AircraftType.get_specifications(aircraft_type)
        
        # Utiliser les pentes personnalisées si fournies, sinon utiliser celles du type
        self.max_climb_slope = max_climb_slope if max_climb_slope is not None else self.specs["max_climb_slope"]
        self.max_descent_slope = max_descent_slope if max_descent_slope is not None else self.specs["max_descent_slope"]
        self.max_bank_angle = self.specs["max_bank_angle"]
    
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
    
    def __str__(self):
        """Représentation textuelle de l'avion"""
        return (f"{self.specs['name']} at ({self.position[0]:.2f}, {self.position[1]:.2f}, "
                f"{self.position[2]:.2f}) km, "
                f"Speed: {self.speed:.1f} km/h, Heading: {self.heading:.1f}°")
