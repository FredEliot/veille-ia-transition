# insertbase_logic.py

from dotenv import load_dotenv
import os
from pathlib import Path


def lancer_insertion():
    # Chargement du .env
    load_dotenv(dotenv_path=Path('.') / '.env')

    # Logique actuelle de ton Insertbase3 ici
    import csv
    import os
    import time
    from pathlib import Path
    from dotenv import load_dotenv
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from pyairtable import Api

    # Chargement des variables d’environnement
    load_dotenv(dotenv_path=Path('.') / '.env')

    # Configuration Selenium
    chrome_options = Options()
    # chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    driver = webdriver.Chrome(options=chrome_options)

    # Préparation du CSV temporaire
    rows = []

    for page in range(1, 4):
        url = f"https://www.assemblee-nationale.fr/dyn/actualites?page={page}"
        print(f"🔎 Chargement de la page {page}...")
        driver.get(url)

        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, "div.news-block--preview"))
            )
        except Exception as e:
            print("❌ Aucun bloc détecté sur cette page.")
            continue

        blocs = driver.find_elements(
            By.CSS_SELECTOR, "div.news-block--preview")

        for b in blocs:
            try:
                titre = b.find_element(
                    By.CSS_SELECTOR, ".news-block--preview-title").text.strip()
                date = b.find_element(
                    By.CSS_SELECTOR, ".news-block--preview-top--date span").text.strip()

                parent = b.find_element(
                    By.XPATH, "./ancestor::div[contains(@class, 'news-block')]")
                a_tag = parent.find_element(By.CSS_SELECTOR, "a.inner")
                href = a_tag.get_attribute("href")
                url = f"https://www.assemblee-nationale.fr{href}" if href else "non trouvé"

                row = {
                    "Date": date,
                    "Résumé": titre,
                    "Lien": url,
                    "Source": "Assemblée Nationale"
                }
                rows.append(row)
                print(f"📌 Article récupéré : {titre}")
            except Exception as e:
                print("⚠️ Erreur lors de la lecture d’un bloc :", e)

    # Sauvegarde dans un CSV pour debug
    with open("actualites_debug.csv", "w", newline="", encoding="utf-8-sig") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=[
                                "Date", "Résumé", "Lien", "Source"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"📦 {len(rows)} actualités enregistrées dans actualites_debug.csv.")
    driver.quit()
    print("✅ Insertion en cours depuis insertbase_logic.py...")
    # ... Airtable / logique métier ...
    # Enregistrement dans Airtable avec filtrage doublons

    api_key = os.getenv("AIRTABLE_TOKEN")
    base_id = os.getenv("AIRTABLE_BASE_ID")
    table_name = "SignauxPolitiques"
    api = Api(api_key)
    table = api.table(base_id, table_name)

    print("🔁 Vérification des Résumés existants dans Airtable...")
    existing_resumes = set()
    for record in table.all():
        resume = record['fields'].get("Résumé")
        if resume:
            existing_resumes.add(resume.strip())

    print("📤 Vérification et envoi vers Airtable...")
    inserted = 0
    skipped = 0
    for row in rows:
        resume_clean = row['Résumé'].strip()
        if resume_clean in existing_resumes:
            print(f"🔁 Déjà présent (ignoré) : {resume_clean}")
            skipped += 1
            continue
        try:
            table.create(row)
            print(f"✅ Enregistré : {resume_clean}")
            inserted += 1
        except Exception as e:
            print(f"❌ Échec d'enregistrement : {resume_clean} — {e}")

    print(
        f"📊 Résumé : {inserted} inséré(s), {skipped} ignoré(s) car déjà existants.")
