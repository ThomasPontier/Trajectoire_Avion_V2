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
            print(f"🧹 Nettoyage de {dir_name}/")
            try:
                shutil.rmtree(dir_name)
            except PermissionError:
                print(f"⚠️  Impossible de supprimer {dir_name}/ (fichiers en cours d'utilisation)")
                print(f"   Le build continuera avec les fichiers existants")
    
    # Supprimer les fichiers .spec anciens si besoin de regénérer
    # spec_file = 'SimulateurTrajectoireAvion.spec'
    # if os.path.exists(spec_file):
    #     os.remove(spec_file)


def check_dependencies():
    """Vérifie que PyInstaller est installé"""
    try:
        import PyInstaller
        print(f"✅ PyInstaller {PyInstaller.__version__} détecté")
        return True
    except ImportError:
        print("❌ PyInstaller n'est pas installé")
        print("📦 Installation de PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        return True


def build_executable():
    """Construit l'exécutable avec PyInstaller"""
    print("\n" + "="*70)
    print("🚀 CONSTRUCTION DE L'EXÉCUTABLE")
    print("="*70 + "\n")
    
    # Vérifier les dépendances
    if not check_dependencies():
        print("❌ Impossible de continuer sans PyInstaller")
        return False
    
    # Nettoyer les anciens builds
    clean_build_dirs()
    
    # Vérifier que le logo existe
    logo_path = "logo.png"
    if not os.path.exists(logo_path):
        print(f"⚠️  Attention : {logo_path} introuvable")
        print("   L'exécutable sera créé sans icône")
        icon_option = []
    else:
        print(f"✅ Logo trouvé : {logo_path}")
        # Convertir le logo en .ico si nécessaire (pour Windows)
        try:
            # Utiliser create_icon.py pour créer un vrai ICO multi-résolutions
            print("🖼️  Création de l'icône multi-résolutions (16, 32, 48, 64, 128, 256)...")
            
            # Importer la fonction depuis create_icon.py
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            from create_icon import create_multi_resolution_ico
            
            icon_path = "logo.ico"
            if create_multi_resolution_ico(logo_path, icon_path):
                # Vérifier que le fichier créé a une taille raisonnable
                ico_size = os.path.getsize(icon_path)
                if ico_size > 10000:  # Au moins 10 Ko pour un vrai multi-résolutions
                    icon_option = ['--icon', icon_path]
                    print(f"✅ Icône multi-tailles créée : {icon_path} ({ico_size:,} octets, 6 résolutions)")
                else:
                    print(f"⚠️  Icône créée mais semble incomplète ({ico_size} octets)")
                    print("   L'exécutable sera créé sans icône")
                    icon_option = []
            else:
                raise Exception("Échec de la création de l'icône")
                
        except Exception as e:
            print(f"⚠️  Impossible de créer l'icône : {e}")
            import traceback
            traceback.print_exc()
            print("   L'exécutable sera créé sans icône")
            icon_option = []
    
    # Vérifier que config.json existe
    if not os.path.exists("config.json"):
        print("⚠️  config.json introuvable, création d'un fichier par défaut...")
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
        print("✅ config.json créé")
    
    # Ajouter les fichiers logo aux données
    data_files = ['--add-data=config.json;.']
    if os.path.exists('logo.ico'):
        data_files.append('--add-data=logo.ico;.')
        print("✅ logo.ico sera inclus dans l'exécutable")
    if os.path.exists('logo.png'):
        data_files.append('--add-data=logo.png;.')
        print("✅ logo.png sera inclus dans l'exécutable")
    
    # Commande PyInstaller
    # S'assurer que l'exécutable précédent n'est pas verrouillé
    target_exe = os.path.join('dist', 'SimulateurTrajectoireAvion.exe')
    if os.path.exists(target_exe):
        try:
            os.remove(target_exe)
            print(f"🗑️  Ancien exécutable supprimé: {target_exe}")
        except PermissionError:
            print(f"❌ Impossible de supprimer {target_exe} (fichier en cours d'utilisation).\n   Fermez l'application SimulateurTrajectoireAvion.exe si elle est en cours et relancez le build.")
            return False

    cmd = [
        'pyinstaller',
        '--name=SimulateurTrajectoireAvion',
        '--onefile',                    # Un seul fichier exécutable
        '--windowed',                   # Pas de console (interface graphique)
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
        '--optimize=2',                 # Optimisation Python
        '--noupx',                      # Désactiver UPX (plus compatible)
    ] + icon_option + ['main.py']
    
    print("\n📋 Commande PyInstaller :")
    print(" ".join(cmd))
    print("\n⏳ Construction en cours... (cela peut prendre plusieurs minutes)\n")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(result.stdout)
        print("\n" + "="*70)
        print("✅ BUILD RÉUSSI !")
        print("="*70)
        print(f"\n📦 Exécutable créé : dist\\SimulateurTrajectoireAvion.exe")
        print(f"📁 Taille : {os.path.getsize('dist/SimulateurTrajectoireAvion.exe') / (1024*1024):.1f} MB")
        print("\n📖 Instructions :")
        print("   1. Copiez 'SimulateurTrajectoireAvion.exe' où vous voulez")
        print("   2. Double-cliquez pour lancer l'application")
        print("   3. Le fichier config.json sera créé automatiquement au premier lancement")
        print("\n💡 Note : Aucune installation Python n'est nécessaire sur l'ordinateur cible")
        return True
    except subprocess.CalledProcessError as e:
        print("\n" + "="*70)
        print("❌ ERREUR LORS DU BUILD")
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
        print("\n❌ Le build a échoué. Vérifiez les messages d'erreur ci-dessus.\n")
        sys.exit(1)
