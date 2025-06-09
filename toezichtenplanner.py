import tkinter as tk
from tkinter import ttk, messagebox
from collections import defaultdict
import random

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

class ToezichtPlannerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Toezichtplanner")

        self.leerkrachten = []
        self.weekschema = defaultdict(list)

        self.setup_widgets()

    def setup_widgets(self):
        frame = ttk.Frame(self.root, padding=10)
        frame.grid(row=0, column=0)

        # Leerkracht toevoegen
        ttk.Label(frame, text="Naam:").grid(row=0, column=0)
        self.naam_entry = ttk.Entry(frame)
        self.naam_entry.grid(row=0, column=1)

        ttk.Label(frame, text="Regime:").grid(row=1, column=0)
        self.regime_var = tk.StringVar()
        self.regime_combobox = ttk.Combobox(frame, textvariable=self.regime_var, values=list(REGIME_MAX_PUNTEN.keys()))
        self.regime_combobox.grid(row=1, column=1)

        ttk.Label(frame, text="Beschikbaarheden:").grid(row=2, column=0)
        self.beschik_vars = {dag: tk.IntVar() for dag in DAGEN}
        for i, dag in enumerate(DAGEN):
            ttk.Checkbutton(frame, text=dag, variable=self.beschik_vars[dag]).grid(row=2, column=1+i)

        ttk.Button(frame, text="Voeg leerkracht toe", command=self.voeg_leerkracht_toe).grid(row=3, column=0, columnspan=3, pady=5)

        # Toezichtschema invoeren
        ttk.Label(frame, text="Toezichtschema:").grid(row=4, column=0, pady=(10, 0))

        self.schema_entries = {}
        for i, dag in enumerate(DAGEN):
            dag_label = ttk.Label(frame, text=dag)
            dag_label.grid(row=5+i, column=0, sticky="w")
            self.schema_entries[dag] = ttk.Entry(frame, width=50)
            self.schema_entries[dag].grid(row=5+i, column=1, columnspan=5)

        ttk.Label(frame, text="(formaat: ochtend=1, middag=2)").grid(row=10, column=1, sticky="w")

        ttk.Button(frame, text="Plan toezichten", command=self.plan_toezichten).grid(row=11, column=0, columnspan=3, pady=10)

        self.result_text = tk.Text(frame, width=80, height=20)
        self.result_text.grid(row=12, column=0, columnspan=10, pady=10)

    def voeg_leerkracht_toe(self):
        naam = self.naam_entry.get()
        regime = self.regime_var.get()
        beschikbaarheden = [dag for dag, var in self.beschik_vars.items() if var.get() == 1]

        if not naam or not regime or not beschikbaarheden:
            messagebox.showerror("Fout", "Vul alle gegevens in.")
            return

        self.leerkrachten.append(Leerkracht(naam, regime, beschikbaarheden))
        messagebox.showinfo("Toegevoegd", f"Leerkracht {naam} toegevoegd.")

        self.naam_entry.delete(0, tk.END)
        self.regime_combobox.set("")
        for var in self.beschik_vars.values():
            var.set(0)

    def parse_weekschema(self):
        self.weekschema.clear()
        for dag in DAGEN:
            inhoud = self.schema_entries[dag].get()
            onderdelen = [stuk.strip() for stuk in inhoud.split(",") if "=" in stuk]
            for item in onderdelen:
                try:
                    naam, gewicht = item.split("=")
                    self.weekschema[dag].append((naam.strip(), int(gewicht.strip())))
                except:
                    messagebox.showerror("Fout", f"Ongeldig toezichtformaat in {dag}: {item}")

    def plan_toezichten(self):
        self.parse_weekschema()

        toezichtschema = defaultdict(str)
        conflicten = []
        for lk in self.leerkrachten:
            lk.toegewezen_toezichten.clear()
            lk.totaal_punten = 0

        for dag in DAGEN:
            for toezicht, gewicht in self.weekschema[dag]:
                kandidaten = [
                    lk for lk in self.leerkrachten
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

        self.result_text.delete("1.0", tk.END)
        self.result_text.insert(tk.END, "--- Toezichtschema ---\n")
        for (dag, toezicht), naam in toezichtschema.items():
            self.result_text.insert(tk.END, f"{dag.capitalize()} - {toezicht}: {naam}\n")

        if conflicten:
            self.result_text.insert(tk.END, "\n⚠️ Conflicten:\n")
            for c in conflicten:
                self.result_text.insert(tk.END, f" - {c}\n")

        self.result_text.insert(tk.END, "\n--- Overzicht per leerkracht ---\n")
        for lk in self.leerkrachten:
            self.result_text.insert(tk.END, f"{lk.naam} ({lk.regime}): {lk.toegewezen_toezichten} - punten: {lk.totaal_punten}/{lk.max_punten}\n")

# Start applicatie
if __name__ == "__main__":
    root = tk.Tk()
    app = ToezichtPlannerApp(root)
    root.mainloop()
