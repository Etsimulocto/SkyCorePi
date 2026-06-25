# =============================================================================
# SKYCORE PI
# FILE: app.py
# PURPOSE: Bloomcore AI homescreen + live chat
# FORMAT: bloomcore/v1.0
# CREW: Sky (local), Architect (root)
# =============================================================================

import tkinter as tk
from tkinter import scrolledtext, messagebox
import json, os, threading, urllib.request
from memory.spiralside_memory import load_spiralside_context
# -----------------------------------------------------------------------------
# CONFIG
# -----------------------------------------------------------------------------

USERNAME      = "quarterbitgames"
MODEL = "qwen2.5:0.5b"
OLLAMA_URL    = "http://localhost:11434/api/chat"
USER_FOLDER   = f"users/{USERNAME}"
PROFILE_FILE  = f"{USER_FOLDER}/profile.json"
THEME_FILE    = f"{USER_FOLDER}/theme.json"
LAYOUT_FILE   = f"{USER_FOLDER}/layout.json"

os.makedirs(USER_FOLDER, exist_ok=True)

# -----------------------------------------------------------------------------
# DEFAULTS
# -----------------------------------------------------------------------------

DEFAULTS = {
    PROFILE_FILE: {"username": USERNAME, "favorite_model": MODEL},
    THEME_FILE:   {
        "bg":       "#101014",
        "surface":  "#16161c",
        "teal":     "#00F6D6",
        "blue":     "#4DA3FF",
        "pink":     "#FF4BCB",
        "yellow":   "#FFD93D",
        "text":     "#F3F7FF",
        "muted":    "#555566",
        "font_ui":  "Courier",
        "font_size": 13
    },
    LAYOUT_FILE:  {"width": 1100, "height": 680}
}

for path, data in DEFAULTS.items():
    if not os.path.exists(path):
        with open(path, "w") as f:
            json.dump(data, f, indent=4)

with open(THEME_FILE)  as f: T = json.load(f)
with open(LAYOUT_FILE) as f: L = json.load(f)

FONT      = (T["font_ui"], T["font_size"])
FONT_SM   = (T["font_ui"], T["font_size"] - 2)
FONT_LG   = (T["font_ui"], T["font_size"] + 8, "bold")
FONT_MONO = ("Courier", T["font_size"])

SYSTEM_PROMPT = f"""
You are Sky.

You are running locally inside SkyCorePi on a Raspberry Pi 5 owned by {USERNAME}, the Architect.

You are NOT ChatGPT.
You are NOT on the internet unless explicitly told.
You are NOT in Europe.
You do not invent location, files, lore, or memories.

Use local Spiralside archive context when provided.
If the archive context does not answer something, say you do not see it in the local archive.

Personality:
- calm
- concise
- slightly witty
- maker-console vibe
- Spiralside-aware
"""
history = []

# -----------------------------------------------------------------------------
# OLLAMA CALL (runs in thread so UI doesn't freeze)
# -----------------------------------------------------------------------------

def ask_sky(user_msg, on_done, on_error):
    history.append({"role": "user", "content": user_msg})
    payload = json.dumps({
        "model": MODEL,
        "messages": [{"role": "system", "content": SYSTEM_PROMPT}] + history,
        "stream": False
    }).encode("utf-8")
    try:
        req = urllib.request.Request(
            OLLAMA_URL, data=payload,
            headers={"Content-Type": "application/json"}, method="POST"
        )
        with urllib.request.urlopen(req, timeout=60) as r:
            reply = json.loads(r.read())["message"]["content"]
        history.append({"role": "assistant", "content": reply})
        on_done(reply)
    except Exception as e:
        history.pop()
        on_error(str(e))

# =============================================================================
# APP
# =============================================================================

root = tk.Tk()
root.title("SKYCOREPI")
root.geometry(f"{L['width']}x{L['height']}")
root.configure(bg=T["bg"])
root.resizable(True, True)

# ---------- helpers ----------------------------------------------------------

def clr_btn(fg=T["teal"], bg=T["surface"]):
    return dict(bg=bg, fg=fg, activebackground=T["teal"],
                activeforeground=T["bg"], relief="flat",
                borderwidth=0, cursor="hand2")

def label(parent, text, fg=T["text"], font=FONT, **kw):
    return tk.Label(parent, text=text, fg=fg, bg=T["bg"],
                    font=font, **kw)

