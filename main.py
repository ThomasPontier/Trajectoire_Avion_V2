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
        
        # Configuration du grid principal
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # Notebook principal avec 4 onglets
        self.main_notebook = ttk.Notebook(self.root)
        self.main_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Onglet 1: Configuration
        self._create_config_tab()
        
        # Onglet 2: Vue 3D
        self._create_3d_view_tab()
        
        # Onglet 3: Vues 2D (XY, XZ, YZ)
        self._create_2d_views_tab()
        
        # Onglet 4: Paramètres (graphiques)
        self._create_parameters_tab()
        
    def _create_config_tab(self):
        """Crée l'onglet de configuration avec sous-onglets et vue 3D"""
        
        config_frame = ttk.Frame(self.main_notebook)
        self.main_notebook.add(config_frame, text="⚙️ Configuration")
        
        # Créer un PanedWindow pour diviser l'écran en 2 parties (gauche et droite)
        paned = ttk.PanedWindow(config_frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Partie gauche : Notebook de configuration
        left_frame = ttk.Frame(paned)
        paned.add(left_frame, weight=1)
        
        config_notebook = ttk.Notebook(left_frame)
        config_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Sous-onglet 1: Environnement
        env_frame = ttk.Frame(config_notebook, padding="10")
        config_notebook.add(env_frame, text="🌍 Environnement")
        self._create_environment_config(env_frame)
        
        # Sous-onglet 2: Obstacles
        obstacles_frame = ttk.Frame(config_notebook, padding="10")
        config_notebook.add(obstacles_frame, text="🚧 Obstacles")
        self._create_obstacles_config(obstacles_frame)
        
        # Sous-onglet 3: Avion
        aircraft_frame = ttk.Frame(config_notebook, padding="10")
        config_notebook.add(aircraft_frame, text="✈️ Avion")
        self._create_aircraft_config(aircraft_frame)
        
        # Partie droite : Vue 3D de prévisualisation
        right_frame = ttk.Frame(paned)
        paned.add(right_frame, weight=1)
        
        # Titre pour la prévisualisation
        preview_label = ttk.Label(right_frame, text="📦 Prévisualisation 3D", 
                                 font=('Arial', 12, 'bold'))
        preview_label.pack(pady=5)
        
        # Créer une figure 3D pour la prévisualisation
        self.fig_3d_config = plt.Figure(figsize=(8, 6))
        self.ax_3d_config = self.fig_3d_config.add_subplot(111, projection='3d')
        
        # Canvas pour la figure 3D dans la configuration
        self.canvas_3d_config = FigureCanvasTkAgg(self.fig_3d_config, master=right_frame)
        self.canvas_3d_config.draw()
        self.canvas_3d_config.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Ajouter une barre d'outils de navigation pour la vue config
        from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
        toolbar_config = NavigationToolbar2Tk(self.canvas_3d_config, right_frame)
        toolbar_config.update()
    
    def _create_3d_view_tab(self):
        """Crée l'onglet avec la vue 3D"""
        
        view_3d_frame = ttk.Frame(self.main_notebook)
        self.main_notebook.add(view_3d_frame, text="📦 Vue 3D")
        
        # Créer la figure 3D
        self.fig_3d = plt.Figure(figsize=(12, 8))
        self.ax_3d = self.fig_3d.add_subplot(111, projection='3d')
        
        # Canvas pour la figure 3D
        self.canvas_3d = FigureCanvasTkAgg(self.fig_3d, master=view_3d_frame)
        self.canvas_3d.draw()
        self.canvas_3d.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Ajouter la barre d'outils de navigation
        from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
        toolbar_3d = NavigationToolbar2Tk(self.canvas_3d, view_3d_frame)
        toolbar_3d.update()
    
    def _create_2d_views_tab(self):
        """Crée l'onglet avec les 3 vues 2D orthogonales"""
        
        views_2d_frame = ttk.Frame(self.main_notebook)
        self.main_notebook.add(views_2d_frame, text="📐 Vues 2D")
        
        # Créer une figure avec 3 sous-graphiques
        self.fig_2d = plt.Figure(figsize=(14, 10))
        
        # Vue de dessus (XY)
        self.ax_xy = self.fig_2d.add_subplot(221)
        self.ax_xy.set_title("Vue de dessus (Plan XY)", fontsize=10, fontweight='bold')
        self.ax_xy.set_xlabel("X (km)")
        self.ax_xy.set_ylabel("Y (km)")
        self.ax_xy.grid(True, alpha=0.3)
        self.ax_xy.set_aspect('equal')
        
        # Vue de face (XZ)
        self.ax_xz = self.fig_2d.add_subplot(223)
        self.ax_xz.set_title("Vue de face (Plan XZ)", fontsize=10, fontweight='bold')
        self.ax_xz.set_xlabel("X (km)")
        self.ax_xz.set_ylabel("Z (altitude, km)")
        self.ax_xz.grid(True, alpha=0.3)
        
        # Vue de côté (YZ)
        self.ax_yz = self.fig_2d.add_subplot(222)
        self.ax_yz.set_title("Vue de côté (Plan YZ)", fontsize=10, fontweight='bold')
        self.ax_yz.set_xlabel("Y (km)")
        self.ax_yz.set_ylabel("Z (altitude, km)")
        self.ax_yz.grid(True, alpha=0.3)
        
        # Espace pour légende
        self.ax_legend = self.fig_2d.add_subplot(224)
        self.ax_legend.axis('off')
        
        self.fig_2d.tight_layout(pad=3.0)
        
        # Canvas pour les vues 2D
        self.canvas_2d = FigureCanvasTkAgg(self.fig_2d, master=views_2d_frame)
        self.canvas_2d.draw()
        self.canvas_2d.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Ajouter la barre d'outils de navigation (pour zoom)
        from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
        toolbar_2d = NavigationToolbar2Tk(self.canvas_2d, views_2d_frame)
        toolbar_2d.update()
    
    def _create_parameters_tab(self):
        """Crée l'onglet avec les graphiques de paramètres"""
        
        params_frame = ttk.Frame(self.main_notebook)
        self.main_notebook.add(params_frame, text="📊 Paramètres")
        
        # Créer la figure pour les paramètres
        self.fig_params = plt.Figure(figsize=(14, 8))
        
        # Canvas
        self.canvas_params = FigureCanvasTkAgg(self.fig_params, master=params_frame)
        self.canvas_params.draw()
        self.canvas_params.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Barre d'outils
        from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
        toolbar_params = NavigationToolbar2Tk(self.canvas_params, params_frame)
        toolbar_params.update()
        
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
        
        # Cap initial avec description détaillée
        ttk.Label(control_frame, text="Cap initial (°):").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.heading_var = tk.DoubleVar(value=90.0)
        heading_entry = ttk.Entry(control_frame, textvariable=self.heading_var, width=15)
        heading_entry.grid(row=row, column=1, pady=5)
        row += 1
        
        # Aide visuelle pour le cap
        ttk.Label(control_frame, text="0°=Nord, 90°=Est, 180°=Sud, 270°=Ouest", 
                 font=('Arial', 7, 'italic'), foreground='gray').grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2)
        row += 1
        
        # Séparateur
        ttk.Separator(control_frame, orient='horizontal').grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=15)
        row += 1
        
        # Options de trajectoire
        ttk.Label(control_frame, text="Options Trajectoire", font=('Arial', 10, 'bold')).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=5)
        row += 1
        
        self.use_realistic_turns_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(control_frame, text="Virages réalistes (rejoindre axe d'approche)", 
                       variable=self.use_realistic_turns_var).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=5)
        row += 1
        
        ttk.Label(control_frame, text="Active le calcul de trajectoire avec virages\nrespectant le rayon de courbure minimum", 
                 font=('Arial', 7, 'italic'), foreground='gray').grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2)
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
            self._draw_config_preview()  # Mettre à jour la preview de configuration
            
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
            self._draw_config_preview()  # Mettre à jour la preview de configuration
            
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
        self._draw_config_preview()  # Mettre à jour la preview de configuration
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
        self._draw_config_preview()  # Mettre à jour la preview de configuration
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
        self._draw_config_preview()  # Mettre à jour la preview de configuration
        
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
        
    def _draw_config_preview(self):
        """Dessine la prévisualisation 3D dans l'onglet Configuration"""
        
        if self.environment is None:
            return
        
        self.ax_3d_config.clear()
        
        # Configuration de l'affichage
        self.ax_3d_config.set_xlim(0, self.environment.size_x)
        self.ax_3d_config.set_ylim(0, self.environment.size_y)
        self.ax_3d_config.set_zlim(0, self.environment.size_z)
        
        self.ax_3d_config.set_xlabel('X (km)', fontsize=8)
        self.ax_3d_config.set_ylabel('Y (km)', fontsize=8)
        self.ax_3d_config.set_zlabel('Z (km)', fontsize=8)
        
        # Dessiner l'aéroport
        airport = self.environment.airport_position
        self.ax_3d_config.scatter([airport[0]], [airport[1]], [airport[2]], 
                          c='red', marker='s', s=150, label='Aéroport')
        
        # Dessiner le point FAF
        faf = self.environment.faf_position
        self.ax_3d_config.scatter([faf[0]], [faf[1]], [faf[2]], 
                          c='blue', marker='^', s=100, label='Point FAF')
        
        # Dessiner l'axe d'approche
        direction = faf - airport
        direction_norm = np.linalg.norm(direction[:2])
        
        if direction_norm > 0:
            direction_unit = direction / direction_norm
            max_distance = max(self.environment.size_x, self.environment.size_y) * 2
            end_point = airport + direction_unit * max_distance
            
            self.ax_3d_config.plot([airport[0], end_point[0]], 
                           [airport[1], end_point[1]], 
                           [airport[2], end_point[2]], 
                           'k--', linewidth=1, alpha=0.5, label='Axe d\'approche')
        
        # Si l'avion est positionné
        if self.aircraft:
            self.ax_3d_config.scatter([self.aircraft.position[0]], [self.aircraft.position[1]], 
                             [self.aircraft.position[2]], c='green', marker='o', s=80, 
                             label='Avion')
            
            # Dessiner un vecteur montrant la direction de l'avion
            heading_rad = np.radians(self.aircraft.heading)
            direction_length = min(self.environment.size_x, self.environment.size_y) * 0.08
            dx = direction_length * np.sin(heading_rad)
            dy = direction_length * np.cos(heading_rad)
            
            self.ax_3d_config.quiver(self.aircraft.position[0], self.aircraft.position[1], 
                            self.aircraft.position[2], dx, dy, 0, 
                            color='green', arrow_length_ratio=0.3, linewidth=1.5, alpha=0.7)
        
        # Dessiner les cylindres (obstacles)
        if hasattr(self, 'cylinders') and self.cylinders:
            for cyl in self.cylinders:
                self._draw_cylinder_on_ax(self.ax_3d_config, cyl['x'], cyl['y'], 
                                         cyl['radius'], cyl['height'])
            
            # Ajouter une entrée de légende pour les cylindres
            self.ax_3d_config.plot([], [], [], 'r-', linewidth=2, alpha=0.5, 
                          label=f'Cylindres ({len(self.cylinders)})')
        
        # Légende
        self.ax_3d_config.legend(loc='upper right', fontsize=7, framealpha=0.8)
        self.ax_3d_config.set_title("Configuration de l'Environnement", fontsize=10, fontweight='bold')
        
        self.canvas_3d_config.draw()
    
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
            
            # Dessiner un vecteur montrant la direction de l'avion
            heading_rad = np.radians(self.aircraft.heading)
            # Direction: sin(heading) pour X (Est), cos(heading) pour Y (Nord)
            direction_length = min(self.environment.size_x, self.environment.size_y) * 0.1
            dx = direction_length * np.sin(heading_rad)
            dy = direction_length * np.cos(heading_rad)
            
            self.ax_3d.quiver(self.aircraft.position[0], self.aircraft.position[1], self.aircraft.position[2],
                            dx, dy, 0, color='green', arrow_length_ratio=0.3, linewidth=2, alpha=0.7)
        
        # Si une trajectoire existe
        if self.trajectory is not None:
            print(f"\n🎨 AFFICHAGE DE LA TRAJECTOIRE")
            print(f"   Nombre de points: {len(self.trajectory)}")
            print(f"   Forme: {self.trajectory.shape}")
            print(f"   Paramètres disponibles: {list(self.trajectory_params.keys()) if self.trajectory_params else 'Aucun'}")
            
            # Vérifier si c'est une nouvelle trajectoire avec virages et segment initial
            if self.trajectory_params and 'turn_radius' in self.trajectory_params:
                print(f"   📍 Type: Trajectoire avec VIRAGE (rayon {self.trajectory_params['turn_radius']:.3f} km)")
                
                # Vérifier s'il y a un segment initial (vol dans le cap initial)
                if 'initial_segment_end_index' in self.trajectory_params:
                    print(f"   📍 Trajectoire en 2 phases: Vol initial → Virage jusqu'au FAF")
                    initial_end_idx = self.trajectory_params['initial_segment_end_index']
                    turn_end_idx = self.trajectory_params['turn_segment_end_index']
                    turn_start = self.trajectory_params.get('turn_start_point', None)
                    intercept = self.trajectory_params['intercept_point']
                    
                    # Phase 1: Vol initial dans la direction du cap (en bleu marine)
                    if initial_end_idx > 0:
                        print(f"   🟦 Dessin VOL INITIAL: {initial_end_idx} points en BLEU MARINE")
                        self.ax_3d.plot(self.trajectory[:initial_end_idx, 0], 
                                       self.trajectory[:initial_end_idx, 1], 
                                       self.trajectory[:initial_end_idx, 2], 
                                       'navy', linewidth=2.5, label='Vol initial (cap)', alpha=0.9)
                        
                        # Marquer le point de début du virage
                        if turn_start is not None:
                            self.ax_3d.scatter([turn_start[0]], [turn_start[1]], [self.trajectory[initial_end_idx-1, 2]], 
                                              c='purple', marker='*', s=200, label='Début virage', zorder=5, 
                                              edgecolors='darkviolet', linewidths=1.5)
                            print(f"   ✓ Point début virage marqué: ({turn_start[0]:.1f}, {turn_start[1]:.1f})")
                    
                    # Phase 2: Virage progressif jusqu'au FAF avec alignement sur piste
                    # Diviser le virage en deux parties : virage + alignement
                    if turn_end_idx > initial_end_idx:
                        n_turn_points = turn_end_idx - initial_end_idx
                        
                        # 60% du virage en magenta (virage progressif)
                        split_idx = initial_end_idx + int(n_turn_points * 0.6)
                        print(f"   � Dessin VIRAGE PROGRESSIF: {split_idx - initial_end_idx} points en MAGENTA")
                        self.ax_3d.plot(self.trajectory[initial_end_idx:split_idx, 0], 
                                       self.trajectory[initial_end_idx:split_idx, 1], 
                                       self.trajectory[initial_end_idx:split_idx, 2], 
                                       'magenta', linewidth=2.5, label='Virage progressif', alpha=0.9)
                        
                        # 40% du virage en vert (alignement final)
                        print(f"   🟢 Dessin ALIGNEMENT PISTE: {turn_end_idx - split_idx} points en VERT")
                        self.ax_3d.plot(self.trajectory[split_idx:turn_end_idx, 0], 
                                       self.trajectory[split_idx:turn_end_idx, 1], 
                                       self.trajectory[split_idx:turn_end_idx, 2], 
                                       'limegreen', linewidth=2.5, label='Alignement piste→FAF', alpha=0.9)
                    
                    # Le virage se termine au FAF - trajectoire complète
                    print(f"   ✅ Trajectoire complète: l'avion arrive au FAF aligné avec la piste")
                    
                else:
                    # Ancienne version sans segment initial (ne devrait plus arriver)
                    print(f"   ⚠️ Version ancienne de trajectoire détectée")
            
            # Nouvelle trajectoire avec alignement progressif sur l'axe piste
            if self.trajectory_params and 'runway_alignment' in self.trajectory_params:
                print(f"   📍 Type: Trajectoire avec ALIGNEMENT PROGRESSIF sur axe piste")
                initial_end = self.trajectory_params.get('initial_segment_end', 0)
                turn_end = self.trajectory_params.get('turn_segment_end', initial_end)
                intercept = self.trajectory_params.get('intercept_point', None)
                
                # Phase 1: Vol initial (bleu marine)
                if initial_end > 0:
                    print(f"   🟦 Dessin VOL INITIAL: {initial_end} points en BLEU MARINE")
                    self.ax_3d.plot(self.trajectory[:initial_end, 0], 
                                   self.trajectory[:initial_end, 1], 
                                   self.trajectory[:initial_end, 2], 
                                   'navy', linewidth=2.5, label='Vol initial (cap)', alpha=0.9)
                
                # Phase 2: Virage progressif (magenta/violet)
                if turn_end > initial_end:
                    n_turn = turn_end - initial_end
                    print(f"   🟣 Dessin VIRAGE PROGRESSIF: {n_turn} points en MAGENTA")
                    self.ax_3d.plot(self.trajectory[initial_end:turn_end, 0], 
                                   self.trajectory[initial_end:turn_end, 1], 
                                   self.trajectory[initial_end:turn_end, 2], 
                                   'magenta', linewidth=2.5, label='Alignement progressif', alpha=0.9)
                    
                    # Marquer le point d'interception (aligné avec la piste)
                    if intercept is not None:
                        self.ax_3d.scatter([intercept[0]], [intercept[1]], [self.trajectory[turn_end-1, 2]], 
                                          c='purple', marker='D', s=150, label='Aligné avec piste', zorder=5, 
                                          edgecolors='darkviolet', linewidths=1.5)
                        print(f"   ✓ Point alignement marqué: ({intercept[0]:.1f}, {intercept[1]:.1f})")
                
                # Phase 3: Sur l'axe piste vers FAF (vert/orange selon altitude)
                if turn_end < len(self.trajectory):
                    altitudes = self.trajectory[turn_end:, 2]
                    if len(altitudes) > 1:
                        altitude_changes = np.diff(altitudes)
                        descent_start = turn_end
                        
                        for i, change in enumerate(altitude_changes):
                            if abs(change) > 0.001:
                                descent_start = turn_end + i
                                break
                        
                        # Approche en palier
                        if descent_start > turn_end:
                            n_level = descent_start - turn_end
                            print(f"   🟢 Dessin APPROCHE SUR PISTE: {n_level} points en VERT")
                            self.ax_3d.plot(self.trajectory[turn_end:descent_start, 0], 
                                           self.trajectory[turn_end:descent_start, 1], 
                                           self.trajectory[turn_end:descent_start, 2], 
                                           'g-', linewidth=2.5, label='Sur axe piste', alpha=0.9)
                        
                        # Descente
                        if descent_start < len(self.trajectory):
                            n_descent = len(self.trajectory) - descent_start
                            print(f"   🟠 Dessin DESCENTE: {n_descent} points en ORANGE")
                            self.ax_3d.plot(self.trajectory[descent_start:, 0], 
                                           self.trajectory[descent_start:, 1], 
                                           self.trajectory[descent_start:, 2], 
                                           'orangered', linewidth=2.5, label='Descente', alpha=0.9)
                    else:
                        # Tout sur l'axe
                        n_runway = len(self.trajectory) - turn_end
                        print(f"   🟢 Dessin SUR PISTE: {n_runway} points en VERT")
                        self.ax_3d.plot(self.trajectory[turn_end:, 0], 
                                       self.trajectory[turn_end:, 1], 
                                       self.trajectory[turn_end:, 2], 
                                       'g-', linewidth=2.5, label='Sur axe piste', alpha=0.9)
            
            # Ancienne trajectoire avec descente
            elif self.trajectory_params and 'descent_start_index' in self.trajectory_params:
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
                print(f"   🟢 Dessin TRAJECTOIRE SIMPLE: {len(self.trajectory)} points en VERT")
                self.ax_3d.plot(self.trajectory[:, 0], self.trajectory[:, 1], 
                               self.trajectory[:, 2], 'g-', linewidth=2.5, label='Trajectoire', alpha=0.9)
            
            print(f"✅ TRAJECTOIRE AFFICHÉE AVEC SUCCÈS\n")
        
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
        
        print(f"🖼️  Rafraîchissement du canvas 3D...")
        self.canvas_3d.draw()
        print(f"✅ Canvas 3D rafraîchi!\n")
        
        # Dessiner aussi les vues 2D
        self._draw_2d_views()
    
    def _draw_2d_views(self):
        """Dessine les vues 2D orthogonales (XY, XZ, YZ)"""
        
        if self.environment is None:
            return
        
        # Nettoyer tous les axes
        self.ax_xy.clear()
        self.ax_xz.clear()
        self.ax_yz.clear()
        self.ax_legend.clear()
        self.ax_legend.axis('off')
        
        # Réappliquer les labels et grilles
        self.ax_xy.set_title("Vue de dessus (Plan XY)", fontsize=10, fontweight='bold')
        self.ax_xy.set_xlabel("X (km)")
        self.ax_xy.set_ylabel("Y (km)")
        self.ax_xy.grid(True, alpha=0.3)
        self.ax_xy.set_aspect('equal')
        
        self.ax_xz.set_title("Vue de face (Plan XZ)", fontsize=10, fontweight='bold')
        self.ax_xz.set_xlabel("X (km)")
        self.ax_xz.set_ylabel("Z (altitude, km)")
        self.ax_xz.grid(True, alpha=0.3)
        
        self.ax_yz.set_title("Vue de côté (Plan YZ)", fontsize=10, fontweight='bold')
        self.ax_yz.set_xlabel("Y (km)")
        self.ax_yz.set_ylabel("Z (altitude, km)")
        self.ax_yz.grid(True, alpha=0.3)
        
        # Définir les limites
        self.ax_xy.set_xlim(0, self.environment.size_x)
        self.ax_xy.set_ylim(0, self.environment.size_y)
        self.ax_xz.set_xlim(0, self.environment.size_x)
        self.ax_xz.set_ylim(0, self.environment.size_z)
        self.ax_yz.set_xlim(0, self.environment.size_y)
        self.ax_yz.set_ylim(0, self.environment.size_z)
        
        # Dessiner l'aéroport
        airport = self.environment.airport_position
        self.ax_xy.scatter(airport[0], airport[1], c='red', marker='s', s=200, label='Aéroport', zorder=5)
        self.ax_xz.scatter(airport[0], airport[2], c='red', marker='s', s=200, zorder=5)
        self.ax_yz.scatter(airport[1], airport[2], c='red', marker='s', s=200, zorder=5)
        
        # Dessiner le FAF
        faf = self.environment.faf_position
        self.ax_xy.scatter(faf[0], faf[1], c='blue', marker='^', s=150, label='FAF', zorder=5)
        self.ax_xz.scatter(faf[0], faf[2], c='blue', marker='^', s=150, zorder=5)
        self.ax_yz.scatter(faf[1], faf[2], c='blue', marker='^', s=150, zorder=5)
        
        # Dessiner l'axe d'approche
        direction = faf - airport
        direction_norm = np.linalg.norm(direction[:2])
        if direction_norm > 0:
            direction_unit = direction / direction_norm
            max_distance = max(self.environment.size_x, self.environment.size_y) * 2
            end_point = airport + direction_unit * max_distance
            
            self.ax_xy.plot([airport[0], end_point[0]], [airport[1], end_point[1]], 
                           'k--', linewidth=1.5, alpha=0.6, label='Axe d\'approche')
            self.ax_xz.plot([airport[0], end_point[0]], [airport[2], end_point[2]], 
                           'k--', linewidth=1.5, alpha=0.6)
            self.ax_yz.plot([airport[1], end_point[1]], [airport[2], end_point[2]], 
                           'k--', linewidth=1.5, alpha=0.6)
        
        # Dessiner l'avion si positionné
        if self.aircraft:
            pos = self.aircraft.position
            self.ax_xy.scatter(pos[0], pos[1], c='green', marker='o', s=100, label='Avion', zorder=5)
            self.ax_xz.scatter(pos[0], pos[2], c='green', marker='o', s=100, zorder=5)
            self.ax_yz.scatter(pos[1], pos[2], c='green', marker='o', s=100, zorder=5)
            
            # Flèche de direction sur la vue XY
            heading_rad = np.radians(self.aircraft.heading)
            arrow_length = min(self.environment.size_x, self.environment.size_y) * 0.05
            dx = arrow_length * np.sin(heading_rad)
            dy = arrow_length * np.cos(heading_rad)
            self.ax_xy.arrow(pos[0], pos[1], dx, dy, head_width=1, head_length=0.5, 
                           fc='green', ec='green', alpha=0.7, linewidth=2, zorder=4)
        
        # Dessiner les cylindres
        if hasattr(self, 'cylinders') and self.cylinders:
            for cyl in self.cylinders:
                # Vue de dessus (XY) - cercle plein
                circle_xy = plt.Circle((cyl['x'], cyl['y']), cyl['radius'], 
                                      color='red', alpha=0.3, label='Cylindre' if cyl == self.cylinders[0] else '')
                self.ax_xy.add_patch(circle_xy)
                
                # Vue de face (XZ) - rectangle
                rect_width = cyl['radius'] * 2
                self.ax_xz.add_patch(plt.Rectangle((cyl['x'] - cyl['radius'], 0), 
                                                   rect_width, cyl['height'], 
                                                   color='red', alpha=0.3))
                
                # Vue de côté (YZ) - rectangle
                self.ax_yz.add_patch(plt.Rectangle((cyl['y'] - cyl['radius'], 0), 
                                                   rect_width, cyl['height'], 
                                                   color='red', alpha=0.3))
        
        # Dessiner la trajectoire si elle existe
        if self.trajectory is not None:
            # Vue XY (dessus)
            if self.trajectory_params and 'runway_alignment' in self.trajectory_params:
                # Nouvelle trajectoire avec alignement piste (3 phases)
                initial_end = self.trajectory_params.get('initial_segment_end', 0)
                turn_end = self.trajectory_params.get('turn_segment_end', initial_end)
                
                # Phase 1: Vol initial (bleu marine)
                if initial_end > 0:
                    self.ax_xy.plot(self.trajectory[:initial_end, 0], 
                                   self.trajectory[:initial_end, 1], 
                                   'navy', linewidth=2, label='Vol initial', alpha=0.9)
                
                # Phase 2: Virage progressif (magenta)
                if turn_end > initial_end:
                    self.ax_xy.plot(self.trajectory[initial_end:turn_end, 0], 
                                   self.trajectory[initial_end:turn_end, 1], 
                                   'magenta', linewidth=2, label='Alignement', alpha=0.9)
                
                # Phase 3: Sur axe piste (vert)
                if turn_end < len(self.trajectory):
                    self.ax_xy.plot(self.trajectory[turn_end:, 0], 
                                   self.trajectory[turn_end:, 1], 
                                   'g-', linewidth=2, label='Sur piste', alpha=0.9)
            
            if self.trajectory_params and 'turn_radius' in self.trajectory_params:
                # Vérifier s'il y a un segment initial (2 phases: vol initial → virage jusqu'au FAF)
                if 'initial_segment_end_index' in self.trajectory_params:
                    initial_end = self.trajectory_params['initial_segment_end_index']
                    turn_end = self.trajectory_params['turn_segment_end_index']
                    
                    # Phase 1: Vol initial (bleu marine)
                    if initial_end > 0:
                        self.ax_xy.plot(self.trajectory[:initial_end, 0], 
                                       self.trajectory[:initial_end, 1], 
                                       'navy', linewidth=2, label='Vol initial', alpha=0.9)
                    
                    # Phase 2: Virage progressif jusqu'au FAF (divisé en 2 couleurs)
                    if turn_end > initial_end:
                        # 60% virage en magenta, 40% alignement en vert
                        split_idx = initial_end + int((turn_end - initial_end) * 0.6)
                        
                        self.ax_xy.plot(self.trajectory[initial_end:split_idx, 0], 
                                       self.trajectory[initial_end:split_idx, 1], 
                                       'magenta', linewidth=2, label='Virage progressif', alpha=0.9)
                        
                        self.ax_xy.plot(self.trajectory[split_idx:turn_end, 0], 
                                       self.trajectory[split_idx:turn_end, 1], 
                                       'limegreen', linewidth=2, label='Alignement→FAF', alpha=0.9)
                else:
                    # Trajectoire simple (pas de phases)
                    self.ax_xy.plot(self.trajectory[:, 0], self.trajectory[:, 1], 
                                   'g-', linewidth=2, label='Trajectoire', alpha=0.9)
            else:
                self.ax_xy.plot(self.trajectory[:, 0], self.trajectory[:, 1], 
                               'g-', linewidth=2, label='Trajectoire', alpha=0.9)
            
            # Vue XZ (face)
            self.ax_xz.plot(self.trajectory[:, 0], self.trajectory[:, 2], 
                           'g-', linewidth=2, alpha=0.9)
            
            # Vue YZ (côté)
            self.ax_yz.plot(self.trajectory[:, 1], self.trajectory[:, 2], 
                           'g-', linewidth=2, alpha=0.9)
        
        # Légende commune
        handles, labels = self.ax_xy.get_legend_handles_labels()
        if handles:
            self.ax_legend.legend(handles, labels, loc='center', fontsize=10, framealpha=0.9)
        
        print(f"🖼️  Rafraîchissement des vues 2D...")
        self.canvas_2d.draw()
        print(f"✅ Vues 2D rafraîchies!\n")
    
    def _draw_cylinder_on_ax(self, ax, x, y, radius, height):
        """Dessine un cylindre (obstacle) sur un axe 3D donné"""
        # Créer le cylindre
        z = np.linspace(0, height, 20)
        theta = np.linspace(0, 2 * np.pi, 30)
        theta_grid, z_grid = np.meshgrid(theta, z)
        x_grid = radius * np.cos(theta_grid) + x
        y_grid = radius * np.sin(theta_grid) + y
        
        # Dessiner la surface du cylindre
        ax.plot_surface(x_grid, y_grid, z_grid, alpha=0.3, color='red', 
                       edgecolor='darkred', linewidth=0.5)
        
        # Dessiner le cercle du sommet
        theta_top = np.linspace(0, 2 * np.pi, 30)
        x_top = radius * np.cos(theta_top) + x
        y_top = radius * np.sin(theta_top) + y
        z_top = np.ones_like(theta_top) * height
        ax.plot(x_top, y_top, z_top, 'r-', linewidth=2, alpha=0.7)
    
    def _draw_cylinder(self, x, y, radius, height):
        """Dessine un cylindre (obstacle) dans l'espace 3D principal"""
        self._draw_cylinder_on_ax(self.ax_3d, x, y, radius, height)
        
    def _draw_parameters(self, time, altitude, slope, speed, heading=None, turn_rate=None):
        """Dessine les graphiques de paramètres"""
        
        self.fig_params.clear()
        
        # Déterminer le nombre de sous-graphiques (4 si on a le taux de virage)
        n_plots = 4 if turn_rate is not None else 3
        
        # Graphique 1: Altitude
        ax1 = self.fig_params.add_subplot(2, 2, 1)
        ax1.plot(time, altitude, 'b-', linewidth=2, label='Altitude')
        ax1.set_xlabel('Temps (s)', fontsize=9)
        ax1.set_ylabel('Altitude (km)', fontsize=9)
        ax1.set_title('Altitude au cours du temps', fontsize=10, fontweight='bold')
        ax1.grid(True, alpha=0.3)
        ax1.legend(fontsize=8)
        
        # Graphique 2: Pente avec limites
        ax2 = self.fig_params.add_subplot(2, 2, 2)
        ax2.plot(time, slope, 'r-', linewidth=2, label='Pente actuelle')
        ax2.set_xlabel('Temps (s)', fontsize=9)
        ax2.set_ylabel('Pente (°)', fontsize=9)
        ax2.set_title('Pente au cours du temps', fontsize=10, fontweight='bold')
        ax2.grid(True, alpha=0.3)
        ax2.axhline(y=0, color='k', linestyle='--', alpha=0.3)
        
        # Afficher les limites de pente si l'avion existe
        if self.aircraft:
            ax2.axhline(y=self.aircraft.max_climb_slope, color='green', 
                       linestyle='--', alpha=0.5, label=f'Montée max ({self.aircraft.max_climb_slope}°)')
            ax2.axhline(y=self.aircraft.max_descent_slope, color='red', 
                       linestyle='--', alpha=0.5, label=f'Descente max ({self.aircraft.max_descent_slope}°)')
        
        ax2.legend(fontsize=7)
        
        # Graphique 3: Vitesse
        ax3 = self.fig_params.add_subplot(2, 2, 3)
        ax3.plot(time, speed, 'g-', linewidth=2, label='Vitesse')
        ax3.set_xlabel('Temps (s)', fontsize=9)
        ax3.set_ylabel('Vitesse (km/h)', fontsize=9)
        ax3.set_title('Vitesse au cours du temps', fontsize=10, fontweight='bold')
        ax3.grid(True, alpha=0.3)
        ax3.legend(fontsize=8)
        
        # Graphique 4: Angle de virage (taux de virage) - NOUVEAU
        if turn_rate is not None:
            ax4 = self.fig_params.add_subplot(2, 2, 4)
            ax4.plot(time, turn_rate, 'purple', linewidth=2, label='Taux de virage')
            ax4.set_xlabel('Temps (s)', fontsize=9)
            ax4.set_ylabel('Taux de virage (°/s)', fontsize=9)
            ax4.set_title('Angle de Virage (Plan XY)', fontsize=10, fontweight='bold')
            ax4.grid(True, alpha=0.3)
            ax4.axhline(y=0, color='k', linestyle='--', alpha=0.3)
            
            # Calculer et afficher les statistiques
            max_turn = np.max(np.abs(turn_rate))
            avg_turn = np.mean(np.abs(turn_rate[turn_rate != 0])) if np.any(turn_rate != 0) else 0
            
            stats_text = f'Max: {max_turn:.2f}°/s\nMoy: {avg_turn:.2f}°/s'
            ax4.text(0.98, 0.97, stats_text, transform=ax4.transAxes,
                    verticalalignment='top', horizontalalignment='right',
                    bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5),
                    fontsize=8)
            
            # Zones de virage (fond coloré)
            positive_mask = turn_rate > 0.1
            negative_mask = turn_rate < -0.1
            if np.any(positive_mask):
                ax4.fill_between(time, 0, turn_rate, where=positive_mask, 
                                alpha=0.2, color='blue', label='Virage gauche')
            if np.any(negative_mask):
                ax4.fill_between(time, 0, turn_rate, where=negative_mask, 
                                alpha=0.2, color='red', label='Virage droite')
            
            ax4.legend(fontsize=7, loc='upper left')
        
        self.fig_params.tight_layout(pad=2.0)
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
            self._draw_config_preview()  # Mettre à jour la preview de configuration
            
            # Sauvegarde automatique de la position
            self._save_config()
            
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
            # Calculer la trajectoire selon l'option choisie
            calculator = TrajectoryCalculator(self.environment)
            
            # Vérifier s'il y a des obstacles
            if len(self.cylinders) > 0:
                print(f"\n🚧 Détection de {len(self.cylinders)} obstacle(s) - activation évitement")
            
            if self.use_realistic_turns_var.get():
                # Trajectoire avec virages réalistes (avec évitement d'obstacles)
                print("\n🔧 Calcul: Trajectoire avec VIRAGES RÉALISTES...")
                self.trajectory, self.trajectory_params = calculator.calculate_trajectory_with_turn(
                    self.aircraft, self.cylinders
                )
            else:
                # Trajectoire directe avec évitement automatique d'obstacles
                print("\n🔧 Calcul: Trajectoire DIRECTE...")
                self.trajectory, self.trajectory_params = calculator.calculate_trajectory(
                    self.aircraft, self.cylinders
                )
            
            print(f"\n📦 Trajectoire calculée: {len(self.trajectory)} points stockés dans self.trajectory")
            print(f"📦 Paramètres stockés: {list(self.trajectory_params.keys())}")
            
            # Mettre à jour les visualisations
            print(f"\n🎨 Appel de _draw_environment() pour afficher la trajectoire...")
            self._draw_environment()
            self._draw_parameters(self.trajectory_params['time'], 
                                self.trajectory_params['altitude'], 
                                self.trajectory_params['slope'], 
                                self.trajectory_params['speed'],
                                self.trajectory_params.get('heading'),
                                self.trajectory_params.get('turn_rate'))
            
            # Message de succès avec informations
            info_msg = "✅ Simulation terminée!\n\n"
            info_msg += f"📊 Distance totale: {self.trajectory_params['distance']:.2f} km\n"
            info_msg += f"⏱️  Temps de vol: {self.trajectory_params['flight_time']*60:.1f} minutes\n"
            info_msg += f"📍 Points de trajectoire: {self.trajectory_params.get('n_points', len(self.trajectory))}\n"
            
            # Informations sur les vitesses
            if 'initial_speed' in self.trajectory_params:
                info_msg += f"\n✈️  Vitesse initiale: {self.trajectory_params['initial_speed']:.1f} km/h\n"
                if 'approach_speed' in self.trajectory_params:
                    info_msg += f"🎯 Vitesse d'approche: {self.trajectory_params['approach_speed']:.1f} km/h\n"
            
            # Informations sur le virage (nouvelle trajectoire avec virages)
            if 'turn_radius' in self.trajectory_params:
                info_msg += f"\n🔄 Rayon de virage: {self.trajectory_params['turn_radius']:.3f} km\n"
                info_msg += f"🎯 Angle de virage: {abs(self.trajectory_params['turn_angle']):.1f}°\n"
                intercept = self.trajectory_params['intercept_point']
                info_msg += f"📍 Point d'interception: ({intercept[0]:.2f}, {intercept[1]:.2f}) km\n"
            
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
