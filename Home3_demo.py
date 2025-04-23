# Home3_demo.py
import os
from pathlib import Path
from datetime import datetime
import pandas as pd
import streamlit as st
from streamlit_option_menu import option_menu
from pyairtable import Api
from dotenv import load_dotenv

# —————————————————————————————————————————————————————————–––––––––––––––––––––––––––––
#                        CONFIGURATION GLOBALE
# —————————————————————————————————————————————————————————–––––––––––––––––––––––––––––

# Charge les variables d’environnement (Airtable)
load_dotenv()
AIRTABLE_TOKEN = os.getenv("AIRTABLE_TOKEN")
BASE_ID = os.getenv("AIRTABLE_BASE_ID")
api = Api(AIRTABLE_TOKEN)

# Chemins des fichiers CSV “demo”
CSV_MOTS = "Output/MotsCles_A_Valider.csv"
CSV_MISS = "Output/Missions_Proposees.csv"

# —————————————————————————————————————————————————————————–––––––––––––––––––––––––––––
#                                    UI
# —————————————————————————————————————————————————————————–––––––––––––––––––––––––––––

st.set_page_config(layout="wide")

# Barre latérale
with st.sidebar:
    selected = option_menu(
        None, ["Matching", "Référentiel Missions"],
        icons=["wrench", "gear"], menu_icon="cast", default_index=0
    )

# —————————————————————————————————————————————————————————–––––––––––––––––––––––––––––
#                                   Matching
# —————————————————————————————————————————————————————————–––––––––––––––––––––––––––––

if selected == "Matching":
    st.header("🔍 Matching des Signaux vs Missions")

    # Lecture simplifiée du CSV généré précédemment
    if os.path.exists(CSV_MOTS):
        try:
            df = pd.read_csv(CSV_MOTS)
            if df.empty:
                st.warning("Aucun signal ou mots-clés à matcher.")
                st.stop()
        except Exception:
            st.error("Impossible de lire le fichier de matching.")
            st.stop()
    else:
        st.warning(f"Fichier `{CSV_MOTS}` introuvable.")
        st.stop()

    # Tri par score si existant, sinon on simule
    if "Score de correspondance" in df.columns:
        df["ScoreNum"] = df["Score de correspondance"].str.rstrip(
            " %").astype(float)
        df = df.sort_values("ScoreNum", ascending=False)
    else:
        df["Score de correspondance"] = "—"

    st.dataframe(
        df[["Titre de la mission", "Score de correspondance"]],
        use_container_width=True
    )

# —————————————————————————————————————————————————————————–––––––––––––––––––––––––––––
#                             Référentiel Missions
# —————————————————————————————————————————————————————————–––––––––––––––––––––––––––––

elif selected == "Référentiel Missions":
    st.header("🗂️ Référentiel de Missions & Mots-clés")

    col1, col2 = st.columns(2)

    # — Arborescence (stub)
    with col1:
        if st.button("📂 Afficher l’arborescence"):
            st.info("Fonction `afficher_arborescence()` (stub)")

    # — Proposition & validation
    with col2:
        st.subheader("📤 Import & Validation CSV")

        tab = st.radio("Choisir", ["Mots-clés", "Missions"])

        if tab == "Mots-clés":
            # Chargement sécurisé
            if not os.path.exists(CSV_MOTS) or os.path.getsize(CSV_MOTS) == 0:
                st.info("📂 Aucune proposition de mots-clés.")
                st.stop()
            df = pd.read_csv(CSV_MOTS)
            # Affichage par champ
            champs = ["Origine du besoin", "Type de transformation",
                      "Fonctions concernées", "Secteur / périmètre"]
            sel = []
            c1, c2 = st.columns(2)
            for i, champ in enumerate(champs):
                col = c1 if i % 2 == 0 else c2
                with col:
                    st.markdown(f"#### {champ}")
                    for val in sorted(df[champ].dropna().unique()):
                        if st.checkbox(val, key=f"{champ}_{val}"):
                            sel.append((champ, val))
            if st.button("✅ Valider mots-clés"):
                table = api.table(BASE_ID, "ReferentielMissions")
                for champ, val in sel:
                    table.create({
                        "Mot-clé mission": val,
                        "Champ associé": champ,
                        "Statut": "Validé",
                        "Proposé par": "IA",
                        "Date de proposition": datetime.today().strftime("%Y-%m-%d")
                    })
                st.success(f"{len(sel)} mots-clés validés.")
                # on ne relit pas les CSV pour ne pas planter
        else:
            # Missions
            if not os.path.exists(CSV_MISS) or os.path.getsize(CSV_MISS) == 0:
                st.info("📂 Aucune mission proposée.")
                st.stop()
            df = pd.read_csv(CSV_MISS)
            sel_idx = []
            for idx, row in df.iterrows():
                with st.expander(row["Titre mission"]):
                    st.markdown(
                        f"- **Type** : {row['Type de transformation']}")
                    st.markdown(
                        f"- **Fonctions** : {row['Fonctions concernées']}")
                    st.markdown(f"- **Secteur** : {row['Secteur concerné']}")
                    st.markdown(f"- **Durée** : {row['Durée estimée']}")
                    if st.checkbox("Valider cette mission", key=f"mis_{idx}"):
                        sel_idx.append(idx)
            if st.button("✅ Valider missions"):
                table = api.table(BASE_ID, "TypologiesMissions")
                cnt = 0
                for i in sel_idx:
                    rec = df.iloc[i].to_dict()
                    rec["Statut"] = "Validé"
                    table.create(rec)
                    cnt += 1
                st.success(f"{cnt} mission(s) validée(s).")
