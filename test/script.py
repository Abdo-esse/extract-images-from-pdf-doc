import os
import csv
import fitz  # PyMuPDF
import pdfplumber
import re

PDF_FILE = "./output/RCA Liste Catégorie.pdf"
IMG_DIR = "photos_joueurs"
CSV_FILE = "joueurs_clean.csv"

os.makedirs(IMG_DIR, exist_ok=True)

# --- En-têtes du tableau ---
header = [
    'PHOTO','NOM','Prénom','Date naissance','Lieu de naissance','CNI',
    'Poste 1','Poste 2','Interne/Externe','Statut','Mode recrutement','Scolarité'
]

csv_rows = []

# --- Ouvrir PDF en double : pdfplumber (tables) + fitz (images) ---
plumber_pdf = pdfplumber.open(PDF_FILE)
fitz_pdf = fitz.open(PDF_FILE)

for page_index, (page_plumber, page_fitz) in enumerate(zip(plumber_pdf.pages, fitz_pdf), start=1):

    print(f"📄 Traitement page {page_index}")

    # EXTRACTION TABLEAU
    tables = page_plumber.extract_tables()
    page_rows = []

    for t in tables:
        for row in t:
            if not row or all(c in [None,""] for c in row):
                continue

            # Ajuster la taille au header
            row = [c if c else "" for c in row]
            while len(row) < len(header):
                row.append("")

            # retirer headers répétés
            if [str(c).strip() for c in row[:len(header)]] == header:
                continue

            page_rows.append(row)

    # EXTRACTION IMAGES
    images = page_fitz.get_images(full=True)
    extracted_images = []

    for img_id, img in enumerate(images, start=1):
        xref = img[0]
        base = fitz_pdf.extract_image(xref)
        ext = base["ext"]
        data = base["image"]

        extracted_images.append((ext, data))

    #
    # --- ASSOCIATION IMAGE → LIGNE ---
    #
    row_index = 0

    for ext, data in extracted_images:

        if row_index >= len(page_rows):
            break  # trop d'images sur la page

        row = page_rows[row_index]

        prenom = re.sub(r"[^\w]", "_", row[2].strip() or "unknown")
        nom = re.sub(r"[^\w]", "_", row[1].strip() or "unknown")

        img_filename = f"{prenom}_{nom}_page{page_index}.png"
        img_path = os.path.join(IMG_DIR, img_filename)

        # écrit image
        with open(img_path, "wb") as f:
            f.write(data)

        # ajoute au CSV
        row_with_photo = row + [img_path]
        csv_rows.append(row_with_photo)

        row_index += 1

    #
    # --- LIGNES SANS IMAGE → CSV quand même ---
    #
    for i in range(row_index, len(page_rows)):
        row = page_rows[i]
        row_without_photo = row + [""]
        csv_rows.append(row_without_photo)


# --- ÉCRITURE CSV FINAL ---
with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(header + ["Photo"])
    writer.writerows(csv_rows)

print("✅ Extraction terminée !")
print(f"📄 CSV généré : {CSV_FILE}")
print(f"🖼️ Images enregistrées : {IMG_DIR}")
