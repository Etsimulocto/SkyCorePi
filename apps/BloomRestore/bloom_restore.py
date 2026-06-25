# bloom_restore.py
# run with: python3 ~/BloomRestore/bloom_restore.py
# path: /home/quarterbitgames/BloomRestore/bloom_restore.py
# description: BloomCore restore point and notes utility for Sky/Architect bench recovery.
# version: 0.1
# format: bloomcore/v1.3

import os
import json
import shutil
import time
import tkinter as tk
from tkinter import messagebox

BASE = os.path.expanduser("~/BloomRestore")
RESTORES = os.path.join(BASE, "restore_points")
LOGS = os.path.join(BASE, "logs")
JOURNAL = os.path.join(LOGS, "bloom_journal.txt")

WATCH_PATHS = [
    os.path.expanduser("~/SkyCam"),
    os.path.expanduser("~/HarnessMap"),
    os.path.expanduser("~/Desktop/SkyCam.desktop"),
    os.path.expanduser("~/Desktop/HarnessMap.desktop"),
    os.path.expanduser("~/.local/share/applications/SkyCam.desktop"),
    os.path.expanduser("~/.local/share/applications/HarnessMap.desktop"),
    os.path.expanduser("~/.config/autostart/skycam.desktop"),
    os.path.expanduser("~/.config/autostart/harnessmap.desktop")
]

BG = "#050505"
FG = "#ffffff"
BTN_BG = "#1b1b1b"
ACTIVE = "#333333"
GOOD = "#7CFF7C"
WARN = "#FFD36A"

os.makedirs(RESTORES, exist_ok=True)
os.makedirs(LOGS, exist_ok=True)

root = tk.Tk()
root.title("🌸 BloomRestore")
root.geometry("760x560")
root.minsize(520, 380)
root.configure(bg=BG)

title = tk.Label(root, text="🌸 BloomRestore", bg=BG, fg=FG, font=("Arial", 20, "bold"))
title.pack(fill="x", pady=8)

status = tk.Label(root, text="Ready", bg=BG, fg=GOOD, font=("Arial", 11, "bold"))
status.pack(fill="x", pady=4)

notes_label = tk.Label(root, text="Restore Notes:", bg=BG, fg=WARN, font=("Arial", 11, "bold"))
notes_label.pack(anchor="w", padx=10)

notes = tk.Text(root, height=7, bg="#111111", fg=FG, insertbackground=FG, relief="flat", font=("Courier", 10))
notes.pack(fill="x", padx=10, pady=6)
notes.insert("1.0", "Stable checkpoint notes here...")

list_frame = tk.Frame(root, bg=BG)
list_frame.pack(fill="both", expand=True, padx=10, pady=8)

scroll = tk.Scrollbar(list_frame)
scroll.pack(side="right", fill="y")

restore_list = tk.Listbox(
    list_frame,
    bg="#111111",
    fg=FG,
    selectbackground="#333333",
    selectforeground=FG,
    yscrollcommand=scroll.set,
    font=("Courier", 10)
)
restore_list.pack(side="left", fill="both", expand=True)
scroll.config(command=restore_list.yview)

def set_status(text, good=True):
    status.config(text=text, fg=GOOD if good else WARN)

def timestamp():
    return time.strftime("%Y-%m-%d_%H-%M-%S")

def write_journal(text):
    with open(JOURNAL, "a") as f:
        f.write("\n" + "=" * 70 + "\n")
        f.write(time.strftime("%Y-%m-%d %H:%M:%S") + "\n")
        f.write(text.strip() + "\n")

def get_restore_dirs():
    items = []
    for name in sorted(os.listdir(RESTORES), reverse=True):
        path = os.path.join(RESTORES, name)
        if os.path.isdir(path):
            items.append(name)
    return items

def refresh_list():
    restore_list.delete(0, tk.END)
    for item in get_restore_dirs():
        restore_list.insert(tk.END, item)

