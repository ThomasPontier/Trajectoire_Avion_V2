#!/usr/bin/env python3
"""
Script pour vérifier la structure interne d'un fichier ICO
en lisant directement les en-têtes binaires
"""

import struct
import os

def verify_ico_structure(ico_path):
    """Lit et affiche la structure complète d'un fichier ICO"""
    
    if not os.path.exists(ico_path):
        print(f"❌ Fichier {ico_path} introuvable")
        return False
    
    print(f"📖 Lecture de {ico_path}...")
    print(f"   Taille: {os.path.getsize(ico_path):,} octets")
    print()
    
    with open(ico_path, 'rb') as f:
        # Lire l'en-tête ICO (6 octets)
        header = f.read(6)
        reserved, image_type, count = struct.unpack('<HHH', header)
        
        print("📋 EN-TÊTE ICO:")
        print(f"   Reserved: {reserved} (doit être 0)")
        print(f"   Type: {image_type} (1 = ICO, 2 = CUR)")
        print(f"   Nombre d'images: {count}")
        print()
        
        if image_type != 1:
            print("❌ Type invalide, ce n'est pas un fichier ICO standard")
            return False
        
        if count == 0:
            print("❌ Aucune image dans le fichier ICO")
            return False
        
        # Lire les directory entries (16 octets chacune)
        print(f"🖼️  RÉSOLUTIONS CONTENUES ({count} image(s)):")
        for i in range(count):
            entry = f.read(16)
            width, height, colors, reserved, planes, bpp, size, offset = struct.unpack('<BBBBHHII', entry)
            
            # Windows utilise 0 pour représenter 256
            actual_width = width if width != 0 else 256
            actual_height = height if height != 0 else 256
            
            print(f"   [{i+1}] {actual_width}x{actual_height} pixels")
            print(f"       - Bits par pixel: {bpp}")
            print(f"       - Taille des données: {size:,} octets")
            print(f"       - Offset: {offset:,}")
            
        print()
        print("✅ Fichier ICO valide avec toutes les résolutions!")
        return True

if __name__ == "__main__":
    print("="*70)
    print(" VÉRIFICATION DE LA STRUCTURE DU FICHIER ICO")
    print("="*70)
    print()
    
    if verify_ico_structure("logo.ico"):
        print()
        print("="*70)
        print("✨ Le fichier ICO est correctement formaté!")
        print("   Vous pouvez maintenant rebuilder l'exe avec: python build_exe.py")
        print("="*70)
