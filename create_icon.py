#!/usr/bin/env python3
"""
Script pour créer un fichier ICO multi-résolutions correctement formaté
pour Windows à partir de logo.png
"""

from PIL import Image
import struct

def create_multi_resolution_ico(png_path, ico_path):
    """
    Crée un fichier ICO avec toutes les résolutions nécessaires
    pour Windows (16x16, 32x32, 48x48, 64x64, 128x128, 256x256)
    """
    print(f"📖 Lecture de {png_path}...")
    img = Image.open(png_path).convert('RGBA')
    
    # Tailles standards pour Windows
    sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    
    # Redimensionner et sauvegarder chaque taille
    images = []
    for size in sizes:
        print(f"   ✓ Création de la résolution {size[0]}x{size[1]}...")
        resized = img.resize(size, Image.Resampling.LANCZOS)
        images.append(resized)
    
    # Sauvegarder en ICO avec toutes les résolutions
    print(f"💾 Sauvegarde dans {ico_path}...")
    
    # Méthode directe : Sauvegarder chaque taille séparément puis les combiner
    try:
        print("   Essai méthode alternative...")
        import io
        
        # Créer des buffers pour chaque image
        image_data = []
        for i, (size, im) in enumerate(zip(sizes, images)):
            buffer = io.BytesIO()
            im.save(buffer, format='PNG')
            png_data = buffer.getvalue()
            image_data.append((size, png_data))
            print(f"   ✓ Image {size[0]}x{size[1]}: {len(png_data)} octets")
        
        # Écrire le fichier ICO manuellement
        with open(ico_path, 'wb') as f:
            # En-tête ICO
            f.write(struct.pack('<HHH', 0, 1, len(image_data)))  # Reserved, Type, Count
            
            # Directory entries
            offset = 6 + (16 * len(image_data))
            for size, data in image_data:
                width = size[0] if size[0] < 256 else 0
                height = size[1] if size[1] < 256 else 0
                f.write(struct.pack('<BBBBHHII',
                    width,          # Width
                    height,         # Height
                    0,              # Color count
                    0,              # Reserved
                    1,              # Color planes
                    32,             # Bits per pixel
                    len(data),      # Size of image data
                    offset          # Offset to image data
                ))
                offset += len(data)
            
            # Image data
            for size, data in image_data:
                f.write(data)
        
        print(f"✅ Fichier ICO créé avec méthode manuelle ({len(image_data)} résolutions)")
        return True
        
    except Exception as e:
        print(f"❌ Toutes les méthodes ont échoué: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import os
    import sys
    
    # Vérifier que logo.png existe
    if not os.path.exists("logo.png"):
        print("❌ Erreur: logo.png introuvable dans le répertoire actuel")
        sys.exit(1)
    
    print("="*70)
    print(" CRÉATION D'ICÔNE MULTI-RÉSOLUTIONS POUR WINDOWS")
    print("="*70)
    print()
    
    success = create_multi_resolution_ico("logo.png", "logo.ico")
    
    if success:
        # Vérifier la taille du fichier créé
        size = os.path.getsize("logo.ico")
        print()
        print(f"📊 Taille du fichier: {size:,} octets")
        
        # Un fichier ICO multi-résolutions devrait faire plusieurs dizaines de Ko
        if size < 5000:
            print("⚠️  ATTENTION: Le fichier semble trop petit pour contenir")
            print("   toutes les résolutions. Il devrait faire au moins 10-20 Ko")
        else:
            print("✅ La taille semble correcte pour un fichier multi-résolutions")
        
        print()
        print("="*70)
        print("✨ Terminé! Vous pouvez maintenant rebuilder avec build_exe.py")
        print("="*70)
    else:
        sys.exit(1)
