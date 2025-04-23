# DemoApp.py
import os
from pathlib import Path
from datetime import datetime
import pandas as pd
import streamlit as st
from streamlit_option_menu import option_menu
from dotenv import load_dotenv
from pyairtable import Api

# Importez vos modules de logique (sans subprocess ni selenium)
from ArboMissions import afficher_arborescence as fn_arbo
from MatchSignals import similarite, match_signaux as fn_match
from ProposeMissions import generate_referentiel, generate_missions as fn_propose
from Interpret3 import interpret_signaux as fn_interpret
# Insertbase3.py inclut du Selenium : on le gardera pour local-only
# from insertbase_logic import lancer_insertion                as fn_scrape_local

# ————————————————————————————————————————————————————————
#                 Initialisation & configuration
# ————————————————————————————————————————————————————————
st.set_page_config(page_title="Veille IA – Démo Cloud", layout="wide")

# Charge .env
load_dotenv()
AIRTABLE_TOKEN = os.getenv("AIRTABLE_TOKEN")
BASE_ID = os.getenv("AIRTABLE_BASE_ID")
api = Api(AIRTABLE_TOKEN)

# CSV “d’entrée” pour la démo
CSV_MOTS = "Output/MotsCles_A_Valider.csv"
CSV_MISSIONS = "Output/Missions_Proposees.csv"

# ————————————————————————————————————————————————————————
#                            Barre latérale
# ————————————————————————————————————————————————————————
with st.sidebar:
    page = option_menu(
        None,
        ["Accueil", "Matching", "Référentiel", "Analyse IA", "Arborescence"],
        icons=["house", "shuffle", "list-task", "cpu", "diagram-3"],
        default_index=0
    )

# ————————————————————————————————————————————————————————
#                              Accueil
# ————————————————————————————————————————————————————————
if page == "Accueil":
    st.title("✅ Veille IA – Démo")
    st.markdown(
        "Bienvenue ! Cette démo présente :\n"
        "- Matching Signaux ↔ Missions  \n"
        "- Validation Mots-clés & Missions  \n"
        "- Interprétation IA (stub)  \n"
        "- Arborescence Missions  \n"
    )

# ————————————————————————————————————————————————————————
#                             Matching
# ————————————————————————————————————————————————————————
elif page == "Matching":
    st.header("🔍 Matching des Signaux vs Missions")
    if not Path(CSV_MOTS).exists():
        st.info("Pas de fichier de matching (Output/MotsCles_A_Valider.csv).")
    else:
        df = pd.read_csv(CSV_MOTS)
        if df.empty:
            st.info("Aucun résultat.")
        else:
            # Si vous avez un champ Score, sinon calculez via fn_match
            if "Score de correspondance" not in df:
                # Exemple d’appel à votre fonction de matching existante
                df["Score de correspondance"] = df["Titre mission"].apply(
                    lambda t: f"{round(fn_match(t, 'exemple')*100,1)} %"
                )
            df = df.sort_values(by="Score de correspondance", ascending=False)
            st.dataframe(
                df[["Titre de la mission", "Score de correspondance"]], use_container_width=True)

# ————————————————————————————————————————————————————————
#                           Référentiel
# ————————————————————————————————————————————————————————
elif page == "Référentiel":
    st.header("🗂️ Validation Référentiel")

    mode = st.radio("Valider :", ["Mots-clés", "Missions"], horizontal=True)

    if mode == "Mots-clés":
        st.subheader("1. Sélection des mots-clés")
        if not Path(CSV_MOTS).exists():
            st.info("Aucun mots-clés à valider.")
            st.stop()
        df = pd.read_csv(CSV_MOTS)
        if df.empty:
            st.info("Le CSV est vide.")
            st.stop()

        sélection = []
        for champ in ["Origine du besoin", "Type de transformation", "Fonctions concernées", "Secteur / périmètre"]:
            st.markdown(f"#### {champ}")
            for v in sorted(df[champ].dropna().unique()):
                if st.checkbox(v, key=champ+v):
                    sélection.append((champ, v))

        if st.button("✅ Insérer mots-clés validés"):
            tbl = api.table(BASE_ID, "ReferentielMissions")
            for champ, val in sélection:
                tbl.create({
                    "Mot-clé mission":   val,
                    "Champ associé":     champ,
                    "Statut":           "Validé",
                    "Proposé par":      "IA",
                    "Date de proposition": datetime.today().strftime("%Y-%m-%d")
                })
            st.success(f"{len(sélection)} mot(s) inséré(s).")

    else:
        st.subheader("2. Sélection des missions")
        if not Path(CSV_MISSIONS).exists():
            st.info("Aucune mission à valider.")
            st.stop()
        df = pd.read_csv(CSV_MISSIONS)
        if df.empty:
            st.info("Le CSV est vide.")
            st.stop()

        sélection = []
        for i, row in df.iterrows():
            with st.expander(row["Titre mission"]):
                st.write(f"- **Type** : {row['Type de transformation']}")
                st.write(f"- **Fonctions** : {row['Fonctions concernées']}")
                st.write(f"- **Secteur** : {row['Secteur concerné']}")
                st.write(f"- **Durée** : {row['Durée estimée']}")
                if st.checkbox("Valider", key=str(i)):
                    sélection.append(i)

        if st.button("✅ Insérer missions validées"):
            tbl = api.table(BASE_ID, "TypologiesMissions")
            for i in sélection:
                rec = df.iloc[i].to_dict()
                rec["Statut"] = "Validé"
                tbl.create(rec)
            st.success(f"{len(sélection)} mission(s) insérée(s).")

# ————————————————————————————————————————————————————————
#                            Analyse IA (stub)
# ————————————————————————————————————————————————————————
elif page == "Analyse IA":
    st.header("🤖 Interprétation IA des signaux")
    st.info("La démo cloud n’exécute pas l’IA en direct.")
    if st.button("Afficher synthèse d’exemple"):
        st.markdown(fn_interpret())  # Retourne un markdown pré-généré

# ————————————————————————————————————————————————————————
#                        Arborescence Missions
# ————————————————————————————————————————————————————————
elif page == "Arborescence":
    st.header("🧠 Générateur de Mission Type")
    fn_arbo()
