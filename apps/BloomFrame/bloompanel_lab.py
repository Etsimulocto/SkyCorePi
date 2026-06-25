# bloompanel_lab.py
# run with: python3 bloompanel_lab.py
# path: /home/quarterbitgames/SkyCorePi/apps/BloomFrame/bloompanel_lab.py
# description: Workspace comic/panel lab for slicing multi-image pages, freehand sketch masks, saving projects, generating layouts, applying procedural frames, and exporting reusable panel packs.
# version: 0.2.0
# updated: 2026-06-25
# format: bloomcore/v1.3
# tags: bloomcore, skycorepi, tkinter, pillow, comic, panels, sketch-mask, workspace, project-save, layout-generator, batch-export
# gpio: none
# dependencies: Pillow >= 9.0
# author: bloomcraft/sky
# license: MIT
# hardware: Raspberry Pi 5 / Windows PC / Linux desktop
# notes: Creates a reusable BloomPanel workspace in the user's home folder. Source images are never overwritten. Sketch panels save polygon points into the project file.
# uuid: bc-app-bloompanel-lab-20260625-002

from __future__ import annotations

import json
import math
import os
import platform
import random
import shutil
import subprocess
import tkinter as tk
from dataclasses import asdict, dataclass
from pathlib import Path
from tkinter import colorchooser, filedialog, messagebox, simpledialog, ttk
from typing import Optional

from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter, ImageOps, ImageTk

APP_TITLE = "BloomPanel Lab"
WORKSPACE_NAME = "BloomPanel"


@dataclass
class PanelBox:
    x1: int
    y1: int
    x2: int
    y2: int
    name: str = "Panel"
    points: Optional[list[list[int]]] = None

    def normalized(self) -> "PanelBox":
        nx1, ny1 = min(self.x1, self.x2), min(self.y1, self.y2)
        nx2, ny2 = max(self.x1, self.x2), max(self.y1, self.y2)
        return PanelBox(nx1, ny1, nx2, ny2, self.name, self.points)

    def size(self) -> tuple[int, int]:
        b = self.normalized()
        return b.x2 - b.x1, b.y2 - b.y1

    def is_sketch(self) -> bool:
        return bool(self.points and len(self.points) >= 3)


