# -*- coding: utf-8 -*-


import streamlit as st
from streamlit_option_menu import option_menu
from ArboMissions import afficher_arborescence
import subprocess
import streamlit.components.v1 as components
from pathlib import Path
from pyairtable import Api
from dotenv import load_dotenv
import os
import pandas as pd
from datetime import datetime, timedelta, timezone

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


# Titre principal
st.set_page_config(page_title="Veille IA - Transformation", layout="wide")
st.title("Veille Stratégique Assistée par IA")

# Menu latéral avec des onglets
with st.sidebar:
    selected = option_menu(
        menu_title="Navigation",
        options=["Accueil", "Scraping", "Analyse IA",
                 "Référentiel Missions", "Matching"],
        icons=["house", "cloud-download", "cpu", "diagram-3", "shuffle"],
        menu_icon="cast",
        default_index=0
    )

# Contenu de l'onglet Accueil
if selected == "Accueil":
    st.header("Bienvenue dans la plateforme de Veille Stratégique")
  # Affichage de la bannière
    image_path = Path("banner.png")
    if image_path.exists():
        st.image(str(image_path), use_container_width=True)
    else:
        st.warning(
            "Bannière non trouvée. Veuillez placer 'banner.png' dans le dossier du script.")

    st.markdown("""
    Cette application permet de détecter, analyser et valoriser des signaux politiques ou réglementaires 
    grâce à l'intelligence artificielle. Naviguez via le menu pour explorer les différentes fonctions.
    """)

# Contenu de l'onglet Scraping
elif selected == "Scraping":
    st.header("Scraping des sources de veille")

    site_options = {
        "Assemblée Nationale (AN)": True,
        "Sénat": False,
        "Journal Officiel": False,
        "Ministères": False
    }

    active_sites = [site for site, active in site_options.items() if active]
    disabled_sites = [site for site,
                      active in site_options.items() if not active]

    selected_site = st.selectbox(
        "Choisir un site à scraper :",
        options=active_sites + [f"{site} (bientôt)" for site in disabled_sites]
    )

    if "(bientôt)" not in selected_site:
        if st.button("Lancer le scraping"):
            with st.spinner("Scraping en cours..."):
                result = subprocess.run(
                    ["python", "Insertbase3.py"], capture_output=True, text=True)
                if result.stdout:
                    st.code(result.stdout)
                if result.stderr:
                    st.error(result.stderr)
            st.success(f"Scraping de {selected_site} terminé.")

        # Affichage de la capture d'écran si disponible
        screenshot_path = Path("screenshot_an.png")
        if screenshot_path.exists():
            st.image(str(screenshot_path),
                     caption="Aperçu de la page Assemblée Nationale", use_container_width=True)
    else:
        st.info("Cette source sera bientôt disponible.")

# Contenu de l'onglet Analyse IA
elif selected == "Analyse IA":
    st.header("Analyse IA des signaux collectés")

    prompt_path = Path("prompt.txt")
    if prompt_path.exists():
        current_prompt = prompt_path.read_text(encoding="utf-8")
    else:
        current_prompt = ""

    with st.expander("Prompt utilisé par l'IA (modifiable)"):
        new_prompt = st.text_area(
            "Modifier le prompt utilisé pour l'analyse IA :", value=current_prompt, height=300)
        if st.button("Enregistrer le nouveau prompt"):
            prompt_path.write_text(new_prompt, encoding="utf-8")
            st.success("Prompt mis à jour avec succès.")

    if st.button("Lancer l'interprétation IA"):
        with st.spinner("Interprétation IA en cours..."):
            result = subprocess.run(
                ["python", "Interpret3.py"], capture_output=True, text=True
            )
            # Affiche uniquement les titres des missions, urgences, et la détection
            import os

            synthese_path = "synthese_streamlit.md"
            if os.path.exists(synthese_path):
                with open(synthese_path, "r", encoding="utf-8") as f:
                    markdown = f.read()
                st.markdown(markdown)
            else:
                st.warning(
                    "Aucune synthèse détectée. Lancez d'abord une interprétation.")

            if result.stderr:
                st.error(result.stderr)
        st.success("Interprétation terminée")


