# bloom_doctor.py
# run with: python3 ~/BloomDoctor/bloom_doctor.py
# path: /home/quarterbitgames/BloomDoctor/bloom_doctor.py
# description: BloomCore bench health checker for camera, clipboard, Git, apps, GPIO/I2C/SPI basics.
# version: 0.1
# updated: 2026-06-25
# format: bloomcore/v1.3
# tags: bloomcore, doctor, diagnostics, raspberrypi, bench, recovery
# author: bloomcraft/sky
# notes: Read-only diagnostic app. Does not change hardware state.

import os
import subprocess
import tkinter as tk
from tkinter import scrolledtext

BG = "#050505"
FG = "#ffffff"
BTN_BG = "#1b1b1b"
ACTIVE = "#333333"
GOOD = "#7CFF7C"
WARN = "#FFD36A"
BAD = "#FF7070"

root = tk.Tk()
root.title("🌸 BloomDoctor")
root.geometry("820x620")
root.minsize(520, 380)
root.configure(bg=BG)

title = tk.Label(root, text="🌸 BloomDoctor", bg=BG, fg=FG, font=("Arial", 20, "bold"))
title.pack(fill="x", pady=8)

status = tk.Label(root, text="Ready to scan bench", bg=BG, fg=WARN, font=("Arial", 12, "bold"))
status.pack(fill="x", pady=4)

output = scrolledtext.ScrolledText(root, bg="#111111", fg=FG, insertbackground=FG, font=("Courier", 10), relief="flat")
output.pack(fill="both", expand=True, padx=10, pady=10)

def sh(cmd):
    try:
        result = subprocess.run(cmd, shell=True, text=True, capture_output=True, timeout=8)
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return 999, "", str(e)

def line(text=""):
    output.insert(tk.END, text + "\n")
    output.see(tk.END)

def pass_line(name, detail=""):
    line(f"PASS  {name} {detail}")

def warn_line(name, detail=""):
    line(f"WARN  {name} {detail}")

def fail_line(name, detail=""):
    line(f"FAIL  {name} {detail}")

def exists(path):
    return os.path.exists(os.path.expanduser(path))

