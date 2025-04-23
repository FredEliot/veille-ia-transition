# MatchSignals.py
import os
import datetime
from dotenv import load_dotenv
from pathlib import Path
from pyairtable import Api
from difflib import SequenceMatcher

# Chargement des variables d'environnement
load_dotenv(dotenv_path=Path('.') / '.env')
AIRTABLE_TOKEN = os.getenv("AIRTABLE_TOKEN")
BASE_ID = os.getenv("AIRTABLE_BASE_ID")

# Connexion Airtable
api = Api(AIRTABLE_TOKEN)
table_signaux = api.table(BASE_ID, "SignauxPolitiques")
table_missions = api.table(BASE_ID, "TypologiesMissions")
table_opportunites = api.table(BASE_ID, "OpportunitesPitcher")

# Chargement des signaux à matcher
signaux = [rec for rec in table_signaux.all(
) if not rec.get("fields", {}).get("Match")]
print(f"🔍 {len(signaux)} signaux à matcher")

# Chargement des missions existantes
missions = table_missions.all()

# Fonction de similarité simple


def similarite(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


# Matching
for signal in signaux:
    champs = signal.get("fields", {})
    mots_cles_signal = champs.get("Mots Clés Missions", "")
    if not mots_cles_signal:
        continue

    meilleurs_matchs = []
    for mission in missions:
        mots_cles_mission = mission.get(
            "fields", {}).get("Mots Clés Missions", "")
        if not mots_cles_mission:
            continue

        score = similarite(mots_cles_signal, mots_cles_mission)
        if score > 0.2:  # seuil de pertinence à ajuster si besoin
            meilleurs_matchs.append((mission, score))

    meilleurs_matchs = sorted(
        meilleurs_matchs, key=lambda x: x[1], reverse=True)[:3]

    for mission, score in meilleurs_matchs:
        table_opportunites.create({
            "Signal lié": [signal["id"]],
            "Mission matchée": [mission["id"]],
            "Scoring match": round(score, 2),
            "Date": datetime.datetime.now().strftime("%Y-%m-%d")
        })

    # Marquer comme matché
    table_signaux.update(signal["id"], {"Match": True})
    print(
        f"✅ Signal {signal['id']} matché avec {len(meilleurs_matchs)} mission(s)")
