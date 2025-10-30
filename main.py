"""
Simulateur de Trajectoire d'Avion - Version 1.1
Projet P21 - ESTACA 4ème année

Ce programme permet de calculer et visualiser la trajectoire optimale
d'un avion pour atteindre le point FAF (Final Approach Fix) d'un aéroport.

Version 1.1 : Ajout de la contrainte de pente maximale selon le type d'avion.
L'avion vole en palier et entame sa descente le plus tard possible.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from mpl_toolkits.mplot3d import Axes3D

from environment import Environment
from aircraft import Aircraft, AircraftType
from trajectory_calculator import TrajectoryCalculator


class FlightSimulatorGUI:
    """Interface graphique principale du simulateur"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Simulateur de Trajectoire d'Avion - P21")
        self.root.geometry("1600x900")
        
        # Initialisation de l'environnement avec valeurs par défaut
        self.environment = None
        self.aircraft = None
        self.trajectory = None
        self.trajectory_params = None  # Stocker les paramètres de la trajectoire
        self.cylinders = []  # Liste des cylindres (obstacles)
        
        self._create_ui()
        
        # Charger la configuration sauvegardée (si elle existe)
        self._load_config_on_startup()
        
        # Initialiser l'affichage des spécifications
        self._on_aircraft_type_changed()
        
        # Créer l'environnement initial
        self._update_environment()
        
        # Dessiner l'environnement avec les cylindres chargés
        self._draw_environment()
        
    def _create_ui(self):
        """Crée l'interface utilisateur"""
        
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configuration du grid
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(0, weight=1)
        
        # Panel de contrôle (gauche)
        self._create_control_panel(main_frame)
        
        # Zone de visualisation (droite)
        self._create_visualization_panel(main_frame)
        
    def _create_control_panel(self, parent):
        """Crée le panel de contrôle avec les paramètres"""
        
        control_frame = ttk.Frame(parent)
        control_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        
        # Créer un notebook (onglets)
        notebook = ttk.Notebook(control_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Onglet 1: Configuration Environnement
        env_frame = ttk.Frame(notebook, padding="10")
        notebook.add(env_frame, text="🌍 Environnement")
        self._create_environment_config(env_frame)
        
        # Onglet 2: Gestion des Obstacles
        obstacles_frame = ttk.Frame(notebook, padding="10")
        notebook.add(obstacles_frame, text="🚧 Obstacles")
        self._create_obstacles_config(obstacles_frame)
        
        # Onglet 3: Configuration Avion
        aircraft_frame = ttk.Frame(notebook, padding="10")
        notebook.add(aircraft_frame, text="✈️ Avion")
        self._create_aircraft_config(aircraft_frame)
        
    def _create_environment_config(self, parent):
        """Crée la configuration de l'environnement"""
        
        row = 0
        
        # Titre
        ttk.Label(parent, text="Dimensions de l'Espace Aérien", font=('Arial', 10, 'bold')).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=5)
        row += 1
        
        # Taille X
        ttk.Label(parent, text="Largeur X (km):").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.env_size_x_var = tk.DoubleVar(value=50.0)
        ttk.Entry(parent, textvariable=self.env_size_x_var, width=15).grid(row=row, column=1, pady=5)
        row += 1
        
        # Taille Y
        ttk.Label(parent, text="Longueur Y (km):").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.env_size_y_var = tk.DoubleVar(value=50.0)
        ttk.Entry(parent, textvariable=self.env_size_y_var, width=15).grid(row=row, column=1, pady=5)
        row += 1
        
        # Taille Z
        ttk.Label(parent, text="Hauteur Z (km):").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.env_size_z_var = tk.DoubleVar(value=5.0)
        ttk.Entry(parent, textvariable=self.env_size_z_var, width=15).grid(row=row, column=1, pady=5)
        row += 1
        
        # Séparateur
        ttk.Separator(parent, orient='horizontal').grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=15)
        row += 1
        
        # Titre Aéroport
        ttk.Label(parent, text="Position de l'Aéroport", font=('Arial', 10, 'bold')).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=5)
        row += 1
        
        # Aéroport X
        ttk.Label(parent, text="Aéroport X (km):").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.airport_x_var = tk.DoubleVar(value=45.0)
        ttk.Entry(parent, textvariable=self.airport_x_var, width=15).grid(row=row, column=1, pady=5)
        row += 1
        
        # Aéroport Y
        ttk.Label(parent, text="Aéroport Y (km):").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.airport_y_var = tk.DoubleVar(value=45.0)
        ttk.Entry(parent, textvariable=self.airport_y_var, width=15).grid(row=row, column=1, pady=5)
        row += 1
        
        # Aéroport Z (généralement 0)
        ttk.Label(parent, text="Aéroport Z (km):").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.airport_z_var = tk.DoubleVar(value=0.0)
        ttk.Entry(parent, textvariable=self.airport_z_var, width=15).grid(row=row, column=1, pady=5)
        row += 1
        
        # Séparateur
        ttk.Separator(parent, orient='horizontal').grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=15)
        row += 1
        
        # Titre FAF
        ttk.Label(parent, text="Position du Point FAF", font=('Arial', 10, 'bold')).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=5)
        row += 1
        
        # FAF X
        ttk.Label(parent, text="FAF X (km):").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.faf_x_var = tk.DoubleVar(value=41.5)
        ttk.Entry(parent, textvariable=self.faf_x_var, width=15).grid(row=row, column=1, pady=5)
        row += 1
        
        # FAF Y
        ttk.Label(parent, text="FAF Y (km):").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.faf_y_var = tk.DoubleVar(value=41.5)
        ttk.Entry(parent, textvariable=self.faf_y_var, width=15).grid(row=row, column=1, pady=5)
        row += 1
        
        # FAF Z
        ttk.Label(parent, text="FAF Z (km):").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.faf_z_var = tk.DoubleVar(value=0.5)
        ttk.Entry(parent, textvariable=self.faf_z_var, width=15).grid(row=row, column=1, pady=5)
        row += 1
        
        # Séparateur
        ttk.Separator(parent, orient='horizontal').grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=15)
        row += 1
        
        # Bouton pour appliquer la configuration
        ttk.Button(parent, text="🔄 Appliquer Configuration", 
                  command=self._apply_environment_config).grid(row=row, column=0, columnspan=2, pady=10, sticky=(tk.W, tk.E))
        row += 1
        
        # Label d'info
        self.env_info_label = ttk.Label(parent, text="", font=('Arial', 8), foreground='green')
        self.env_info_label.grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2)
    
    def _create_obstacles_config(self, parent):
        """Crée l'onglet de gestion des obstacles (cylindres)"""
        
        # Créer un canvas avec scrollbar pour permettre le défilement
        canvas = tk.Canvas(parent, borderwidth=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Bind mouse wheel pour scroll
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Contenu de l'onglet dans le frame scrollable
        row = 0
        
        # Titre
        ttk.Label(scrollable_frame, text="Gestion des Cylindres (Obstacles)", 
                 font=('Arial', 11, 'bold')).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=5)
        row += 1
        
        ttk.Label(scrollable_frame, text="Les cylindres représentent des zones interdites de vol", 
                 font=('Arial', 8, 'italic'), foreground='gray').grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2)
        row += 1
        
        # Séparateur
        ttk.Separator(scrollable_frame, orient='horizontal').grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        row += 1
        
        # Section: Ajouter un nouveau cylindre
        ttk.Label(scrollable_frame, text="➕ Nouveau Cylindre", 
                 font=('Arial', 10, 'bold')).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=5)
        row += 1
        
        # Position X
        ttk.Label(scrollable_frame, text="Position X (km):").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.cyl_x_var = tk.DoubleVar(value=25.0)
        ttk.Entry(scrollable_frame, textvariable=self.cyl_x_var, width=15).grid(row=row, column=1, pady=5)
        row += 1
        
        # Position Y
        ttk.Label(scrollable_frame, text="Position Y (km):").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.cyl_y_var = tk.DoubleVar(value=25.0)
        ttk.Entry(scrollable_frame, textvariable=self.cyl_y_var, width=15).grid(row=row, column=1, pady=5)
        row += 1
        
        # Rayon
        ttk.Label(scrollable_frame, text="Rayon (km):").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.cyl_radius_var = tk.DoubleVar(value=2.0)
        ttk.Entry(scrollable_frame, textvariable=self.cyl_radius_var, width=15).grid(row=row, column=1, pady=5)
        row += 1
        
        # Hauteur
        ttk.Label(scrollable_frame, text="Hauteur (km):").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.cyl_height_var = tk.DoubleVar(value=3.0)
        ttk.Entry(scrollable_frame, textvariable=self.cyl_height_var, width=15).grid(row=row, column=1, pady=5)
        row += 1
        
        # Bouton ajouter
        ttk.Button(scrollable_frame, text="➕ Ajouter ce Cylindre", 
                  command=self._add_cylinder).grid(row=row, column=0, columnspan=2, pady=10, sticky=(tk.W, tk.E))
        row += 1
        
        # Séparateur
        ttk.Separator(scrollable_frame, orient='horizontal').grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        row += 1
        
        # Section: Liste des cylindres
        ttk.Label(scrollable_frame, text="📋 Cylindres Actifs", 
                 font=('Arial', 10, 'bold')).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=5)
        row += 1
        
        # Frame avec scrollbar pour la liste des cylindres
        list_container = ttk.Frame(scrollable_frame)
        list_container.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        list_scrollbar = ttk.Scrollbar(list_container)
        list_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.cylinders_listbox = tk.Listbox(list_container, height=8, 
                                             yscrollcommand=list_scrollbar.set, 
                                             font=('Courier', 9))
        self.cylinders_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        list_scrollbar.config(command=self.cylinders_listbox.yview)
        
        # Bind double-click pour sélectionner et éditer
        self.cylinders_listbox.bind('<Double-Button-1>', self._edit_selected_cylinder)
        
        row += 1
        
        # Boutons de gestion
        buttons_frame = ttk.Frame(scrollable_frame)
        buttons_frame.grid(row=row, column=0, columnspan=2, pady=10, sticky=(tk.W, tk.E))
        
        ttk.Button(buttons_frame, text="✏️ Éditer Sélectionné", 
                  command=self._edit_selected_cylinder).pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        ttk.Button(buttons_frame, text="🗑️ Supprimer Sélectionné", 
                  command=self._remove_selected_cylinder).pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        row += 1
        
        buttons_frame2 = ttk.Frame(scrollable_frame)
        buttons_frame2.grid(row=row, column=0, columnspan=2, pady=5, sticky=(tk.W, tk.E))
        
        ttk.Button(buttons_frame2, text="🗑️ Supprimer Dernier", 
                  command=self._remove_last_cylinder).pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        ttk.Button(buttons_frame2, text="🗑️ Tout Supprimer", 
                  command=self._clear_cylinders).pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        row += 1
        
        # Séparateur
        ttk.Separator(scrollable_frame, orient='horizontal').grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=15)
        row += 1
        
        # Section: Sauvegarde/Chargement
        ttk.Label(scrollable_frame, text="💾 Sauvegarde & Chargement", 
                 font=('Arial', 10, 'bold')).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=5)
        row += 1
        
        save_buttons_frame = ttk.Frame(scrollable_frame)
        save_buttons_frame.grid(row=row, column=0, columnspan=2, pady=5, sticky=(tk.W, tk.E))
        
        ttk.Button(save_buttons_frame, text="💾 Sauvegarder Configuration", 
                  command=self._save_config).pack(fill=tk.X, pady=2)
        ttk.Button(save_buttons_frame, text="📂 Charger Configuration", 
                  command=self._load_config).pack(fill=tk.X, pady=2)
        
        # Initialiser la liste des cylindres
        self.cylinders = []
        
    def _create_aircraft_config(self, parent):
        """Crée la configuration de l'avion"""
        
        control_frame = parent
        
        row = 0
        
        # Type d'avion
        ttk.Label(control_frame, text="Type d'avion:", font=('Arial', 9, 'bold')).grid(row=row, column=0, sticky=tk.W, pady=5)
        self.aircraft_type_var = tk.StringVar(value="commercial")
        aircraft_combo = ttk.Combobox(control_frame, textvariable=self.aircraft_type_var, 
                                     values=AircraftType.get_all_types(), 
                                     state='readonly', width=13)
        aircraft_combo.grid(row=row, column=1, pady=5)
        aircraft_combo.bind('<<ComboboxSelected>>', self._on_aircraft_type_changed)
        row += 1
        
        # Affichage des contraintes du type d'avion
        self.aircraft_specs_label = ttk.Label(control_frame, text="", font=('Arial', 8), foreground='blue')
        self.aircraft_specs_label.grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2)
        row += 1
        
        # Séparateur
        ttk.Separator(control_frame, orient='horizontal').grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        row += 1
        
        # Position X
        ttk.Label(control_frame, text="Position X (km):").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.pos_x_var = tk.DoubleVar(value=0.0)
        ttk.Entry(control_frame, textvariable=self.pos_x_var, width=15).grid(row=row, column=1, pady=5)
        row += 1
        
        # Position Y
        ttk.Label(control_frame, text="Position Y (km):").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.pos_y_var = tk.DoubleVar(value=0.0)
        ttk.Entry(control_frame, textvariable=self.pos_y_var, width=15).grid(row=row, column=1, pady=5)
        row += 1
        
        # Altitude
        ttk.Label(control_frame, text="Altitude (km):").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.altitude_var = tk.DoubleVar(value=3.0)
        ttk.Entry(control_frame, textvariable=self.altitude_var, width=15).grid(row=row, column=1, pady=5)
        row += 1
        
        # Vitesse
        ttk.Label(control_frame, text="Vitesse (km/h):").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.speed_var = tk.DoubleVar(value=250.0)
        ttk.Entry(control_frame, textvariable=self.speed_var, width=15).grid(row=row, column=1, pady=5)
        row += 1
        
        # Cap initial
        ttk.Label(control_frame, text="Cap initial (°):").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.heading_var = tk.DoubleVar(value=90.0)
        ttk.Entry(control_frame, textvariable=self.heading_var, width=15).grid(row=row, column=1, pady=5)
        row += 1
        
        # Séparateur
        ttk.Separator(control_frame, orient='horizontal').grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=15)
        row += 1
        
        # Informations sur l'environnement
        ttk.Label(control_frame, text="Informations Environnement", font=('Arial', 10, 'bold')).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=5)
        row += 1
        
        self.airport_info_label = ttk.Label(control_frame, text="Aéroport: Configuration en cours...", font=('Arial', 8))
        self.airport_info_label.grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2)
        row += 1
        
        self.faf_info_label = ttk.Label(control_frame, text="FAF: Configuration en cours...", font=('Arial', 8))
        self.faf_info_label.grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2)
        row += 1
        
        # Séparateur
        ttk.Separator(control_frame, orient='horizontal').grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=15)
        row += 1
        
        # Boutons
        button_frame = ttk.Frame(control_frame)
        button_frame.grid(row=row, column=0, columnspan=2, pady=10)
        
        ttk.Button(button_frame, text="Valider Position", command=self._validate_position).pack(fill=tk.X, pady=5)
        ttk.Button(button_frame, text="Lancer Simulation", command=self._run_simulation).pack(fill=tk.X, pady=5)
        ttk.Button(button_frame, text="Réinitialiser", command=self._reset).pack(fill=tk.X, pady=5)
        
    def _create_visualization_panel(self, parent):
        """Crée le panel de visualisation"""
        
        viz_frame = ttk.Frame(parent)
        viz_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        viz_frame.columnconfigure(0, weight=1)
        viz_frame.rowconfigure(0, weight=1)
        viz_frame.rowconfigure(1, weight=1)
        
        # Visualisation 3D avec marges pour la légende
        self.fig_3d = plt.Figure(figsize=(10, 6))
        self.ax_3d = self.fig_3d.add_subplot(111, projection='3d')
        
        # Ajuster les marges pour faire de la place à la légende
        self.fig_3d.subplots_adjust(right=0.85)
        
        self.canvas_3d = FigureCanvasTkAgg(self.fig_3d, master=viz_frame)
        self.canvas_3d.get_tk_widget().grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # Graphiques de paramètres
        self.fig_params = plt.Figure(figsize=(8, 4))
        self.canvas_params = FigureCanvasTkAgg(self.fig_params, master=viz_frame)
        self.canvas_params.get_tk_widget().grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Affichage initial de l'environnement
        self._draw_environment()
    
    def _update_environment(self):
        """Crée ou met à jour l'environnement avec les valeurs par défaut ou personnalisées"""
        if self.environment is None:
            # Première initialisation - utiliser les valeurs des variables
            size_x = self.env_size_x_var.get() if hasattr(self, 'env_size_x_var') else 50
            size_y = self.env_size_y_var.get() if hasattr(self, 'env_size_y_var') else 50
            size_z = self.env_size_z_var.get() if hasattr(self, 'env_size_z_var') else 5
            
            self.environment = Environment(size_x=size_x, size_y=size_y, size_z=size_z)
            
            # Appliquer les positions personnalisées si elles existent
            if hasattr(self, 'airport_x_var'):
                self.environment.airport_position = np.array([
                    self.airport_x_var.get(),
                    self.airport_y_var.get(),
                    self.airport_z_var.get()
                ])
            
            if hasattr(self, 'faf_x_var'):
                self.environment.faf_position = np.array([
                    self.faf_x_var.get(),
                    self.faf_y_var.get(),
                    self.faf_z_var.get()
                ])
        
        # Mettre à jour les affichages d'info si les widgets existent
        if hasattr(self, 'airport_info_label'):
            airport_info = self.environment.get_airport_info()
            self.airport_info_label.config(
                text=f"Aéroport: ({airport_info['x']:.1f}, {airport_info['y']:.1f}, {airport_info['z']:.1f}) km"
            )
        
        if hasattr(self, 'faf_info_label'):
            faf_info = self.environment.get_faf_info()
            self.faf_info_label.config(
                text=f"FAF: ({faf_info['x']:.1f}, {faf_info['y']:.1f}, {faf_info['z']:.1f}) km"
            )
    
    def _apply_environment_config(self):
        """Applique la configuration personnalisée de l'environnement"""
        try:
            # Récupérer les valeurs
            size_x = self.env_size_x_var.get()
            size_y = self.env_size_y_var.get()
            size_z = self.env_size_z_var.get()
            
            airport_x = self.airport_x_var.get()
            airport_y = self.airport_y_var.get()
            airport_z = self.airport_z_var.get()
            
            faf_x = self.faf_x_var.get()
            faf_y = self.faf_y_var.get()
            faf_z = self.faf_z_var.get()
            
            # Validations
            if size_x <= 0 or size_y <= 0 or size_z <= 0:
                raise ValueError("Les dimensions doivent être positives")
            
            if not (0 <= airport_x <= size_x):
                raise ValueError(f"Aéroport X doit être entre 0 et {size_x} km")
            if not (0 <= airport_y <= size_y):
                raise ValueError(f"Aéroport Y doit être entre 0 et {size_y} km")
            if not (0 <= airport_z <= size_z):
                raise ValueError(f"Aéroport Z doit être entre 0 et {size_z} km")
            
            if not (0 <= faf_x <= size_x):
                raise ValueError(f"FAF X doit être entre 0 et {size_x} km")
            if not (0 <= faf_y <= size_y):
                raise ValueError(f"FAF Y doit être entre 0 et {size_y} km")
            if not (0 <= faf_z <= size_z):
                raise ValueError(f"FAF Z doit être entre 0 et {size_z} km")
            
            # Créer le nouvel environnement
            self.environment = Environment(size_x=size_x, size_y=size_y, size_z=size_z)
            
            # Appliquer les positions personnalisées
            self.environment.airport_position = np.array([airport_x, airport_y, airport_z])
            self.environment.faf_position = np.array([faf_x, faf_y, faf_z])
            
            # Réinitialiser la simulation
            self.aircraft = None
            self.trajectory = None
            self.trajectory_params = None
            
            # Mettre à jour l'affichage
            self._update_environment()
            self._draw_environment()
            
            # Message de succès
            self.env_info_label.config(
                text="✅ Configuration appliquée avec succès!",
                foreground='green'
            )
            
            # Sauvegarde automatique
            self._save_config()
            
            messagebox.showinfo("Succès", 
                              f"Environnement configuré:\n\n"
                              f"Espace: {size_x} x {size_y} x {size_z} km\n"
                              f"Aéroport: ({airport_x:.1f}, {airport_y:.1f}, {airport_z:.1f}) km\n"
                              f"FAF: ({faf_x:.1f}, {faf_y:.1f}, {faf_z:.1f}) km")
            
        except ValueError as e:
            self.env_info_label.config(
                text=f"❌ Erreur: {str(e)}",
                foreground='red'
            )
            messagebox.showerror("Erreur", str(e))
    
    def _save_config(self):
        """Sauvegarde la configuration complète dans un fichier JSON"""
        import json
        import os
        
        try:
            config = {
                'environment': {
                    'size_x': self.env_size_x_var.get(),
                    'size_y': self.env_size_y_var.get(),
                    'size_z': self.env_size_z_var.get(),
                    'airport': {
                        'x': self.airport_x_var.get(),
                        'y': self.airport_y_var.get(),
                        'z': self.airport_z_var.get()
                    },
                    'faf': {
                        'x': self.faf_x_var.get(),
                        'y': self.faf_y_var.get(),
                        'z': self.faf_z_var.get()
                    }
                },
                'cylinders': self.cylinders,
                'aircraft': {
                    'type': self.aircraft_type_var.get(),
                    'position': {
                        'x': self.pos_x_var.get(),
                        'y': self.pos_y_var.get(),
                        'z': self.altitude_var.get()
                    },
                    'speed': self.speed_var.get(),
                    'heading': self.heading_var.get()
                }
            }
            
            config_file = os.path.join(os.path.dirname(__file__), 'config.json')
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            
            # Pas de message pour la sauvegarde automatique
            # messagebox.showinfo("Succès", f"Configuration sauvegardée dans:\n{config_file}")
            
        except Exception as e:
            print(f"Erreur de sauvegarde: {e}")
            # Ne pas afficher de popup d'erreur pour éviter de bloquer l'interface
    
    def _load_config_on_startup(self):
        """Charge silencieusement la configuration au démarrage"""
        import json
        import os
        
        try:
            # Utiliser le répertoire du script
            if hasattr(self, '__file__'):
                script_dir = os.path.dirname(os.path.abspath(__file__))
            else:
                script_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()
            
            config_file = os.path.join(script_dir, 'config.json')
            
            if not os.path.exists(config_file):
                return  # Pas de configuration sauvegardée, utiliser les valeurs par défaut
            
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Charger l'environnement
            env = config.get('environment', {})
            size_x = env.get('size_x', 50)
            size_y = env.get('size_y', 50)
            size_z = env.get('size_z', 5)
            
            self.env_size_x_var.set(size_x)
            self.env_size_y_var.set(size_y)
            self.env_size_z_var.set(size_z)
            
            airport = env.get('airport', {})
            self.airport_x_var.set(airport.get('x', 25))
            self.airport_y_var.set(airport.get('y', 25))
            self.airport_z_var.set(airport.get('z', 0))
            
            faf = env.get('faf', {})
            self.faf_x_var.set(faf.get('x', 15))
            self.faf_y_var.set(faf.get('y', 15))
            self.faf_z_var.set(faf.get('z', 1.5))
            
            # Charger les cylindres
            self.cylinders = config.get('cylinders', [])
            
            # Mettre à jour l'affichage de la liste des cylindres
            if hasattr(self, 'cylinders_listbox'):
                self._update_cylinders_list()
            
            # Charger l'avion
            aircraft = config.get('aircraft', {})
            self.aircraft_type_var.set(aircraft.get('type', 'commercial'))
            
            position = aircraft.get('position', {})
            self.pos_x_var.set(position.get('x', 0))
            self.pos_y_var.set(position.get('y', 0))
            self.altitude_var.set(position.get('z', 3))
            
            self.speed_var.set(aircraft.get('speed', 250))
            self.heading_var.set(aircraft.get('heading', 90))
            
        except Exception as e:
            print(f"Erreur lors du chargement de la configuration: {e}")
            # Continuer avec les valeurs par défaut
    
    def _load_config(self):
        """Charge la configuration depuis le fichier JSON (avec message utilisateur)"""
        import json
        import os
        
        try:
            config_file = os.path.join(os.path.dirname(__file__), 'config.json')
            
            if not os.path.exists(config_file):
                messagebox.showinfo("Info", "Aucune configuration sauvegardée trouvée")
                return
            
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Charger l'environnement
            env = config.get('environment', {})
            self.env_size_x_var.set(env.get('size_x', 50))
            self.env_size_y_var.set(env.get('size_y', 50))
            self.env_size_z_var.set(env.get('size_z', 5))
            
            airport = env.get('airport', {})
            self.airport_x_var.set(airport.get('x', 25))
            self.airport_y_var.set(airport.get('y', 25))
            self.airport_z_var.set(airport.get('z', 0))
            
            faf = env.get('faf', {})
            self.faf_x_var.set(faf.get('x', 15))
            self.faf_y_var.set(faf.get('y', 15))
            self.faf_z_var.set(faf.get('z', 1.5))
            
            # Charger les cylindres
            self.cylinders = config.get('cylinders', [])
            self._update_cylinders_list()
            
            # Charger l'avion
            aircraft = config.get('aircraft', {})
            self.aircraft_type_var.set(aircraft.get('type', 'commercial'))
            
            position = aircraft.get('position', {})
            self.pos_x_var.set(position.get('x', 0))
            self.pos_y_var.set(position.get('y', 0))
            self.altitude_var.set(position.get('z', 3))
            
            self.speed_var.set(aircraft.get('speed', 250))
            self.heading_var.set(aircraft.get('heading', 90))
            
            # Appliquer la configuration de l'environnement
            self._apply_environment_config()
            
            messagebox.showinfo("Succès", f"Configuration chargée depuis:\n{config_file}\n\n"
                                         f"Environnement: {self.env_size_x_var.get()}x{self.env_size_y_var.get()}x{self.env_size_z_var.get()} km\n"
                                         f"Cylindres: {len(self.cylinders)}\n"
                                         f"Type d'avion: {self.aircraft_type_var.get()}")
            
        except Exception as e:
            messagebox.showerror("Erreur de chargement", f"Impossible de charger la configuration:\n{str(e)}")
    
    def _add_cylinder(self):
        """Ajoute un cylindre (obstacle) à l'environnement"""
        try:
            if self.environment is None:
                messagebox.showwarning("Attention", "Veuillez d'abord appliquer la configuration de l'environnement")
                return
            
            x = self.cyl_x_var.get()
            y = self.cyl_y_var.get()
            radius = self.cyl_radius_var.get()
            height = self.cyl_height_var.get()
            
            # Validations
            if not (0 <= x <= self.environment.size_x):
                raise ValueError(f"Position X doit être entre 0 et {self.environment.size_x} km")
            if not (0 <= y <= self.environment.size_y):
                raise ValueError(f"Position Y doit être entre 0 et {self.environment.size_y} km")
            if radius <= 0:
                raise ValueError("Le rayon doit être positif")
            if height <= 0 or height > self.environment.size_z:
                raise ValueError(f"La hauteur doit être entre 0 et {self.environment.size_z} km")
            
            # Ajouter le cylindre
            cylinder = {
                'x': x,
                'y': y,
                'radius': radius,
                'height': height
            }
            self.cylinders.append(cylinder)
            
            # Mettre à jour la liste
            self._update_cylinders_list()
            
            # Redessiner l'environnement
            self._draw_environment()
            
            # Sauvegarde automatique
            self._save_config()
            
            messagebox.showinfo("Succès", f"Cylindre ajouté:\nPosition: ({x:.1f}, {y:.1f}) km\n"
                                         f"Rayon: {radius:.1f} km\nHauteur: {height:.1f} km")
            
        except ValueError as e:
            messagebox.showerror("Erreur", str(e))
    
    def _remove_last_cylinder(self):
        """Supprime le dernier cylindre ajouté"""
        if not self.cylinders:
            messagebox.showwarning("Attention", "Aucun cylindre à supprimer")
            return
        
        removed = self.cylinders.pop()
        self._update_cylinders_list()
        self._draw_environment()
        self._save_config()  # Sauvegarde automatique
        
        messagebox.showinfo("Succès", f"Cylindre supprimé:\nPosition: ({removed['x']:.1f}, {removed['y']:.1f}) km")
    
    def _clear_cylinders(self):
        """Supprime tous les cylindres"""
        if not self.cylinders:
            messagebox.showwarning("Attention", "Aucun cylindre à supprimer")
            return
        
        count = len(self.cylinders)
        self.cylinders.clear()
        self._update_cylinders_list()
        self._draw_environment()
        self._save_config()  # Sauvegarde automatique
        
        messagebox.showinfo("Succès", f"{count} cylindre(s) supprimé(s)")
    
    def _edit_selected_cylinder(self, event=None):
        """Édite le cylindre sélectionné"""
        selection = self.cylinders_listbox.curselection()
        if not selection:
            messagebox.showwarning("Attention", "Veuillez sélectionner un cylindre à éditer")
            return
        
        index = selection[0]
        if index >= len(self.cylinders):
            return
            
        cyl = self.cylinders[index]
        
        # Remplir les champs avec les valeurs actuelles
        self.cyl_x_var.set(cyl['x'])
        self.cyl_y_var.set(cyl['y'])
        self.cyl_radius_var.set(cyl['radius'])
        self.cyl_height_var.set(cyl['height'])
        
        # Supprimer l'ancien
        self.cylinders.pop(index)
        self._update_cylinders_list()
        self._draw_environment()
        
        messagebox.showinfo("Édition", "Cylindre chargé dans les champs.\nModifiez les valeurs puis cliquez sur 'Ajouter ce Cylindre'")
    
    def _remove_selected_cylinder(self):
        """Supprime le cylindre sélectionné"""
        selection = self.cylinders_listbox.curselection()
        if not selection:
            messagebox.showwarning("Attention", "Veuillez sélectionner un cylindre à supprimer")
            return
        
        index = selection[0]
        if index >= len(self.cylinders):
            return
            
        removed = self.cylinders.pop(index)
        self._update_cylinders_list()
        self._draw_environment()
        self._save_config()  # Sauvegarde automatique
        
        messagebox.showinfo("Succès", f"Cylindre supprimé:\nPosition: ({removed['x']:.1f}, {removed['y']:.1f}) km")
    
    def _update_cylinders_list(self):
        """Met à jour l'affichage de la liste des cylindres"""
        self.cylinders_listbox.delete(0, tk.END)
        
        if not self.cylinders:
            self.cylinders_listbox.insert(tk.END, "Aucun cylindre")
        else:
            for i, cyl in enumerate(self.cylinders, 1):
                self.cylinders_listbox.insert(tk.END, 
                    f"#{i}: X={cyl['x']:.1f} Y={cyl['y']:.1f} R={cyl['radius']:.1f} H={cyl['height']:.1f}")
        
    def _draw_environment(self):
        """Dessine l'environnement 3D"""
        
        if self.environment is None:
            return
        
        self.ax_3d.clear()
        
        # Configuration de l'affichage
        self.ax_3d.set_xlim(0, self.environment.size_x)
        self.ax_3d.set_ylim(0, self.environment.size_y)
        self.ax_3d.set_zlim(0, self.environment.size_z)
        
        self.ax_3d.set_xlabel('')
        self.ax_3d.set_ylabel('')
        self.ax_3d.set_zlabel('')
        
        # Désactiver les valeurs sur les axes
        self.ax_3d.set_xticklabels([])
        self.ax_3d.set_yticklabels([])
        self.ax_3d.set_zticklabels([])
        
        # Dessiner l'aéroport
        airport = self.environment.airport_position
        self.ax_3d.scatter([airport[0]], [airport[1]], [airport[2]], 
                          c='red', marker='s', s=200, label='Aéroport')
        
        # Dessiner le point FAF
        faf = self.environment.faf_position
        self.ax_3d.scatter([faf[0]], [faf[1]], [faf[2]], 
                          c='blue', marker='^', s=150, label='Point FAF')
        
        # Dessiner l'axe d'approche (demi-droite partant de l'aéroport et passant par le FAF)
        # Calculer le vecteur directeur de l'aéroport vers le FAF
        direction = faf - airport
        direction_norm = np.linalg.norm(direction[:2])  # Norme dans le plan XY
        
        if direction_norm > 0:
            # Normaliser le vecteur directeur
            direction_unit = direction / direction_norm
            
            # Prolonger la demi-droite au-delà du FAF (jusqu'à la limite de l'espace)
            # Calculer la distance max possible dans cette direction
            max_distance = max(self.environment.size_x, self.environment.size_y) * 2
            
            # Point de départ : aéroport
            # Point d'arrivée : prolongement au-delà du FAF
            end_point = airport + direction_unit * max_distance
            
            # Tracer la demi-droite en pointillés noirs
            self.ax_3d.plot([airport[0], end_point[0]], 
                           [airport[1], end_point[1]], 
                           [airport[2], end_point[2]], 
                           'k--', linewidth=1.5, alpha=0.6, label='Axe d\'approche')
        
        # Si l'avion est positionné
        if self.aircraft:
            self.ax_3d.scatter([self.aircraft.position[0]], [self.aircraft.position[1]], 
                             [self.aircraft.position[2]], c='green', marker='o', s=100, 
                             label='Avion')
        
        # Si une trajectoire existe
        if self.trajectory is not None:
            # Vérifier si on a un point de début de descente et transition
            if self.trajectory_params and 'descent_start_index' in self.trajectory_params:
                descent_idx = self.trajectory_params['descent_start_index']
                transition_end_idx = self.trajectory_params.get('transition_end_index', descent_idx)
                
                # Phase de vol en palier (en vert)
                if descent_idx > 0:
                    self.ax_3d.plot(self.trajectory[:descent_idx, 0], 
                                   self.trajectory[:descent_idx, 1], 
                                   self.trajectory[:descent_idx, 2], 
                                   'g-', linewidth=2.5, label='Vol en palier', alpha=0.9)
                    
                    # Marquer le point de début de transition
                    transition_point = self.trajectory[descent_idx]
                    self.ax_3d.scatter([transition_point[0]], [transition_point[1]], [transition_point[2]], 
                                      c='gold', marker='*', s=200, label='Début transition', zorder=5, edgecolors='orange', linewidths=1.5)
                
                # Phase de transition (en jaune/gold pour différencier)
                if transition_end_idx > descent_idx:
                    self.ax_3d.plot(self.trajectory[descent_idx:transition_end_idx, 0], 
                                   self.trajectory[descent_idx:transition_end_idx, 1], 
                                   self.trajectory[descent_idx:transition_end_idx, 2], 
                                   'gold', linewidth=2.5, label='Transition progressive', alpha=0.9)
                    
                    # Marquer le point de fin de transition
                    descent_start_point = self.trajectory[transition_end_idx]
                    self.ax_3d.scatter([descent_start_point[0]], [descent_start_point[1]], [descent_start_point[2]], 
                                      c='orange', marker='v', s=150, label='Début descente', zorder=5, edgecolors='red', linewidths=1.5)
                
                # Phase de descente linéaire (en orange)
                if transition_end_idx < len(self.trajectory):
                    self.ax_3d.plot(self.trajectory[transition_end_idx:, 0], 
                                   self.trajectory[transition_end_idx:, 1], 
                                   self.trajectory[transition_end_idx:, 2], 
                                   'orangered', linewidth=2.5, label='Descente', alpha=0.9)
            else:
                # Trajectoire simple (lissée)
                self.ax_3d.plot(self.trajectory[:, 0], self.trajectory[:, 1], 
                               self.trajectory[:, 2], 'g-', linewidth=2.5, label='Trajectoire', alpha=0.9)
        
        # Dessiner les cylindres (obstacles) s'ils existent
        if hasattr(self, 'cylinders') and self.cylinders:
            for i, cyl in enumerate(self.cylinders):
                self._draw_cylinder(cyl['x'], cyl['y'], cyl['radius'], cyl['height'])
            
            # Ajouter une entrée de légende pour les cylindres
            self.ax_3d.plot([], [], [], 'r-', linewidth=3, alpha=0.7, 
                          label=f'Cylindres ({len(self.cylinders)})')
        
        # Légende à l'extérieur du graphe (à droite)
        self.ax_3d.legend(loc='center left', bbox_to_anchor=(1.05, 0.5), fontsize=8, framealpha=0.9, 
                         edgecolor='black', fancybox=True, shadow=True)
        self.ax_3d.set_title("Espace Aérien 3D - Version 1.1+ (Trajectoire Lissée)", pad=20)
        
        self.canvas_3d.draw()
    
    def _draw_cylinder(self, x, y, radius, height):
        """Dessine un cylindre (obstacle) dans l'espace 3D"""
        # Créer le cylindre
        z = np.linspace(0, height, 20)
        theta = np.linspace(0, 2 * np.pi, 30)
        theta_grid, z_grid = np.meshgrid(theta, z)
        x_grid = radius * np.cos(theta_grid) + x
        y_grid = radius * np.sin(theta_grid) + y
        
        # Dessiner la surface du cylindre
        self.ax_3d.plot_surface(x_grid, y_grid, z_grid, alpha=0.3, color='red', 
                               edgecolor='darkred', linewidth=0.5)
        
        # Dessiner le cercle du sommet
        theta_top = np.linspace(0, 2 * np.pi, 30)
        x_top = radius * np.cos(theta_top) + x
        y_top = radius * np.sin(theta_top) + y
        z_top = np.ones_like(theta_top) * height
        self.ax_3d.plot(x_top, y_top, z_top, 'r-', linewidth=2, alpha=0.7)
        
    def _draw_parameters(self, time, altitude, slope, speed):
        """Dessine les graphiques de paramètres"""
        
        self.fig_params.clear()
        
        # Graphique 1: Altitude
        ax1 = self.fig_params.add_subplot(131)
        ax1.plot(time, altitude, 'b-', linewidth=2, label='Altitude')
        ax1.set_xlabel('Temps (s)')
        ax1.set_ylabel('Altitude (km)')
        ax1.set_title('Altitude au cours du temps')
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        
        # Graphique 2: Pente avec limites
        ax2 = self.fig_params.add_subplot(132)
        ax2.plot(time, slope, 'r-', linewidth=2, label='Pente actuelle')
        ax2.set_xlabel('Temps (s)')
        ax2.set_ylabel('Pente (°)')
        ax2.set_title('Pente au cours du temps')
        ax2.grid(True, alpha=0.3)
        ax2.axhline(y=0, color='k', linestyle='--', alpha=0.3)
        
        # Afficher les limites de pente si l'avion existe
        if self.aircraft:
            ax2.axhline(y=self.aircraft.max_climb_slope, color='green', 
                       linestyle='--', alpha=0.5, label=f'Pente max montée ({self.aircraft.max_climb_slope}°)')
            ax2.axhline(y=self.aircraft.max_descent_slope, color='red', 
                       linestyle='--', alpha=0.5, label=f'Pente max descente ({self.aircraft.max_descent_slope}°)')
        
        ax2.legend(fontsize=7)
        
        # Graphique 3: Vitesse
        ax3 = self.fig_params.add_subplot(133)
        ax3.plot(time, speed, 'g-', linewidth=2, label='Vitesse')
        ax3.set_xlabel('Temps (s)')
        ax3.set_ylabel('Vitesse (km/h)')
        ax3.set_title('Vitesse au cours du temps')
        ax3.grid(True, alpha=0.3)
        ax3.legend()
        
        self.fig_params.tight_layout()
        self.canvas_params.draw()
        
    def _on_aircraft_type_changed(self, event=None):
        """Appelé quand le type d'avion change"""
        aircraft_type = self.aircraft_type_var.get()
        specs = AircraftType.get_specifications(aircraft_type)
        
        # Mettre à jour l'affichage des spécifications
        specs_text = (f"Pente max montée: {specs['max_climb_slope']:.1f}° | "
                     f"Pente max descente: {specs['max_descent_slope']:.1f}° | "
                     f"Vitesse typique: {specs['typical_speed']} km/h")
        self.aircraft_specs_label.config(text=specs_text)
        
        # Mettre à jour la vitesse suggérée
        self.speed_var.set(specs['typical_speed'])
    
    def _validate_position(self):
        """Valide et positionne l'avion"""
        
        try:
            x = self.pos_x_var.get()
            y = self.pos_y_var.get()
            z = self.altitude_var.get()
            speed = self.speed_var.get()
            heading = self.heading_var.get()
            aircraft_type = self.aircraft_type_var.get()
            
            # Vérifications
            if not (0 <= x <= self.environment.size_x):
                raise ValueError(f"Position X doit être entre 0 et {self.environment.size_x} km")
            if not (0 <= y <= self.environment.size_y):
                raise ValueError(f"Position Y doit être entre 0 et {self.environment.size_y} km")
            if not (0 <= z <= self.environment.size_z):
                raise ValueError(f"Altitude doit être entre 0 et {self.environment.size_z} km")
            if speed <= 0:
                raise ValueError("La vitesse doit être positive")
            
            # Créer l'avion avec le type sélectionné
            self.aircraft = Aircraft(
                position=np.array([x, y, z]),
                speed=speed,
                heading=heading,
                aircraft_type=aircraft_type
            )
            
            # Réinitialiser la trajectoire
            self.trajectory = None
            
            # Mettre à jour l'affichage
            self._draw_environment()
            
            messagebox.showinfo("Succès", f"Position de l'avion validée!\n"
                                        f"Type: {self.aircraft.specs['name']}\n"
                                        f"Pente max descente: {self.aircraft.max_descent_slope:.1f}°")
            
        except ValueError as e:
            messagebox.showerror("Erreur", str(e))
            
    def _run_simulation(self):
        """Lance la simulation de trajectoire"""
        
        if self.aircraft is None:
            messagebox.showwarning("Attention", "Veuillez d'abord valider la position de l'avion!")
            return
        
        try:
            # Calculer la trajectoire
            calculator = TrajectoryCalculator(self.environment)
            self.trajectory, self.trajectory_params = calculator.calculate_trajectory(self.aircraft)
            
            # Mettre à jour les visualisations
            self._draw_environment()
            self._draw_parameters(self.trajectory_params['time'], 
                                self.trajectory_params['altitude'], 
                                self.trajectory_params['slope'], 
                                self.trajectory_params['speed'])
            
            # Message de succès avec informations
            info_msg = "✅ Simulation terminée!\n\n"
            info_msg += f"📊 Distance totale: {self.trajectory_params['distance']:.2f} km\n"
            info_msg += f"⏱️  Temps de vol: {self.trajectory_params['flight_time']*60:.1f} minutes\n"
            info_msg += f"📍 Points de trajectoire: {self.trajectory_params.get('n_points', len(self.trajectory))}\n"
            
            if 'level_flight_distance' in self.trajectory_params:
                info_msg += f"\n🛫 Vol en palier: {self.trajectory_params['level_flight_distance']:.2f} km\n"
                
                if 'transition_distance' in self.trajectory_params:
                    info_msg += f"🔄 Transition progressive: {self.trajectory_params['transition_distance']:.2f} km\n"
                
                info_msg += f"🛬 Distance de descente: {self.trajectory_params['descent_distance']:.2f} km\n"
                actual_slope = np.min(self.trajectory_params['slope'])
                info_msg += f"📐 Pente de descente: {actual_slope:.2f}° (max: {self.aircraft.max_descent_slope:.1f}°)"
            
            messagebox.showinfo("Succès", info_msg)
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la simulation: {str(e)}")
            
    def _reset(self):
        """Réinitialise la simulation"""
        
        self.aircraft = None
        self.trajectory = None
        self.trajectory_params = None
        
        # Réinitialiser les valeurs
        self.pos_x_var.set(0.0)
        self.pos_y_var.set(0.0)
        self.altitude_var.set(3.0)
        self.speed_var.set(250.0)
        self.heading_var.set(90.0)
        
        # Réinitialiser les graphiques
        self.fig_params.clear()
        self.canvas_params.draw()
        
        # Redessiner l'environnement
        self._draw_environment()


def main():
    """Point d'entrée principal"""
    root = tk.Tk()
    app = FlightSimulatorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
