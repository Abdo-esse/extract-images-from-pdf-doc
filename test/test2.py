import os
import csv
import fitz  # PyMuPDF
import pdfplumber
import re

# --- Configurations ---
PDF_FILE = "./output/RCA Liste Catégorie.pdf"  # chemin PDF
IMG_DIR = "photos_joueurs"
CSV_FILE = "joueurs_clean.csv"

os.makedirs(IMG_DIR, exist_ok=True)

# --- Extraction du tableau PDF ---
table_data = []
with pdfplumber.open(PDF_FILE) as pdf:
    for page in pdf.pages:
        tables = page.extract_tables()
        for table in tables:
            for row in table:
                # Garder exactement le nombre de colonnes et les cellules vides
                if row and any(cell is not None and cell != '' for cell in row):
                    table_data.append([cell if cell is not None else '' for cell in row])

# --- Détecter et supprimer les répétitions de header ---
header = ['PHOTO','NOM','Prénom','Date naissance','Lieu de naissance','CNI',
          'Poste 1','Poste 2','Interne/Externe','Statut','Mode recrutement','Scolarité']
clean_table = []
for row in table_data:
    if [str(c).strip() for c in row[:len(header)]] == header:
        continue
    while len(row) < len(header):
        row.append('')
    clean_table.append(row)

# --- Extraction des images en haute résolution ---
doc = fitz.open(PDF_FILE)
image_index = 1
image_paths = []

for page_num, page in enumerate(doc, start=1):
    images = page.get_images(full=True)
    for img_index, img in enumerate(images, start=1):
        xref = img[0]
        base_image = doc.extract_image(xref)
        image_bytes = base_image["image"]
        image_ext = base_image["ext"]
        
        # Nom temporaire avant renommage
        image_name = f"{IMG_DIR}/temp_{image_index}.{image_ext}"
        with open(image_name, "wb") as f:
            f.write(image_bytes)
        image_paths.append(image_name)
        image_index += 1

# --- Association photo → joueur et renommage ---
final_image_paths = []
for i, row in enumerate(clean_table):
    prenom = row[2].strip() if len(row) > 2 else "unknown"
    nom = row[1].strip() if len(row) > 1 else "unknown"
    # Nettoyage du nom pour fichier
    prenom_clean = re.sub(r'[^\w]', '_', prenom)
    nom_clean = re.sub(r'[^\w]', '_', nom)
    if i < len(image_paths):
        ext = os.path.splitext(image_paths[i])[1]
        new_image_name = f"{IMG_DIR}/{prenom_clean}_{nom_clean}_{i+1}{ext}"
        os.rename(image_paths[i], new_image_name)
        row.append(new_image_name)
        final_image_paths.append(new_image_name)
    else:
        unknown_name = f"{IMG_DIR}/unknown_{i+1}.png"
        row.append(unknown_name)
        final_image_paths.append(unknown_name)

# --- Écriture CSV final ---
with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(header + ['Photo'])
    for row in clean_table:
        writer.writerow([cell if cell is not None else '' for cell in row])

print(f"✅ Extraction terminée ! CSV généré : {CSV_FILE}")
print(f"✅ {len(final_image_paths)} photos traitées dans {IMG_DIR}")