def scan():
    output.delete("1.0", tk.END)
    status.config(text="Scanning...", fg=WARN)

    line("=" * 70)
    line("BLOOMDOCTOR BENCH SCAN")
    line("=" * 70)
    line("")

    # Session
    session = os.environ.get("XDG_SESSION_TYPE", "unknown")
    display = os.environ.get("DISPLAY", "")
    wayland = os.environ.get("WAYLAND_DISPLAY", "")
    line("DESKTOP SESSION")
    line("-" * 70)
    line(f"Session: {session}")
    line(f"DISPLAY: {display}")
    line(f"WAYLAND_DISPLAY: {wayland}")
    if session.lower() == "x11":
        pass_line("Desktop", "X11 session detected")
    elif session.lower() == "wayland":
        pass_line("Desktop", "Wayland session detected")
    else:
        warn_line("Desktop", "Unknown session type")
    line("")

    # Clipboard tools
    line("CLIPBOARD")
    line("-" * 70)
    rc, out, err = sh("command -v xclip")
    if rc == 0:
        pass_line("xclip", out)
    else:
        warn_line("xclip", "missing")

    rc, out, err = sh("command -v wl-copy")
    if rc == 0:
        pass_line("wl-copy", out)
    else:
        warn_line("wl-copy", "missing")

    if session.lower() == "x11" and sh("command -v xclip")[0] == 0:
        pass_line("Clipboard ready", "X11 + xclip")
    elif session.lower() == "wayland" and sh("command -v wl-copy")[0] == 0:
        pass_line("Clipboard ready", "Wayland + wl-copy")
    else:
        warn_line("Clipboard", "Session/tool mismatch possible")
    line("")

    # Camera
    line("CAMERA")
    line("-" * 70)
    rc, out, err = sh("v4l2-ctl --list-devices")
    if "Arducam" in out:
        pass_line("Arducam detected")
        for block in out.split("\n\n"):
            if "Arducam" in block:
                line(block)
    else:
        fail_line("Arducam", "not found by v4l2")
        if err:
            line(err)

    rc, out, err = sh("python3 -c \"import cv2; cap=cv2.VideoCapture('/dev/video0',cv2.CAP_V4L2); print(cap.isOpened()); cap.release()\"")
    if "True" in out:
        pass_line("/dev/video0", "OpenCV can open camera")
    else:
        warn_line("/dev/video0", "OpenCV could not open. Camera may be busy or moved.")
    line("")

    # Camera busy check
    rc, out, err = sh("fuser -v /dev/video0 2>&1")
    if out.strip():
        warn_line("Camera busy check", "Something may be using /dev/video0")
        line(out)
    else:
        pass_line("Camera busy check", "No process reported")
    line("")

    # Apps
    line("BLOOMCORE APPS")
    line("-" * 70)
    apps = [
        ("SkyCam", "~/SkyCam/skycam.py"),
        ("HarnessMap", "~/HarnessMap/harness_map.py"),
        ("BloomRestore", "~/BloomRestore/bloom_restore.py"),
        ("BloomDoctor", "~/BloomDoctor/bloom_doctor.py"),
    ]
    for name, path in apps:
        if exists(path):
            pass_line(name, path)
        else:
            fail_line(name, f"missing {path}")
    line("")

    # Desktop icons
    line("DESKTOP ICONS")
    line("-" * 70)
    icons = [
        ("SkyCam desktop", "~/Desktop/SkyCam.desktop"),
        ("HarnessMap desktop", "~/Desktop/HarnessMap.desktop"),
        ("BloomRestore desktop", "~/Desktop/BloomRestore.desktop"),
        ("BloomDoctor desktop", "~/Desktop/BloomDoctor.desktop"),
    ]
    for name, path in icons:
        if exists(path):
            pass_line(name, path)
        else:
            warn_line(name, f"missing {path}")
    line("")

    # Git
    line("GITHUB / GIT")
    line("-" * 70)
    rc, out, err = sh("git --version")
    if rc == 0:
        pass_line("git", out)
    else:
        fail_line("git", "not installed")

    if exists("~/SkyCorePi/.git"):
        pass_line("SkyCorePi repo", "~/SkyCorePi")
        rc, out, err = sh("cd ~/SkyCorePi && git status --short")
        if out.strip():
            warn_line("Git status", "uncommitted changes")
            line(out)
        else:
            pass_line("Git status", "clean")
        rc, out, err = sh("cd ~/SkyCorePi && git remote -v")
        line(out)
    else:
        warn_line("SkyCorePi repo", "not found at ~/SkyCorePi")
    line("")

    # I2C/SPI/GPIO basics
    line("HARDWARE BUS CHECKS")
    line("-" * 70)

    if exists("/dev/i2c-1"):
        pass_line("I2C", "/dev/i2c-1 exists")
        rc, out, err = sh("command -v i2cdetect")
        if rc == 0:
            rc, scanout, scanerr = sh("i2cdetect -y 1")
            line(scanout if scanout else scanerr)
        else:
            warn_line("i2cdetect", "missing package i2c-tools")
    else:
        warn_line("I2C", "/dev/i2c-1 not found")

    if exists("/dev/spidev0.0") or exists("/dev/spidev0.1"):
        pass_line("SPI", "spidev exists")
        rc, out, err = sh("ls -l /dev/spidev*")
        line(out)
    else:
        warn_line("SPI", "No /dev/spidev* found")

    rc, out, err = sh("command -v pinctrl")
    if rc == 0:
        pass_line("pinctrl", out)
    else:
        warn_line("pinctrl", "not found")
    line("")

    # TFT harness file
    line("HARNESS FILES")
    line("-" * 70)
    if exists("~/HarnessMap/data/harness.json"):
        pass_line("Harness JSON", "~/HarnessMap/data/harness.json")
    else:
        fail_line("Harness JSON", "missing")

    if exists("~/SkyCorePi/hardware/harnesses/ILI9488_35_TFT_SPI.md"):
        pass_line("TFT hardware doc", "SkyCorePi hardware doc exists")
    else:
        warn_line("TFT hardware doc", "not in repo yet")
    line("")

    line("=" * 70)
    line("SCAN COMPLETE")
    line("=" * 70)
    status.config(text="Scan complete", fg=GOOD)

def open_repo():
    os.system('xdg-open "$HOME/SkyCorePi" >/dev/null 2>&1 &')

def open_terminal():
    os.system('lxterminal >/dev/null 2>&1 &')

bar = tk.Frame(root, bg=BG)
bar.pack(fill="x", padx=10, pady=8)

def button(text, command):
    return tk.Button(
        bar,
        text=text,
        command=command,
        bg=BTN_BG,
        fg=FG,
        activebackground=ACTIVE,
        activeforeground=FG,
        relief="flat",
        bd=0,
        padx=12,
        pady=10,
        font=("Arial", 10, "bold")
    )

button("🔍 SCAN BENCH", scan).pack(side="left", padx=4)
button("📂 OPEN REPO", open_repo).pack(side="left", padx=4)
button("💻 TERMINAL", open_terminal).pack(side="left", padx=4)

scan()
root.mainloop()
