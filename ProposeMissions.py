import os
import json
import datetime
from pathlib import Path
import pandas as pd
from dotenv import load_dotenv
from pyairtable import Api
from openai import OpenAI

# Chargement des variables d'environnement
load_dotenv(dotenv_path=Path('.') / '.env')
AIRTABLE_TOKEN = os.getenv("AIRTABLE_TOKEN")
BASE_ID = os.getenv("AIRTABLE_BASE_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Connexion aux APIs
api = Api(AIRTABLE_TOKEN)
table_signaux = api.table(BASE_ID, "SignauxPolitiques")
table_referentiel = api.table(BASE_ID, "ReferentielMissions")
table_missions = api.table(BASE_ID, "TypologiesMissions")

# Préparation OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)

# Chargement du prompt depuis un fichier texte externe
with open("promptRefMissions.txt", "r", encoding="utf-8") as f:
    base_prompt = f.read()

with open("promptMissionSynthese.txt", "r", encoding="utf-8") as f:
    synthese_prompt_template = f.read()

# Chargement des signaux non encore lus par ProposeMission
signaux = [rec for rec in table_signaux.all() if not rec.get(
    "fields", {}).get("ReferentielMissionLu")]

# Chargement du référentiel existant
records_ref = table_referentiel.all()
ref_mots_cles = {r["fields"].get("Mot-clé mission", "").lower(): r["fields"]
                 for r in records_ref if "Mot-clé mission" in r["fields"] and r["fields"].get("Statut") == "Validé"}

# Conteneurs
propositions_referentiel = []
propositions_missions = []

# Traitement des signaux
for signal in signaux:
    fields = signal.get("fields", {})
    titre = fields.get("Thème", "")
    contexte = fields.get("Commentaires pour action", "")
    impact = fields.get("Champ d’impact", "Organisation")
    secteurs = fields.get("Secteurs impactés", "Autre")
    signal_id = signal["id"]

    # Génération des mots-clés
    prompt = base_prompt.format(titre=titre, contexte=contexte)
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": base_prompt.format(
            titre=titre, contexte=contexte)}],
        temperature=0.7
    )
    try:
        mots_cles_structures = json.loads(response.choices[0].message.content)
        for mot_data in mots_cles_structures:
            mot_data["Statut"] = "En attente"
            mot_data["Proposé par"] = "IA"
            mot_data["Date de proposition"] = datetime.date.today().isoformat()
            mot_data["Signal source"] = signal_id
            propositions_referentiel.append(mot_data)
    except Exception as e:
        print(f"Erreur parsing JSON enrichi : {e}")

    # Génération d'une mission complète si mots-clés validés
    mots_cles = ["pilotage de projet"]
    mots_cles_valides = [m for m in mots_cles if m.lower() in ref_mots_cles]

    if mots_cles:
        synthese_prompt = synthese_prompt_template.format(
            titre=titre,
            contexte=contexte,
            mots_cles="\n".join(mots_cles_valides),
            secteur=secteurs,
            champ_impact=impact
        )
        synth_response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": synthese_prompt}],
            temperature=0.7
        )
        try:
            mission_json = json.loads(
                synth_response.choices[0].message.content)
            mission_json["Signal source"] = signal_id
            mission_json["Date de proposition"] = datetime.date.today(
            ).isoformat()
            propositions_missions.append(mission_json)
        except Exception as e:
            print(f"Erreur de parsing JSON pour mission : {e}")

    # Proposer des compléments pour les mots-clés non validés
    for mot in mots_cles:
        mot_clean = mot.lower()
        if mot_clean not in ref_mots_cles:
            propositions_referentiel.append({
                "Mot-clé missions": mot,
                "Impact métiers": impact,
                "Secteur concerné": secteurs,
                "Fonctions concernées": "À proposer",
                "Type de transformation": "À proposer",
                "Proposé par": "IA",
                "Statut": "En attente",
                "Date de proposition": datetime.date.today().isoformat(),
                "Signal source": signal_id
            })

    # Marquer comme traité
    table_signaux.update(signal_id, {"ReferentielMissionLu": True})

# Export CSV
df_missions = pd.DataFrame(propositions_missions)
df_referentiel = pd.DataFrame(propositions_referentiel)

df_missions.to_csv(
    "/Users/fredoh/veille-ia-env/Output/Missions_Proposees.csv", index=False)
df_referentiel.to_csv(
    "/Users/fredoh/veille-ia-env/Output/MotsCles_A_Valider.csv", index=False)

print(f"✅ {len(df_missions)} missions générées | {len(df_referentiel)} entrées à valider dans le référentiel")
