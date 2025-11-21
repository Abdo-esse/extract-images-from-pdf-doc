import fitz  # PyMuPDF
import os
import csv
import re
import unicodedata
from openpyxl import Workbook

PDF_PATH = "./output/RCA Liste Catégorie.pdf"

# ================================
# 1. EXTRACTION DES IMAGES
# ================================

print("📸 Extraction des images...")

doc = fitz.open(PDF_PATH)
output_photos_dir = "photos"
os.makedirs(output_photos_dir, exist_ok=True)

image_paths = []
image_index = 0

for page_index, page in enumerate(doc):
    images = page.get_images(full=True)

    for img in images:
        xref = img[0]
        pix = fitz.Pixmap(doc, xref)

        image_index += 1
        image_path = f"{output_photos_dir}/image_{image_index}.png"

        if pix.n < 5:
            pix.save(image_path)
        else:
            pix = fitz.Pixmap(fitz.csRGB, pix)
            pix.save(image_path)

        image_paths.append(image_path)

print(f"✔ {len(image_paths)} images extraites.")


# ================================
# 2. EXTRACTION DU TEXTE
# ================================

print("\n📄 Extraction du texte...")

text = ""
for page in doc:
    text += page.get_text()

lines = text.split("\n")
clean_lines = [l.strip() for l in lines if l.strip() != ""]


# ================================
# 3. RECONSTRUCTION DES BLOCS JOUEURS
# ================================

print("\n🧩 Reconstruction des blocs joueurs...")

players = []
i = 0

while i < len(clean_lines):

    # Nom détecté ? (MAJUSCULES)
    if i + 11 < len(clean_lines) and re.match(r"^[A-ZÀÂÄÇÉÈÊËÎÏÔÖÙÛÜŸ'-]{2,}$", clean_lines[i]):

        player = {
            "nom": clean_lines[i],
            "prenom": clean_lines[i+1],
            "date_naissance": clean_lines[i+2],
            "lieu": clean_lines[i+3],
            "cni": clean_lines[i+4],
            "poste1": clean_lines[i+5],
            "poste2": clean_lines[i+6],
            "interne_externe": clean_lines[i+7],
            "statut": clean_lines[i+8],
            "mode_recrutement": clean_lines[i+9],
            "scolarite": clean_lines[i+10]
        }

        players.append(player)
        i += 12

    else:
        i += 1

print(f"✔ {len(players)} joueurs détectés.")


# ================================
# 4. ASSOCIATION PHOTOS ↔ JOUEURS
# ================================

print("\n🖼 Association des photos...")

def safe_filename(name):
    name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    name = name.replace(" ", "_")
    return name

output_named_photos = "photos_joueurs_nommes"
os.makedirs(output_named_photos, exist_ok=True)

if len(players) != len(image_paths):
    print(f"⚠️ Attention : {len(players)} joueurs mais {len(image_paths)} photos.")
    print("Association par ordre d'apparition.")

for idx, player in enumerate(players):
    if idx < len(image_paths):
        src = image_paths[idx]
        dst = f"{output_named_photos}/{safe_filename(player['nom'])}_{safe_filename(player['prenom'])}.png"
        os.rename(src, dst)
        player["photo"] = dst
    else:
        player["photo"] = ""

print("✔ Photos associées.")


# ================================
# 5. EXPORT CSV
# ================================

csv_path = "joueurs_extrait.csv"

print("\n💾 Export CSV...")

with open(csv_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow([
        "Nom", "Prénom", "Date naissance", "Lieu de naissance", "CNI",
        "Poste 1", "Poste 2", "Interne/Externe", "Statut",
        "Mode recrutement", "Scolarité", "Photo"
    ])

    for p in players:
        writer.writerow([
            p["nom"], p["prenom"], p["date_naissance"], p["lieu"], p["cni"],
            p["poste1"], p["poste2"], p["interne_externe"], p["statut"],
            p["mode_recrutement"], p["scolarite"], p["photo"]
        ])

print(f"✔ CSV généré : {csv_path}")


# ================================
# 6. EXPORT EXCEL (XLSX)
# ================================

excel_path = "joueurs_extrait.xlsx"

print("💾 Export Excel...")

wb = Workbook()
ws = wb.active
ws.title = "Joueurs"

headers = [
    "Nom", "Prénom", "Date naissance", "Lieu de naissance", "CNI",
    "Poste 1", "Poste 2", "Interne/Externe", "Statut",
    "Mode recrutement", "Scolarité", "Photo"
]

ws.append(headers)

for p in players:
    ws.append([
        p["nom"], p["prenom"], p["date_naissance"], p["lieu"], p["cni"],
        p["poste1"], p["poste2"], p["interne_externe"], p["statut"],
        p["mode_recrutement"], p["scolarite"], p["photo"]
    ])

wb.save(excel_path)

print(f"✔ Excel généré : {excel_path}")


# ================================
# FIN
# ================================

print("\n🎉 Extraction terminée avec succès !")
print(f"📁 Photos : {output_named_photos}")
print(f"📄 CSV : {csv_path}")
print(f"📘 Excel : {excel_path}")
