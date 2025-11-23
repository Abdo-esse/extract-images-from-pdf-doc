# import os
# import csv
# import fitz  # PyMuPDF
# import pdfplumber
# import re

# # --- Configurations ---
# PDF_FILE = "./Copie de Fiche avec photo U14 (3).pdf"
# IMG_DIR = "photos_joueurs"
# CSV_FILE = "joueurs_clean.csv"

# os.makedirs(IMG_DIR, exist_ok=True)


# def safe_name(s):
#     return re.sub(r"[^\w]", "_", s.strip() if s else "unknown")


# # ------------------------------
# #   EXTRAIRE AUTOMATIQUEMENT LE HEADER
# # ------------------------------

# print("🔍 Extraction automatique du header...")

# with pdfplumber.open(PDF_FILE) as pdf_temp:
#     extracted_header = None

#     for page in pdf_temp.pages:
#         tables = page.extract_tables()
#         if tables and len(tables[0]) > 0:
#             extracted_header = [c.strip() if c else "" for c in tables[0][0]]
#             break

# if extracted_header:
#     print("📌 Header détecté :", extracted_header)
# else:
#     raise ValueError("❌ Impossible d'extraire le header automatiquement !")

# # Ajouter colonne Photo à la fin
# header = extracted_header + ["Photo"]


# # ---------------------------------
# #       TRAITEMENT PRINCIPAL
# # ---------------------------------

# with open(CSV_FILE, "w", newline="", encoding="utf-8") as f_csv:
#     writer = csv.writer(f_csv)
#     writer.writerow(header)

#     with pdfplumber.open(PDF_FILE) as pdf_plumber, fitz.open(PDF_FILE) as pdf_fitz:

#         image_index_global = 1

#         for page_index, (page_p, page_f) in enumerate(zip(pdf_plumber.pages, pdf_fitz), start=1):
#             print(f"\n📄 Traitement page {page_index}...")

#             # --- Extraction table
#             tables = page_p.extract_tables()
#             if not tables:
#                 print("  ⚠️ Pas de table sur cette page")
#                 continue

#             table = tables[0]

#             # --- Nettoyer lignes vides
#             table_rows = [r for r in table if any(c and c.strip() for c in r)]
#             if not table_rows:
#                 continue

#             # Retirer header répété dans les pages suivantes
#             if table_rows[0] == extracted_header:
#                 table_rows = table_rows[1:]

#             # --- Extraire positions exactes des lignes
#             words = page_p.extract_words(extra_attrs=["top", "bottom"])
#             lines_bbox = []
#             current_top = None
#             current_line = []

#             for w in words:
#                 if current_top is None:
#                     current_top = w["top"]

#                 if abs(w["top"] - current_top) > 3:
#                     if current_line:
#                         y_top = min(wd["top"] for wd in current_line)
#                         y_bottom = max(wd["bottom"] for wd in current_line)
#                         lines_bbox.append((current_line, y_top, y_bottom))
#                     current_line = []
#                     current_top = w["top"]

#                 current_line.append(w)

#             if current_line:
#                 y_top = min(wd["top"] for wd in current_line)
#                 y_bottom = max(wd["bottom"] for wd in current_line)
#                 lines_bbox.append((current_line, y_top, y_bottom))

#             # --- Extraire les images
#             images_on_page = []
#             for img in page_f.get_images(full=True):
#                 try:
#                     xref = img[0]
#                     base = pdf_fitz.extract_image(xref)
#                     rects = page_f.get_image_rects(xref)
#                     if not rects:
#                         continue
#                     rect = rects[0]
#                     y_center = (rect.y0 + rect.y1) / 2
#                     images_on_page.append({
#                         "data": base["image"],
#                         "ext": base["ext"],
#                         "y_center": y_center,
#                         "bbox": rect
#                     })
#                 except Exception as e:
#                     print(f"  ⚠️ Erreur image: {e}")

#             print(f"  📸 {len(images_on_page)} images trouvées sur cette page.")

#             # --- Associer ligne + image
#             for row_index, row in enumerate(table_rows):
#                 row = [c if c else "" for c in row]

#                 # Compléter si manque des colonnes
#                 while len(row) < len(header) - 1:
#                     row.append("")

#                 matched_img = None

#                 if row_index < len(lines_bbox):
#                     _, y_top, y_bottom = lines_bbox[row_index]

#                     for img in images_on_page:
#                         if y_top <= img["y_center"] <= y_bottom:
#                             matched_img = img
#                             break

#                 if matched_img:
#                     prenom = safe_name(row[2] if len(row) > 2 else "")
#                     nom = safe_name(row[1] if len(row) > 1 else "")
#                     img_path = os.path.join(
#                         IMG_DIR,
#                         f"{prenom}_{nom}_page{page_index}_{image_index_global}.{matched_img['ext']}"
#                     )
#                     try:
#                         with open(img_path, "wb") as f_img:
#                             f_img.write(matched_img["data"])
#                         print(f"  ✅ Image sauvée: {os.path.basename(img_path)}")