# Contenu de l'onglet Arborescence Missions
# Onglet Référentiel Missions
elif selected == "Référentiel Missions":
    st.header("🧩 Référentiel Missions")
    st.write("Visualisez l’arborescence des missions-types ou générez automatiquement des missions à partir des signaux détectés.")

    # Initialiser l'état des boutons
    if "afficher_arbo" not in st.session_state:
        st.session_state.afficher_arbo = False
    if "proposer_mission" not in st.session_state:
        st.session_state.proposer_mission = False

    # Deux colonnes côte à côte
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📂 Arborescence des missions")
        if st.button("Afficher l’arborescence"):
            st.session_state.afficher_arbo = True
        if st.session_state.afficher_arbo:
            with st.container():
                afficher_arborescence()

    with col2:
        st.subheader("⚙️ Génération automatique")
        if st.button("Proposer des missions automatiquement"):
            st.session_state.proposer_mission = True
        if st.session_state.proposer_mission:
            with st.container():
                try:
                    result = subprocess.run(
                        ["python", "ProposeMissions.py"], capture_output=True, text=True)
                    if result.returncode == 0:
                        st.success("✅ Propositions générées avec succès.")
                        st.code(result.stdout, language='text')
                    else:
                        st.error("❌ Erreur lors de la génération.")
                        st.code(result.stderr, language='text')
                except Exception as e:
                    st.error(f"Erreur lors de l'exécution : {e}")
        # 🔹 Bloc : Validation des mots-clés proposés dans ReferentielMissions
        st.markdown("---")
        st.subheader("📌 Sélectionner et valider les mots-clés par catégorie")

        file_path = "Output/MotsCles_A_Valider.csv"

        # Charger une seule fois le fichier si non déjà en mémoire
        # Chargement sécurisé
        if "df_propositions" not in st.session_state:
            if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                try:
                    df_temp = pd.read_csv(file_path)
                    if df_temp.empty or df_temp.columns.empty:
                        st.warning(
                            "📂 Le fichier CSV est vide (aucune ligne ou colonne).")
                        st.stop()
                    else:
                        st.session_state.df_propositions = df_temp
                except pd.errors.EmptyDataError:
                    st.warning(
                        "📂 Le fichier CSV ne contient aucune donnée exploitable.")
                    st.stop()
            else:
                st.warning(
                    f"📂 Le fichier '{file_path}' est introuvable ou vide.")
                st.stop()

        df_propositions = st.session_state.df_propositions

        from datetime import datetime
        champs_mots_cles = [
            "Origine du besoin",
            "Type de transformation",
            "Fonctions concernées",
            "Secteur / périmètre"
        ]

        mots_cles_selectionnes = []

        col_gauche, col_droite = st.columns(2)

        def afficher_bloc_selection(col, champ, valeurs):
            with col:
                st.markdown(f"#### 📂 {champ}")
                if not valeurs:
                    st.caption("Aucune valeur disponible.")
                for val in sorted(set(valeurs)):
                    if st.checkbox(val, key=f"{champ}_{val}"):
                        mots_cles_selectionnes.append((val, champ))

        # Affichage réparti
        for i, champ in enumerate(champs_mots_cles):
            valeurs = df_propositions[champ].dropna().tolist()
            if i % 2 == 0:
                afficher_bloc_selection(col_gauche, champ, valeurs)
            else:
                afficher_bloc_selection(col_droite, champ, valeurs)

        # Insertion dans Airtable sans déclencher d'erreurs de champ fermé
        if st.button("✅ Insérer les mots-clés sélectionnés dans ReferentielMissions"):
            table_ref = api.table(BASE_ID, "ReferentielMissions")
            from datetime import datetime
            compteur = 0
            for mot, champ in mots_cles_selectionnes:
                try:
                    table_ref.create({
                        "Mot-clé mission": mot,
                        "Champ associé": champ,  # Nouveau champ texte à créer si besoin dans Airtable
                        "Statut": "Validé",
                        "Proposé par": "IA",
                        "Date de proposition": datetime.today().strftime("%Y-%m-%d")
                    })
                    compteur += 1
                except Exception as e:
                    st.error(
                        f"Erreur d'insertion pour '{mot}' ({champ}) : {e}")
            st.success(
                f"{compteur} mot(s)-clé(s) inséré(s) dans Airtable avec succès.")

        # 🔹 Bloc : Validation des missions proposées dans TypologiesMissions

        st.markdown("---")
        st.subheader("🧩 Sélectionner et valider les missions proposées")

        file_path_missions = "Output/Missions_Proposees.csv"

        # Chargement sécurisé
        if "df_missions" not in st.session_state:
            import os
            import pandas as pd
            if os.path.exists(file_path_missions) and os.path.getsize(file_path_missions) > 0:
                try:
                    df_temp = pd.read_csv(file_path_missions)
                    if df_temp.empty or df_temp.columns.empty:
                        st.warning(
                            "📂 Le fichier CSV est vide (aucune ligne ou colonne).")
                        st.stop()
                    else:
                        st.session_state.df_missions = df_temp
                except pd.errors.EmptyDataError:
                    st.warning(
                        "📂 Le fichier CSV ne contient aucune donnée exploitable.")
                    st.stop()
            else:
                st.warning(
                    f"📂 Le fichier '{file_path_missions}' est introuvable ou vide.")
                st.stop()

        df_missions = st.session_state.df_missions

        missions_selectionnees = []

        # Affichage des missions avec case à cocher
        for idx, row in df_missions.iterrows():
            titre = row["Titre mission"]
            transformation = row["Type de transformation"]
            fonctions = row["Fonctions concernées"]
            secteur = row["Secteur concerné"]
            duree = row["Durée estimée"]

            with st.expander(f"📝 {titre}"):
                st.markdown(f"- **Transformation** : {transformation}")
                st.markdown(f"- **Fonctions concernées** : {fonctions}")
                st.markdown(f"- **Secteur** : {secteur}")
                st.markdown(f"- **Durée estimée** : {duree}")
                if st.checkbox("✅ Valider cette mission", key=f"mission_{idx}"):
                    missions_selectionnees.append(row)

        # Insertion dans Airtable
        if st.button("📤 Insérer les missions sélectionnées dans TypologiesMissions"):
            table_missions = api.table(BASE_ID, "TypologiesMissions")
            from datetime import datetime
            compteur = 0
            for row in missions_selectionnees:
                try:
                    data = row.to_dict()
                    data["Statut"] = "Validé"
                    table_missions.create(data)
                    compteur += 1
                except Exception as e:
                    st.error(
                        f"Erreur d'insertion pour la mission : {row['Titre mission']} — {e}")
            st.success(
                f"{compteur} mission(s) insérée(s) avec succès dans TypologiesMissions.")
            open(file_path_missions, "w").close()
            st.stop()