def create_restore():
    note_text = notes.get("1.0", tk.END).strip()
    if not note_text:
        note_text = "No notes entered."

    name = "restore_" + timestamp()
    dest = os.path.join(RESTORES, name)
    files_dir = os.path.join(dest, "files")
    os.makedirs(files_dir, exist_ok=True)

    copied = []
    missing = []

    for src in WATCH_PATHS:
        if os.path.exists(src):
            safe_name = src.replace(os.path.expanduser("~"), "HOME").replace("/", "__")
            target = os.path.join(files_dir, safe_name)
            try:
                if os.path.isdir(src):
                    shutil.copytree(src, target, dirs_exist_ok=True)
                else:
                    shutil.copy2(src, target)
                copied.append(src)
            except Exception as e:
                missing.append(f"{src} ERROR {e}")
        else:
            missing.append(src)

    meta = {
        "name": name,
        "created": time.strftime("%Y-%m-%d %H:%M:%S"),
        "notes": note_text,
        "copied": copied,
        "missing": missing
    }

    with open(os.path.join(dest, "restore_notes.json"), "w") as f:
        json.dump(meta, f, indent=2)

    with open(os.path.join(dest, "README.txt"), "w") as f:
        f.write("BloomCore Restore Point\n")
        f.write("=======================\n\n")
        f.write("Name: " + name + "\n")
        f.write("Created: " + meta["created"] + "\n\n")
        f.write("Notes:\n" + note_text + "\n\n")
        f.write("Copied:\n")
        for c in copied:
            f.write("  OK  " + c + "\n")
        f.write("\nMissing / skipped:\n")
        for m in missing:
            f.write("  --  " + m + "\n")

    write_journal(f"Created restore point: {name}\n\nNotes:\n{note_text}")
    refresh_list()
    set_status(f"Created {name}", True)

def selected_restore():
    sel = restore_list.curselection()
    if not sel:
        return None
    return restore_list.get(sel[0])

def view_notes():
    name = selected_restore()
    if not name:
        set_status("Select a restore point first", False)
        return
    readme = os.path.join(RESTORES, name, "README.txt")
    if os.path.exists(readme):
        os.system(f'xdg-open "{readme}" >/dev/null 2>&1 &')
        set_status("Opened restore notes", True)

def open_folder():
    os.system(f'xdg-open "{RESTORES}" >/dev/null 2>&1 &')
    set_status("Opened restore folder", True)

def open_journal():
    if not os.path.exists(JOURNAL):
        write_journal("Bloom journal created.")
    os.system(f'xdg-open "{JOURNAL}" >/dev/null 2>&1 &')
    set_status("Opened Bloom journal", True)

def restore_selected():
    name = selected_restore()
    if not name:
        set_status("Select a restore point first", False)
        return

    ok = messagebox.askyesno(
        "Restore?",
        "Restore selected files from:\n\n" + name + "\n\nThis will overwrite current SkyCam/HarnessMap files."
    )
    if not ok:
        return

    src_files = os.path.join(RESTORES, name, "files")
    restored = 0

    for safe_name in os.listdir(src_files):
        src = os.path.join(src_files, safe_name)
        original = safe_name.replace("HOME", os.path.expanduser("~"), 1).replace("__", "/")

        try:
            if os.path.isdir(src):
                if os.path.exists(original):
                    shutil.rmtree(original)
                shutil.copytree(src, original)
            else:
                os.makedirs(os.path.dirname(original), exist_ok=True)
                shutil.copy2(src, original)
            restored += 1
        except Exception as e:
            write_journal(f"Restore error from {name}: {original} : {e}")

    write_journal(f"Restored from: {name}\nFiles restored: {restored}")
    set_status(f"Restored {restored} items from {name}", True)

button_bar = tk.Frame(root, bg=BG)
button_bar.pack(fill="x", padx=10, pady=8)

def button(text, command):
    return tk.Button(
        button_bar,
        text=text,
        command=command,
        bg=BTN_BG,
        fg=FG,
        activebackground=ACTIVE,
        activeforeground=FG,
        relief="flat",
        bd=0,
        padx=10,
        pady=9,
        font=("Arial", 10, "bold")
    )

button("➕ CREATE RESTORE", create_restore).pack(side="left", padx=3)
button("♻ RESTORE SELECTED", restore_selected).pack(side="left", padx=3)
button("📝 VIEW NOTES", view_notes).pack(side="left", padx=3)
button("📖 JOURNAL", open_journal).pack(side="left", padx=3)
button("📂 FOLDER", open_folder).pack(side="left", padx=3)

refresh_list()
root.mainloop()
