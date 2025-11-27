"""
Module de gestion de l'environnement aérien
"""

import numpy as np


class Environment:    
    def __init__(self, size_x=50, size_y=50, size_z=5):
        """
        Initialise l'environnement
        
        """
        self.size_x = size_x
        self.size_y = size_y
        self.size_z = size_z
        
        # Position de l'aéroport (coin opposé, au sol)
        self.airport_position = np.array([size_x * 0.9, size_y * 0.9, 0.0])
        
        # Point FAF (Final Approach Fix) - à 5 km de l'aéroport, altitude 0.5 km
        # Le FAF est aligné sur l'axe d'approche
        approach_distance = 5.0  # km avant l'aéroport
        approach_altitude = 0.5  # km
        
        # Calculer la position du FAF (aligné sur l'axe d'approche)
        direction = np.array([-1, -1, 0])  # Direction vers le sud-ouest
        direction = direction / np.linalg.norm(direction)
        
        self.faf_position = np.array([
            self.airport_position[0] - approach_distance * direction[0],
            self.airport_position[1] - approach_distance * direction[1],
            approach_altitude
        ])
        
        # Angle de descente standard pour l'approche finale (3 degrés)
        self.final_approach_angle = 3.0
        
    def get_airport_info(self):
        """Retourne les informations sur l'aéroport"""
        return {
            'x': self.airport_position[0],
            'y': self.airport_position[1],
            'z': self.airport_position[2]
        }
    
    def get_faf_info(self):
        """Retourne les informations sur le point FAF"""
        return {
            'x': self.faf_position[0],
            'y': self.faf_position[1],
            'z': self.faf_position[2]
        }
