# toezichtplanner_webapp.py

import streamlit as st
from collections import defaultdict
import random

st.set_page_config(page_title="Toezichtplanner", layout="wide")

DAGEN = ["maandag", "dinsdag", "woensdag", "donderdag", "vrijdag"]
REGIME_MAX_PUNTEN = {
    "voltijds": 10,
    "4/5": 8,
    "halftijds": 6
}

class Leerkracht:
    def __init__(self, naam, regime, beschikbaarheden):
        self.naam = naam
        self.regime = regime
        self.beschikbaarheden = beschikbaarheden
        self.max_punten = REGIME_MAX_PUNTEN[regime]
        self.toegewezen_toezichten = []
        self.totaal_punten = 0

    def is_beschikbaar(self, dag):
        return dag in self.beschikbaarheden

    def heeft_nog_capaciteit(self, gewicht):
        return self.totaal_punten + gewicht <= self.max_punten

    def wijs_toezicht_toe(self, dag, toezicht, gewicht):
        self.toegewezen_toezichten.append((dag, toezicht))
        self.totaal_punten += gewicht

# --- App Interface ---

st.title("📋 Toezichtplanner Webapp")

st.sidebar.header("➕ Voeg leerkrachten toe")
if "leerkrachten" not in st.session_state:
    st.session_state.leerkrachten = []

naam = st.sidebar.text_input("Naam")
regime = st.sidebar.selectbox("Regime", list(REGIME_MAX_PUNTEN.keys()))
beschikbaarheden = st.sidebar.multiselect("Beschikbare dagen", DAGEN)

if st.sidebar.button("➕ Voeg toe"):
    if naam and regime and beschikbaarheden:
        st.session_state.leerkrachten.append(
            Leerkracht(naam, regime, beschikbaarheden)
        )
        st.sidebar.success(f"{naam} toegevoegd.")
    else:
        st.sidebar.error("Vul alle velden in.")

st.subheader("📅 Weekschema voor toezichten")
st.markdown("Voer per dag in welke toezichten er zijn, en geef per toezicht een gewicht.")
st.caption("Bijvoorbeeld: `ochtend=1, middag=2, speelplaats=1`")

weekschema = {}
for dag in DAGEN:
    invoer = st.text_input(f"{dag.capitalize()}", key=dag)
    schema = []
    onderdelen = [stuk.strip() for stuk in invoer.split(",") if "=" in stuk]
    for item in onderdelen:
        try:
            naam, gewicht = item.split("=")
            schema.append((naam.strip(), int(gewicht.strip())))
        except:
            st.warning(f"Ongeldig item in {dag}: {item}")
    weekschema[dag] = schema

if st.button("🧠 Plan toezichten"):
    toezichtschema = defaultdict(str)
    conflicten = []
    for lk in st.session_state.leerkrachten:
        lk.toegewezen_toezichten.clear()
        lk.totaal_punten = 0

    for dag in DAGEN:
        for toezicht, gewicht in weekschema[dag]:
            kandidaten = [
                lk for lk in st.session_state.leerkrachten
                if lk.is_beschikbaar(dag) and lk.heeft_nog_capaciteit(gewicht)
                and (dag, toezicht) not in lk.toegewezen_toezichten
            ]
            random.shuffle(kandidaten)
            if kandidaten:
                gekozen = kandidaten[0]
                gekozen.wijs_toezicht_toe(dag, toezicht, gewicht)
                toezichtschema[(dag, toezicht)] = gekozen.naam
            else:
                conflicten.append(f"{dag} - {toezicht} (geen geschikte leerkracht)")

    st.success("Toezichten gepland!")

    st.subheader("📋 Toezichtschema")
    for (dag, toezicht), naam in sorted(toezichtschema.items()):
        st.markdown(f"**{dag.capitalize()} - {toezicht}:** {naam}")

    if conflicten:
        st.subheader("⚠️ Conflicten")
        for conflict in conflicten:
            st.markdown(f"- {conflict}")

    st.subheader("👩‍🏫 Overzicht per leerkracht")
    for lk in st.session_state.leerkrachten:
        st.markdown(f"**{lk.naam}** ({lk.regime}) → {lk.toegewezen_toezichten} — {lk.totaal_punten}/{lk.max_punten} punten")