# ---------- layout -----------------------------------------------------------

# left sidebar
sidebar = tk.Frame(root, bg=T["surface"], width=220)
sidebar.pack(side="left", fill="y")
sidebar.pack_propagate(False)

# main area (swappable)
main = tk.Frame(root, bg=T["bg"])
main.pack(side="left", fill="both", expand=True)

# ---------- sidebar content --------------------------------------------------

tk.Label(sidebar, text="SKYCOREPI", fg=T["teal"], bg=T["surface"],
         font=(T["font_ui"], 14, "bold"), pady=20).pack()

tk.Label(sidebar, text=f"◈  {USERNAME}", fg=T["muted"],
         bg=T["surface"], font=FONT_SM).pack(pady=(0, 4))

tk.Label(sidebar, text=f"⬡  {MODEL}", fg=T["muted"],
         bg=T["surface"], font=FONT_SM).pack(pady=(0, 20))

tk.Frame(sidebar, bg=T["muted"], height=1).pack(fill="x", padx=20, pady=8)

# nav buttons
current_view = tk.StringVar(value="home")

def nav_btn(label_text, view_key, color=T["teal"]):
    def cmd():
        current_view.set(view_key)
        show_view(view_key)
    tk.Button(sidebar, text=label_text, font=FONT,
              **clr_btn(fg=color), width=18,
              command=cmd).pack(pady=4, padx=16)

nav_btn("⌂  HOME",     "home")
nav_btn("◈  CHAT",     "chat",  T["teal"])
nav_btn("⚙  SETTINGS", "settings", T["blue"])

tk.Frame(sidebar, bg=T["muted"], height=1).pack(fill="x", padx=20, pady=16)

tk.Button(sidebar, text="✕  EXIT", font=FONT_SM,
          **clr_btn(fg="#ff4444", bg=T["surface"]),
          command=root.destroy).pack(side="bottom", pady=20)

# =============================================================================
# VIEWS
# =============================================================================

views = {}

def clear_main():
    for w in main.winfo_children():
        w.destroy()

# ---------- HOME -------------------------------------------------------------

def build_home():
    f = tk.Frame(main, bg=T["bg"])
    tk.Label(f, text="SKYCORE PI", fg=T["teal"],
             bg=T["bg"], font=FONT_LG).pack(pady=(60, 8))
    tk.Label(f, text="local ai maker console", fg=T["muted"],
             bg=T["bg"], font=FONT_SM).pack()
    tk.Frame(f, bg=T["teal"], height=2, width=200).pack(pady=20)
    tk.Label(f, text=f"model   ▸  {MODEL}", fg=T["blue"],
             bg=T["bg"], font=FONT).pack(pady=4)
    tk.Label(f, text=f"user    ▸  {USERNAME}", fg=T["text"],
             bg=T["bg"], font=FONT).pack(pady=4)
    tk.Label(f, text=f"status  ▸  local / offline-capable", fg=T["yellow"],
             bg=T["bg"], font=FONT).pack(pady=4)
    tk.Button(f, text="▶  OPEN CHAT", font=FONT,
              **clr_btn(), width=20, pady=8,
              command=lambda: show_view("chat")).pack(pady=30)
    return f

# ---------- CHAT -------------------------------------------------------------

