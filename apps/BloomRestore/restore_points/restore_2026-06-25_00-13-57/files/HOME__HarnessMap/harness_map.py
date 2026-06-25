import json
import os
import tkinter as tk
from tkinter import ttk, messagebox

BASE = os.path.expanduser("~/HarnessMap")
DATA_DIR = os.path.join(BASE, "data")
DATA_FILE = os.path.join(DATA_DIR, "harness.json")
os.makedirs(DATA_DIR, exist_ok=True)

BG = "#050505"
FG = "#ffffff"
BTN_BG = "#1b1b1b"
BTN_FG = "#ffffff"
ENTRY_BG = "#111111"
GOOD = "#7CFF7C"
WARN = "#FFD36A"
LINE = "#333333"

DEFAULT_DATA = {
    "project": "BloomCore Harness",
    "wires": [
        {"label": "GPIO17/P11", "color": "Blue", "gpio": "GPIO17", "pin": "Pin 11", "device": "Rotary Encoder", "signal": "CLK", "notes": "Encoder clock wire"},
        {"label": "GPIO18/P12", "color": "Green", "gpio": "GPIO18", "pin": "Pin 12", "device": "Rotary Encoder", "signal": "DT", "notes": "Encoder data wire"},
        {"label": "GPIO27/P13", "color": "Yellow", "gpio": "GPIO27", "pin": "Pin 13", "device": "Rotary Encoder", "signal": "SW", "notes": "Encoder push switch"},
        {"label": "5V/P2", "color": "Red", "gpio": "5V", "pin": "Pin 2", "device": "Power Rail", "signal": "5V", "notes": "Power"},
        {"label": "GND/P6", "color": "Black", "gpio": "GND", "pin": "Pin 6", "device": "Ground Rail", "signal": "Ground", "notes": "Common ground"}
    ]
}

def load_data():
    if not os.path.exists(DATA_FILE):
        save_data(DEFAULT_DATA)
        return DEFAULT_DATA
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return DEFAULT_DATA

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

data = load_data()

root = tk.Tk()
root.title("🌸 HarnessMap")
root.geometry("980x680")
root.minsize(520, 420)
root.configure(bg=BG)

title = tk.Label(root, text="🌸 BloomCore HarnessMap", bg=BG, fg=FG, font=("Arial", 18, "bold"))
title.pack(fill="x", pady=8)

status = tk.Label(root, text=f"Loaded: {DATA_FILE}", bg=BG, fg=GOOD, font=("Arial", 10, "bold"))
status.pack(fill="x")

main = tk.Frame(root, bg=BG)
main.pack(fill="both", expand=True, padx=8, pady=8)

canvas = tk.Canvas(main, bg=BG, highlightthickness=0)
scroll = ttk.Scrollbar(main, orient="vertical", command=canvas.yview)
content = tk.Frame(canvas, bg=BG)

content.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
canvas.create_window((0, 0), window=content, anchor="nw")
canvas.configure(yscrollcommand=scroll.set)

canvas.pack(side="left", fill="both", expand=True)
scroll.pack(side="right", fill="y")

fields = ["label", "color", "gpio", "pin", "device", "signal", "notes"]
entries = []

def styled_entry(parent, value=""):
    e = tk.Entry(parent, bg=ENTRY_BG, fg=FG, insertbackground=FG, relief="flat", font=("Arial", 10))
    e.insert(0, value)
    return e

def make_button(parent, text, command):
    return tk.Button(parent, text=text, command=command, bg=BTN_BG, fg=BTN_FG, activebackground="#333333", activeforeground=FG, relief="flat", padx=8, pady=6, font=("Arial", 10, "bold"))

def render():
    for widget in content.winfo_children():
        widget.destroy()
    entries.clear()

    header = tk.Frame(content, bg=BG)
    header.pack(fill="x", pady=4)

    for i, name in enumerate(["Label", "Color", "GPIO", "Pin", "Device", "Signal", "Notes", ""]):
        tk.Label(header, text=name, bg=BG, fg=WARN, font=("Arial", 10, "bold"), width=14 if name != "Notes" else 26, anchor="w").grid(row=0, column=i, padx=2)

    for idx, wire in enumerate(data["wires"]):
        row = tk.Frame(content, bg=BG)
        row.pack(fill="x", pady=3)

        row_entries = {}
        for col, field in enumerate(fields):
            width = 14
            if field == "notes":
                width = 26
            e = styled_entry(row, wire.get(field, ""))
            e.config(width=width)
            e.grid(row=0, column=col, padx=2, sticky="ew")
            row_entries[field] = e

        def delete_row(i=idx):
            data["wires"].pop(i)
            render()
            status.config(text="Row deleted. Press SAVE to write file.", fg=WARN)

        make_button(row, "X", delete_row).grid(row=0, column=len(fields), padx=2)
        entries.append(row_entries)

    diagram = tk.Label(content, text=build_diagram(), bg="#080808", fg=FG, justify="left", anchor="w", font=("Courier", 10), padx=12, pady=12)
    diagram.pack(fill="x", pady=12)

def collect():
    data["wires"] = []
    for row in entries:
        wire = {}
        for field in fields:
            wire[field] = row[field].get().strip()
        data["wires"].append(wire)

def add_wire():
    collect()
    data["wires"].append({"label": "", "color": "", "gpio": "", "pin": "", "device": "", "signal": "", "notes": ""})
    render()
    status.config(text="New wire added. Press SAVE to write file.", fg=WARN)

def save():
    collect()
    save_data(data)
    render()
    status.config(text=f"Saved: {DATA_FILE}", fg=GOOD)

def open_data_folder():
    os.system(f'xdg-open "{DATA_DIR}" >/dev/null 2>&1 &')

def build_diagram():
    lines = []
    lines.append("Raspberry Pi 5 Harness Map")
    lines.append("=" * 72)
    for w in data["wires"]:
        label = w.get("label", "")
        color = w.get("color", "")
        gpio = w.get("gpio", "")
        pin = w.get("pin", "")
        device = w.get("device", "")
        signal = w.get("signal", "")
        notes = w.get("notes", "")
        lines.append(f"{pin:<8} {gpio:<8} ── {color:<8} ── {device:<20} {signal:<8} [{label}]")
        if notes:
            lines.append(f"          notes: {notes}")
    return "\n".join(lines)

bottom = tk.Frame(root, bg=BG)
bottom.pack(fill="x", padx=8, pady=8)

make_button(bottom, "➕ ADD WIRE", add_wire).pack(side="left", padx=4)
make_button(bottom, "💾 SAVE", save).pack(side="left", padx=4)
make_button(bottom, "📂 OPEN DATA", open_data_folder).pack(side="left", padx=4)

tk.Label(bottom, text="Edit file by bash: nano ~/HarnessMap/data/harness.json", bg=BG, fg=FG, font=("Arial", 10)).pack(side="right", padx=4)

render()
root.mainloop()