#                         image_index_global += 1
#                         images_on_page.remove(matched_img)

#                         writer.writerow(row + [img_path])

#                     except Exception as e:
#                         print(f"  ❌ Erreur en sauvegarde image: {e}")

#                 else:
#                     # Pas d'image → écrire avec colonne vide
#                     writer.writerow(row + [""])






import os
import csv
import fitz  # PyMuPDF
import pdfplumber
import re

# --- Configurations ---
PDF_FILE = "./Informations  Centre de formation U15.pdf"
IMG_DIR = "photos_joueurs"
CSV_FILE = "joueurs_clean.csv"

os.makedirs(IMG_DIR, exist_ok=True)

header = ['#', '', '', '', '', '']


def safe_name(s):
    return re.sub(r"[^\w]", "_", s.strip() if s else "unknown")


def extract_fallback_screenshot(page_f, y_top, y_bottom, index, page_index):
    """
    Extrait une capture de la zone PHOTO (fallback)
    lorsque qu'il n'y a pas de vraie image.
    """

    # Coordonnées précises de la colonne PHOTO dans ton PDF
    x0 = 40    # bord gauche de la colonne photo
    x1 = 160   # bord droit de la colonne photo

    rect = fitz.Rect(x0, y_top, x1, y_bottom)

    pix = page_f.get_pixmap(clip=rect, dpi=150, alpha=False)
    img_path = os.path.join(
        IMG_DIR,
        f"fallback_page{page_index}_{index}.png"
    )
    pix.save(img_path)

    print(f"  🟨 Fallback extrait : {os.path.basename(img_path)}")

    return img_path


with open(CSV_FILE, "w", newline="", encoding="utf-8") as f_csv:
    writer = csv.writer(f_csv)
    writer.writerow(header + ["Photo fichier"])

    with pdfplumber.open(PDF_FILE) as pdf_p, fitz.open(PDF_FILE) as pdf_f:

        image_index_global = 1

        for page_index, (page_p, page_f) in enumerate(zip(pdf_p.pages, pdf_f), start=1):
            print(f"\n📄 Traitement page {page_index}...")

            # --- Extraction tableau
            tables = page_p.extract_tables()
            if not tables:
                print("  ⚠️ Pas de tableau sur cette page")
                continue
            table = tables[0]

            # --- Extraction lignes bbox
            words = page_p.extract_words(extra_attrs=["top", "bottom"])
            lines_bbox = []
            current_top = None
            current_line = []

            for w in words:
                if current_top is None:
                    current_top = w["top"]

                if abs(w["top"] - current_top) > 3:
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

            # --- Extraction vraies images
            images_on_page = []
            for img in page_f.get_images(full=True):
                xref = img[0]
                base = pdf_f.extract_image(xref)
                rects = page_f.get_image_rects(xref)
                if rects:
                    rect = rects[0]
                    y_center = (rect.y0 + rect.y1) / 2

                    images_on_page.append({
                        "data": base["image"],
                        "ext": base["ext"],
                        "y_center": y_center,
                        "bbox": rect
                    })

            print(f"  📸 {len(images_on_page)} vraies images trouvées")

            # --- Traitement lignes
            for r_index, row in enumerate(table):

                if not row or all(c in ["", None] for c in row):
                    continue

                while len(row) < len(header):
                    row.append("")

                prenom = safe_name(row[2] if len(row) > 2 else "")
                nom = safe_name(row[1] if len(row) > 1 else "")

                matched_img = None

                # MATCHING IMAGE → LIGNE
                if r_index < len(lines_bbox):
                    _, top, bottom = lines_bbox[r_index]
                    center_line = (top + bottom) / 2

                    best_dist = 9999
                    best_img = None

                    for img in images_on_page:
                        dist = abs(img["y_center"] - center_line)
                        if dist < best_dist:
                            best_dist = dist
                            best_img = img

                    if best_dist < 80:  # tolérance élargie
                        matched_img = best_img

                # --- CAS 1 : vraie image trouvée
                if matched_img:
                    img_path = os.path.join(
                        IMG_DIR,
                        f"{prenom}_{nom}_{page_index}_{image_index_global}.{matched_img['ext']}"
                    )

                    with open(img_path, "wb") as f_img:
                        f_img.write(matched_img["data"])

                    print(f"  ✅ Image extraite : {os.path.basename(img_path)}")

                    images_on_page.remove(matched_img)
                    image_index_global += 1
                    writer.writerow(row + [img_path])
                    continue

                # --- CAS 2 : AUCUNE image → FALLBACK screenshot
                img_path = extract_fallback_screenshot(
                    page_f, top, bottom,
                    image_index_global, page_index
                )
                image_index_global += 1
                writer.writerow(row + [img_path])