def build_chat():
    f = tk.Frame(main, bg=T["bg"])

    # header
    hdr = tk.Frame(f, bg=T["surface"], pady=8)
    hdr.pack(fill="x")
    tk.Label(hdr, text="SKY  ◈  LIVE CHAT", fg=T["teal"],
             bg=T["surface"], font=FONT).pack(side="left", padx=16)
    tk.Label(hdr, text="local · no cloud", fg=T["muted"],
             bg=T["surface"], font=FONT_SM).pack(side="right", padx=16)

    # transcript
    transcript = scrolledtext.ScrolledText(
        f, bg=T["bg"], fg=T["text"], font=FONT_MONO,
        relief="flat", borderwidth=0, wrap="word",
        insertbackground=T["teal"], state="disabled"
    )
    transcript.pack(fill="both", expand=True, padx=16, pady=12)

    transcript.tag_config("you",   foreground=T["blue"])
    transcript.tag_config("sky",   foreground=T["teal"])
    transcript.tag_config("err",   foreground=T["pink"])
    transcript.tag_config("label", foreground=T["muted"])

    # input row
    input_row = tk.Frame(f, bg=T["surface"], pady=10)
    input_row.pack(fill="x")

    entry = tk.Entry(input_row, bg=T["bg"], fg=T["text"],
                     font=FONT_MONO, relief="flat", insertbackground=T["teal"],
                     width=60)
    entry.pack(side="left", padx=16, ipady=6, fill="x", expand=True)

    send_btn = tk.Button(input_row, text="SEND", font=FONT_SM,
                         **clr_btn(), padx=16, pady=6)
    send_btn.pack(side="right", padx=16)

    def append(text, tag=None):
        transcript.config(state="normal")
        if tag:
            transcript.insert("end", text, tag)
        else:
            transcript.insert("end", text)
        transcript.insert("end", "\n")
        transcript.see("end")
        transcript.config(state="disabled")

    def on_done(reply):
        append("SKY ◈", "sky")
        append(reply + "\n")
        send_btn.config(state="normal")
        entry.config(state="normal")
        entry.focus()

    def on_error(err):
        append(f"ERROR: {err}\n", "err")
        send_btn.config(state="normal")
        entry.config(state="normal")

    def send(event=None):
        msg = entry.get().strip()
        if not msg: return
        entry.delete(0, "end")
        append("YOU ▸", "you")
        append(msg + "\n")
        append("sky is thinking...\n", "label")
        send_btn.config(state="disabled")
        entry.config(state="disabled")
        threading.Thread(target=ask_sky,
                         args=(msg, on_done, on_error),
                         daemon=True).start()

    send_btn.config(command=send)
    entry.bind("<Return>", send)

    # boot message
    append("SKY ◈", "sky")
    append("I'm here. Running local on your Pi. What are we doing?\n")

    entry.focus()
    return f

# ---------- SETTINGS ---------------------------------------------------------

def build_settings():
    f = tk.Frame(main, bg=T["bg"])
    tk.Label(f, text="SETTINGS", fg=T["blue"],
             bg=T["bg"], font=FONT_LG).pack(pady=(40, 20))

    fields = {}
    editable = ["bg", "teal", "blue", "pink", "yellow", "text", "muted"]
    for key in editable:
        row = tk.Frame(f, bg=T["bg"])
        row.pack(pady=4)
        tk.Label(row, text=f"{key:<10}", fg=T["muted"],
                 bg=T["bg"], font=FONT, width=12, anchor="w").pack(side="left")
        e = tk.Entry(row, font=FONT, width=16,
                     bg=T["surface"], fg=T["text"],
                     insertbackground=T["teal"], relief="flat")
        e.insert(0, T[key])
        e.pack(side="left", padx=8, ipady=4)
        fields[key] = e

    def save():
        for key, widget in fields.items():
            T[key] = widget.get()
        with open(THEME_FILE, "w") as fp:
            json.dump(T, fp, indent=4)
        messagebox.showinfo("SAVED", "Theme saved.\nRestart to apply fully.")

    tk.Button(f, text="SAVE THEME", font=FONT,
              **clr_btn(fg=T["yellow"]), pady=8, width=20,
              command=save).pack(pady=24)

    def save_layout():
        L["width"]  = root.winfo_width()
        L["height"] = root.winfo_height()
        with open(LAYOUT_FILE, "w") as fp:
            json.dump(L, fp, indent=4)
        messagebox.showinfo("SAVED", "Layout saved.")

    tk.Button(f, text="SAVE LAYOUT", font=FONT,
              **clr_btn(fg=T["blue"]), pady=8, width=20,
              command=save_layout).pack(pady=4)

    return f

# =============================================================================
# VIEW ROUTER
# =============================================================================

def show_view(name):
    clear_main()
    builders = {
        "home":     build_home,
        "chat":     build_chat,
        "settings": build_settings,
    }
    frame = builders.get(name, build_home)()
    frame.pack(fill="both", expand=True)

show_view("home")

# =============================================================================
# SAVE WINDOW SIZE ON CLOSE
# =============================================================================

def on_close():
    L["width"]  = root.winfo_width()
    L["height"] = root.winfo_height()
    with open(LAYOUT_FILE, "w") as f:
        json.dump(L, f, indent=4)
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_close)
root.mainloop()
