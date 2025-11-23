import fitz  # PyMuPDF
from PIL import Image
import io
import os
import re

def extraire_joueurs_pdf(chemin_pdf, dossier_sortie="joueurs_extraits"):
    """
    Extrait les photos et noms des joueurs d'un PDF
    
    Args:
        chemin_pdf: Chemin vers le fichier PDF
        dossier_sortie: Dossier où sauvegarder les images
    """
    
    # Créer le dossier de sortie s'il n'existe pas
    if not os.path.exists(dossier_sortie):
        os.makedirs(dossier_sortie)
    
    # Ouvrir le PDF
    doc = fitz.open(chemin_pdf)
    
    joueurs_extraits = []
    compteur_image = 0
    
    print(f"Traitement de {len(doc)} pages...")
    
    for num_page in range(len(doc)):
        page = doc[num_page]
        
        # Extraire le texte de la page
        texte = page.get_text()
        
        # Chercher le nom du joueur (généralement en majuscules après "JOUEUR")
        lignes = texte.split('\n')
        nom_joueur = None
        
        for i, ligne in enumerate(lignes):
            # Le nom est généralement après l'ID et avant la date
            if ligne.strip() and len(ligne.strip()) > 5:
                # Pattern pour détecter un nom (lettres et espaces)
                if re.match(r'^[A-Z\s]+$', ligne.strip()) and ligne.strip() not in ['JOUEUR', 'AMATEUR', 'PROFESSIONAL']:
                    nom_joueur = ligne.strip()
                    break
        
        # Extraire les images de la page
        images = page.get_images()
        
        for img_index, img in enumerate(images):
            try:
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]
                
                # Convertir en PIL Image
                image = Image.open(io.BytesIO(image_bytes))
                
                # Filtrer les petites images (logos, etc.)
                largeur, hauteur = image.size
                if largeur < 50 or hauteur < 50:
                    continue
                
                # Créer un nom de fichier
                if nom_joueur:
                    nom_fichier = f"{nom_joueur.replace(' ', '_')}_{compteur_image}.{image_ext}"
                else:
                    nom_fichier = f"joueur_{num_page}_{img_index}.{image_ext}"
                
                chemin_complet = os.path.join(dossier_sortie, nom_fichier)
                
                # Sauvegarder l'image
                image.save(chemin_complet)
                
                joueurs_extraits.append({
                    'nom': nom_joueur if nom_joueur else f"Joueur_{num_page}_{img_index}",
                    'fichier': nom_fichier,
                    'page': num_page + 1
                })
                
                compteur_image += 1
                print(f"✓ Extrait: {nom_joueur if nom_joueur else 'Inconnu'} -> {nom_fichier}")
                
            except Exception as e:
                print(f"✗ Erreur lors de l'extraction de l'image {img_index} page {num_page + 1}: {e}")
    
    doc.close()
    
    # Résumé
    print(f"\n{'='*50}")
    print(f"RÉSUMÉ DE L'EXTRACTION")
    print(f"{'='*50}")
    print(f"Total d'images extraites: {len(joueurs_extraits)}")
    print(f"Dossier de sortie: {dossier_sortie}")
    print(f"\nListe des joueurs extraits:")
    for joueur in joueurs_extraits:
        print(f"  - {joueur['nom']} (Page {joueur['page']})")
    
    return joueurs_extraits


# Utilisation du script
if __name__ == "__main__":
    # Remplacez par le chemin de votre PDF
    chemin_pdf = "./LICENCE U21 2 25 26.pdf"
    
    # Extraire les joueurs
    joueurs = extraire_joueurs_pdf(chemin_pdf)
    
    print(f"\n✓ Extraction terminée! {len(joueurs)} images sauvegardées.")