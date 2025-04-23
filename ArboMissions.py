import streamlit as st
from pyairtable import Api
import os

# Config Streamlit


def afficher_arborescence():
    st.title("🧠 Générateur de mission type pour manager de transition")

    st.markdown("""
    Ce module vous aide à cadrer une mission potentielle à partir de signaux détectés
    (veille politique, législative, conjoncture).
    Choisissez les éléments ci-dessous pour générer une fiche mission synthétique.
    """)

    # Airtable setup
    # api_key = os.getenv("AIRTABLE_TOKEN")
    # base_id = os.getenv("AIRTABLE_BASE_ID")
    # table = Api(api_key).table(base_id, "TypologiesMissions")

    # Airtable setup
    api_key = os.getenv("AIRTABLE_TOKEN")
    base_id = os.getenv("AIRTABLE_BASE_ID")
    table_name = "TypologiesMissions"
    api = Api(api_key)
    table = api.table(base_id, table_name)

    # Chargement des valeurs autorisées depuis RéférentielMissions
    table_ref = api.table(base_id, "ReferentielMissions")
    records = table_ref.all()
    records_valides = [r["fields"] for r in records if r.get(
        "fields", {}).get("Statut") == "Validé"]

    def valeurs_uniques(champ):
        return sorted(set(rec.get(champ) for rec in records_valides if champ in rec and rec.get(champ)))

    # Extraire les listes pour chaque champ
    liste_origine = valeurs_uniques("Origine du besoin")
    liste_transformation = valeurs_uniques("Type de transformation")
    liste_fonctions = valeurs_uniques("Fonctions concernées")
    liste_secteurs = valeurs_uniques("Secteur / périmètre")

    # Étape 1 : Origine du besoin
    origine = st.radio(
        "Quelle est la cause principale du besoin de transformation ?", liste_origine)

    # Étape 2 : Type de transformation
    types_transfo = st.multiselect(
        "Quels sont les types de transformation envisagés ?", liste_transformation)

    # Étape 3 : Fonctions concernées
    metiers = st.multiselect(
        "Quelles sont les fonctions principalement concernées ?", liste_fonctions)

    # Étape 4 : Secteur d'activité
    secteur = st.selectbox("Secteur d'activité cible", liste_secteurs)

    # Étape 5 : Taille de l'entreprise
    taille = st.selectbox("Taille de l'entreprise", [
        "Petite (0-49 salariés)",
        "Moyenne (50-249 salariés)",
        "Grande (>250 salariés)",
        "À définir"
    ])

    # Étape 6 : Implantation géographique
    implantation = st.selectbox("Implantation géographique", [
        "Locale",
        "Régionale",
        "Nationale",
        "Internationale",
        "À définir"
    ])

    # Étape 7 : Urgence perçue
    urgence = st.radio("Niveau d'urgence de la mission", [
        "Faible", "Moyenne", "Élevée", "À définir"
    ])

    # Génération
    st.header("5️⃣ Résumé de mission")
    if st.button("🎯 Générer la fiche mission"):

        titre = f"Mission de transformation liée à une {origine.lower()} dans le secteur {secteur}"
        impact = ', '.join(types_transfo)
        fonctions = ', '.join(metiers)

        # Affichage
        st.subheader("📄 Fiche mission proposée")
        st.markdown(f"""
        **Titre** : {titre}

        **Contexte** : Besoin identifié suite à une situation de type *{origine}*, générant une ou plusieurs transformations : *{impact}*.

        **Objectifs** :
        - Identifier les leviers opérationnels
        - Structurer le pilotage de la transformation
        - Accompagner les équipes dans la mise en œuvre

        **Fonctions clés à impliquer** : {fonctions}

        **Périmètre** :
        - Taille de l'entreprise : {taille}
        - Implantation : {implantation}
        - Urgence : {urgence}

        _À approfondir avec un diagnostic plus détaillé._
        """)

        # Enregistrement Airtable
        mots_cles_missions = ", ".join(
            sorted(set(m.lower().strip() for m in metiers + types_transfo)))

        table.create({
            "Titre mission": titre,
            "Type de transformation": impact,
            "Impact métiers": fonctions,  # ✅ Nouveau champ ajouté ici
            "Secteur concerné": secteur,
            "Durée estimée": "À définir",  # ou laisser vide
            "Livrables attendus": "À définir avec le client",
            "Pré-requis internes": f"Entreprise {taille}, site {implantation}, urgence {urgence}",
            "Mots Clés Missions": mots_cles_missions,

        })

        st.success("✅ Mission ajoutée à Airtable avec succès.")
