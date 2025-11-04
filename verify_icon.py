"""
Script pour vérifier si l'icône est correctement embarquée dans l'exécutable
"""
import os
import sys

try:
    # Méthode 1: Utiliser PIL pour vérifier le contenu du .ico
    print("="*70)
    print("VÉRIFICATION DU FICHIER logo.ico")
    print("="*70)
    
    from PIL import Image
    
    if os.path.exists('logo.ico'):
        img = Image.open('logo.ico')
        print(f"✅ logo.ico trouvé")
        print(f"   Format: {img.format}")
        print(f"   Mode: {img.mode}")
        print(f"   Taille: {img.size}")
        
        # Essayer de lire toutes les résolutions dans l'ICO
        try:
            img.seek(0)
            sizes = []
            for i in range(100):  # Essayer jusqu'à 100 images
                try:
                    img.seek(i)
                    sizes.append(img.size)
                except EOFError:
                    break
            print(f"   Résolutions disponibles: {sizes}")
        except:
            pass
    else:
        print("❌ logo.ico introuvable")
    
    print("\n" + "="*70)
    print("VÉRIFICATION DE L'EXÉCUTABLE")
    print("="*70)
    
    exe_path = "dist\\SimulateurTrajectoireAvion.exe"
    if os.path.exists(exe_path):
        size_mb = os.path.getsize(exe_path) / (1024*1024)
        print(f"✅ Exécutable trouvé: {exe_path}")
        print(f"   Taille: {size_mb:.1f} MB")
        
        # Sur Windows, essayer d'extraire les ressources de l'exe
        if sys.platform == 'win32':
            try:
                import win32api
                import win32con
                
                # Essayer de lire les icônes de l'exécutable
                print("\n   Tentative de lecture des ressources de l'exe...")
                handle = win32api.LoadLibraryEx(exe_path, 0, win32con.LOAD_LIBRARY_AS_DATAFILE)
                if handle:
                    print("   ✅ Ressources accessibles dans l'exécutable")
                    win32api.FreeLibrary(handle)
                else:
                    print("   ⚠️  Impossible d'accéder aux ressources")
            except ImportError:
                print("   ⚠️  Module win32api non disponible (pip install pywin32 pour vérifier)")
            except Exception as e:
                print(f"   ⚠️  Erreur lors de la vérification des ressources: {e}")
    else:
        print(f"❌ Exécutable introuvable: {exe_path}")
    
    print("\n" + "="*70)
    print("RECOMMANDATIONS")
    print("="*70)
    print("""
Si l'icône ne s'affiche toujours pas dans la barre des tâches:

1. Vérifiez que logo.ico a plusieurs résolutions (16, 32, 48, 64, 128, 256)
2. L'icône doit être au format ICO Windows standard (pas juste un PNG renommé)
3. PyInstaller doit avoir correctement embarqué l'icône dans l'exe
4. Windows 10 peut cacher les icônes - essayez de :
   - Supprimer l'ancien exe
   - Nettoyer %temp%
   - Redémarrer l'ordinateur (solution radicale mais efficace)
   
5. Vérifiez visuellement dans l'explorateur si l'exe a une icône
   (clic droit > Propriétés sur l'exe)
    """)

except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc()
