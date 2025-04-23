import os
from dotenv import load_dotenv
from pathlib import Path
from pyairtable import Api
import pandas as pd

# Chargement de l'environnement
load_dotenv(dotenv_path=Path('.') / '.env')

api_key = os.getenv("AIRTABLE_TOKEN")
base_id = os.getenv("AIRTABLE_BASE_ID")
table_name = "SignauxPolitiques"

api = Api(api_key)
table = api.table(base_id, table_name)

# Lecture des enregistrements
records = table.all()
data = []
for record in records:
    fields = record.get("fields", {})
    data.append({
        "Date": fields.get("Date"),
        "Résumé": fields.get("Résumé"),
        "Lien": fields.get("Lien"),
        "Source": fields.get("Source")
    })

df = pd.DataFrame(data)

# Détection des doublons par lien
duplicates = df[df.duplicated(subset=["Lien"], keep=False)]
print(f"{len(duplicates)} doublons trouvés :")
print(duplicates.sort_values("Lien"))
