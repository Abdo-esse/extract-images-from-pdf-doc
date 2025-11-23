import os
import csv
import fitz  # PyMuPDF
import pdfplumber
import re

# --- Configurations ---
PDF_FILE = "./RCA Liste Catégorie.pdf"
IMG_DIR = "photos_joueurs"
CSV_FILE = "joueurs_clean.csv"

os.makedirs(IMG_DIR, exist_ok=True)

header = [
    'PHOTO','NOM','Prénom','Date naissance','Lieu de naissance','CNI',
    'Poste 1','Poste 2','Interne/Externe','Statut','Mode recrutement','Scolarité'
]

def safe_name(s):
    return re.sub(r"[^\w]", "_", s.strip() if s else "unknown")

with open(CSV_FILE, "w", newline="", encoding="utf-8") as f_csv:
    writer = csv.writer(f_csv)
    writer.writerow(header + ["Photo"])

    with pdfplumber.open(PDF_FILE) as pdf_plumber, fitz.open(PDF_FILE) as pdf_fitz:

        image_index_global = 1

        for page_index, (page_p, page_f) in enumerate(zip(pdf_plumber.pages, pdf_fitz), start=1):
            print(f"📄 Traitement page {page_index}...")

            # --- Extraire table
            tables = page_p.extract_tables()
            if not tables:
                continue
            table = tables[0]

            # --- Extraire positions exactes des lignes via pdfplumber ---
            words = page_p.extract_words(extra_attrs=["top","bottom"])
            lines_bbox = []
            current_top = None
            current_line = []
            for w in words:
                if current_top is None:
                    current_top = w["top"]
                if abs(w["top"] - current_top) > 3:
                    # nouvelle ligne
                    if current_line:
                        y_top = min(wd["top"] for wd in current_line)
                        y_bottom = max(wd["bottom"] for wd in current_line)
                        lines_bbox.append((current_line, y_top, y_bottom))
                    current_line = []
                    current_top = w["top"]
                current_line.append(w)
            if current_line:
                y_top = min(wd["top"] for wd in current_line)
                y_bottom = max(wd["bottom"] for wd in current_line)
                lines_bbox.append((current_line, y_top, y_bottom))

            # --- Extraire images avec positions ---
            images_on_page = []
            for img in page_f.get_images(full=True):
                try:
                    xref = img[0]
                    base = pdf_fitz.extract_image(xref)
                    rects = page_f.get_image_rects(xref)
                    if not rects:
                        continue
                    rect = rects[0]
                    y_center = (rect.y0 + rect.y1)/2
                    images_on_page.append({
                        "data": base["image"],
                        "ext": base["ext"],
                        "y_center": y_center,
                        "bbox": rect
                    })
                except Exception as e:
                    print(f"  ⚠️ Erreur image: {e}")

            print(f"  ℹ️ {len(images_on_page)} images trouvées sur cette page")

            # --- Associer image à la ligne la plus proche ---
            for row_index, row in enumerate(table):
                if not row or all(c in [None, ""] for c in row):
                    continue
                row = [c if c else "" for c in row]
                while len(row) < len(header):
                    row.append("")

                # Skip header répété
                if [str(c).strip() for c in row[:len(header)]] == header:
                    continue

                # Vérifier si cette ligne contient une image
                matched_img = None
                for img in images_on_page:
                    # Comparer avec bbox de ligne
                    if row_index < len(lines_bbox):
                        _, y_top, y_bottom = lines_bbox[row_index]
                        if y_top <= img["y_center"] <= y_bottom:
                            matched_img = img
                            break

                if matched_img:
                    prenom = safe_name(row[2])
                    nom = safe_name(row[1])
                    img_path = os.path.join(
                        IMG_DIR,
                        f"{prenom}_{nom}_page{page_index}_{image_index_global}.{matched_img['ext']}"
                    )
                    try:
                        with open(img_path, "wb") as f_img:
                            f_img.write(matched_img["data"])
                        image_index_global += 1
                        print(f"  ✅ Image sauvegardée: {os.path.basename(img_path)} → {nom} {prenom}")
                        # Retirer image pour ne pas la réutiliser
                        images_on_page.remove(matched_img)
                        # Écrire CSV uniquement si image présente
                        writer.writerow(row + [img_path])
                    except Exception as e:
                        print(f"  ❌ Erreur sauvegarde: {e}")
