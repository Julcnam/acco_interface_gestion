from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import os
import tarfile
from pathlib import Path
import config
from docx import Document
import os
from alive_progress import alive_bar


# Chemin de téléchargement des fichiers
download_path = config.DOWNLOAD_PATH


# Fonction pour s'assurer que le répertoire de téléchargement existe et lancer les téléchargements
def ensure_download_path():
    print("Ouverture de Chrome et lancement des téléchargements...")

    download_dir = Path(download_path)
    download_dir.mkdir(parents=True, exist_ok=True)
    options = webdriver.ChromeOptions()
    prefs = {"download.default_directory": str(download_dir)}
    options.add_experimental_option("prefs", prefs)

    driver = webdriver.Chrome(options=options)
    driver.get("https://echanges.dila.gouv.fr/OPENDATA/ACCO/")

    elements = driver.find_elements(By.XPATH, "//a[contains(@href, '.tar.gz')]")
    existing_files = set(download_dir.iterdir())

    to_download = []
    for elem in elements:
        href = elem.get_attribute("href")
        filename = Path(href).name
        filename = filename.replace(".tar.gz","")
        if download_dir / filename not in existing_files:
            to_download.append(elem)

    if not to_download:
        print("Aucun nouveau fichier à télécharger.")
        driver.quit()
        return

    with alive_bar(len(to_download), title="Téléchargement...") as bar:
        for elem in to_download:
            elem.click()
            bar()
            time.sleep(0.3)  

    def wait_for_downloads():
        while any(f.suffix == ".crdownload" for f in download_dir.iterdir()):
            time.sleep(1)

    wait_for_downloads()
    print("Téléchargements terminés.")
    driver.quit()


# Fonction pour extraire les fichiers .tar.gz dans le répertoire de téléchargement
def ensure_extract_files():
    print("Extraction des fichiers...")
    download_dir = Path(download_path)
    archives = [
        a for a in download_dir.iterdir()
        if a.is_file() and a.suffixes == [".tar", ".gz"]
    ]
    
    if not archives:
        print("Aucune archive à extraire.")
        return

    with alive_bar(len(archives), title="Extraction...") as bar:
        for archive in archives:
            extract_dir = download_dir / archive.stem.replace(".tar", "")
            extract_dir.mkdir(exist_ok=True)

            print(f"Extraction de {archive.name} vers {extract_dir}...")

            with tarfile.open(archive, "r:gz") as tar:
                tar.extractall(path=extract_dir)

            archive.unlink()
            print(f"{archive.name} extrait et supprimé.")
            bar()

    print("Extraction terminée.")

def docx_to_txt(docx_path, txt_path):
    try:
        # Vérification de l'existence du fichier
        if not os.path.isfile(docx_path):
            raise FileNotFoundError(f"Fichier introuvable : {docx_path}")

        # Lecture du fichier DOCX
        doc = Document(docx_path)

        # Extraction du texte
        full_text = []
        for para in doc.paragraphs:
            if para.text.strip():  # Ignorer les lignes vides
                full_text.append(para.text)

        # Écriture dans le fichier TXT
        with open(txt_path, "w", encoding="utf-8") as txt_file:
            txt_file.write("\n".join(full_text))

        print(f"Conversion réussie : {txt_path}")

    except Exception as e:
        print(f"Erreur lors de la conversion : {e}")


def ensure_conversion_txt():
    base_path = Path(config.DOWNLOAD_PATH)
    docx_files = [
        path for path in base_path.rglob("*.docx")
        if path.is_file() and not path.with_suffix(".txt").exists()
    ]

    if not docx_files:
        print("Aucun fichier à convertir.")
        return

    with alive_bar(len(docx_files), title="Conversion...") as bar:
        for path in docx_files:
            txt_path = path.with_suffix(".txt")
            docx_to_txt(str(path), str(txt_path))
            path.unlink()
            bar()

    print("Conversion terminée.")
           