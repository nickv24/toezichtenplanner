# toezichtplanner_webapp.py (met vaste duur, vaste aantallen en warme maaltijdtoezicht)
import streamlit as st
from collections import defaultdict
import random
import json
import os

st.set_page_config(page_title="Toezichtplanner", layout="wide")

DAGEN = ["maandag", "dinsdag", "woensdag", "donderdag", "vrijdag"]
TIJDSLOTS = ["08:15", "10:20", "11:25", "11:35", "11:55", "12:25", "14:45"]

LOCATIES_PER_TIJD = {
    "08:15": ["grote speelplaats", "kleuterspeelplaats", "toiletten"],
    "10:20": ["grote speelplaats", "kleuterspeelplaats", "toiletten"],
    "11:25": ["grote speelplaats", "kleuterspeelplaats", "toiletten", "refter", "kleuterrefter"],
    "11:35": ["grote speelplaats"],  # Alleen woensdag
    "11:55": ["grote speelplaats", "kleuterspeelplaats", "toiletten", "refter", "kleuterrefter"],
    "12:25": ["grote speelplaats", "kleuterspeelplaats", "toiletten"],
    "14:45": ["grote speelplaats", "kleuterspeelplaats", "toiletten"]
}

DUUR_PER_TIJD = {
    "08:15": 20,
    "10:20": 15,
    "11:25": 30,
    "11:35": 15,
    "11:55": 30,
    "12:25": 15,
    "14:45": 15
}

AANTAL_PER_LOCATIE = {
    ("11:25", "refter"): 2,
    ("11:55", "refter"): 2,
    ("12:25", "grote speelplaats"): 2,
    ("woensdag", "11:35"): 2
}

LEERKRACHTEN_FILE = "leerkrachten.json"

REGIME_MAX_PUNTEN = {
    "voltijds": 100,
    "4/5": 80,
    "halftijds": 60
}

class Leerkracht:
    def __init__(self, naam, regime, niet_beschikbaarheden, functie, warme_maaltijd=False):
        self.naam = naam
        self.regime = regime
        self.functie = functie
        self.warme_maaltijd = warme_maaltijd
        self.max_punten = REGIME_MAX_PUNTEN[regime]
        self.niet_beschikbaarheden = niet_beschikbaarheden
        self.toegewezen_toezichten = []
        self.totaal_punten = 0

    def is_beschikbaar(self, dag, tijd):
        return tijd not in self.niet_beschikbaarheden.get(dag, [])

    def heeft_nog_capaciteit(self, duur):
        return self.totaal_punten + duur <= self.max_punten

    def voorkeur_score(self, locatie):
        if self.functie == "kleuter" and locatie in ["kleuterspeelplaats", "kleuterrefter", "toiletten"]:
            return 3
        if self.functie == "lager" and locatie in ["grote speelplaats", "refter", "kleuterspeelplaats"]:
            return 2
        if self.functie == "alles":
            return 1
        return 0

    def wijs_toezicht_toe(self, dag, tijd, locatie, duur):
        self.toegewezen_toezichten.append((dag, tijd, locatie))
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
st.title("\ud83d\udcc4 Toezichtplanner Webapp (met vaste waardes en maaltijdtoezicht)")

st.sidebar.header("\ud83c\udfe2 Leerkrachtenbeheer")
if "leerkrachten" not in st.session_state:
    st.session_state.leerkrachten = load_leerkrachten()

namen = [lk.naam for lk in st.session_state.leerkrachten]
selected = st.sidebar.selectbox("Kies of voeg leerkracht toe:", ["Nieuwe leerkracht"] + namen)

if selected == "Nieuwe leerkracht":
    naam = st.sidebar.text_input("Naam", key="new")
    regime = st.sidebar.selectbox("Regime", list(REGIME_MAX_PUNTEN.keys()), index=0)
    functie = st.sidebar.selectbox("Functie", ["lager", "kleuter", "alles"], index=2)
    warme_maaltijd = st.sidebar.checkbox("Toegewezen voor warme maaltijden?", value=False)
    niet_beschikbaarheden = {}
    st.sidebar.markdown("Selecteer momenten waarop deze leerkracht **niet beschikbaar** is:")
    for dag in DAGEN:
        slots = st.sidebar.multiselect(f"{dag}", TIJDSLOTS, key=dag)
        if slots:
            niet_beschikbaarheden[dag] = slots
    if st.sidebar.button("➕ Opslaan"):
        st.session_state.leerkrachten.append(Leerkracht(naam, regime, niet_beschikbaarheden, functie, warme_maaltijd))
        save_leerkrachten(st.session_state.leerkrachten)
        st.sidebar.success(f"{naam} toegevoegd.")
        st.experimental_rerun()
else:
    st.sidebar.write(f"**{selected}** is al opgeslagen. Bewerk in JSON indien nodig.")

# --- Planner ---
if st.button("\ud83d\ude80 Genereer planning"):
    toezichtschema = defaultdict(list)
    conflicten = []

    for lk in st.session_state.leerkrachten:
        lk.toegewezen_toezichten.clear()
        lk.totaal_punten = 0

    for dag in DAGEN:
        for tijd in TIJDSLOTS:
            if dag == "woensdag" and tijd in ["11:25", "11:55", "12:25", "14:45"]:
                continue  # geen toezichten meer na 11:35
            duur = DUUR_PER_TIJD[tijd]
            locaties = LOCATIES_PER_TIJD.get(tijd, [])
            for locatie in locaties:
                aantal = AANTAL_PER_LOCATIE.get((tijd, locatie), 1)
                if dag == "woensdag" and tijd == "11:35":
                    aantal = AANTAL_PER_LOCATIE.get((dag, tijd), 1)
                toezicht_naam = locatie
                kandidaten = [lk for lk in st.session_state.leerkrachten if lk.is_beschikbaar(dag, tijd) and lk.heeft_nog_capaciteit(duur)]
                kandidaten.sort(key=lambda x: -x.voorkeur_score(locatie))
                toegewezen = 0
                for lk in kandidaten:
                    if toegewezen >= aantal:
                        break
                    lk.wijs_toezicht_toe(dag, tijd, locatie, duur)
                    toezichtschema[(dag, tijd, locatie)].append(lk.naam)
                    toegewezen += 1
                if toegewezen < aantal:
                    conflicten.append(f"{dag} {tijd} ({locatie}): tekort ({toegewezen}/{aantal})")

    # Warme maaltijden toewijzen
    for lk in st.session_state.leerkrachten:
        if lk.warme_maaltijd:
            lk.wijs_toezicht_toe("dagelijks", "maaltijd", "warme maaltijden", 30)
            toezichtschema[("dagelijks", "maaltijd", "warme maaltijden")].append(lk.naam)

    st.subheader("\ud83d\udccb Toezichtschema")
    for (dag, tijd, locatie), namen in sorted(toezichtschema.items()):
        st.markdown(f"**{dag} {tijd} - {locatie}**: {', '.join(namen)}")

    if conflicten:
        st.error("⚠️ Onvoldoende leerkrachten voor:")
        for c in conflicten:
            st.markdown(f"- {c}")

    st.subheader("\ud83d\udc69\u200d\ud83c\udfeb Leerkrachtensamenvatting")
    for lk in st.session_state.leerkrachten:
        st.markdown(f"**{lk.naam}** ({lk.functie}, {lk.regime}) – {lk.totaal_punten}/{lk.max_punten} punten")
        st.markdown(f"Toezichten: {lk.toegewezen_toezichten}")

    save_leerkrachten(st.session_state.leerkrachten)
