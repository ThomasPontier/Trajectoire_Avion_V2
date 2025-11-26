"""Script de construction de l'exécutable du Simulateur de Trajectoire d'Avion
Ce script automatise la création d'un fichier .exe standalone avec PyInstaller
"""

import os
import sys
import shutil
import subprocess


def clean_build_dirs():
    """Nettoie les répertoires de build précédents"""
    dirs_to_clean = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            print(f" Nettoyage de {dir_name}/")
            try:
                shutil.rmtree(dir_name)
            except PermissionError:
                print(f"  Impossible de supprimer {dir_name}/ (fichiers en cours d'utilisation)")
                print(f"   Le build continuera avec les fichiers existants")


def check_dependencies():
    """Vérifie que PyInstaller est installé"""
    try:
        import PyInstaller
        print(f" PyInstaller {PyInstaller.__version__} détecté")
        return True
    except ImportError:
        print(" PyInstaller n'est pas installé")
        print(" Installation de PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        return True


def build_executable():
    """Construit l'exécutable avec PyInstaller"""
    print("\n" + "="*70)
    print(" CONSTRUCTION DE L'EXÉCUTABLE")
    print("="*70 + "\n")

    # Se placer dans le répertoire du script pour que les chemins relatifs fonctionnent
    script_dir = os.path.dirname(os.path.abspath(__file__))
    try:
        os.chdir(script_dir)
    except Exception as e:
        print(f" Impossible de changer de répertoire vers {script_dir}: {e}")
        return False
    else:
        print(f" Répertoire de travail: {os.getcwd()}")
    
    # Vérifier les dépendances
    if not check_dependencies():
        print(" Impossible de continuer sans PyInstaller")
        return False
    
    # Nettoyer les anciens builds
    clean_build_dirs()
    
    logo_path = "logo.png"
    if not os.path.exists(logo_path):
        print(f"  Attention : {logo_path} introuvable")
        print("   L'exécutable sera créé sans icône")
        icon_option = []
    else:
        print(f" Logo trouvé : {logo_path}")
        try:
            print(" Création de l'icône multi-résolutions...")
            
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            from create_icon import create_multi_resolution_ico
            
            icon_path = "logo.ico"
            if create_multi_resolution_ico(logo_path, icon_path):
                ico_size = os.path.getsize(icon_path)
                if ico_size > 10000:
                    icon_option = ['--icon', icon_path]
                    print(f" Icône créée : {icon_path} ({ico_size:,} octets)")
                else:
                    print(f"  Icône créée mais semble incomplète ({ico_size} octets)")
                    print("   L'exécutable sera créé sans icône")
                    icon_option = []
            else:
                raise Exception("Échec de la création de l'icône")
                
        except Exception as e:
            print(f"  Impossible de créer l'icône : {e}")
            import traceback
            traceback.print_exc()
            print("   L'exécutable sera créé sans icône")
            icon_option = []
    
    # Vérifier que config.json existe
    if not os.path.exists("config.json"):
        print("  config.json introuvable, création par défaut...")
        default_config = """{
    "environment": {
        "size_x": 100.0,
        "size_y": 100.0,
        "size_z": 10.0,
        "airport": {
            "x": 5.0,
            "y": 25.0,
            "z": 0.0
        },
        "faf": {
            "x": 20.0,
            "y": 25.0,
            "z": 1.0
        }
    },
    "cylinders": [],
    "aircraft": {
        "type": "commercial",
        "position": {
            "x": 70.0,
            "y": 70.0,
            "z": 3.0
        },
        "speed": 250.0,
        "heading": 180.0
    }
}"""
        with open("config.json", "w", encoding="utf-8") as f:
            f.write(default_config)
        print(" config.json créé")
    
    data_files = ['--add-data=config.json;.']
    if os.path.exists('logo.ico'):
        data_files.append('--add-data=logo.ico;.')
        print("" logo.ico inclus")
    if os.path.exists('logo.png'):
        data_files.append('--add-data=logo.png;.')
        print("logo.png inclus")
    
    target_exe = os.path.join('dist', 'SimulateurTrajectoireAvion.exe')
    if os.path.exists(target_exe):
        try:
            os.remove(target_exe)
            print(f"  Ancien exécutable supprimé: {target_exe}")
        except PermissionError:
            print(f" Impossible de supprimer {target_exe} (fichier en cours d'utilisation).\n   Fermez l'application SimulateurTrajectoireAvion.exe si elle est en cours et relancez le build.")
            return False

    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--name=SimulateurTrajectoireAvion',
        '--onefile',
        '--windowed',
    ] + data_files + [
        '--hidden-import=numpy',
        '--hidden-import=matplotlib',
        '--hidden-import=matplotlib.backends.backend_tkagg',
        '--hidden-import=mpl_toolkits.mplot3d',
        '--hidden-import=tkinter',
        '--hidden-import=PIL',
        '--hidden-import=PIL._tkinter_finder',
        '--collect-all=matplotlib',
        '--collect-all=numpy',
        '--exclude-module=PySide6',
        '--exclude-module=PySide2',
        '--exclude-module=PyQt5',
        '--optimize=2',
        '--noupx',
    ] + icon_option + ['main.py']

    entry_point = os.path.join(os.getcwd(), 'main.py')
    if not os.path.isfile(entry_point):
        print(f"Fichier d'entree introuvable: {entry_point}")
        print("   Assurez-vous de lancer ce script depuis n'importe où: il se repositionne automatiquement.")
        return False
    
    print("\nCommande PyInstaller :")
    print(" ".join(cmd))
    print("\n Construction en cours... (cela peut prendre plusieurs minutes)\n")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(result.stdout)
        print("\n" + "="*70)
        print(" BUILD RÉUSSI !")
        print("="*70)
        print(f"\n Exécutable créé : dist\\SimulateurTrajectoireAvion.exe")
        print(f"📁 Taille : {os.path.getsize('dist/SimulateurTrajectoireAvion.exe') / (1024*1024):.1f} MB")
        print("\n📖 Instructions :")
        print("   1. Copiez 'SimulateurTrajectoireAvion.exe' où vous voulez")
        print("   2. Double-cliquez pour lancer l'application")
        print("   3. Le fichier config.json sera créé automatiquement au premier lancement")
        print("\n💡 Note : Aucune installation Python n'est nécessaire sur l'ordinateur cible")
        return True
    except subprocess.CalledProcessError as e:
        print("\n" + "="*70)
        print("ERREUR LORS DU BUILD")
        print("="*70)
        print(e.stderr)
        return False


if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════════════╗
    ║     SIMULATEUR DE TRAJECTOIRE D'AVION - BUILD EXÉCUTABLE        ║
    ║                      Projet P21 - ESTACA                         ║
    ╚══════════════════════════════════════════════════════════════════╝
    """)
    
    success = build_executable()
    
    if success:
        print("\n✨ Build terminé avec succès !")
        print("🚀 Vous pouvez maintenant distribuer l'exécutable\n")
        sys.exit(0)
    else:
        print("\nLe build a echoue. Verifiez les messages d'erreur ci-dessus.\n")
        sys.exit(1)
