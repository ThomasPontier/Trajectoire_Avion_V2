"""
Module de création d'icône multi-résolutions pour Windows

"""

import os
from PIL import Image


def create_multi_resolution_ico(png_path, ico_path):
    try:
        # Charger l'image PNG
        with Image.open(png_path) as img:
            # Convertir en RGBA si nécessaire
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            
            # Tailles d'icône standard pour Windows
            sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
            
            # Créer les images redimensionnées
            icon_images = []
            for size in sizes:
                # Redimensionner avec un bon algorithme de rééchantillonnage
                resized = img.resize(size, Image.Resampling.LANCZOS)
                icon_images.append(resized)
            
            # Sauvegarder le fichier ICO multi-résolutions
            # Utiliser une approche plus compatible
            icon_images[0].save(
                ico_path,
                format='ICO',
                sizes=[size for size in sizes],
                append_images=icon_images[1:],
                optimize=False  # Désactiver l'optimisation qui peut causer des problèmes
            )
            
            # Vérifier que l'icône créée a une taille raisonnable
            file_size = os.path.getsize(ico_path)
            if file_size < 5000:  # Moins de 5 Ko = problème probable
                # Fallback : créer une icône simple avec la plus grande taille
                print(f"Icone multi-resolutions trop petite ({file_size} octets), creation d'une icone simple...")
                largest_img = img.resize((256, 256), Image.Resampling.LANCZOS)
                largest_img.save(ico_path, format='ICO')
                file_size = os.path.getsize(ico_path)
            
            print(f"Icone multi-resolutions creee : {ico_path} ({file_size:,} octets)")
            return True
            
    except ImportError as e:
        print(f"Pillow n'est pas installe : {e}")
        print("Installation de Pillow...")
        import subprocess
        import sys
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow"])
            print("Pillow installe, relancez le build")
        except Exception:
            print("Impossible d'installer Pillow automatiquement")
        return False
        
    except Exception as e:
        print(f"Erreur lors de la creation de l'icone : {e}")
        return False


def create_simple_ico(png_path, ico_path):
    try:
        with Image.open(png_path) as img:
            # Convertir en RGBA
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            
            # Redimensionner à 256x256 (taille standard)
            img = img.resize((256, 256), Image.Resampling.LANCZOS)
            
            # Sauvegarder
            img.save(ico_path, format='ICO')
            
            print(f"Icone simple creee : {ico_path}")
            return True
            
    except Exception as e:
        print(f"Erreur lors de la creation de l'icone simple : {e}")
        return False


if __name__ == "__main__":
    # Test du module
    if os.path.exists("logo.png"):
        print("Test de creation d'icone...")
        if create_multi_resolution_ico("logo.png", "test_logo.ico"):
            size = os.path.getsize("test_logo.ico")
            print(f"Test reussi : {size:,} octets")
        else:
            print("Test echoue")
    else:
        print("Fichier logo.png introuvable pour le test")