# Contenu de l'onglet Matching
elif selected == "Matching":
    st.header("🧠 Matching des signaux avec les missions-types")
    st.write(
        "Cet outil permet d'associer les signaux détectés à des missions-types pertinentes.")

    if st.button("Lancer le matching"):
        try:
            # Exécution du script MatchSignals.py
            result = subprocess.run(
                ["python", "MatchSignals.py"], capture_output=True, text=True)
            if result.returncode == 0:
                st.success("✅ Matching effectué avec succès.")

                # Connexion à Airtable
                load_dotenv()
                AIRTABLE_TOKEN = os.getenv("AIRTABLE_TOKEN")
                BASE_ID = os.getenv("AIRTABLE_BASE_ID")
                api = Api(AIRTABLE_TOKEN)
                table_opportunites = api.table(BASE_ID, "OpportunitesPitcher")

                # Lecture des opportunités
                records = table_opportunites.all()
                data = []

                for rec in records:
                    champs = rec.get("fields", {})

                    # Extraction robuste du titre
                    titre = "Sans titre"
                    champ_lie = champs.get(
                        "Mission potentielle (from Signal lié)")
                    if isinstance(champ_lie, list) and len(champ_lie) > 0:
                        if isinstance(champ_lie[0], dict):
                            titre = champ_lie[0].get("name", "Sans titre")
                        elif isinstance(champ_lie[0], str):
                            titre = champ_lie[0]
                    elif isinstance(champ_lie, str):
                        titre = champ_lie

                    # Score avec badge visuel
                    score = champs.get("Scoring match", 0)
                    try:
                        score_num = float(score)
                    except Exception:
                        score_num = 0

                    if score_num > 0.4:
                        badge = "🔥"
                    elif score_num > 0.2:
                        badge = "✅"
                    else:
                        badge = "➖"

                    from datetime import datetime, timedelta

                    # Récupération et parsing du champ "Date"
                    date_str = champs.get("Date")
                    is_new = False
                    if date_str:
                        try:
                            # On extrait uniquement la date (sans heure)
                            date_obj = datetime.fromisoformat(
                                date_str.replace("Z", "+00:00")).date()
                            today = datetime.today().date()
                            is_new = date_obj == today
                        except Exception:
                            pass

                    # Badge "🆕" si mission récente
                    titre_affiche = f"{titre} {'🆕' if is_new else ''}"

                    data.append({
                        "Titre de la mission": titre_affiche,
                        "Score_num": score_num,
                        "Score de correspondance": f"{badge} {round(score_num * 100, 1)} %"
                    })

                # Affichage avec style
                if data:
                    st.markdown("### 🧩 Missions les plus pertinentes")
                    df = pd.DataFrame(data).sort_values(
                        by="Score_num", ascending=False)
                    df_display = df[["Titre de la mission",
                                     "Score de correspondance"]]
                    st.dataframe(
                        df_display.style.set_properties(**{
                            'text-align': 'center',
                            'font-size': '16px'
                        }),
                        use_container_width=True
                    )
                else:
                    st.info("Aucune opportunité trouvée pour le moment.")
            else:
                st.error("❌ Une erreur est survenue pendant le matching.")
                st.code(result.stderr, language='text')
        except Exception as e:
            st.error(f"Erreur lors de l'exécution : {e}")