class BloomPanelLab:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("1640x960")
        self.root.minsize(1220, 780)
        self.root.configure(bg="#0c0c12")

        self.workspace = Path.home() / WORKSPACE_NAME
        self.projects_dir = self.workspace / "Projects"
        self.exports_dir = self.workspace / "Exports"
        self.assets_dir = self.workspace / "Assets"
        self.templates_dir = self.workspace / "Templates"
        self.ensure_workspace()

        self.source: Optional[Image.Image] = None
        self.source_path: Optional[str] = None
        self.project_name = tk.StringVar(value="Untitled")
        self.panels: list[PanelBox] = []
        self.selected_index: Optional[int] = None
        self.scale = 1.0
        self.offset_x = 0
        self.offset_y = 0
        self.drag_start = None
        self.sketch_points_canvas: list[tuple[int, int]] = []
        self.preview_photo = None
        self.selected_photo = None
        self.thumb_photos: list[ImageTk.PhotoImage] = []
        self.vars = {}
        self.color_buttons = {}
        self.last_export: Optional[Path] = None

        self.build_style()
        self.build_ui()
        self.apply_frame_recipe("Core Spear")
        self.refresh_recent_projects()

    def ensure_workspace(self):
        for folder in (self.workspace, self.projects_dir, self.exports_dir, self.assets_dir, self.templates_dir):
            folder.mkdir(parents=True, exist_ok=True)
        recipe_file = self.templates_dir / "frame_recipes.json"
        if not recipe_file.exists():
            recipe_file.write_text(json.dumps(self.default_recipes(), indent=2), encoding="utf-8")

    def build_style(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TFrame", background="#181820")
        style.configure("TLabel", background="#181820", foreground="#eeeeff")
        style.configure("TScale", background="#181820")
        style.configure("TButton", padding=6)

    def var(self, name, kind, value):
        v = kind(value=value)
        self.vars[name] = v
        return v

    def build_ui(self):
        top = tk.Frame(self.root, bg="#20202c", padx=8, pady=7)
        top.pack(fill=tk.X)
        for text, cmd, color in [
            ("Load Source", self.load_source, "#343448"),
            ("New Project", self.new_project, "#343448"),
            ("Save Project", self.save_project, "#343448"),
            ("Load Project", self.load_project_dialog, "#343448"),
            ("Generate Layout", self.generate_layout, "#3a5a99"),
            ("Export Pack", self.export_pack, "#5b2cff"),
            ("Open Workspace", self.open_workspace, "#343448"),
        ]:
            tk.Button(top, text=text, command=cmd, bg=color, fg="white", relief=tk.FLAT, padx=12, pady=7).pack(side=tk.LEFT, padx=3)
        tk.Label(top, text="Project:", bg="#20202c", fg="#ddddee").pack(side=tk.LEFT, padx=(14, 3))
        tk.Entry(top, textvariable=self.project_name, bg="#111118", fg="white", insertbackground="white", width=24).pack(side=tk.LEFT)
        self.status = tk.StringVar(value=f"Workspace: {self.workspace}")
        tk.Label(top, textvariable=self.status, bg="#20202c", fg="#cfd0e6").pack(side=tk.RIGHT, padx=10)

        body = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, sashwidth=7, bg="#0a0a10")
        body.pack(fill=tk.BOTH, expand=True)
        left = tk.Frame(body, bg="#181820", width=390)
        center = tk.Frame(body, bg="#09090f")
        right = tk.Frame(body, bg="#14141d", width=340)
        body.add(left, minsize=360)
        body.add(center, minsize=650)
        body.add(right, minsize=300)

        self.build_left(left)
        self.canvas = tk.Canvas(center, bg="#07070b", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<Configure>", lambda _e: self.redraw_canvas())
        self.canvas.bind("<ButtonPress-1>", self.on_down)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_up)
        self.canvas.bind("<Button-3>", self.delete_panel_at)
        self.build_right(right)

    def build_left(self, parent):
        canvas = tk.Canvas(parent, bg="#181820", highlightthickness=0, width=382)
        bar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=canvas.yview)
        inner = tk.Frame(canvas, bg="#181820")
        inner.bind("<Configure>", lambda _e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw", width=372)
        canvas.configure(yscrollcommand=bar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        bar.pack(side=tk.RIGHT, fill=tk.Y)

        self.add_title(inner, "Tools")
        self.var("tool", tk.StringVar, "Rectangle Panel")
        for label, value in [("▭ Rectangle Panel", "Rectangle Panel"), ("✎ Sketch Panel", "Sketch Panel"), ("↖ Select / Move", "Select")]:
            tk.Radiobutton(inner, text=label, variable=self.vars["tool"], value=value, bg="#181820", fg="#eeeeff", selectcolor="#2b2b3a", activebackground="#181820", command=self.refresh_all).pack(anchor="w", padx=16, pady=2)

        self.add_title(inner, "Sketch Mask")
        self.add_slider(inner, "Stroke width", "sketch_width", 1, 36, 6)
        self.add_slider(inner, "Smoothing", "sketch_smooth", 0, 90, 45)
        self.add_slider(inner, "Simplify", "sketch_simplify", 0, 40, 8)
        self.add_slider(inner, "Mask feather", "mask_feather", 0, 40, 2)
        self.add_slider(inner, "Border wobble", "sketch_wobble", 0, 30, 8)
        self.var("auto_close", tk.BooleanVar, True)
        self.var("clip_to_sketch", tk.BooleanVar, True)
        tk.Checkbutton(inner, text="Auto-close sketch shape", variable=self.vars["auto_close"], bg="#181820", fg="#eeeeff", selectcolor="#2b2b3a", activebackground="#181820").pack(anchor="w", padx=16, pady=2)
        tk.Checkbutton(inner, text="Clip image to sketch mask", variable=self.vars["clip_to_sketch"], bg="#181820", fg="#eeeeff", selectcolor="#2b2b3a", activebackground="#181820", command=self.refresh_all).pack(anchor="w", padx=16, pady=2)
        row = tk.Frame(inner, bg="#181820"); row.pack(fill=tk.X, padx=12, pady=5)
        ttk.Button(row, text="Clear Sketch Panel", command=self.clear_selected_sketch).pack(side=tk.LEFT, padx=2)
        ttk.Button(row, text="Sketch Tool", command=lambda: self.vars["tool"].set("Sketch Panel")).pack(side=tk.LEFT, padx=2)

        self.add_title(inner, "Splitter")
        self.add_slider(inner, "Grid columns", "grid_cols", 1, 12, 3)
        self.add_slider(inner, "Grid rows", "grid_rows", 1, 12, 4)
        self.add_slider(inner, "Gutter X", "gutter_x", 0, 140, 8)
        self.add_slider(inner, "Gutter Y", "gutter_y", 0, 140, 8)
        self.add_slider(inner, "Trim edge", "trim", 0, 160, 6)
        self.add_slider(inner, "Detect dark", "detect_threshold", 0, 250, 52)
        self.add_slider(inner, "Min panel", "min_panel", 20, 900, 120)
        row = tk.Frame(inner, bg="#181820"); row.pack(fill=tk.X, padx=12, pady=5)
        ttk.Button(row, text="Auto Grid", command=self.auto_grid).pack(side=tk.LEFT, padx=2)
        ttk.Button(row, text="Detect Gutters", command=self.auto_detect).pack(side=tk.LEFT, padx=2)
        ttk.Button(row, text="Clear", command=self.clear_panels).pack(side=tk.LEFT, padx=2)

        self.add_title(inner, "Layout Generator")
        self.add_combo(inner, "Layout type", "layout_type", ["Comic Grid", "Golden Spiral", "Big Hero", "Manga Slice", "Broken Glass", "Webtoon Stack", "Chaos Cards"], "Comic Grid")
        self.add_slider(inner, "Layout count", "layout_count", 2, 24, 8)
        ttk.Button(inner, text="Generate Layout From Source", command=self.generate_layout).pack(fill=tk.X, padx=15, pady=5)

        self.add_title(inner, "Frame Forge")
        self.add_combo(inner, "Recipe", "recipe", list(self.default_recipes().keys()) + ["Random Per Panel"], "Core Spear")
        self.vars["recipe"].trace_add("write", lambda *_: self.apply_frame_recipe(self.vars["recipe"].get(), soft=True))
        self.add_slider(inner, "Outer", "outer", 0, 280, 46)
        self.add_slider(inner, "Inner", "inner", 0, 120, 12)
        self.add_slider(inner, "Mat", "mat", 0, 280, 20)
        self.add_slider(inner, "Radius", "radius", 0, 240, 16)
        self.add_slider(inner, "Bevel", "bevel", 0, 70, 8)
        self.add_slider(inner, "Ink rough", "rough", 0, 55, 8)
        self.add_slider(inner, "Glow", "glow", 0, 150, 32)
        self.add_slider(inner, "Shadow", "shadow", 0, 170, 38)
        self.add_slider(inner, "Texture", "texture", 0, 100, 45)
        self.add_slider(inner, "Color boost", "boost", 0, 230, 118)
        self.add_color(inner, "Outer color", "outer_color", "#080810")
        self.add_color(inner, "Inner color", "inner_color", "#ff47d7")
        self.add_color(inner, "Mat color", "mat_color", "#101018")
        self.add_color(inner, "Glow color", "glow_color", "#5cf3ff")

        self.add_title(inner, "Export")
        self.var("contact_sheet", tk.BooleanVar, True)
        self.var("overwrite_pack", tk.BooleanVar, True)
        self.var("number_labels", tk.BooleanVar, True)
        self.var("copy_source", tk.BooleanVar, True)
        for label, name in [("Make contact sheet", "contact_sheet"), ("Reuse same project export folder", "overwrite_pack"), ("Panel number labels", "number_labels"), ("Copy source into project", "copy_source")]:
            tk.Checkbutton(inner, text=label, variable=self.vars[name], bg="#181820", fg="#eeeeff", selectcolor="#2b2b3a", activebackground="#181820", command=self.refresh_selected_preview).pack(anchor="w", padx=16, pady=3)

        self.add_title(inner, "Mouse")
        tk.Label(inner, text="Rectangle tool: left-drag a box\nSketch tool: draw a closed-ish shape\nSelect tool: click a panel\nRight-click: delete panel\nSketch panels export as transparent masks", bg="#181820", fg="#cfcfe0", justify=tk.LEFT).pack(fill=tk.X, padx=16, pady=8)

    def build_right(self, parent):
        tk.Label(parent, text="RECENT PROJECTS", bg="#14141d", fg="#d7c4ff", font=("TkDefaultFont", 12, "bold")).pack(anchor="w", padx=10, pady=(9, 2))
        self.recent_box = tk.Listbox(parent, height=5, bg="#101018", fg="white", selectbackground="#5b2cff", highlightthickness=0)
        self.recent_box.pack(fill=tk.X, padx=8, pady=4)
        self.recent_box.bind("<Double-Button-1>", lambda _e: self.load_selected_recent())

        tk.Label(parent, text="PANEL STRIP", bg="#14141d", fg="#d7c4ff", font=("TkDefaultFont", 12, "bold")).pack(anchor="w", padx=10, pady=(10, 2))
        self.strip_canvas = tk.Canvas(parent, bg="#14141d", highlightthickness=0)
        strip_scroll = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self.strip_canvas.yview)
        self.strip_inner = tk.Frame(self.strip_canvas, bg="#14141d")
        self.strip_inner.bind("<Configure>", lambda _e: self.strip_canvas.configure(scrollregion=self.strip_canvas.bbox("all")))
        self.strip_canvas.create_window((0, 0), window=self.strip_inner, anchor="nw", width=310)
        self.strip_canvas.configure(yscrollcommand=strip_scroll.set)
        self.strip_canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=(6, 0), pady=3)
        strip_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        tk.Label(parent, text="SKETCH / FRAMED PREVIEW", bg="#14141d", fg="#d7c4ff", font=("TkDefaultFont", 12, "bold")).pack(anchor="w", padx=10, pady=(8, 2))
        self.preview_canvas = tk.Canvas(parent, bg="#08080d", highlightthickness=0, height=285)
        self.preview_canvas.pack(fill=tk.X, padx=8, pady=8)

    def add_title(self, parent, text):
        tk.Label(parent, text=text, bg="#181820", fg="#d7c4ff", font=("TkDefaultFont", 12, "bold")).pack(anchor="w", padx=12, pady=(14, 6))

    def add_slider(self, parent, label, name, low, high, value):
        row = tk.Frame(parent, bg="#181820"); row.pack(fill=tk.X, padx=10, pady=4)
        v = self.var(name, tk.IntVar, value)
        tk.Label(row, text=label, bg="#181820", fg="#eeeeff", width=15, anchor="w").pack(side=tk.LEFT)
        ttk.Scale(row, from_=low, to=high, variable=v, command=lambda _v: self.refresh_all()).pack(side=tk.LEFT, fill=tk.X, expand=True)
        tk.Spinbox(row, from_=low, to=high, textvariable=v, width=5, command=self.refresh_all, bg="#262634", fg="white", insertbackground="white", buttonbackground="#343448").pack(side=tk.RIGHT, padx=(6, 0))

    def add_combo(self, parent, label, name, values, value):
        row = tk.Frame(parent, bg="#181820"); row.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(row, text=label, bg="#181820", fg="#eeeeff", width=15, anchor="w").pack(side=tk.LEFT)
        v = self.var(name, tk.StringVar, value)
        combo = ttk.Combobox(row, textvariable=v, values=values, state="readonly")
        combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        combo.bind("<<ComboboxSelected>>", lambda _e: self.refresh_all())

    def add_color(self, parent, label, name, value):
        row = tk.Frame(parent, bg="#181820"); row.pack(fill=tk.X, padx=10, pady=5)
        v = self.var(name, tk.StringVar, value)
        tk.Label(row, text=label, bg="#181820", fg="#eeeeff", width=15, anchor="w").pack(side=tk.LEFT)
        b = tk.Button(row, text=value, bg=value, fg=self.contrast(value), relief=tk.FLAT, width=13)
        b.configure(command=lambda: self.pick_color(name, b)); b.pack(side=tk.LEFT)
        self.color_buttons[name] = b

    def pick_color(self, name, button):
        color = colorchooser.askcolor(self.vars[name].get(), parent=self.root)[1]
        if color:
            self.vars[name].set(color); button.configure(text=color, bg=color, fg=self.contrast(color)); self.refresh_all()

    @staticmethod
    def contrast(color):
        try:
            r, g, b = (int(color[i:i + 2], 16) for i in (1, 3, 5))
            return "black" if r * 299 + g * 587 + b * 114 > 150000 else "white"
        except Exception:
            return "white"

    def refresh_all(self):
        self.redraw_canvas(); self.refresh_selected_preview()

    def load_source(self):
        path = filedialog.askopenfilename(title="Load source page/collage", filetypes=[("Images", "*.png *.jpg *.jpeg *.webp *.bmp *.tif *.tiff"), ("All files", "*")])
        if not path:
            return
        try:
            self.source = Image.open(path).convert("RGBA")
            self.source_path = path
            stem = Path(path).stem[:48]
            if self.project_name.get() == "Untitled":
                self.project_name.set(stem)
            self.panels.clear(); self.selected_index = None
            self.status.set(f"Loaded {Path(path).name} — {self.source.width}×{self.source.height}")
            self.refresh_all(); self.refresh_strip()
        except Exception as error:
            messagebox.showerror(APP_TITLE, f"Could not load image:\n{error}")

    def new_project(self):
        name = simpledialog.askstring(APP_TITLE, "Project name:", initialvalue="BloomPanel Project")
        if not name:
            return
        self.project_name.set(self.safe_name(name)); self.source = None; self.source_path = None
        self.panels.clear(); self.selected_index = None; self.refresh_all(); self.refresh_strip()

    def safe_name(self, name):
        safe = "".join(c if c.isalnum() or c in "-_ ." else "_" for c in name).strip()
        return safe or "BloomPanel_Project"

    def project_file(self):
        return self.projects_dir / f"{self.safe_name(self.project_name.get())}.bloompanel.json"

    def save_project(self):
        data = {
            "format": "bloompanel/v0.2",
            "project_name": self.project_name.get(),
            "source_path": self.source_path,
            "panels": [asdict(p) for p in self.panels],
            "settings": {k: v.get() for k, v in self.vars.items() if k not in {"recipe"}},
            "recipe": self.vars["recipe"].get(),
        }
        path = self.project_file(); path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        if self.source_path and self.vars["copy_source"].get():
            asset_folder = self.assets_dir / self.safe_name(self.project_name.get()); asset_folder.mkdir(parents=True, exist_ok=True)
            try:
                shutil.copy2(self.source_path, asset_folder / Path(self.source_path).name)
            except Exception:
                pass
        self.status.set(f"Saved project: {path}"); self.refresh_recent_projects()

    def load_project_dialog(self):
        path = filedialog.askopenfilename(title="Load BloomPanel project", initialdir=self.projects_dir, filetypes=[("BloomPanel project", "*.bloompanel.json"), ("JSON", "*.json")])
        if path:
            self.load_project(Path(path))

    def refresh_recent_projects(self):
        self.recent_box.delete(0, tk.END)
        for p in sorted(self.projects_dir.glob("*.bloompanel.json"), key=lambda p: p.stat().st_mtime, reverse=True)[:12]:
            self.recent_box.insert(tk.END, p.stem.replace(".bloompanel", ""))

    def load_selected_recent(self):
        selection = self.recent_box.curselection()
        if not selection:
            return
        path = self.projects_dir / f"{self.recent_box.get(selection[0])}.bloompanel.json"
        if path.exists():
            self.load_project(path)

    def load_project(self, path: Path):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            self.project_name.set(data.get("project_name", path.stem))
            self.source_path = data.get("source_path")
            self.source = Image.open(self.source_path).convert("RGBA") if self.source_path and os.path.exists(self.source_path) else None
            self.panels = [PanelBox(**p) for p in data.get("panels", [])]
            recipe = data.get("recipe", "Core Spear")
            if recipe in self.default_recipes() or recipe == "Random Per Panel":
                self.vars["recipe"].set(recipe)
            for k, value in data.get("settings", {}).items():
                if k in self.vars:
                    self.vars[k].set(value)
            self.refresh_color_buttons(); self.selected_index = 0 if self.panels else None
            self.status.set(f"Loaded project: {path.name}"); self.refresh_all(); self.refresh_strip()
        except Exception as error:
            messagebox.showerror(APP_TITLE, f"Could not load project:\n{error}")

    def auto_grid(self):
        if not self.source: return
        cols, rows = self.vars["grid_cols"].get(), self.vars["grid_rows"].get()
        gx, gy, trim = self.vars["gutter_x"].get(), self.vars["gutter_y"].get(), self.vars["trim"].get()
        w, h = self.source.width - trim * 2, self.source.height - trim * 2
        self.panels.clear()
        for r in range(rows):
            for c in range(cols):
                x1 = int(trim + c * w / cols + gx / 2); y1 = int(trim + r * h / rows + gy / 2)
                x2 = int(trim + (c + 1) * w / cols - gx / 2); y2 = int(trim + (r + 1) * h / rows - gy / 2)
                self.panels.append(PanelBox(x1, y1, x2, y2, f"Panel {len(self.panels)+1}"))
        self.selected_index = 0 if self.panels else None; self.refresh_all(); self.refresh_strip()

    def auto_detect(self):
        if not self.source: return
        gray = ImageOps.grayscale(self.source).resize((min(900, self.source.width), min(900, self.source.height)))
        w, h = gray.size; threshold = self.vars["detect_threshold"].get(); pix = gray.load()
        cols = [x for x in range(w) if sum(1 for y in range(h) if pix[x, y] < threshold) > h * 0.72]
        rows = [y for y in range(h) if sum(1 for x in range(w) if pix[x, y] < threshold) > w * 0.72]
        xcuts, ycuts = self.cluster(cols, w), self.cluster(rows, h)
        sx, sy = self.source.width / w, self.source.height / h; trim = self.vars["trim"].get(); minimum = self.vars["min_panel"].get()
        found = []
        for y1, y2 in zip(ycuts[:-1], ycuts[1:]):
            for x1, x2 in zip(xcuts[:-1], xcuts[1:]):
                p = PanelBox(int(x1*sx)+trim, int(y1*sy)+trim, int(x2*sx)-trim, int(y2*sy)-trim, f"Panel {len(found)+1}").normalized()
                if p.size()[0] >= minimum and p.size()[1] >= minimum:
                    found.append(p)
        self.panels = found; self.selected_index = 0 if found else None; self.refresh_all(); self.refresh_strip()

    @staticmethod
    def cluster(values, maximum):
        if not values: return [0, maximum]
        groups = []; a = b = values[0]
        for v in values[1:]:
            if v <= b + 2: b = v
            else: groups.append((a, b)); a = b = v
        groups.append((a, b))
        cuts = [0] + [((a+b)//2) for a, b in groups if 10 < ((a+b)//2) < maximum-10] + [maximum]
        return sorted(set(cuts))

    def generate_layout(self):
        if not self.source:
            messagebox.showinfo(APP_TITLE, "Load a source image first."); return
        kind = self.vars["layout_type"].get(); count = self.vars["layout_count"].get(); trim = self.vars["trim"].get()
        W, H = self.source.width - trim * 2, self.source.height - trim * 2; X, Y = trim, trim; panels: list[PanelBox] = []
        if kind == "Comic Grid":
            cols = max(1, round(math.sqrt(count))); rows = math.ceil(count / cols)
            for i in range(count):
                c, r = i % cols, i // cols
                panels.append(PanelBox(int(X+c*W/cols+8), int(Y+r*H/rows+8), int(X+(c+1)*W/cols-8), int(Y+(r+1)*H/rows-8), f"Panel {i+1}"))
        elif kind == "Big Hero":
            panels.append(PanelBox(X, Y, X+int(W*.62), Y+int(H*.62), "Hero")); side_x = X + int(W*.64)
            for i in range(count-1): panels.append(PanelBox(side_x, Y + int(i * H/(count-1)), X+W, Y + int((i+1) * H/(count-1)) - 8, f"Side {i+1}"))
        elif kind == "Golden Spiral":
            x, y, w, h = X, Y, W, H
            for i in range(count):
                if i % 2 == 0:
                    cut = int(w * .618); panels.append(PanelBox(x, y, x+cut-8, y+h, f"Spiral {i+1}")); x += cut; w -= cut
                else:
                    cut = int(h * .618); panels.append(PanelBox(x, y, x+w, y+cut-8, f"Spiral {i+1}")); y += cut; h -= cut
                if w < 80 or h < 80: break
        elif kind == "Webtoon Stack":
            for i in range(count):
                inset = 20 + (i % 3) * 18; panels.append(PanelBox(X+inset, Y + int(i * H / count) + 10, X+W-inset, Y + int((i+1) * H / count) - 10, f"Stack {i+1}"))
        else:
            for i in range(count):
                rw = random.randint(max(80, W//5), max(100, W//2)); rh = random.randint(max(80, H//6), max(100, H//3))
                x1 = random.randint(X, max(X, X+W-rw)); y1 = random.randint(Y, max(Y, Y+H-rh))
                if kind == "Broken Glass":
                    pts = [[x1, y1+random.randint(0, rh//3)], [x1+rw-random.randint(0, rw//4), y1], [x1+rw, y1+rh-random.randint(0, rh//4)], [x1+random.randint(0, rw//3), y1+rh]]
                    panels.append(self.panel_from_points(pts, f"Shard {i+1}"))
                else:
                    panels.append(PanelBox(x1, y1, x1+rw, y1+rh, f"Chaos {i+1}"))
        self.panels = panels; self.selected_index = 0 if panels else None; self.refresh_all(); self.refresh_strip()

    def clear_panels(self):
        self.panels.clear(); self.selected_index = None; self.refresh_all(); self.refresh_strip()

    def clear_selected_sketch(self):
        if self.selected_index is None or self.selected_index >= len(self.panels): return
        p = self.panels[self.selected_index]
        self.panels[self.selected_index] = PanelBox(p.x1, p.y1, p.x2, p.y2, p.name, None)
        self.refresh_all(); self.refresh_strip()

    def canvas_to_image(self, x, y):
        if self.scale <= 0: return 0, 0
        return int((x - self.offset_x) / self.scale), int((y - self.offset_y) / self.scale)

    def image_to_canvas(self, x, y):
        return int(x * self.scale + self.offset_x), int(y * self.scale + self.offset_y)

    def panel_at(self, cx, cy):
        ix, iy = self.canvas_to_image(cx, cy)
        for i in reversed(range(len(self.panels))):
            p = self.panels[i].normalized()
            if p.x1 <= ix <= p.x2 and p.y1 <= iy <= p.y2:
                return i
        return None

    def on_down(self, event):
        if not self.source: return
        tool = self.vars["tool"].get()
        if tool == "Select":
            hit = self.panel_at(event.x, event.y)
            if hit is not None:
                self.selected_index = hit; self.refresh_all(); self.refresh_strip()
            return
        hit = self.panel_at(event.x, event.y)
        if hit is not None and tool == "Rectangle Panel":
            self.selected_index = hit; self.refresh_all(); self.refresh_strip(); return
        self.drag_start = (event.x, event.y)
        self.sketch_points_canvas = [(event.x, event.y)]
        self.canvas.delete("temp")

    def on_drag(self, event):
        if not self.drag_start: return
        tool = self.vars["tool"].get()
        if tool == "Sketch Panel":
            last = self.sketch_points_canvas[-1]
            if abs(event.x - last[0]) + abs(event.y - last[1]) >= 3:
                self.sketch_points_canvas.append((event.x, event.y))
                self.canvas.create_line(last[0], last[1], event.x, event.y, fill="#fff36d", width=max(1, self.vars["sketch_width"].get()), tags="temp", capstyle=tk.ROUND, smooth=True)
        else:
            self.canvas.delete("temp"); x, y = self.drag_start
            self.canvas.create_rectangle(x, y, event.x, event.y, outline="#63f6ff", width=3, dash=(6, 4), tags="temp")

    def on_up(self, event):
        if not self.source or not self.drag_start: return
        tool = self.vars["tool"].get()
        if tool == "Sketch Panel":
            self.sketch_points_canvas.append((event.x, event.y))
            image_points = [list(self.canvas_to_image(x, y)) for x, y in self.sketch_points_canvas]
            image_points = self.clean_points(image_points)
            if len(image_points) >= 3:
                p = self.panel_from_points(image_points, f"Sketch {len(self.panels)+1}")
                if p.size()[0] > 30 and p.size()[1] > 30:
                    self.panels.append(p); self.selected_index = len(self.panels)-1
        else:
            x0, y0 = self.drag_start; x1, y1 = self.canvas_to_image(x0, y0); x2, y2 = self.canvas_to_image(event.x, event.y)
            p = PanelBox(x1, y1, x2, y2, f"Panel {len(self.panels)+1}").normalized()
            p.x1 = max(0, min(self.source.width, p.x1)); p.x2 = max(0, min(self.source.width, p.x2)); p.y1 = max(0, min(self.source.height, p.y1)); p.y2 = max(0, min(self.source.height, p.y2))
            if p.size()[0] > 30 and p.size()[1] > 30:
                self.panels.append(p); self.selected_index = len(self.panels)-1
        self.drag_start = None; self.sketch_points_canvas = []; self.canvas.delete("temp"); self.refresh_all(); self.refresh_strip()

    def clean_points(self, points: list[list[int]]) -> list[list[int]]:
        if not points: return []
        simplify = max(1, self.vars["sketch_simplify"].get())
        filtered = []
        for p in points:
            if not filtered or abs(p[0]-filtered[-1][0]) + abs(p[1]-filtered[-1][1]) >= simplify:
                filtered.append(p)
        smooth = self.vars["sketch_smooth"].get()
        if smooth > 0 and len(filtered) > 4:
            rounds = max(1, smooth // 30)
            for _ in range(rounds):
                new = [filtered[0]]
                for i in range(1, len(filtered)-1):
                    x = int((filtered[i-1][0] + filtered[i][0]*2 + filtered[i+1][0]) / 4)
                    y = int((filtered[i-1][1] + filtered[i][1]*2 + filtered[i+1][1]) / 4)
                    new.append([x, y])
                new.append(filtered[-1]); filtered = new
        if self.vars["auto_close"].get() and filtered[0] != filtered[-1]:
            filtered.append(filtered[0])
        return filtered

    def panel_from_points(self, points: list[list[int]], name: str) -> PanelBox:
        xs = [p[0] for p in points]; ys = [p[1] for p in points]
        x1 = max(0, min(xs)); y1 = max(0, min(ys)); x2 = min(self.source.width, max(xs)); y2 = min(self.source.height, max(ys))
        clipped = [[max(0, min(self.source.width, p[0])), max(0, min(self.source.height, p[1]))] for p in points]
        return PanelBox(x1, y1, x2, y2, name, clipped)

    def delete_panel_at(self, event):
        hit = self.panel_at(event.x, event.y)
        if hit is not None:
            del self.panels[hit]; self.selected_index = None; self.refresh_all(); self.refresh_strip()

    def redraw_canvas(self):
        self.canvas.delete("all")
        if not self.source:
            self.canvas.create_text(self.canvas.winfo_width()//2, self.canvas.winfo_height()//2, text="LOAD SOURCE\nthen draw rectangles, sketch masks, detect gutters, or generate layouts", fill="#77778c", font=("TkDefaultFont", 22, "bold"), justify=tk.CENTER)
            return
        cw, ch = max(1, self.canvas.winfo_width()), max(1, self.canvas.winfo_height())
        self.scale = min((cw-30)/self.source.width, (ch-30)/self.source.height, 1.0)
        preview = self.source.resize((int(self.source.width*self.scale), int(self.source.height*self.scale)), Image.Resampling.LANCZOS)
        self.offset_x, self.offset_y = (cw-preview.width)//2, (ch-preview.height)//2
        self.preview_photo = ImageTk.PhotoImage(preview)
        self.canvas.create_image(self.offset_x, self.offset_y, image=self.preview_photo, anchor="nw")
        for i, p in enumerate(self.panels):
            b = p.normalized(); color = "#fff36d" if i == self.selected_index else "#63f6ff"
            if p.is_sketch():
                pts = [self.image_to_canvas(x, y) for x, y in p.points]
                flat = [n for point in pts for n in point]
                self.canvas.create_polygon(flat, outline=color, fill="", width=3, smooth=True)
                lx, ly = pts[0]
            else:
                x1, y1 = self.image_to_canvas(b.x1, b.y1); x2, y2 = self.image_to_canvas(b.x2, b.y2)
                self.canvas.create_rectangle(x1, y1, x2, y2, outline=color, width=3); lx, ly = x1, y1
            self.canvas.create_rectangle(lx, ly, lx+64, ly+25, fill="#000", outline=color)
            self.canvas.create_text(lx+32, ly+12, text=str(i+1), fill=color, font=("TkDefaultFont", 11, "bold"))
        self.status.set(f"{len(self.panels)} panels | {self.project_name.get()} | Tool: {self.vars['tool'].get()}")

    def refresh_strip(self):
        for child in self.strip_inner.winfo_children(): child.destroy()
        self.thumb_photos.clear()
        if not self.source or not self.panels:
            tk.Label(self.strip_inner, text="No panels yet.", bg="#14141d", fg="#aaaabb").pack(padx=10, pady=10); return
        for i, p in enumerate(self.panels):
            crop = self.render_panel_crop(p, transparent=False); crop.thumbnail((185, 105), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(crop); self.thumb_photos.append(photo)
            bg = "#34344a" if i == self.selected_index else "#20202c"
            card = tk.Frame(self.strip_inner, bg=bg, padx=5, pady=5); card.pack(fill=tk.X, padx=8, pady=5)
            tk.Label(card, image=photo, bg=bg).pack(side=tk.LEFT)
            kind = "SKETCH" if p.is_sketch() else "RECT"
            tk.Button(card, text=f"{i+1:02d} {kind}\n{p.size()[0]}×{p.size()[1]}", command=lambda n=i: self.select_panel(n), bg=bg, fg="white", relief=tk.FLAT, justify=tk.LEFT).pack(side=tk.LEFT, padx=8)

    def select_panel(self, i):
        self.selected_index = i; self.refresh_all(); self.refresh_strip()

    def refresh_selected_preview(self):
        self.preview_canvas.delete("all")
        if not self.source or self.selected_index is None or self.selected_index >= len(self.panels):
            self.preview_canvas.create_text(160, 135, text="Select panel", fill="#77778c", font=("TkDefaultFont", 14, "bold")); return
        img = self.frame_panel(self.panels[self.selected_index], self.selected_index)
        img.thumbnail((315, 265), Image.Resampling.LANCZOS)
        self.selected_photo = ImageTk.PhotoImage(img)
        self.preview_canvas.create_image(160, 140, image=self.selected_photo, anchor="center")

    def clamp(self, p):
        b = p.normalized()
        return (max(0, min(self.source.width, b.x1)), max(0, min(self.source.height, b.y1)), max(0, min(self.source.width, b.x2)), max(0, min(self.source.height, b.y2)))

    def render_panel_crop(self, panel: PanelBox, transparent=True) -> Image.Image:
        crop = self.source.crop(self.clamp(panel)).convert("RGBA")
        if panel.is_sketch() and self.vars["clip_to_sketch"].get():
            b = panel.normalized()
            relative = [(x - b.x1, y - b.y1) for x, y in panel.points]
            mask = Image.new("L", crop.size, 0)
            draw = ImageDraw.Draw(mask)
            draw.polygon(relative, fill=255)
            feather = self.vars["mask_feather"].get()
            if feather > 0:
                mask = mask.filter(ImageFilter.GaussianBlur(feather))
            crop.putalpha(mask)
            outline = Image.new("RGBA", crop.size, (0, 0, 0, 0))
            od = ImageDraw.Draw(outline)
            wobble = self.vars["sketch_wobble"].get()
            line_points = relative
            for offset in range(max(1, self.vars["sketch_width"].get() // 3)):
                jittered = [(x + random.randint(-wobble, wobble), y + random.randint(-wobble, wobble)) for x, y in line_points]
                od.line(jittered, fill=(0, 0, 0, 200), width=max(1, self.vars["sketch_width"].get()), joint="curve")
            crop = Image.alpha_composite(crop, outline)
        elif not transparent:
            bg = Image.new("RGBA", crop.size, "#101018")
            bg.alpha_composite(crop)
            crop = bg
        return crop

    def export_pack(self):
        if not self.source or not self.panels:
            messagebox.showinfo(APP_TITLE, "Load source and create panels first."); return
        project = self.safe_name(self.project_name.get()); folder = self.exports_dir / project
        if folder.exists() and not self.vars["overwrite_pack"].get():
            n = 2
            while (self.exports_dir / f"{project}_{n:02d}").exists(): n += 1
            folder = self.exports_dir / f"{project}_{n:02d}"
        folder.mkdir(parents=True, exist_ok=True)
        if self.vars["overwrite_pack"].get():
            for old in folder.glob("*.png"): old.unlink()
        exported = []
        for i, p in enumerate(self.panels):
            framed = self.frame_panel(p, i)
            path = folder / f"panel_{i+1:02d}.png"; framed.save(path); exported.append((i, framed.copy()))
        if self.vars["contact_sheet"].get(): self.make_contact_sheet(exported).save(folder / "_CONTACT_SHEET.png")
        manifest = {"project": self.project_name.get(), "source": self.source_path, "count": len(exported), "recipe": self.vars["recipe"].get(), "sketch_panels": sum(1 for p in self.panels if p.is_sketch())}
        (folder / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        self.last_export = folder; self.save_project(); messagebox.showinfo(APP_TITLE, f"Exported pack:\n{folder}")

    def frame_panel(self, panel: PanelBox, index: int) -> Image.Image:
        return self.frame_image(self.render_panel_crop(panel, transparent=True), index)

    def frame_image(self, image: Image.Image, index: int):
        recipe_name = self.vars["recipe"].get()
        recipe = random.choice(list(self.default_recipes().values())) if recipe_name == "Random Per Panel" else self.collect_current_recipe()
        image = ImageEnhance.Color(image).enhance(recipe["boost"] / 100)
        image = ImageEnhance.Contrast(image).enhance(1.08)
        image = ImageOps.expand(image, recipe["mat"], recipe["mat_color"])
        image = ImageOps.expand(image, recipe["inner"], recipe["inner_color"])
        image = self.rough_expand(image, recipe["outer"], recipe["outer_color"], recipe["rough"])
        image = self.add_texture(image, recipe["outer"], recipe["texture"])
        image = self.add_bevel(image, recipe["bevel"])
        if self.vars["number_labels"].get(): image = self.add_label(image, index+1)
        if recipe["radius"] > 0 and not self.panels[index].is_sketch(): image = self.rounded(image, recipe["radius"])
        return self.shadow_glow(image, recipe["shadow"], recipe["glow"], recipe["glow_color"])

    def collect_current_recipe(self):
        return {k: self.vars[k].get() for k in ["outer", "inner", "mat", "radius", "bevel", "rough", "glow", "shadow", "texture", "boost", "outer_color", "inner_color", "mat_color", "glow_color"]}

    def rough_expand(self, image, border, color, rough):
        if border <= 0: return image
        img = ImageOps.expand(image, border, color)
        if rough <= 0: return img
        draw = ImageDraw.Draw(img)
        for _ in range(max(18, (img.width+img.height)//15)):
            side = random.choice("tblr")
            if side in "tb":
                y = random.randint(0, border-1) if side == "t" else random.randint(img.height-border, img.height-1)
                x = random.randint(0, img.width); draw.line((x, y, min(img.width, x+random.randint(15,120)), y+random.randint(-rough, rough)), fill=(0,0,0,135), width=random.randint(1, max(1, rough//3)))
            else:
                x = random.randint(0, border-1) if side == "l" else random.randint(img.width-border, img.width-1)
                y = random.randint(0, img.height); draw.line((x, y, x+random.randint(-rough, rough), min(img.height, y+random.randint(15,120))), fill=(0,0,0,135), width=random.randint(1, max(1, rough//3)))
        return img

    def add_texture(self, image, border, amount):
        if amount <= 0 or border <= 0: return image
        overlay = Image.new("RGBA", image.size, (0,0,0,0)); draw = ImageDraw.Draw(overlay); alpha = int(amount*1.25)
        for x in range(-image.height, image.width, 18): draw.line((x, 0, x+image.height, image.height), fill=(255,255,255,alpha), width=1)
        for y in range(0, image.height, 37): draw.line((0, y, image.width, y), fill=(0,0,0,alpha//2), width=1)
        mask = Image.new("L", image.size, 255); ImageDraw.Draw(mask).rectangle((border, border, image.width-border, image.height-border), fill=0)
        overlay.putalpha(ImageChops.multiply(overlay.getchannel("A"), mask))
        return Image.alpha_composite(image, overlay)

    @staticmethod
    def add_bevel(image, bevel):
        if bevel <= 0: return image
        overlay = Image.new("RGBA", image.size, (0,0,0,0)); draw = ImageDraw.Draw(overlay)
        for i in range(bevel):
            a = int(95*(1-i/max(1, bevel)))
            draw.line((i,i,image.width-i-1,i), fill=(255,255,255,a)); draw.line((i,i,i,image.height-i-1), fill=(255,255,255,a))
            draw.line((i,image.height-i-1,image.width-i-1,image.height-i-1), fill=(0,0,0,a)); draw.line((image.width-i-1,i,image.width-i-1,image.height-i-1), fill=(0,0,0,a))
        return Image.alpha_composite(image, overlay)

    @staticmethod
    def rounded(image, radius):
        mask = Image.new("L", image.size, 0); ImageDraw.Draw(mask).rounded_rectangle((0,0,image.width-1,image.height-1), radius=radius, fill=255)
        image = image.copy(); image.putalpha(mask); return image

    @staticmethod
    def shadow_glow(image, shadow, glow, glow_color):
        margin = max(22, shadow+glow+26); canvas = Image.new("RGBA", (image.width+margin*2, image.height+margin*2), (0,0,0,0)); alpha = image.getchannel("A")
        if glow > 0:
            ga = alpha.filter(ImageFilter.MaxFilter(max(3, glow*2+1))).filter(ImageFilter.GaussianBlur(glow)); gl = Image.new("RGBA", image.size, glow_color); gl.putalpha(ga.point(lambda p: int(p*.72))); canvas.alpha_composite(gl, (margin, margin))
        if shadow > 0:
            sa = alpha.filter(ImageFilter.MaxFilter(max(3, shadow+1))).filter(ImageFilter.GaussianBlur(max(1, shadow//2))); sh = Image.new("RGBA", image.size, "#000000"); sh.putalpha(sa.point(lambda p: int(p*.62))); canvas.alpha_composite(sh, (margin+shadow//3, margin+shadow//3))
        canvas.alpha_composite(image, (margin, margin)); return canvas

    @staticmethod
    def add_label(image, number):
        image = image.copy(); draw = ImageDraw.Draw(image); pad = max(10, image.width//100)
        draw.rounded_rectangle((pad, pad, pad+104, pad+31), radius=8, fill="#050509", outline="#5cf3ff", width=2)
        draw.text((pad+10, pad+8), f"PANEL {number:02d}", fill="#ffffff")
        return image

    def make_contact_sheet(self, exported):
        cols = min(3, len(exported)); rows = math.ceil(len(exported)/cols); sheet = Image.new("RGBA", (cols*390+30, rows*320+80), "#07070c"); draw = ImageDraw.Draw(sheet); draw.text((24, 18), f"BloomPanel Lab — {self.project_name.get()}", fill="#d7c4ff")
        for n, (i, img) in enumerate(exported):
            thumb = img.copy(); thumb.thumbnail((330, 240), Image.Resampling.LANCZOS); tile = Image.new("RGBA", (370, 300), "#101018"); tile.alpha_composite(thumb, ((370-thumb.width)//2, 22)); d = ImageDraw.Draw(tile); d.rounded_rectangle((12,12,358,288), radius=18, outline="#5cf3ff", width=2); d.text((22,263), f"Panel {i+1:02d}", fill="#fff")
            sheet.alpha_composite(tile, (20+(n%cols)*390, 60+(n//cols)*320))
        return sheet

    def default_recipes(self):
        return {
            "Core Spear": dict(outer=46, inner=12, mat=20, radius=16, bevel=8, rough=8, glow=32, shadow=38, texture=45, boost=122, outer_color="#080810", inner_color="#ff47d7", mat_color="#101018", glow_color="#5cf3ff"),
            "Long Glitter": dict(outer=30, inner=8, mat=18, radius=48, bevel=4, rough=18, glow=18, shadow=36, texture=55, boost=135, outer_color="#ff4fd8", inner_color="#ffee55", mat_color="#ffffff", glow_color="#8b5cf6"),
            "Walnut Relic": dict(outer=92, inner=7, mat=28, radius=8, bevel=18, rough=5, glow=0, shadow=40, texture=75, boost=108, outer_color="#4a2818", inner_color="#bc8a5f", mat_color="#e8dcc4", glow_color="#ffffff"),
            "Sky Glass": dict(outer=34, inner=3, mat=14, radius=46, bevel=12, rough=0, glow=30, shadow=20, texture=18, boost=116, outer_color="#0a1020", inner_color="#9be7ff", mat_color="#101827", glow_color="#84f7ff"),
            "Science Snap": dict(outer=20, inner=4, mat=40, radius=8, bevel=3, rough=4, glow=8, shadow=30, texture=10, boost=110, outer_color="#f1e7cf", inner_color="#7c5cff", mat_color="#fff6dc", glow_color="#7c5cff"),
            "Void Shrine": dict(outer=60, inner=4, mat=10, radius=24, bevel=10, rough=3, glow=45, shadow=48, texture=50, boost=125, outer_color="#030514", inner_color="#7986ff", mat_color="#080a18", glow_color="#a855f7"),
        }

    def apply_frame_recipe(self, name, soft=False):
        if name == "Random Per Panel": return
        recipe = self.default_recipes().get(name)
        if not recipe: return
        for k, v in recipe.items():
            if k in self.vars: self.vars[k].set(v)
        self.refresh_color_buttons()
        if soft: self.refresh_all()

    def refresh_color_buttons(self):
        for name, button in self.color_buttons.items():
            value = self.vars[name].get(); button.configure(text=value, bg=value, fg=self.contrast(value))

    def open_workspace(self):
        self.open_folder(self.workspace)

    def open_folder(self, folder: Path):
        try:
            if platform.system() == "Windows": os.startfile(folder)
            elif platform.system() == "Darwin": subprocess.Popen(["open", str(folder)])
            else: subprocess.Popen(["xdg-open", str(folder)])
        except Exception as error:
            messagebox.showerror(APP_TITLE, f"Could not open folder:\n{error}")


if __name__ == "__main__":
    root = tk.Tk()
    BloomPanelLab(root)
    root.mainloop()
