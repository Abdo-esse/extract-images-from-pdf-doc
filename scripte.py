import csv
import os
from openpyxl import Workbook
from openpyxl.drawing.image import Image as XLImage
from PIL import Image

CSV_FILE = "joueurs_clean.csv"
IMG_DIR = "photos_joueurs"
EXCEL_FILE = "joueurs_compress.xlsx"

MAX_SIZE = (100, 100)  # largeur/hauteur max pour les images
temp_files = []

wb = Workbook()
ws = wb.active
ws.title = "Joueurs"

with open(CSV_FILE, newline="", encoding="utf-8") as f_csv:
    reader = csv.reader(f_csv)
    for row_index, row in enumerate(reader, start=1):
        for col_index, value in enumerate(row, start=1):
            # Colonne photo
            if col_index == len(row) and value and os.path.exists(value):
                # Ouvrir et compresser l'image
                img_pil = Image.open(value)
                img_pil.thumbnail(MAX_SIZE)  # réduit la taille max
                temp_path = os.path.join(IMG_DIR, f"temp_{row_index}.png")
                img_pil.save(temp_path, optimize=True)
                temp_files.append(temp_path)  # garder la liste pour supprimer plus tard

                # Ajouter dans Excel
                img_excel = XLImage(temp_path)
                ws.row_dimensions[row_index].height = 60
                ws.add_image(img_excel, f"{chr(64+col_index)}{row_index}")
            else:
                ws.cell(row=row_index, column=col_index, value=value)

wb.save(EXCEL_FILE)
print(f"✅ Excel compressé créé: {EXCEL_FILE}")

# Supprimer les fichiers temporaires après sauvegarde
for f in temp_files:
    if os.path.exists(f):
        os.remove(f)
