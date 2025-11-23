import fitz  # PyMuPDF
from PIL import Image
import io
import os
import re

def nettoyer_nom(nom):
    """ Nettoie un nom pour créer un nom de fichier propre """
    if not nom:
        return "Inconnu"
    nom = nom.strip()
    nom = nom.replace(" ", "_")
    nom = re.sub(r'[^A-Za-z0-9_]', '', nom)
    return nom


def extraire_nom_joueur(texte):
    """
    Trouve le nom du joueur dans le texte de la page.
    Format dans ton PDF = lignes en MAJUSCULE ou Nom Composé
    """
    lignes = texte.split("\n")

    for ligne in lignes:
        l = ligne.strip()

        # détecter ID joueur (ex: 020269M08)
        if re.match(r'^\d{6}M\d{2}$', l):
            continue

        # Nom en majuscule (PDF U18 OCP)
        if re.match(r'^[A-Z][A-Za-z\s\-]+$', l) and len(l.split()) >= 2:
            return l.strip()

    return None


def extraire_joueurs_pdf(chemin_pdf, dossier_sortie="joueurs_extraits"):
    """
    Extrait les images du PDF, une seule photo par joueur,
    nommée avec le nom du joueur uniquement.
    """

    if not os.path.exists(dossier_sortie):
        os.makedirs(dossier_sortie)

    doc = fitz.open(chemin_pdf)
    joueurs = []

    print(f"📄 Traitement de {len(doc)} pages...\n")

    for i in range(len(doc)):
        page = doc[i]
        texte = page.get_text()
        nom = extraire_nom_joueur(texte)
        nom_fichier = nettoyer_nom(nom)

        images = page.get_images()

        photo_trouvee = False

        for img in images:
            try:
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                ext = base_image["ext"]

                image = Image.open(io.BytesIO(image_bytes))
                w, h = image.size

                # éviter logos / QR / petites images
                if w < 100 or h < 100:
                    continue

                # nom final
                fichier_final = f"{nom_fichier}.{ext}"
                chemin_final = os.path.join(dossier_sortie, fichier_final)

                image.save(chemin_final)

                print(f"✓ Page {i+1}: {nom} → {fichier_final}")

                joueurs.append({
                    "nom": nom,
                    "page": i+1,
                    "fichier": fichier_final
                })

                photo_trouvee = True
                break

            except Exception as e:
                print(f"⚠ Erreur extraction page {i+1}: {e}")

        if not photo_trouvee:
            print(f"⚠ Page {i+1}: Aucune photo trouvée pour {nom}")

    doc.close()

    print("\n==============================")
    print("📊 RÉSUMÉ")
    print("==============================")
    print(f"Photos extraites : {len(joueurs)}")
    print(f"Dossier : {os.path.abspath(dossier_sortie)}")

    return joueurs


# Utilisation
if __name__ == "__main__":
    chemin_pdf = "./"
    extraire_joueurs_pdf(chemin_pdf)
