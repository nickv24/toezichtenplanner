# toezichtplanner_webapp.py (met automatische puntenverdeling en rooster)
import streamlit as st
from collections import defaultdict
import random
import json
import os
import pandas as pd

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
    ("12:25", "grote speelplaats"): 2
}

LEERKRACHTEN_FILE = "leerkrachten.json"

class Leerkracht:
    def __init__(self, naam, regime, niet_beschikbaarheden, functie, warme_maaltijd=False):
        self.naam = naam
        self.regime = regime
        self.functie = functie
        self.warme_maaltijd = warme_maaltijd
        self.max_punten = 0  # wordt later berekend
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
st.title("📄 Toezichtplanner Webapp (automatische verdeling + rooster)")

st.sidebar.header("🏫 Leerkrachtenbeheer")
if "leerkrachten" not in st.session_state:
    st.session_state.leerkrachten = load_leerkrachten()

namen = [lk.naam for lk in st.session_state.leerkrachten]
selected = st.sidebar.selectbox("Kies of voeg leerkracht toe:", ["Nieuwe leerkracht"] + namen)

if selected == "Nieuwe leerkracht":
    naam = st.sidebar.text_input("Naam", key="new")
    regime = st.sidebar.selectbox("Regime", ["voltijds", "4/5", "halftijds"], index=0)
    functie = st.sidebar.selectbox("Functie", ["lager", "kleuter", "alles"], index=2)
    warme_maaltijd = st.sidebar.checkbox("Toegewezen voor warme maaltijden?", value=False)
    niet_beschikbaarheden = {}
    st.sidebar.markdown("Selecteer momenten waarop deze leerkracht **niet beschikbaar** is:")
    for dag in DAGEN:
        slots = st.sidebar.multiselect(f"{dag}", TIJDSLOTS, key=dag)
        if slots:
            niet_beschikbaarheden[dag] = slots
if st.sidebar.button("➕ Opslaan"):
    st.session_state.nieuwe_leerkracht_toegevoegd = naam
    st.session_state.leerkrachten.append(Leerkracht(naam, regime, niet_beschikbaarheden, functie, warme_maaltijd))
    save_leerkrachten(st.session_state.leerkrachten)
    st.sidebar.success(f"{naam} toegevoegd.")
    st.rerun()
else:
    lk = next(l for l in st.session_state.leerkrachten if l.naam == selected)
    naam = st.sidebar.text_input("Naam", value=lk.naam)
    regime = st.sidebar.selectbox("Regime", ["voltijds", "4/5", "halftijds"], index=["voltijds", "4/5", "halftijds"].index(lk.regime))
    functie = st.sidebar.selectbox("Functie", ["lager", "kleuter", "alles"], index=["lager", "kleuter", "alles"].index(lk.functie))
    warme_maaltijd = st.sidebar.checkbox("Toegewezen voor warme maaltijden?", value=lk.warme_maaltijd)
    niet_beschikbaarheden = {}
    st.sidebar.markdown("Pas momenten aan waarop deze leerkracht **niet beschikbaar** is:")
    for dag in DAGEN:
        huidige = lk.niet_beschikbaarheden.get(dag, [])
        slots = st.sidebar.multiselect(f"{dag}", TIJDSLOTS, default=huidige, key=f"edit_{dag}")
        if slots:
            niet_beschikbaarheden[dag] = slots

    if st.sidebar.button("💾 Wijzigingen opslaan"):
        lk.naam = naam
        lk.regime = regime
        lk.functie = functie
        lk.warme_maaltijd = warme_maaltijd
        lk.niet_beschikbaarheden = niet_beschikbaarheden
        save_leerkrachten(st.session_state.leerkrachten)
        st.sidebar.success(f"Wijzigingen aan {naam} opgeslagen.")
        st.rerun()

    if st.sidebar.button("🗑️ Verwijder leerkracht"):
        st.session_state.leerkrachten = [l for l in st.session_state.leerkrachten if l.naam != selected]
        save_leerkrachten(st.session_state.leerkrachten)
        st.sidebar.success(f"Leerkracht {selected} verwijderd.")
        st.rerun()

# --- Feedback nieuwe leerkracht ---
if "nieuwe_leerkracht_toegevoegd" in st.session_state:
    st.success(f"✅ Leerkracht '{st.session_state.nieuwe_leerkracht_toegevoegd}' succesvol toegevoegd!")
    del st.session_state.nieuwe_leerkracht_toegevoegd

# --- Planner ---
if st.button("🚀 Genereer planning"):
    toezichtschema = defaultdict(list)
    conflicten = []

    alle_toezichten = []
    for dag in DAGEN:
        for tijd in TIJDSLOTS:
            if dag == "woensdag" and tijd in ["11:25", "11:55", "12:25", "14:45"]:
                continue
            locaties = LOCATIES_PER_TIJD.get(tijd, [])
            for locatie in locaties:
                if (tijd, locatie) in AANTAL_PER_LOCATIE:
                    aantal = AANTAL_PER_LOCATIE[(tijd, locatie)]
                elif dag == "woensdag" and tijd == "11:35":
                    aantal = 2
                else:
    
    for dag, tijd, locatie, duur in alle_toezichten:
        kandidaten = [lk for lk in st.session_state.leerkrachten if lk.is_beschikbaar(dag, tijd) and lk.heeft_nog_capaciteit(duur)]
        kandidaten.sort(key=lambda x: -x.voorkeur_score(locatie))
        if kandidaten:
            gekozen = kandidaten[0]
            gekozen.wijs_toezicht_toe(dag, tijd, locatie, duur)
            toezichtschema[(dag, tijd, locatie)].append(gekozen.naam)
        else:
            conflicten.append(f"{dag} {tijd} ({locatie}): geen geschikte leerkracht")

    for lk in st.session_state.leerkrachten:
        if lk.warme_maaltijd:
            lk.wijs_toezicht_toe("dagelijks", "maaltijd", "warme maaltijden", 30)
            toezichtschema[("dagelijks", "maaltijd", "warme maaltijden")].append(lk.naam)

    st.subheader("📋 Rooster")
    rooster = pd.DataFrame(columns=["Tijd"] + DAGEN)
    for tijd in TIJDSLOTS:
        rij = {"Tijd": tijd}
        for dag in DAGEN:
            items = [f"{loc}: {', '.join(toezichtschema[(dag, tijd, loc)])}" for loc in LOCATIES_PER_TIJD.get(tijd, []) if (dag, tijd, loc) in toezichtschema]
            rij[dag] = "
".join(items).join(items)
        rooster = pd.concat([rooster, pd.DataFrame([rij])], ignore_index=True)
    st.dataframe(rooster)

    csv = rooster.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download rooster als CSV", data=csv, file_name="toezicht_rooster.csv", mime="text/csv")

    if conflicten:
        st.error("⚠️ Onvoldoende leerkrachten voor:")
        for c in conflicten:
            st.markdown(f"- {c}")

    st.subheader("👩‍🏫 Leerkrachtensamenvatting")
    for lk in st.session_state.leerkrachten:
        st.markdown(f"**{lk.naam}** ({lk.functie}, {lk.regime}) – {lk.totaal_punten}/{lk.max_punten} punten")
        st.markdown(f"Toezichten: {lk.toegewezen_toezichten}")

    save_leerkrachten(st.session_state.leerkrachten)
