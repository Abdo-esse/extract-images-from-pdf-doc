import fitz  # PyMuPDF
import os
import csv
import re

PDF_PATH = "./output/RCA Liste Catégorie.pdf"

# ================================
# 1. EXTRACTION DES IMAGES
# ================================

doc = fitz.open(PDF_PATH)

output_photos_dir = "photos"
os.makedirs(output_photos_dir, exist_ok=True)

image_index = 0
image_paths = []

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

print(f"{len(image_paths)} images extraites.")



# ================================
# 2. EXTRACTION DU TEXTE
# ================================

text = ""
for page in doc:
    text += page.get_text()

lines = text.split("\n")

# DEBUG: Save sample text to inspect format
with open("text_debug.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(lines[:50]))  # First 50 lines

print("\n=== SAMPLE TEXT (first 20 lines) ===")
for i, line in enumerate(lines[:20]):
    print(f"{i}: {repr(line)}")
print("\n")

# ================================
# 3. DÉTECTION AUTOMATIQUE DES LIGNES JOUEURS
# ================================

pattern = re.compile(
    r"([A-ZÀÂÄÇÉÈÊËÎÏÔÖÙÛÜŸ'-]+)\s+([A-ZÀÂÄÇÉÈÊËÎÏÔÖÙÛÜŸa-zàâäçéèêëîïôöùûüÿ' -]+)\s+"
    r"(\d{2}/\d{2}/\d{4})\s+([A-Za-zÀ-ÖØ-öø-ÿ()\/ ]+)\s+"
    r"([A-Z0-9/]+)\s+([A-Za-zÀ-ÖØ-öø-ÿ ]*)\s*([A-Za-zÀ-ÖØ-öø-ÿ ]*)\s*"
    r"(Interne|Externe)\s+([A-Za-zÀ-ÖØ-öø-ÿ ]+)\s+([A-Za-zÀ-ÖØ-öø-ÿ ]*)"
)

players = []

for line in lines:
    m = pattern.search(line)
    if m:
        players.append({
            "nom": m.group(1),
            "prenom": m.group(2),
            "date_naissance": m.group(3),
            "lieu": m.group(4).strip(),
            "cni": m.group(5),
            "poste1": m.group(6).strip(),
            "poste2": m.group(7).strip(),
            "interne_externe": m.group(8),
            "statut": m.group(9).strip(),
            "mode_recrutement": m.group(10).strip()
        })

print(f"{len(players)} joueurs détectés dans le texte.")



# ================================
# 4. ASSOCIATION PHOTOS ↔ JOUEURS
# ================================

if len(players) != len(image_paths):
    print("\n⚠️ ATTENTION : nombre de photos ≠ nombre de joueurs.")
    print("Association faite par ordre d'apparition.\n")

output_named_photos = "photos_joueurs_nommes"
os.makedirs(output_named_photos, exist_ok=True)

for idx, player in enumerate(players):
    if idx < len(image_paths):
        src = image_paths[idx]
        if os.path.exists(src):
            dst = f"{output_named_photos}/{player['nom']}_{player['prenom']}.png"
            os.rename(src, dst)
            player["photo"] = dst
        else:
            player["photo"] = ""
    else:
        player["photo"] = ""



# ================================
# 5. EXPORT CSV FINAL
# ================================

csv_path = "joueurs_extrait.csv"

with open(csv_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow([
        "Nom",
        "Prénom",
        "Date naissance",
        "Lieu de naissance",
        "CNI",
        "Poste 1",
        "Poste 2",
        "Interne/Externe",
        "Statut",
        "Mode recrutement",
        "Photo"
    ])
    
    for p in players:
        writer.writerow([
            p["nom"],
            p["prenom"],
            p["date_naissance"],
            p["lieu"],
            p["cni"],
            p["poste1"],
            p["poste2"],
            p["interne_externe"],
            p["statut"],
            p["mode_recrutement"],
            p["photo"]
        ])

print(f"\n🎉 Extraction terminée !")
print(f"📁 Photos nommées dans : {output_named_photos}")
print(f"📄 CSV généré : {csv_path}")
