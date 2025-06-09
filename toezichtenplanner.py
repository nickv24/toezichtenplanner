# toezichtplanner_webapp.py (aangepaste versie)
import streamlit as st
from collections import defaultdict
import random
import json
import os

st.set_page_config(page_title="Toezichtplanner", layout="wide")

DAGEN = ["maandag", "dinsdag", "woensdag", "donderdag", "vrijdag"]
TOEZICHT_DUREN = {"kort": 15, "middel": 20, "lang": 30}

# Tijdslots: standaard
STANDARD_SLOTS = ["08:00", "10:00", "12:00", "14:00", "15:30"]

LEERKRACHTEN_FILE = "leerkrachten.json"

REGIME_MAX_PUNTEN = {
    "voltijds": 100,
    "4/5": 80,
    "halftijds": 60
}

class Leerkracht:
    def __init__(self, naam, regime, niet_beschikbaarheden):
        self.naam = naam
        self.regime = regime
        self.max_punten = REGIME_MAX_PUNTEN[regime]
        self.niet_beschikbaarheden = niet_beschikbaarheden  # dict: {dag: [tijd]}
        self.toegewezen_toezichten = []
        self.totaal_punten = 0

    def is_beschikbaar(self, dag, tijd):
        return tijd not in self.niet_beschikbaarheden.get(dag, [])

    def heeft_nog_capaciteit(self, gewicht):
        return self.totaal_punten + gewicht <= self.max_punten

    def wijs_toezicht_toe(self, dag, tijd, duur):
        self.toegewezen_toezichten.append((dag, tijd))
        self.totaal_punten += duur

def load_leerkrachten():
    if not os.path.exists(LEERKRACHTEN_FILE):
        return []
    with open(LEERKRACHTEN_FILE, "r") as f:
        data = json.load(f)
    return [Leerkracht(**d) for d in data]

def save_leerkrachten(leerkrachten):
    with open(LEERKRACHTEN_FILE, "w") as f:
        json.dump([lk.__dict__ for lk in leerkrachten], f, indent=2)

# --- UI ---

st.title("📄 Toezichtplanner (aangepast)")

# --- Beheer leerkrachten ---
st.sidebar.header("🏢 Leerkrachtenbeheer")
if "leerkrachten" not in st.session_state:
    st.session_state.leerkrachten = load_leerkrachten()

namen = [lk.naam for lk in st.session_state.leerkrachten]
selected = st.sidebar.selectbox("Kies of voeg leerkracht toe:", ["Nieuwe leerkracht"] + namen)

if selected == "Nieuwe leerkracht":
    naam = st.sidebar.text_input("Naam", key="new")
    regime = st.sidebar.selectbox("Regime", list(REGIME_MAX_PUNTEN.keys()), index=0)
    niet_beschikbaarheden = {}
    st.sidebar.markdown("Selecteer momenten waarop deze leerkracht **niet beschikbaar** is:")
    for dag in DAGEN:
        slots = st.sidebar.multiselect(f"{dag}", STANDARD_SLOTS, key=dag)
        if slots:
            niet_beschikbaarheden[dag] = slots
    if st.sidebar.button("➕ Opslaan"):
        st.session_state.leerkrachten.append(Leerkracht(naam, regime, niet_beschikbaarheden))
        save_leerkrachten(st.session_state.leerkrachten)
        st.sidebar.success(f"{naam} toegevoegd.")
        st.experimental_rerun()
else:
    st.sidebar.write(f"**{selected}** is al opgeslagen. Bewerk in JSON indien nodig.")

# --- Planning invoer ---
st.subheader("🗓️ Toezichtmomenten invoeren")

schema_input = {}
for dag in DAGEN:
    st.markdown(f"**{dag.capitalize()}**")
    momenten = []
    for tijd in STANDARD_SLOTS:
        col1, col2 = st.columns([2, 1])
        toezicht_naam = col1.text_input(f"{dag}-{tijd}-naam", placeholder="toezicht naam", key=f"{dag}-{tijd}-naam")
        duur_selectie = col2.selectbox("Duur", options=list(TOEZICHT_DUREN.values()), index=0, key=f"{dag}-{tijd}-duur")
        aantal_nodig = st.slider("Aantal leerkrachten nodig", 1, 5, 1, key=f"{dag}-{tijd}-aantal")
        if toezicht_naam:
            momenten.append((tijd, toezicht_naam, duur_selectie, aantal_nodig))
    schema_input[dag] = momenten

# --- Planner ---
if st.button("🧠 Plan toezichten"):
    toezichtschema = defaultdict(list)
    conflicten = []

    for lk in st.session_state.leerkrachten:
        lk.toegewezen_toezichten.clear()
        lk.totaal_punten = 0

    for dag, momenten in schema_input.items():
        for tijd, toezicht_naam, duur, aantal in momenten:
            kandidaten = [lk for lk in st.session_state.leerkrachten if lk.is_beschikbaar(dag, tijd) and lk.heeft_nog_capaciteit(duur)]
            random.shuffle(kandidaten)
            toegewezen = 0
            for lk in kandidaten:
                if toegewezen >= aantal:
                    break
                lk.wijs_toezicht_toe(dag, tijd, duur)
                toezichtschema[(dag, tijd, toezicht_naam)].append(lk.naam)
                toegewezen += 1
            if toegewezen < aantal:
                conflicten.append(f"{dag} {tijd} ({toezicht_naam}): tekort ({toegewezen}/{aantal})")

    # --- Resultaat ---
    st.subheader("📅 Toezichtschema")
    for (dag, tijd, naam), lijst in sorted(toezichtschema.items()):
        st.markdown(f"**{dag} {tijd} - {naam}**: {', '.join(lijst)}")

    if conflicten:
        st.warning("⚠️ Conflicten:")
        for c in conflicten:
            st.text(f"- {c}")

    st.subheader("👩‍🏫 Overzicht per leerkracht")
    for lk in st.session_state.leerkrachten:
        st.markdown(f"**{lk.naam}** ({lk.regime}) → {lk.toegewezen_toezichten} — {lk.totaal_punten}/{lk.max_punten} punten")

    save_leerkrachten(st.session_state.leerkrachten)
