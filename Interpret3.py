import json
import os
import datetime
import re

from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path
from pyairtable import Api

# Chargement des variables d’environnement
load_dotenv(dotenv_path=Path('.') / '.env')
AIRTABLE_TOKEN = os.getenv("AIRTABLE_TOKEN")
BASE_ID = os.getenv("AIRTABLE_BASE_ID")
TABLE_NAME = os.getenv("AIRTABLE_TABLE_NAME")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Connexion Airtable & OpenAI
api = Api(AIRTABLE_TOKEN)
table = api.table(BASE_ID, TABLE_NAME)
client = OpenAI(api_key=OPENAI_API_KEY)

# Constantes pour éviter la duplication de chaînes
FIELD_CHAMP_IMPACT = "Champ d’impact"
FIELD_SECTEURS_IMPACTES = "Secteurs impactés"
FIELD_URGENCE = "Urgence perçue"
FIELD_OPPORTUNITE = "Opportunité détectée ?"
FIELD_COMMENTAIRES = "Commentaires pour action"
FIELD_THEME = "Thème"
FIELD_MISSION = "Mission potentielle"
FIELD_DATE = "Date d’analyse"
FIELD_MOTS_CLES_MISSIONS = "Mots Clés Missions"

# Sélection des enregistrements non analysés
records = table.all()
to_analyze = [rec for rec in records if not rec.get(
    "fields", {}).get(FIELD_CHAMP_IMPACT)]

# 🔍 Résumé des nouvelles missions détectées
detected_missions = []

for rec in to_analyze:
    fields = rec.get("fields", {})
    titre = fields.get("Résumé", "")
    url = fields.get("Lien", "")
    source = fields.get("Source", "Source inconnue")
    date = fields.get("Date", "Date inconnue")

    # Chargement du prompt depuis le fichier prompt.txt

    prompt_file = Path("prompt.txt")
    if prompt_file.exists():
        prompt_template = prompt_file.read_text(encoding="utf-8")
    else:
        raise FileNotFoundError("Le fichier prompt.txt est introuvable.")

    # Exemple d'utilisation avec les variables dynamiques
    prompt = prompt_template.format(
        titre=titre, source=source, date=date, url=url)

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Tu es un assistant qui produit uniquement du JSON structuré pour analyse stratégique."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )

        raw = response.choices[0].message.content.strip()

        # Extraction du bloc JSON s'il est encadré de balises ```json ... ```
        match = re.search(r"```json(.*?)```", raw, re.DOTALL)
        if match:
            raw = match.group(1).strip()

        try:
            result = json.loads(raw)
        except json.JSONDecodeError as json_err:
            print(f"❌ Erreur de parsing JSON : {json_err}")
            print(f"🧾 Contenu brisé :\n{raw}")
            continue

        print("✅ JSON bien parsé :", result)

        secteurs = result.get(FIELD_SECTEURS_IMPACTES, [])
        if isinstance(secteurs, str):
            secteurs = [secteurs]

        missions = result.get(FIELD_MISSION, [])
        if isinstance(missions, str):
            missions = [missions]

        commentaire = result.get(FIELD_COMMENTAIRES, "")

        champ_impact = result.get(FIELD_CHAMP_IMPACT)
        if isinstance(champ_impact, list):
            champ_impact = ", ".join(champ_impact)

        mots_cles = result.get("Mots Clés Missions")
        if isinstance(mots_cles, str):
            # Tentative de conversion si c’est une chaîne de texte
            try:
                mots_cles = json.loads(mots_cles)
            except Exception as e:
                print(
                    f"⚠️ Échec de conversion JSON pour 'Mots Clés Missions' : {mots_cles}")
                # fallback : on garde la chaîne sous forme de liste
                mots_cles = [mots_cles]
                raise e  # pour journalisation ou interruption si tu veux bloquer ici

        payload = {
            FIELD_CHAMP_IMPACT: champ_impact,
            FIELD_SECTEURS_IMPACTES: ", ".join(secteurs),
            FIELD_URGENCE: result.get(FIELD_URGENCE),
            FIELD_OPPORTUNITE: result.get(FIELD_OPPORTUNITE),
            FIELD_COMMENTAIRES: commentaire,
            FIELD_THEME: result.get(FIELD_THEME),
            FIELD_MISSION: ", ".join(missions),
            FIELD_MOTS_CLES_MISSIONS: ", ".join(sorted(set(m.lower().strip() for m in mots_cles))),
            FIELD_DATE: datetime.datetime.now().strftime("%Y-%m-%d")
        }

        # Vérification minimale des champs essentiels
        if not payload[FIELD_CHAMP_IMPACT]:
            print(
                f"❌ Données manquantes dans la réponse JSON. Enregistrement ignoré : {titre}")
            continue

        print("📦 Données envoyées à Airtable :", payload)
        res = table.update(rec["id"], payload)
        print("✅ Mise à jour effectuée pour :", titre)

        if result.get(FIELD_OPPORTUNITE) == "Oui":

            mission_line = (
                f"### 🟢 {titre}  \n"
                f"&nbsp;&nbsp;&nbsp;&nbsp; 🧩 **Missions potentielles** : {', '.join(missions) if missions else 'Aucune'}  \n"
                f"&nbsp;&nbsp;&nbsp;&nbsp; ⚠️ **Urgence** : {result.get(FIELD_URGENCE) or 'Non précisée'}  \n"
                f"&nbsp;&nbsp;&nbsp;&nbsp; 🎯 **Action de suivi** : {commentaire or 'Non renseigné'}  \n"
            )
            print(mission_line)
            detected_missions.append(mission_line)

        print("🧾 Résultat Airtable :", res)

    except Exception as e:
        print(f"❌ Erreur générale : {e}")
        print(f"🔁 Contenu IA brut : {raw if 'raw' in locals() else 'N/A'}")

# 🧾 Affichage final des missions potentielles
with open("synthese_streamlit.md", "w", encoding="utf-8") as f:
    f.write("")
    if detected_missions:
        f.write("# 📊 Synthèse des missions détectées\n\n")
        f.write("\n\n".join(detected_missions))
    else:
        f.write("### Aucune mission potentielle détectée.")
