

import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from mpl_toolkits.mplot3d import Axes3D

from environment import Environment
from aircraft import Aircraft, AircraftType
from trajectory_calculator import TrajectoryCalculator


# Configuration par défaut (utilisée si aucun fichier config n'est trouvé)
DEFAULT_CONFIG = {
    "environment": {
        "size_x": 100.0,
        "size_y": 100.0,
        "size_z": 10.0,
        "airport": {"x": 5.0, "y": 25.0, "z": 0.0},
        "faf": {"x": 20.0, "y": 25.0, "z": 1.0},
    },
    "cylinders": [
        {"x": 50.0, "y": 50.0, "radius": 2.0, "height": 3.0}
    ],
    "aircraft": {
        "type": "commercial",
        "position": {"x": 70.0, "y": 70.0, "z": 3.0},
        "speed": 250.0,
        "heading": 180.0,
    },
    "simulation": {
        "num_trajectories": 10  # Nombre de trajectoires pour les simulations multiples
    },
}


class FlightSimulatorGUI:
    """Interface graphique principale du simulateur"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Simulateur de Trajectoire d'Avion - P21")
        self.root.geometry("1600x900")
        
        # Charger et définir l'icône de l'application
        self._set_window_icon()
        
        # Initialisation de l'environnement avec valeurs par défaut
        self.environment = None
        self.aircraft = None
        self.trajectory = None
        self.trajectory_params = None  # Stocker les paramètres de la trajectoire
        self.cylinders = []  # Liste des cylindres (obstacles)
        
        # Variables pour les simulations multiples
        self.multiple_trajectories = []  # Liste des trajectoires multiples
        self.multiple_trajectories_params = []  # Liste des paramètres des trajectoires multiples
        self.failed_trajectory_positions = []  # Liste des positions où les trajectoires ont échoué
        
        # Gérer la fermeture de la fenêtre pour sauvegarder la configuration
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        self._create_ui()
        
        # Charger la configuration sauvegardée (si elle existe)
        self._load_config_on_startup()
        
        # Initialiser l'affichage des spécifications
        self._on_aircraft_type_changed()
        
        # Initialiser le texte du bouton de simulations multiples
        self._update_button_text()
        
        # Créer l'environnement initial
        self._update_environment()
        
        # Dessiner l'environnement avec les cylindres chargés
        self._draw_environment()
    
    # ========== MÉTHODES UTILITAIRES GÉNÉRIQUES ==========
    
    def _create_label_entry(self, parent, row, label_text, var, width=15):
        """Crée une paire label/entry standardisée et retourne la ligne suivante"""
        ttk.Label(parent, text=label_text).grid(row=row, column=0, sticky=tk.W, pady=5)
        ttk.Entry(parent, textvariable=var, width=width).grid(row=row, column=1, pady=5)
        return row + 1
    
    def _create_separator(self, parent, row):
        """Crée un séparateur horizontal et retourne la ligne suivante"""
        ttk.Separator(parent, orient='horizontal').grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=15)
        return row + 1
    
    def _create_section_title(self, parent, row, title, font_size=10):
        """Crée un titre de section et retourne la ligne suivante"""
        ttk.Label(parent, text=title, font=('Arial', font_size, 'bold')).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=5)
        return row + 1
    
    def _setup_canvas_scroll(self, canvas):
        """Configure le scroll sur un canvas (mousewheel + clavier)"""
        def on_mousewheel(e):
            canvas.yview_scroll(int(-1*(e.delta/120)), "units")
        canvas.bind('<Enter>', lambda e: canvas.bind_all("<MouseWheel>", on_mousewheel))
        canvas.bind('<Leave>', lambda e: canvas.unbind_all("<MouseWheel>"))
        canvas.bind("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
        canvas.bind("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))
        canvas.bind("<Up>", lambda e: canvas.yview_scroll(-1, "units"))
        canvas.bind("<Down>", lambda e: canvas.yview_scroll(1, "units"))
        canvas.bind("<Prior>", lambda e: canvas.yview_scroll(-10, "units"))
        canvas.bind("<Next>", lambda e: canvas.yview_scroll(10, "units"))
    
    def _plot_trajectory_segment(self, ax, trajectory, start_idx, end_idx, color, label, linewidth=2.5, alpha=0.9):
        """Trace un segment de trajectoire sur un axe 3D avec style donné"""
        if end_idx > start_idx and start_idx < len(trajectory):
            ax.plot(trajectory[start_idx:end_idx, 0], trajectory[start_idx:end_idx, 1], 
                   trajectory[start_idx:end_idx, 2], color=color, linewidth=linewidth, 
                   label=label, alpha=alpha)
    
    def _draw_trajectory_phases(self, ax):
        """Dessine les différentes phases de la trajectoire principale"""
        if self.trajectory is None:
            return
        
        params = self.trajectory_params
        
        # Nouvelle trajectoire avec virages et segment initial
        if params and 'turn_radius' in params and 'initial_segment_end_index' in params:
            initial_end = params['initial_segment_end_index']
            turn_end = params['turn_segment_end_index']
            
            # Phase 1: Vol initial
            if initial_end > 0:
                self._plot_trajectory_segment(ax, self.trajectory, 0, initial_end, 'navy', 'Vol initial (cap)')
                # Marquer début virage
                if 'turn_start_point' in params:
                    ax.scatter([params['turn_start_point'][0]], [params['turn_start_point'][1]], 
                              [self.trajectory[initial_end-1, 2]], c='purple', marker='*', s=200, 
                              label='Début virage', zorder=5, edgecolors='darkviolet', linewidths=1.5)
            
            # Phase 2: Virage (divisé en virage progressif + alignement)
            if turn_end > initial_end:
                split_idx = initial_end + int((turn_end - initial_end) * 0.6)
                self._plot_trajectory_segment(ax, self.trajectory, initial_end, split_idx, 'magenta', 'Virage progressif')
                self._plot_trajectory_segment(ax, self.trajectory, split_idx, turn_end, 'limegreen', 'Alignement piste→FAF')
        
        # Nouvelle trajectoire avec alignement progressif sur axe piste
        elif params and 'runway_alignment' in params:
            initial_end = params.get('initial_segment_end', 0)
            turn_end = params.get('turn_segment_end', initial_end)
            
            self._plot_trajectory_segment(ax, self.trajectory, 0, initial_end, 'navy', 'Vol initial (cap)')
            self._plot_trajectory_segment(ax, self.trajectory, initial_end, turn_end, 'magenta', 'Alignement progressif')
            
            # Phase 3: Sur axe piste (vert/orange selon descente)
            if turn_end < len(self.trajectory):
                altitudes = self.trajectory[turn_end:, 2]
                if len(altitudes) > 1:
                    descent_start = turn_end
                    for i, change in enumerate(np.diff(altitudes)):
                        if abs(change) > 0.001:
                            descent_start = turn_end + i
                            break
                    self._plot_trajectory_segment(ax, self.trajectory, turn_end, descent_start, 'g', 'Sur axe piste', linewidth=2.5)
                    self._plot_trajectory_segment(ax, self.trajectory, descent_start, len(self.trajectory), 'orangered', 'Descente', linewidth=2.5)
                else:
                    self._plot_trajectory_segment(ax, self.trajectory, turn_end, len(self.trajectory), 'g', 'Sur axe piste', linewidth=2.5)
        
        # Ancienne trajectoire avec descente
        elif params and 'descent_start_index' in params:
            descent_idx = params['descent_start_index']
            transition_end = params.get('transition_end_index', descent_idx)
            self._plot_trajectory_segment(ax, self.trajectory, 0, descent_idx, 'g', 'Vol en palier')
            self._plot_trajectory_segment(ax, self.trajectory, descent_idx, transition_end, 'gold', 'Transition progressive')
            self._plot_trajectory_segment(ax, self.trajectory, transition_end, len(self.trajectory), 'orangered', 'Descente')
        else:
            # Trajectoire simple
            ax.plot(self.trajectory[:, 0], self.trajectory[:, 1], self.trajectory[:, 2], 
                   'g-', linewidth=2.5, label='Trajectoire', alpha=0.9)
    
    def _draw_multiple_trajectories_on_ax(self, ax):
        """Dessine les trajectoires multiples sur un axe 3D donné"""
        if not hasattr(self, 'multiple_trajectories') or not self.multiple_trajectories:
            return
        
        colors = ['red', 'blue', 'green', 'orange', 'purple', 'brown', 'pink', 'gray', 'olive', 'cyan']
        for i, trajectory in enumerate(self.multiple_trajectories):
            color = colors[i % len(colors)]
            ax.plot(trajectory[:, 0], trajectory[:, 1], trajectory[:, 2], 
                   color=color, linewidth=2.0, alpha=0.7, label=f'Trajectoire {i+1}')
            # Marquer le point de départ
            ax.scatter([trajectory[0, 0]], [trajectory[0, 1]], [trajectory[0, 2]], 
                      c=color, marker='o', s=80, alpha=0.8, edgecolors='black', linewidths=1)
        print(f"✅ {len(self.multiple_trajectories)} TRAJECTOIRES MULTIPLES AFFICHÉES\n")
    
    def _draw_failed_positions(self, ax):
        """Dessine les positions des tentatives échouées"""
        if not hasattr(self, 'failed_trajectory_positions') or not self.failed_trajectory_positions:
            return
        
        print(f"\n💥 AFFICHAGE DE {len(self.failed_trajectory_positions)} POSITIONS ÉCHOUÉES")
        for i, failed_pos in enumerate(self.failed_trajectory_positions):
            pos, attempt_num = failed_pos['position'], failed_pos['attempt_number']
            print(f"   ❌ Position échouée {i+1} (tentative #{attempt_num}): ({pos[0]:.1f}, {pos[1]:.1f}, {pos[2]:.1f})")
            ax.scatter([pos[0]], [pos[1]], [pos[2]], c='red', marker='x', s=150, 
                      alpha=0.8, linewidths=3, label=f'Échec #{attempt_num}' if i == 0 else '')
            ax.text(pos[0], pos[1], pos[2] + 0.2, f'#{attempt_num}', 
                   fontsize=8, color='red', weight='bold')
    
    def _refresh_cylinder_display(self):
        """Met à jour l'affichage après modification des cylindres"""
        self._update_cylinders_list()
        self._draw_environment()
        self._draw_config_preview()
        self._save_config()
    
    def _setup_2d_axis(self, ax, title, xlabel, ylabel, xlim, ylim, equal_aspect=False):
        """Configure un axe 2D avec paramètres standard"""
        ax.set_title(title, fontsize=10, fontweight='bold')
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.grid(True, alpha=0.3)
        ax.set_xlim(xlim)
        ax.set_ylim(ylim)
        if equal_aspect:
            ax.set_aspect('equal')
    
    def _set_window_icon(self):
        """Définit l'icône de la fenêtre et de la barre des tâches"""
        import os
        import sys
        try:
            # Déterminer le répertoire de l'application
            if getattr(sys, 'frozen', False):
                # Application empaquetée avec PyInstaller (onefile extrait dans _MEIPASS)
                app_dir = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
            else:
                # Script Python normal
                app_dir = os.path.dirname(os.path.abspath(__file__))
            
            # Chercher d'abord un fichier .ico (meilleur pour Windows)
            ico_path = os.path.join(app_dir, 'logo.ico')
            png_path = os.path.join(app_dir, 'logo.png')
            
            icon_loaded = False
            
            # MÉTHODE SPÉCIALE POUR WINDOWS 10 : Utiliser ctypes pour définir l'AppUserModelID
            # Cela force Windows à utiliser l'icône de l'exécutable dans la barre des tâches
            if sys.platform == 'win32':
                try:
                    import ctypes
                    # Définir un AppUserModelID unique pour cette application
                    # Cela aide Windows 10/11 à identifier correctement l'application
                    myappid = 'estaca.trajectoireavion.simulateur.v1'
                    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
                except Exception as e:
                    pass
            
            # Méthode 1: Utiliser .ico avec iconbitmap (Windows)
            if sys.platform == 'win32' and os.path.exists(ico_path):
                try:
                    # Utiliser le chemin absolu
                    abs_ico_path = os.path.abspath(ico_path)
                    self.root.iconbitmap(default=abs_ico_path)
                    icon_loaded = True
                except Exception as e:
                    pass
            
            # Méthode 2: Utiliser PNG avec iconphoto (multiplateforme)
            if os.path.exists(png_path):
                try:
                    from PIL import Image, ImageTk
                    logo_image = Image.open(png_path)
                    # Créer plusieurs tailles pour meilleure qualité
                    sizes = [(16, 16), (32, 32), (48, 48), (64, 64)]
                    photos = []
                    for size in sizes:
                        img_resized = logo_image.resize(size, Image.Resampling.LANCZOS)
                        photo = ImageTk.PhotoImage(img_resized)
                        photos.append(photo)
                    
                    # Définir l'icône pour la fenêtre (utiliser la plus grande)
                    self.root.iconphoto(True, *photos)
                    
                    # Garder les références pour éviter le garbage collection
                    self.root._icon_photos = photos
                    
                    icon_loaded = True
                except Exception as e:
                    pass
            
            if not icon_loaded:
                print("⚠️  Aucun logo trouvé ou chargé (.ico ou .png)")
                
        except Exception as e:
            print(f"⚠️  Impossible de charger le logo: {e}")
            import traceback
            traceback.print_exc()
    
    def _on_closing(self):
        """Gestionnaire de fermeture de la fenêtre"""
        try:
            # Sauvegarder la configuration avant de fermer
            self._save_config()
            print("💾 Configuration sauvegardée avant fermeture")
        except Exception as e:
            print(f"⚠️  Erreur lors de la sauvegarde: {e}")
        finally:
            # Fermer l'application
            self.root.destroy()
        
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
        
        # Sous-onglet 3: Avion (avec scrollbar) - Optimisé
        aircraft_main_frame = ttk.Frame(config_notebook)
        config_notebook.add(aircraft_main_frame, text="✈️ Avion")
        
        # Canvas scrollable avec configuration automatique
        aircraft_canvas = tk.Canvas(aircraft_main_frame, highlightthickness=0)
        aircraft_scrollbar = ttk.Scrollbar(aircraft_main_frame, orient="vertical", command=aircraft_canvas.yview)
        aircraft_scrollable_frame = ttk.Frame(aircraft_canvas, padding="10")
        aircraft_scrollable_frame.bind("<Configure>", lambda e: aircraft_canvas.configure(scrollregion=aircraft_canvas.bbox("all")))
        aircraft_canvas.create_window((0, 0), window=aircraft_scrollable_frame, anchor="nw")
        aircraft_canvas.configure(yscrollcommand=aircraft_scrollbar.set)
        aircraft_canvas.pack(side="left", fill="both", expand=True)
        aircraft_scrollbar.pack(side="right", fill="y")
        self._setup_canvas_scroll(aircraft_canvas)
        self.aircraft_canvas = aircraft_canvas
        
        self._create_aircraft_config(aircraft_scrollable_frame)
        
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
        """Crée la configuration de l'environnement - Optimisé avec méthodes utilitaires"""
        row = 0
        
        # Dimensions de l'espace aérien
        row = self._create_section_title(parent, row, "Dimensions de l'Espace Aérien")
        self.env_size_x_var = tk.DoubleVar(value=DEFAULT_CONFIG["environment"]["size_x"])
        self.env_size_y_var = tk.DoubleVar(value=DEFAULT_CONFIG["environment"]["size_y"])
        self.env_size_z_var = tk.DoubleVar(value=DEFAULT_CONFIG["environment"]["size_z"])
        row = self._create_label_entry(parent, row, "Largeur X (km):", self.env_size_x_var)
        row = self._create_label_entry(parent, row, "Longueur Y (km):", self.env_size_y_var)
        row = self._create_label_entry(parent, row, "Hauteur Z (km):", self.env_size_z_var)
        row = self._create_separator(parent, row)
        
        # Position de l'Aéroport
        row = self._create_section_title(parent, row, "Position de l'Aéroport")
        self.airport_x_var = tk.DoubleVar(value=DEFAULT_CONFIG["environment"]["airport"]["x"])
        self.airport_y_var = tk.DoubleVar(value=DEFAULT_CONFIG["environment"]["airport"]["y"])
        self.airport_z_var = tk.DoubleVar(value=DEFAULT_CONFIG["environment"]["airport"]["z"])
        row = self._create_label_entry(parent, row, "Aéroport X (km):", self.airport_x_var)
        row = self._create_label_entry(parent, row, "Aéroport Y (km):", self.airport_y_var)
        row = self._create_label_entry(parent, row, "Aéroport Z (km):", self.airport_z_var)
        row = self._create_separator(parent, row)
        
        # Position du Point FAF
        row = self._create_section_title(parent, row, "Position du Point FAF")
        self.faf_x_var = tk.DoubleVar(value=DEFAULT_CONFIG["environment"]["faf"]["x"])
        self.faf_y_var = tk.DoubleVar(value=DEFAULT_CONFIG["environment"]["faf"]["y"])
        self.faf_z_var = tk.DoubleVar(value=DEFAULT_CONFIG["environment"]["faf"]["z"])
        row = self._create_label_entry(parent, row, "FAF X (km):", self.faf_x_var)
        row = self._create_label_entry(parent, row, "FAF Y (km):", self.faf_y_var)
        row = self._create_label_entry(parent, row, "FAF Z (km):", self.faf_z_var)
        row = self._create_separator(parent, row)
        
        # Bouton pour appliquer la configuration
        ttk.Button(parent, text="🔄 Appliquer Configuration", 
                  command=self._apply_environment_config).grid(row=row, column=0, columnspan=2, pady=10, sticky=(tk.W, tk.E))
        row += 1
        
        # Label d'info
        self.env_info_label = ttk.Label(parent, text="", font=('Arial', 8), foreground='green')
        self.env_info_label.grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2)
    
    def _create_obstacles_config(self, parent):
        """Crée l'onglet de gestion des obstacles (cylindres) - Optimisé"""
        # Canvas scrollable
        canvas = tk.Canvas(parent, borderwidth=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        self._setup_canvas_scroll(canvas)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        row = 0
        row = self._create_section_title(scrollable_frame, row, "Gestion des Cylindres (Obstacles)", 11)
        ttk.Label(scrollable_frame, text="Les cylindres représentent des zones interdites de vol",
                  font=('Arial', 8, 'italic'), foreground='gray').grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2)
        row = self._create_separator(scrollable_frame, row + 1) - 1

        # Section: Nouveau cylindre
        row = self._create_section_title(scrollable_frame, row, "➕ Nouveau Cylindre")
        self.cyl_x_var = tk.DoubleVar(value=DEFAULT_CONFIG['cylinders'][0]['x'])
        self.cyl_y_var = tk.DoubleVar(value=DEFAULT_CONFIG['cylinders'][0]['y'])
        self.cyl_radius_var = tk.DoubleVar(value=DEFAULT_CONFIG['cylinders'][0]['radius'])
        self.cyl_height_var = tk.DoubleVar(value=DEFAULT_CONFIG['cylinders'][0]['height'])
        row = self._create_label_entry(scrollable_frame, row, "Position X (km):", self.cyl_x_var)
        row = self._create_label_entry(scrollable_frame, row, "Position Y (km):", self.cyl_y_var)
        row = self._create_label_entry(scrollable_frame, row, "Rayon (km):", self.cyl_radius_var)
        row = self._create_label_entry(scrollable_frame, row, "Hauteur (km):", self.cyl_height_var)
        ttk.Button(scrollable_frame, text="➕ Ajouter ce Cylindre",
                   command=self._add_cylinder).grid(row=row, column=0, columnspan=2, pady=10, sticky=(tk.W, tk.E))
        row = self._create_separator(scrollable_frame, row + 1) - 1

        # Liste des cylindres
        row = self._create_section_title(scrollable_frame, row, "📋 Cylindres Actifs")
        list_container = ttk.Frame(scrollable_frame)
        list_container.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        list_scrollbar = ttk.Scrollbar(list_container)
        list_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.cylinders_listbox = tk.Listbox(list_container, height=8, yscrollcommand=list_scrollbar.set, font=('Courier', 9))
        self.cylinders_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        list_scrollbar.config(command=self.cylinders_listbox.yview)
        self.cylinders_listbox.bind('<Double-Button-1>', self._edit_selected_cylinder)
        row += 1

        # Boutons de gestion (compactés)
        for btn_texts_cmds in [
            [("✏️ Éditer Sélectionné", self._edit_selected_cylinder), ("🗑️ Supprimer Sélectionné", self._remove_selected_cylinder)],
            [("🗑️ Supprimer Dernier", self._remove_last_cylinder), ("🗑️ Tout Supprimer", self._clear_cylinders)]
        ]:
            btn_frame = ttk.Frame(scrollable_frame)
            btn_frame.grid(row=row, column=0, columnspan=2, pady=5, sticky=(tk.W, tk.E))
            for text, cmd in btn_texts_cmds:
                ttk.Button(btn_frame, text=text, command=cmd).pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
            row += 1

        self.cylinders = [dict(c) for c in DEFAULT_CONFIG.get("cylinders", [])]
        
    def _create_aircraft_config(self, parent):
        """Crée la configuration de l'avion - Optimisé"""
        row = 0
        
        # Type d'avion
        ttk.Label(parent, text="Type d'avion:", font=('Arial', 9, 'bold')).grid(row=row, column=0, sticky=tk.W, pady=5)
        self.aircraft_type_var = tk.StringVar(value="commercial")
        self.num_trajectories_var = tk.IntVar(value=DEFAULT_CONFIG["simulation"]["num_trajectories"])
        aircraft_combo = ttk.Combobox(parent, textvariable=self.aircraft_type_var, 
                                     values=AircraftType.get_all_types(), state='readonly', width=13)
        aircraft_combo.grid(row=row, column=1, pady=5)
        aircraft_combo.bind('<<ComboboxSelected>>', self._on_aircraft_type_changed)
        self.aircraft_specs_label = ttk.Label(parent, text="", font=('Arial', 8), foreground='blue')
        self.aircraft_specs_label.grid(row=row+1, column=0, columnspan=2, sticky=tk.W, pady=2)
        row = self._create_separator(parent, row + 2) - 1
        
        # Paramètres de position et vol
        self.pos_x_var = tk.DoubleVar(value=DEFAULT_CONFIG["aircraft"]["position"]["x"])
        self.pos_y_var = tk.DoubleVar(value=DEFAULT_CONFIG["aircraft"]["position"]["y"])
        self.altitude_var = tk.DoubleVar(value=DEFAULT_CONFIG["aircraft"]["position"]["z"])
        self.speed_var = tk.DoubleVar(value=DEFAULT_CONFIG["aircraft"]["speed"])
        self.heading_var = tk.DoubleVar(value=DEFAULT_CONFIG["aircraft"]["heading"])
        row = self._create_label_entry(parent, row, "Position X (km):", self.pos_x_var)
        row = self._create_label_entry(parent, row, "Position Y (km):", self.pos_y_var)
        row = self._create_label_entry(parent, row, "Altitude (km):", self.altitude_var)
        row = self._create_label_entry(parent, row, "Vitesse (km/h):", self.speed_var)
        row = self._create_label_entry(parent, row, "Cap initial (°):", self.heading_var)
        ttk.Label(parent, text="0°=Nord, 90°=Est, 180°=Sud, 270°=Ouest", 
                 font=('Arial', 7, 'italic'), foreground='gray').grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2)
        row = self._create_separator(parent, row + 1) - 1
        
        # Section Pentes
        row = self._create_section_title(parent, row, "Pentes de Vol")
        self.max_climb_slope_var = tk.DoubleVar(value=15.0)
        self.max_descent_slope_var = tk.DoubleVar(value=-3.0)
        row = self._create_label_entry(parent, row, "Pente max montée (°):", self.max_climb_slope_var)
        row = self._create_label_entry(parent, row, "Pente max descente (°):", self.max_descent_slope_var)
        ttk.Label(parent, text="Le type d'avion définit des valeurs par défaut", 
                 font=('Arial', 7, 'italic'), foreground='gray').grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2)
        row = self._create_separator(parent, row + 1)
        
        # Informations sur l'environnement
        row = self._create_section_title(parent, row, "Informations Environnement")
        self.airport_info_label = ttk.Label(parent, text="Aéroport: Configuration en cours...", font=('Arial', 8))
        self.airport_info_label.grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2)
        self.faf_info_label = ttk.Label(parent, text="FAF: Configuration en cours...", font=('Arial', 8))
        self.faf_info_label.grid(row=row+1, column=0, columnspan=2, sticky=tk.W, pady=2)
        row = self._create_separator(parent, row + 2)
        
        # Simulations multiples
        ttk.Label(parent, text="Simulations Multiples:", font=('Arial', 9, 'bold')).grid(row=row, column=0, sticky=tk.W, pady=5)
        ttk.Label(parent, text="Nombre de trajectoires:").grid(row=row+1, column=0, sticky=tk.W, pady=5)
        num_traj_frame = ttk.Frame(parent)
        num_traj_frame.grid(row=row+1, column=1, pady=5)
        self.num_traj_spinbox = tk.Spinbox(num_traj_frame, from_=1, to=50, 
            textvariable=self.num_trajectories_var, width=8, command=self._update_button_text)
        self.num_traj_spinbox.pack(side=tk.LEFT)
        for event in ['<KeyRelease>', '<FocusOut>']:
            self.num_traj_spinbox.bind(event, lambda e: self._update_button_text())
        row = self._create_separator(parent, row + 2)
        
        # Boutons de contrôle
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=row, column=0, columnspan=2, pady=10)
        for text, cmd in [("Valider Position", self._validate_position),
                          ("Lancer Simulation", self._run_simulation),
                          ("10 Simulations Aléatoires", self._run_multiple_random_simulations),
                          ("Effacer Trajectoires Multiples", self._clear_multiple_trajectories)]:
            btn = ttk.Button(button_frame, text=text, command=cmd)
            btn.pack(fill=tk.X, pady=5)
            if "10 Simulations" in text:
                self.multiple_sim_button = btn
        ttk.Button(button_frame, text="Réinitialiser", command=self._reset).pack(fill=tk.X, pady=5)
        parent.update_idletasks()
        if hasattr(self, 'aircraft_canvas'):
            self.aircraft_canvas.configure(scrollregion=self.aircraft_canvas.bbox("all"))
        

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
            
            # Sauvegarde automatique
            self._save_config()
            
            # Message de succès
            self.env_info_label.config(
                text="✅ Configuration appliquée avec succès!",
                foreground='green'
            )
            
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
        import sys
        
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
                    'heading': self.heading_var.get(),
                    'max_climb_slope': self.max_climb_slope_var.get() if hasattr(self, 'max_climb_slope_var') else None,
                    'max_descent_slope': self.max_descent_slope_var.get() if hasattr(self, 'max_descent_slope_var') else None
                },
                'simulation': {
                    'num_trajectories': self.num_trajectories_var.get()
                }
            }
            
            # Déterminer le répertoire de l'application
            if getattr(sys, 'frozen', False):
                script_dir = os.path.dirname(sys.executable)
            else:
                script_dir = os.path.dirname(os.path.abspath(__file__))
            
            config_file = os.path.join(script_dir, 'config.json')
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            
        except Exception as e:
            print(f"⚠️  Erreur de sauvegarde: {e}")
    
    def _load_config_on_startup(self):
        """Charge silencieusement la configuration au démarrage"""
        import json
        import os
        import sys
        
        try:
            # Déterminer le répertoire de l'application
            # Pour les exécutables PyInstaller, utiliser le répertoire de l'exe
            if getattr(sys, 'frozen', False):
                # Application empaquetée avec PyInstaller
                script_dir = os.path.dirname(sys.executable)
            else:
                # Script Python normal
                script_dir = os.path.dirname(os.path.abspath(__file__))
            
            config_file = os.path.join(script_dir, 'config.json')

            # Stratégie de chargement:
            # 1) Si un config.json existe à côté du script/exe, on l'utilise (config utilisateur persistante)
            # 2) Sinon, si on est en mode PyInstaller, on tente de charger le config.json embarqué dans _MEIPASS
            #    et on le copie comme base dans le dossier de l'exe pour les prochaines fois
            # 3) Sinon, on garde les valeurs par défaut codées

            config = None
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            else:
                # Fallback: config par défaut embarquée dans le bundle PyInstaller
                if getattr(sys, 'frozen', False):
                    meipass_dir = getattr(sys, '_MEIPASS', None)
                    if meipass_dir:
                        packaged_cfg = os.path.join(meipass_dir, 'config.json')
                        if os.path.exists(packaged_cfg):
                            try:
                                with open(packaged_cfg, 'r', encoding='utf-8') as f:
                                    config = json.load(f)
                                # Copier comme base pour les prochaines exécutions
                                try:
                                    with open(config_file, 'w', encoding='utf-8') as out:
                                        json.dump(config, out, indent=4, ensure_ascii=False)
                                except Exception as copy_err:
                                    # Pas bloquant si on ne peut pas écrire (dossier protégé, etc.)
                                    print(f"⚠️  Impossible d'écrire config par défaut à {config_file}: {copy_err}")
                            except Exception as e:
                                print(f"⚠️  Échec de lecture du config embarqué: {e}")
                                config = None
            
            if not config:
                # Pas de config chargeable, utiliser la config par défaut codée
                config = DEFAULT_CONFIG
            
            # À partir d'ici, appliquer la configuration chargée
            # Charger l'environnement
            env = config.get('environment', {})
            size_x = env.get('size_x', DEFAULT_CONFIG['environment']['size_x'])
            size_y = env.get('size_y', DEFAULT_CONFIG['environment']['size_y'])
            size_z = env.get('size_z', DEFAULT_CONFIG['environment']['size_z'])
            
            self.env_size_x_var.set(size_x)
            self.env_size_y_var.set(size_y)
            self.env_size_z_var.set(size_z)
            
            airport = env.get('airport', {})
            self.airport_x_var.set(airport.get('x', DEFAULT_CONFIG['environment']['airport']['x']))
            self.airport_y_var.set(airport.get('y', DEFAULT_CONFIG['environment']['airport']['y']))
            self.airport_z_var.set(airport.get('z', DEFAULT_CONFIG['environment']['airport']['z']))
            
            faf = env.get('faf', {})
            self.faf_x_var.set(faf.get('x', DEFAULT_CONFIG['environment']['faf']['x']))
            self.faf_y_var.set(faf.get('y', DEFAULT_CONFIG['environment']['faf']['y']))
            self.faf_z_var.set(faf.get('z', DEFAULT_CONFIG['environment']['faf']['z']))
            
            # Charger les cylindres
            self.cylinders = config.get('cylinders', DEFAULT_CONFIG.get('cylinders', []))
            
            # Mettre à jour l'affichage de la liste des cylindres
            if hasattr(self, 'cylinders_listbox'):
                self._update_cylinders_list()
            
            # Charger l'avion
            aircraft = config.get('aircraft', {})
            self.aircraft_type_var.set(aircraft.get('type', DEFAULT_CONFIG['aircraft']['type']))
            
            position = aircraft.get('position', {})
            self.pos_x_var.set(position.get('x', DEFAULT_CONFIG['aircraft']['position']['x']))
            self.pos_y_var.set(position.get('y', DEFAULT_CONFIG['aircraft']['position']['y']))
            self.altitude_var.set(position.get('z', DEFAULT_CONFIG['aircraft']['position']['z']))
            
            self.speed_var.set(aircraft.get('speed', DEFAULT_CONFIG['aircraft']['speed']))
            self.heading_var.set(aircraft.get('heading', DEFAULT_CONFIG['aircraft']['heading']))
            
            # Charger les pentes personnalisées si elles existent
            if hasattr(self, 'max_climb_slope_var'):
                max_climb_slope = aircraft.get('max_climb_slope')
                if max_climb_slope is not None:
                    self.max_climb_slope_var.set(max_climb_slope)
            
            if hasattr(self, 'max_descent_slope_var'):
                max_descent_slope = aircraft.get('max_descent_slope')
                if max_descent_slope is not None:
                    self.max_descent_slope_var.set(max_descent_slope)
            
            # Charger les paramètres de simulation
            simulation = config.get('simulation', {})
            if hasattr(self, 'num_trajectories_var'):
                self.num_trajectories_var.set(simulation.get('num_trajectories', DEFAULT_CONFIG['simulation']['num_trajectories']))
            
        except Exception as e:
            print(f"Erreur lors du chargement de la configuration: {e}")
            # Continuer avec les valeurs par défaut
    
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
            self._refresh_cylinder_display()
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
        self._refresh_cylinder_display()
        messagebox.showinfo("Succès", f"Cylindre supprimé:\nPosition: ({removed['x']:.1f}, {removed['y']:.1f}) km")
    
    def _clear_cylinders(self):
        """Supprime tous les cylindres"""
        if not self.cylinders:
            messagebox.showwarning("Attention", "Aucun cylindre à supprimer")
            return
        count = len(self.cylinders)
        self.cylinders.clear()
        self._refresh_cylinder_display()
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
        self.cyl_x_var.set(cyl['x'])
        self.cyl_y_var.set(cyl['y'])
        self.cyl_radius_var.set(cyl['radius'])
        self.cyl_height_var.set(cyl['height'])
        self.cylinders.pop(index)
        self._refresh_cylinder_display()
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
        self._refresh_cylinder_display()
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
        
    def _setup_3d_axis(self, ax, title="", label_size=10):
        """Configure un axe 3D avec les paramètres de base de l'environnement"""
        if self.environment is None:
            return
        ax.clear()
        ax.set_xlim(0, self.environment.size_x)
        ax.set_ylim(0, self.environment.size_y)
        ax.set_zlim(0, self.environment.size_z)
        ax.set_box_aspect([self.environment.size_x, self.environment.size_y, self.environment.size_z])
        if label_size > 0:
            ax.set_xlabel('X (km)', fontsize=label_size)
            ax.set_ylabel('Y (km)', fontsize=label_size)
            ax.set_zlabel('Z (km)', fontsize=label_size)
        if title:
            ax.set_title(title, fontsize=label_size+2, fontweight='bold' if label_size >= 10 else 'normal')
    
    def _draw_basic_elements(self, ax, draw_aircraft=True, draw_direction_arrow=True):
        """Dessine les éléments de base: aéroport, FAF, axe, avion"""
        if self.environment is None:
            return
        
        airport = self.environment.airport_position
        faf = self.environment.faf_position
        ax.scatter([airport[0]], [airport[1]], [airport[2]], 
                  c='red', marker='s', s=150, label='Aéroport')
        ax.scatter([faf[0]], [faf[1]], [faf[2]], 
                  c='blue', marker='^', s=100, label='Point FAF')
        
        # Axe d'approche
        direction = faf - airport
        direction_norm = np.linalg.norm(direction[:2])
        if direction_norm > 0:
            direction_unit = direction / direction_norm
            max_distance = max(self.environment.size_x, self.environment.size_y) * 2
            end_point = airport + direction_unit * max_distance
            ax.plot([airport[0], end_point[0]], [airport[1], end_point[1]], 
                   [airport[2], end_point[2]], 'k--', linewidth=1, alpha=0.5, label='Axe d\'approche')
        
        # Avion
        if draw_aircraft and self.aircraft:
            ax.scatter([self.aircraft.position[0]], [self.aircraft.position[1]], 
                      [self.aircraft.position[2]], c='green', marker='o', s=80, label='Avion')
            if draw_direction_arrow:
                heading_rad = np.radians(self.aircraft.heading)
                direction_length = min(self.environment.size_x, self.environment.size_y) * 0.08
                dx = direction_length * np.sin(heading_rad)
                dy = direction_length * np.cos(heading_rad)
                ax.quiver(self.aircraft.position[0], self.aircraft.position[1], 
                         self.aircraft.position[2], dx, dy, 0, 
                         color='green', arrow_length_ratio=0.3, linewidth=1.5, alpha=0.7)
    
    def _draw_config_preview(self):
        """Dessine la prévisualisation 3D dans l'onglet Configuration"""
        self._setup_3d_axis(self.ax_3d_config, "Configuration de l'Environnement", 8)
        self._draw_basic_elements(self.ax_3d_config)
        
        # Dessiner les cylindres
        if hasattr(self, 'cylinders') and self.cylinders:
            for cyl in self.cylinders:
                self._draw_cylinder_on_ax(self.ax_3d_config, cyl['x'], cyl['y'], 
                                         cyl['radius'], cyl['height'])
            self.ax_3d_config.plot([], [], [], 'r-', linewidth=2, alpha=0.5, 
                          label=f'Cylindres ({len(self.cylinders)})')
        
        self.ax_3d_config.legend(loc='upper right', fontsize=7, framealpha=0.8)
        self.canvas_3d_config.draw()
    
    def _draw_environment(self):
        """Dessine l'environnement 3D - Version optimisée"""
        if self.environment is None:
            return
        
        # Configuration de l'axe 3D principal
        self._setup_3d_axis(self.ax_3d, "Espace Aérien 3D - Version 1.1+ (Trajectoire Lissée)", 0)
        self.ax_3d.set_xticklabels([])
        self.ax_3d.set_yticklabels([])
        self.ax_3d.set_zticklabels([])
        
        # Dessiner éléments de base (aéroport, FAF, axe d'approche, avion)
        self._draw_basic_elements(self.ax_3d, draw_aircraft=True, draw_direction_arrow=True)
        
        # Dessiner la trajectoire principale si elle existe
        self._draw_trajectory_phases(self.ax_3d)
        
        # Dessiner les trajectoires multiples
        self._draw_multiple_trajectories_on_ax(self.ax_3d)
        
        # Dessiner les positions échouées
        self._draw_failed_positions(self.ax_3d)
        
        # Dessiner les cylindres (obstacles)
        if hasattr(self, 'cylinders') and self.cylinders:
            for cyl in self.cylinders:
                self._draw_cylinder(cyl['x'], cyl['y'], cyl['radius'], cyl['height'])
            self.ax_3d.plot([], [], [], 'r-', linewidth=3, alpha=0.7, 
                          label=f'Cylindres ({len(self.cylinders)})')
        
        # Légende et affichage
        self.ax_3d.legend(loc='center left', bbox_to_anchor=(1.05, 0.5), fontsize=8, 
                         framealpha=0.9, edgecolor='black', fancybox=True, shadow=True)
        self.ax_3d.set_title("Espace Aérien 3D - Version 1.1+ (Trajectoire Lissée)", pad=20)
        self.canvas_3d.draw()
        
        # Dessiner les vues 2D
        self._draw_2d_views()
    
    def _draw_2d_views(self):
        """Dessine les vues 2D orthogonales (XY, XZ, YZ) - Optimisé"""
        if self.environment is None:
            return
        
        # Nettoyer et configurer les axes
        for ax in [self.ax_xy, self.ax_xz, self.ax_yz, self.ax_legend]:
            ax.clear()
        self.ax_legend.axis('off')
        
        # Configuration des axes avec limites
        self._setup_2d_axis(self.ax_xy, "Vue de dessus (Plan XY)", "X (km)", "Y (km)",
                           (0, self.environment.size_x), (0, self.environment.size_y), equal_aspect=True)
        self._setup_2d_axis(self.ax_xz, "Vue de face (Plan XZ)", "X (km)", "Z (altitude, km)",
                           (0, self.environment.size_x), (0, self.environment.size_z))
        self._setup_2d_axis(self.ax_yz, "Vue de côté (Plan YZ)", "Y (km)", "Z (altitude, km)",
                           (0, self.environment.size_y), (0, self.environment.size_z))
        
        # Dessiner aéroport et FAF
        airport, faf = self.environment.airport_position, self.environment.faf_position
        for ax, (i1, i2) in zip([self.ax_xy, self.ax_xz, self.ax_yz], [(0,1), (0,2), (1,2)]):
            ax.scatter(airport[i1], airport[i2], c='blue', marker='s', s=100, label='Aéroport' if ax == self.ax_xy else None, zorder=5)
            ax.scatter(faf[i1], faf[i2], c='red', marker='^', s=100, label='FAF' if ax == self.ax_xy else None, zorder=5)
        
        # Axe d'approche
        direction = faf - airport
        if np.linalg.norm(direction[:2]) > 0:
            direction_unit = direction / np.linalg.norm(direction[:2])
            end_point = airport + direction_unit * max(self.environment.size_x, self.environment.size_y) * 2
            self.ax_xy.plot([airport[0], end_point[0]], [airport[1], end_point[1]], 
                           'k--', linewidth=1.5, alpha=0.6, label='Axe d\'approche')
            self.ax_xz.plot([airport[0], end_point[0]], [airport[2], end_point[2]], 'k--', linewidth=1.5, alpha=0.6)
            self.ax_yz.plot([airport[1], end_point[1]], [airport[2], end_point[2]], 'k--', linewidth=1.5, alpha=0.6)
        
        # Avion avec flèche
        if self.aircraft:
            pos = self.aircraft.position
            for ax, (i1, i2) in zip([self.ax_xy, self.ax_xz, self.ax_yz], [(0,1), (0,2), (1,2)]):
                ax.scatter(pos[i1], pos[i2], c='green', marker='o', s=100, 
                          label='Avion' if ax == self.ax_xy else None, zorder=5)
            heading_rad = np.radians(self.aircraft.heading)
            arrow_length = min(self.environment.size_x, self.environment.size_y) * 0.05
            self.ax_xy.arrow(pos[0], pos[1], arrow_length * np.sin(heading_rad), 
                           arrow_length * np.cos(heading_rad), head_width=1, head_length=0.5, 
                           fc='green', ec='green', alpha=0.7, linewidth=2, zorder=4)
        
        # Cylindres
        if hasattr(self, 'cylinders') and self.cylinders:
            for cyl in self.cylinders:
                self.ax_xy.add_patch(plt.Circle((cyl['x'], cyl['y']), cyl['radius'], 
                    color='red', alpha=0.3, label='Cylindre' if cyl == self.cylinders[0] else ''))
                rect_width = cyl['radius'] * 2
                self.ax_xz.add_patch(plt.Rectangle((cyl['x'] - cyl['radius'], 0), 
                    rect_width, cyl['height'], color='red', alpha=0.3))
                self.ax_yz.add_patch(plt.Rectangle((cyl['y'] - cyl['radius'], 0), 
                    rect_width, cyl['height'], color='red', alpha=0.3))
        
        # Trajectoire principale
        if self.trajectory is not None:
            if self.trajectory_params and self.trajectory_params.get('has_altitude_turns', False):
                self._draw_spiral_trajectory_2d()
            else:
                self._draw_normal_trajectory_2d()
            self.ax_xz.plot(self.trajectory[:, 0], self.trajectory[:, 2], 'g-', linewidth=2, alpha=0.9)
            self.ax_yz.plot(self.trajectory[:, 1], self.trajectory[:, 2], 'g-', linewidth=2, alpha=0.9)
        
        # Trajectoires multiples
        if hasattr(self, 'multiple_trajectories') and self.multiple_trajectories:
            colors = ['red', 'blue', 'green', 'orange', 'purple', 'brown', 'pink', 'gray', 'olive', 'cyan']
            for i, traj in enumerate(self.multiple_trajectories):
                color = colors[i % len(colors)]
                self.ax_xy.plot(traj[:, 0], traj[:, 1], color=color, linewidth=1.5, alpha=0.6, 
                               label=f'Traj. {i+1}' if i < 3 else '')
                self.ax_xz.plot(traj[:, 0], traj[:, 2], color=color, linewidth=1.5, alpha=0.6)
                self.ax_yz.plot(traj[:, 1], traj[:, 2], color=color, linewidth=1.5, alpha=0.6)
                for ax, idx in [(self.ax_xy, (0,1)), (self.ax_xz, (0,2)), (self.ax_yz, (1,2))]:
                    ax.scatter([traj[0, idx[0]]], [traj[0, idx[1]]], c=color, marker='o', 
                              s=50, alpha=0.8, edgecolors='black', linewidths=0.5)
        
        # Légende
        handles, labels = self.ax_xy.get_legend_handles_labels()
        if handles:
            self.ax_legend.legend(handles, labels, loc='center', fontsize=10, framealpha=0.9)
        self.canvas_2d.draw()
    
    def _draw_spiral_trajectory_2d(self):
        """Dessine une trajectoire avec spirales de manière visible dans les vues 2D"""
        spiral_points = self.trajectory_params.get('spiral_points', 0)
        
        if spiral_points > 0:
            # Partie 1: Spirale (tours automatiques) avec visualisation améliorée
            spiral_trajectory = self.trajectory[:spiral_points]
            normal_trajectory = self.trajectory[spiral_points:]
            
            # Dessiner la spirale avec des couleurs dégradées pour chaque tour
            self._draw_enhanced_spiral_xy(spiral_trajectory)
            
            # Dessiner la trajectoire normale après la spirale
            if len(normal_trajectory) > 0:
                self.ax_xy.plot(normal_trajectory[:, 0], normal_trajectory[:, 1], 
                               'limegreen', linewidth=3, label='→ Vers FAF', alpha=0.9, zorder=3)
        else:
            # Pas de spirale, dessiner normalement
            self._draw_normal_trajectory_2d()
        
        # Dessiner dans les autres vues (XZ et YZ) avec couleurs normales
        self.ax_xz.plot(self.trajectory[:, 0], self.trajectory[:, 2], 
                       'purple', linewidth=2, label='Trajectoire', alpha=0.8)
        self.ax_yz.plot(self.trajectory[:, 1], self.trajectory[:, 2], 
                       'purple', linewidth=2, label='Trajectoire', alpha=0.8)
    
    def _draw_enhanced_spiral_xy(self, spiral_trajectory):
        """Dessine une spirale avec visualisation améliorée dans la vue XY"""
        if len(spiral_trajectory) < 100:
            # Spirale trop courte, dessiner normalement
            self.ax_xy.plot(spiral_trajectory[:, 0], spiral_trajectory[:, 1], 
                           'orange', linewidth=2, label='Tours', alpha=0.8)
            return
        
        # Calculer le nombre de tours approximatif
        n_points = len(spiral_trajectory)
        estimated_turns = self.trajectory_params.get('turns_completed', 1)
        points_per_turn = max(100, n_points // max(1, int(estimated_turns)))
        
        # Couleurs pour les tours successifs
        turn_colors = ['red', 'darkorange', 'gold', 'orange', 'yellow', 'coral']
        
        # Dessiner chaque tour avec une couleur différente et épaisseur variable
        turn_number = 0
        for i in range(0, n_points, points_per_turn):
            end_idx = min(i + points_per_turn, n_points)
            if end_idx - i < 10:  # Segment trop court
                continue
                
            segment = spiral_trajectory[i:end_idx]
            color = turn_colors[turn_number % len(turn_colors)]
            
            # Épaisseur décroissante pour montrer la progression
            linewidth = 4 - (turn_number * 0.5)
            linewidth = max(1.5, linewidth)
            
            # Transparence croissante pour les tours plus anciens
            alpha = 1.0 - (turn_number * 0.15)
            alpha = max(0.4, alpha)
            
            label = f'Tour {turn_number + 1}' if turn_number < 3 else None
            
            self.ax_xy.plot(segment[:, 0], segment[:, 1], 
                           color=color, linewidth=linewidth, label=label, 
                           alpha=alpha, zorder=4 + turn_number)
            
            # Ajouter des flèches directionnelles sur chaque tour
            if len(segment) > 20:
                mid_idx = len(segment) // 2
                if mid_idx + 5 < len(segment):
                    # Direction de la flèche
                    dx = segment[mid_idx + 5, 0] - segment[mid_idx, 0]
                    dy = segment[mid_idx + 5, 1] - segment[mid_idx, 1]
                    
                    # Normaliser et ajuster la taille
                    length = np.sqrt(dx*dx + dy*dy)
                    if length > 0:
                        arrow_scale = 0.3
                        dx = (dx / length) * arrow_scale
                        dy = (dy / length) * arrow_scale
                        
                        self.ax_xy.arrow(segment[mid_idx, 0], segment[mid_idx, 1], 
                                        dx, dy, head_width=0.2, head_length=0.15, 
                                        fc=color, ec=color, alpha=alpha*1.2, 
                                        linewidth=1, zorder=6)
            
            turn_number += 1
        
        # Marquer le centre de la spirale
        if len(spiral_trajectory) > 10:
            center_x = np.mean(spiral_trajectory[:, 0])
            center_y = np.mean(spiral_trajectory[:, 1])
            self.ax_xy.scatter(center_x, center_y, c='darkred', marker='x', s=100, 
                              label='Centre spirale', zorder=7, linewidth=3)
    
    def _draw_normal_trajectory_2d(self):
        """Dessine une trajectoire normale (sans spirales) dans les vues 2D"""
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
        
        elif self.trajectory_params and 'turn_radius' in self.trajectory_params:
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
        
        # Dessiner dans les autres vues
        self.ax_xz.plot(self.trajectory[:, 0], self.trajectory[:, 2], 
                       'g-', linewidth=2, label='Trajectoire', alpha=0.9)
        self.ax_yz.plot(self.trajectory[:, 1], self.trajectory[:, 2], 
                       'g-', linewidth=2, label='Trajectoire', alpha=0.9)

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
        
        # Graphique 3: Angle de virage (taux de virage)
        if turn_rate is not None:
            ax3 = self.fig_params.add_subplot(2, 2, 3)
            ax3.plot(time, turn_rate, 'purple', linewidth=2, label='Taux de virage')
            ax3.set_xlabel('Temps (s)', fontsize=9)
            ax3.set_ylabel('Taux de virage (°/s)', fontsize=9)
            ax3.set_title('Angle de Virage (Plan XY)', fontsize=10, fontweight='bold')
            ax3.grid(True, alpha=0.3)
            ax3.axhline(y=0, color='k', linestyle='--', alpha=0.3)
            
            # Calculer et afficher les statistiques
            max_turn = np.max(np.abs(turn_rate))
            avg_turn = np.mean(np.abs(turn_rate[turn_rate != 0])) if np.any(turn_rate != 0) else 0
            
            stats_text = f'Max: {max_turn:.2f}°/s\nMoy: {avg_turn:.2f}°/s'
            ax3.text(0.98, 0.97, stats_text, transform=ax3.transAxes,
                    verticalalignment='top', horizontalalignment='right',
                    bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5),
                    fontsize=8)
            
            # Zones de virage (fond coloré)
            positive_mask = turn_rate > 0.1
            negative_mask = turn_rate < -0.1
            if np.any(positive_mask):
                ax3.fill_between(time, 0, turn_rate, where=positive_mask, 
                                alpha=0.2, color='blue', label='Virage gauche')
            if np.any(negative_mask):
                ax3.fill_between(time, 0, turn_rate, where=negative_mask, 
                                alpha=0.2, color='red', label='Virage droite')
            
            ax3.legend(fontsize=7, loc='upper left')
        
        self.fig_params.tight_layout(pad=2.0)
        self.canvas_params.draw()
    
    def _draw_multiple_parameters(self):
        """Dessine les graphiques de paramètres pour toutes les trajectoires multiples"""
        
        if not hasattr(self, 'multiple_trajectories_params') or not self.multiple_trajectories_params:
            return
        
        self.fig_params.clear()
        
        print(f"\n📊 AFFICHAGE DES PARAMÈTRES DE {len(self.multiple_trajectories_params)} TRAJECTOIRES")
        
        # Couleurs distinctes pour les trajectoires multiples
        colors = ['red', 'blue', 'green', 'orange', 'purple', 'brown', 'pink', 'gray', 'olive', 'cyan']
        
        # Graphique 1: Altitude
        ax1 = self.fig_params.add_subplot(2, 2, 1)
        ax1.set_xlabel('Temps (s)', fontsize=9)
        ax1.set_ylabel('Altitude (km)', fontsize=9)
        ax1.set_title('Altitude au cours du temps (Toutes trajectoires)', fontsize=10, fontweight='bold')
        ax1.grid(True, alpha=0.3)
        
        # Graphique 2: Pente
        ax2 = self.fig_params.add_subplot(2, 2, 2)
        ax2.set_xlabel('Temps (s)', fontsize=9)
        ax2.set_ylabel('Pente (°)', fontsize=9)
        ax2.set_title('Pente au cours du temps (Toutes trajectoires)', fontsize=10, fontweight='bold')
        ax2.grid(True, alpha=0.3)
        ax2.axhline(y=0, color='k', linestyle='--', alpha=0.3)
        
        # Graphique 3: Taux de virage (si disponible)
        ax3 = self.fig_params.add_subplot(2, 2, 3)
        ax3.set_xlabel('Temps (s)', fontsize=9)
        ax3.set_ylabel('Taux de virage (°/s)', fontsize=9)
        ax3.set_title('Taux de virage (Toutes trajectoires)', fontsize=10, fontweight='bold')
        ax3.grid(True, alpha=0.3)
        ax3.axhline(y=0, color='k', linestyle='--', alpha=0.3)
        
        # Dessiner chaque trajectoire
        for i, params in enumerate(self.multiple_trajectories_params):
            color = colors[i % len(colors)]
            alpha = 0.7 if len(self.multiple_trajectories_params) <= 5 else 0.5
            linewidth = 1.5 if len(self.multiple_trajectories_params) <= 5 else 1.0
            
            label = f'Traj. {i+1}' if i < 10 else ''  # Limiter les labels
            
            # Altitude
            if 'time' in params and 'altitude' in params:
                ax1.plot(params['time'], params['altitude'], color=color, 
                        linewidth=linewidth, alpha=alpha, label=label)
            
            # Pente
            if 'time' in params and 'slope' in params:
                ax2.plot(params['time'], params['slope'], color=color, 
                        linewidth=linewidth, alpha=alpha, label=label)
            
            # Taux de virage (si disponible)
            if 'time' in params and 'turn_rate' in params and params['turn_rate'] is not None:
                ax3.plot(params['time'], params['turn_rate'], color=color, 
                        linewidth=linewidth, alpha=alpha, label=label)
        
        # Afficher les limites de pente si l'avion existe
        if self.aircraft:
            ax2.axhline(y=self.aircraft.max_climb_slope, color='green', 
                       linestyle='--', alpha=0.5, label=f'Montée max ({self.aircraft.max_climb_slope}°)')
            ax2.axhline(y=self.aircraft.max_descent_slope, color='red', 
                       linestyle='--', alpha=0.5, label=f'Descente max ({self.aircraft.max_descent_slope}°)')
        
        # Légendes (seulement si pas trop de trajectoires)
        if len(self.multiple_trajectories_params) <= 10:
            ax1.legend(fontsize=7, loc='best')
            ax2.legend(fontsize=7, loc='best')
            ax3.legend(fontsize=7, loc='best')
        
        self.fig_params.tight_layout(pad=2.0)
        self.canvas_params.draw()
        
        print(f"✅ PARAMÈTRES DE {len(self.multiple_trajectories_params)} TRAJECTOIRES AFFICHÉS\n")
        
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
        
        # Mettre à jour les pentes par défaut (si les variables existent)
        if hasattr(self, 'max_climb_slope_var'):
            self.max_climb_slope_var.set(specs['max_climb_slope'])
        if hasattr(self, 'max_descent_slope_var'):
            self.max_descent_slope_var.set(specs['max_descent_slope'])
    
    def _update_button_text(self):
        """Met à jour le texte du bouton de simulations multiples"""
        try:
            num_traj = self.num_trajectories_var.get()
            if num_traj <= 0:
                num_traj = 1
                self.num_trajectories_var.set(1)
            elif num_traj > 50:
                num_traj = 50
                self.num_trajectories_var.set(50)
            
            # Mettre à jour le texte du bouton
            if hasattr(self, 'multiple_sim_button'):
                self.multiple_sim_button.config(text=f"{num_traj} Simulations Aléatoires")
        except (ValueError, tk.TclError):
            # En cas d'erreur (valeur non numérique), remettre la valeur par défaut
            self.num_trajectories_var.set(10)
            if hasattr(self, 'multiple_sim_button'):
                self.multiple_sim_button.config(text="10 Simulations Aléatoires")
    
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
                aircraft_type=aircraft_type,
                max_climb_slope=self.max_climb_slope_var.get(),
                max_descent_slope=self.max_descent_slope_var.get()
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
        
        # Réinitialiser les trajectoires multiples pour basculer vers mode simple
        self.multiple_trajectories = []
        self.multiple_trajectories_params = []
        
        try:
            # Calculer la trajectoire selon l'option choisie
            calculator = TrajectoryCalculator(self.environment)
            
            # Trajectoire avec courbes de Bézier (mode principal)
            self.trajectory, self.trajectory_params = calculator.calculate_trajectory(
                self.aircraft, self.cylinders
            )
            
            # Mettre à jour les visualisations
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
            
            # Information sur la vitesse
            info_msg += f"\n✈️  Vitesse: {self.aircraft.speed:.1f} km/h (constante)\n"
            
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
    
    def _generate_random_position(self):
        """
        Génère une position aléatoire valide selon les contraintes:
        - Plus de 1km du sol (altitude > 1km)
        - Plus de 1km des bords de la carte 
        - Pas dans un obstacle (cylindres)
        - Plus de 20km du point FAF (distance horizontale dans le plan XY)
        """
        import random
        
        if self.environment is None:
            return None
        
        max_attempts = 1000
        faf_pos = self.environment.faf_position
        
        for attempt in range(max_attempts):
            # Générer position aléatoire avec contraintes de bords (>1km)
            x = random.uniform(1.0, self.environment.size_x - 1.0)
            y = random.uniform(1.0, self.environment.size_y - 1.0)
            z = random.uniform(1.0, self.environment.size_z)  # >1km du sol
            
            # Cap aléatoire
            heading = random.uniform(0, 360)
            
            position = np.array([x, y, z])
            
            # Vérifier distance au FAF dans le plan XY uniquement (>20km)
            position_xy = np.array([x, y])
            faf_pos_xy = np.array([faf_pos[0], faf_pos[1]])
            distance_to_faf_xy = np.linalg.norm(position_xy - faf_pos_xy)
            if distance_to_faf_xy <= 20.0:
                continue
                
            # Vérifier qu'on n'est pas dans un obstacle
            in_obstacle = False
            for cylinder in self.cylinders:
                # Distance horizontale au centre du cylindre
                dist_horizontal = np.sqrt((x - cylinder['x'])**2 + (y - cylinder['y'])**2)
                # Vérifier si dans le cylindre (horizontalement et verticalement)
                if (dist_horizontal <= cylinder['radius'] and z <= cylinder['height']):
                    in_obstacle = True
                    break
            
            if not in_obstacle:
                return (x, y, z, heading)
        
        # Si aucune position trouvée après max_attempts
        return None
    
    def _run_multiple_random_simulations(self):
        """Lance X simulations aléatoires avec positions différentes (X configurable par l'utilisateur)"""
        
        if self.environment is None:
            messagebox.showwarning("Attention", "Veuillez d'abord configurer l'environnement!")
            return
        
        # Récupérer le nombre de trajectoires configuré
        try:
            num_trajectories = self.num_trajectories_var.get()
            if num_trajectories <= 0:
                messagebox.showwarning("Attention", "Le nombre de trajectoires doit être supérieur à 0!")
                return
            if num_trajectories > 50:
                messagebox.showwarning("Attention", "Le nombre maximum de trajectoires est limité à 50!")
                return
        except (ValueError, tk.TclError):
            messagebox.showerror("Erreur", "Veuillez entrer un nombre valide de trajectoires!")
            return
        
        # Réinitialiser la trajectoire simple pour basculer vers mode multiple
        self.trajectory = None
        self.trajectory_params = None
        
        # Garder les trajectoires multiples existantes (mode cumul)
        if not hasattr(self, 'multiple_trajectories'):
            self.multiple_trajectories = []
        if not hasattr(self, 'multiple_trajectories_params'):
            self.multiple_trajectories_params = []
        if not hasattr(self, 'failed_trajectory_positions'):
            self.failed_trajectory_positions = []
        
        # Sauvegarder la position actuelle de l'avion
        original_aircraft_config = None
        if self.aircraft:
            original_aircraft_config = {
                'position': np.array(self.aircraft.position),
                'speed': self.aircraft.speed,
                'heading': self.aircraft.heading,
                'aircraft_type': self.aircraft.aircraft_type
            }
        
        successful_simulations = 0
        failed_positions = 0
        failed_attempts = []  # Liste pour stocker les numéros des tentatives échouées
        
        try:
            for i in range(num_trajectories):
                print(f"\n🎲 === SIMULATION ALÉATOIRE {i+1}/{num_trajectories} ===")
                
                # Générer position aléatoire valide
                random_pos = self._generate_random_position()
                if random_pos is None:
                    print(f"❌ Impossible de générer une position valide pour la simulation {i+1}")
                    failed_positions += 1
                    failed_attempts.append(i+1)
                    # Stocker l'échec de génération de position
                    self.failed_trajectory_positions.append({
                        'position': [0, 0, 0],  # Position par défaut puisqu'aucune n'a pu être générée
                        'heading': 0,
                        'attempt_number': i+1,
                        'reason': 'Position valide non trouvée'
                    })
                    continue
                
                x, y, z, heading = random_pos
                
                # Calculer la distance au FAF en XY pour confirmation
                faf_pos = self.environment.faf_position
                distance_xy = np.sqrt((x - faf_pos[0])**2 + (y - faf_pos[1])**2)
                print(f"📍 Position générée: ({x:.1f}, {y:.1f}, {z:.1f}) km, cap: {heading:.0f}°")
                print(f"   📏 Distance au FAF (plan XY): {distance_xy:.1f} km")
                
                # Créer un avion temporaire à cette position
                from aircraft import Aircraft, AircraftType
                aircraft_type = self.aircraft_type_var.get() if hasattr(self, 'aircraft_type_var') else "commercial"
                speed = self.speed_var.get() if hasattr(self, 'speed_var') else 250.0
                
                temp_aircraft = Aircraft(
                    aircraft_type=getattr(AircraftType, aircraft_type.upper()),
                    position=np.array([x, y, z]),
                    speed=speed,
                    heading=heading,
                    max_climb_slope=self.max_climb_slope_var.get() if hasattr(self, 'max_climb_slope_var') else None,
                    max_descent_slope=self.max_descent_slope_var.get() if hasattr(self, 'max_descent_slope_var') else None
                )
                
                # Calculer la trajectoire avec courbes de Bézier
                calculator = TrajectoryCalculator(self.environment)
                
                try:
                    trajectory, trajectory_params = calculator.calculate_trajectory(
                        temp_aircraft, self.cylinders
                    )
                    
                    # Vérifier si la trajectoire a pu être calculée sans collision
                    if trajectory is None:
                        print(f"❌ Erreur simulation {i+1}: Impossible d'éviter les obstacles depuis cette position")
                        failed_positions += 1
                        failed_attempts.append(i+1)
                        # Stocker la position de l'échec avec le numéro de tentative
                        self.failed_trajectory_positions.append({
                            'position': [x, y, z],
                            'heading': heading,
                            'attempt_number': i+1,
                            'reason': 'Collision avec obstacles'
                        })
                        continue
                    
                    # Stocker la trajectoire sûre
                    self.multiple_trajectories.append(trajectory)
                    self.multiple_trajectories_params.append(trajectory_params)
                    successful_simulations += 1
                    
                    print(f"✅ Simulation {i+1} réussie - {len(trajectory)} points calculés")
                    
                except Exception as e:
                    print(f"❌ Erreur simulation {i+1}: {str(e)}")
                    failed_positions += 1
                    failed_attempts.append(i+1)
                    # Stocker la position de l'échec avec le numéro de tentative
                    self.failed_trajectory_positions.append({
                        'position': [x, y, z],
                        'heading': heading,
                        'attempt_number': i+1,
                        'reason': str(e)
                    })
                    continue
            
            # Restaurer l'avion original
            if original_aircraft_config:
                self.aircraft = Aircraft(
                    aircraft_type=getattr(AircraftType, original_aircraft_config['aircraft_type'].upper()),
                    position=original_aircraft_config['position'],
                    speed=original_aircraft_config['speed'],
                    heading=original_aircraft_config['heading']
                )
            
            # Mettre à jour l'affichage
            self._draw_environment()
            self._draw_multiple_parameters()  # Afficher les paramètres de toutes les trajectoires
            
            # Message de résultats
            if successful_simulations > 0:
                total_trajectories = len(self.multiple_trajectories)
                info_msg = f"✅ {successful_simulations}/{num_trajectories} nouvelles simulations réussies!\n"
                info_msg += f"📊 Total des trajectoires affichées: {total_trajectories}\n\n"
                if failed_positions > 0:
                    info_msg += f"⚠️ {failed_positions} tentatives échouées (numéros: {', '.join(map(str, failed_attempts))})\n\n"
                
                info_msg += "Les trajectoires sont affichées avec des couleurs différentes:\n"
                colors = ['red', 'blue', 'green', 'orange', 'purple', 'brown', 'pink', 'gray', 'olive', 'cyan']
                for i in range(successful_simulations):
                    color_name = colors[i] if i < len(colors) else f"couleur_{i+1}"
                    distance = self.multiple_trajectories_params[i].get('distance', 0)
                    flight_time = self.multiple_trajectories_params[i].get('flight_time', 0)
                    info_msg += f"• Trajectoire {i+1}: {color_name} - {distance:.1f}km, {flight_time*60:.1f}min\n"
                
                messagebox.showinfo("Simulations Terminées", info_msg)
            else:
                messagebox.showerror("Échec", "Aucune simulation n'a pu être réalisée.\nVérifiez les contraintes de l'environnement.")
        
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors des simulations multiples: {str(e)}")
    
    def _clear_multiple_trajectories(self):
        """Efface toutes les trajectoires multiples"""
        
        if hasattr(self, 'multiple_trajectories') and self.multiple_trajectories:
            count = len(self.multiple_trajectories)
            self.multiple_trajectories = []
            self.multiple_trajectories_params = []
            self.failed_trajectory_positions = []
            
            # Mettre à jour l'affichage
            self._draw_environment()
            
            # Réinitialiser les graphiques de paramètres
            self.fig_params.clear()
            self.canvas_params.draw()
            
            messagebox.showinfo("Effacement", f"{count} trajectoires multiples effacées!")
        else:
            messagebox.showinfo("Information", "Aucune trajectoire multiple à effacer.")
            
    def _reset(self):
        """Réinitialise la simulation"""
        
        self.aircraft = None
        self.trajectory = None
        self.trajectory_params = None
        
        # Réinitialiser les trajectoires multiples
        self.multiple_trajectories = []
        self.multiple_trajectories_params = []
        self.failed_trajectory_positions = []
        
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
    import sys
    if sys.platform == 'win32':
        try:
            import ctypes
            myappid = 'estaca.trajectoireavion.simulateur.v1'
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except Exception:
            pass
    root = tk.Tk()
    app = FlightSimulatorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()