# bloompanel_breaker.py
# run with: python3 bloompanel_breaker.py
# path: /home/quarterbitgames/SkyCorePi/apps/BloomFrame/bloompanel_breaker.py
# description: Splits a multi-image comic/collage/page into individual panels, applies wild frame styles, and batch exports framed images.
# version: 0.1.0
# updated: 2026-06-25
# format: bloomcore/v1.3
# tags: bloomcore, skycorepi, tkinter, pillow, image, comic, panel, slicer, frame, batch-export
# gpio: none
# dependencies: Pillow >= 9.0
# author: bloomcraft/sky
# license: MIT
# hardware: Raspberry Pi 5 or desktop Linux
# notes: Keeps the source image intact. Exports panel crops into a selected folder.
# uuid: bc-app-bloompanel-breaker-20260625-001

from __future__ import annotations

import os
import random
import tkinter as tk
from dataclasses import dataclass
from tkinter import colorchooser, filedialog, messagebox, ttk
from typing import Optional

from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter, ImageOps, ImageTk

APP_TITLE = "BloomPanel Breaker"


@dataclass
class PanelBox:
    x1: int
    y1: int
    x2: int
    y2: int

    def normalized(self) -> "PanelBox":
        return PanelBox(min(self.x1, self.x2), min(self.y1, self.y2), max(self.x1, self.x2), max(self.y1, self.y2))

    def size(self):
        box = self.normalized()
        return box.x2 - box.x1, box.y2 - box.y1


class BloomPanelBreaker:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("1420x900")
        self.root.minsize(1120, 720)
        self.root.configure(bg="#101018")

        self.source: Optional[Image.Image] = None
        self.source_path: Optional[str] = None
        self.preview_photo = None
        self.panels: list[PanelBox] = []
        self.selected_index: Optional[int] = None
        self.drag_start_canvas = None
        self.temp_rect = None
        self.scale = 1.0
        self.offset_x = 0
        self.offset_y = 0
        self.vars = {}
        self.color_buttons = {}

        self.build_style()
        self.build_ui()
        self.apply_style("Chaos Neon")

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
        variable = kind(value=value)
        self.vars[name] = variable
        return variable

    def build_ui(self):
        toolbar = tk.Frame(self.root, bg="#20202c", padx=8, pady=7)
        toolbar.pack(fill=tk.X)
        buttons = [
            ("Load Big Image", self.load_image),
            ("Auto Grid", self.auto_grid),
            ("Auto Detect", self.auto_detect_panels),
            ("Clear Panels", self.clear_panels),
            ("Export Selected", self.export_selected),
            ("Export All", self.export_all),
        ]
        for text, command in buttons:
            tk.Button(toolbar, text=text, command=command, bg="#343448", fg="white",
                      activebackground="#513f6b", relief=tk.FLAT, padx=12, pady=7).pack(side=tk.LEFT, padx=3)
        self.status = tk.StringVar(value="Load a comic page, collage, or multi-image sheet.")
        tk.Label(toolbar, textvariable=self.status, bg="#20202c", fg="#d7d7e7").pack(side=tk.RIGHT, padx=10)

        body = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, sashwidth=7, bg="#0b0b10")
        body.pack(fill=tk.BOTH, expand=True)
        left = tk.Frame(body, bg="#181820", width=390)
        right = tk.Frame(body, bg="#0b0b10")
        body.add(left, minsize=360)
        body.add(right, minsize=650)

        self.build_controls(left)
        self.canvas = tk.Canvas(right, bg="#09090f", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<Configure>", lambda _e: self.redraw())
        self.canvas.bind("<ButtonPress-1>", self.on_down)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_up)
        self.canvas.bind("<Button-3>", self.delete_at_pointer)

    def build_controls(self, parent):
        canvas = tk.Canvas(parent, bg="#181820", highlightthickness=0, width=382)
        bar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=canvas.yview)
        panel = tk.Frame(canvas, bg="#181820")
        panel.bind("<Configure>", lambda _e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=panel, anchor="nw", width=372)
        canvas.configure(yscrollcommand=bar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        bar.pack(side=tk.RIGHT, fill=tk.Y)

        self.add_title(panel, "Panel Splitter")
        self.add_slider(panel, "Grid columns", "grid_cols", 1, 12, 3)
        self.add_slider(panel, "Grid rows", "grid_rows", 1, 12, 4)
        self.add_slider(panel, "Gutter X", "gutter_x", 0, 80, 10)
        self.add_slider(panel, "Gutter Y", "gutter_y", 0, 80, 10)
        self.add_slider(panel, "Trim edge", "trim_edge", 0, 100, 8)
        self.add_slider(panel, "Detect threshold", "detect_threshold", 0, 250, 50)
        self.add_slider(panel, "Minimum panel", "min_panel", 20, 500, 120)

        self.add_title(panel, "Frame Style")
        self.add_combo(panel, "Export style", "style", ["Chaos Neon", "Comic Ink", "Polaroid Stack", "Walnut Relic", "Sky Glass", "Science Snap", "System Card", "Random Per Panel"], "Chaos Neon")
        self.add_slider(panel, "Outer frame", "outer", 0, 220, 44)
        self.add_slider(panel, "Inner frame", "inner", 0, 90, 10)
        self.add_slider(panel, "Mat", "mat", 0, 220, 18)
        self.add_slider(panel, "Corner radius", "radius", 0, 180, 16)
        self.add_slider(panel, "Bevel", "bevel", 0, 45, 7)
        self.add_slider(panel, "Ink jitter", "jitter", 0, 32, 7)
        self.add_slider(panel, "Glow", "glow", 0, 100, 25)
        self.add_slider(panel, "Shadow", "shadow", 0, 120, 30)
        self.add_slider(panel, "Texture", "texture", 0, 100, 35)
        self.add_slider(panel, "Boost color", "boost", 0, 200, 110)
        self.add_color(panel, "Outer color", "outer_color", "#101018")
        self.add_color(panel, "Inner color", "inner_color", "#ff4fd8")
        self.add_color(panel, "Mat color", "mat_color", "#eee7d8")
        self.add_color(panel, "Glow color", "glow_color", "#5cf3ff")

        self.add_title(panel, "Presets")
        for name in ["Chaos Neon", "Comic Ink", "Polaroid Stack", "Walnut Relic", "Sky Glass", "Science Snap", "System Card"]:
            tk.Button(panel, text=name, command=lambda n=name: self.apply_style(n), bg="#2d2d3a",
                      fg="white", activebackground="#4d3f66", relief=tk.FLAT, pady=8).pack(fill=tk.X, padx=15, pady=3)

        self.add_title(panel, "Mouse")
        tk.Label(panel, text="Left-drag: draw a panel box\nClick existing box: select it\nRight-click box: delete it\nAuto Grid: fast clean slices\nAuto Detect: experimental black-gutter finder",
                 bg="#181820", fg="#cfcfe0", justify=tk.LEFT).pack(fill=tk.X, padx=16, pady=8)

    def add_title(self, parent, text):
        tk.Label(parent, text=text, bg="#181820", fg="#d7c4ff", font=("TkDefaultFont", 12, "bold")).pack(anchor="w", padx=12, pady=(14, 6))

    def add_slider(self, parent, label, name, low, high, value):
        row = tk.Frame(parent, bg="#181820")
        row.pack(fill=tk.X, padx=10, pady=4)
        variable = self.var(name, tk.IntVar, value)
        tk.Label(row, text=label, bg="#181820", fg="#eeeeff", width=16, anchor="w").pack(side=tk.LEFT)
        ttk.Scale(row, from_=low, to=high, variable=variable, command=lambda _v: self.redraw()).pack(side=tk.LEFT, fill=tk.X, expand=True)
        tk.Spinbox(row, from_=low, to=high, textvariable=variable, width=5, command=self.redraw,
                   bg="#262634", fg="white", insertbackground="white", buttonbackground="#343448").pack(side=tk.RIGHT, padx=(6, 0))

    def add_combo(self, parent, label, name, values, value):
        row = tk.Frame(parent, bg="#181820")
        row.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(row, text=label, bg="#181820", fg="#eeeeff", width=16, anchor="w").pack(side=tk.LEFT)
        variable = self.var(name, tk.StringVar, value)
        combo = ttk.Combobox(row, values=values, textvariable=variable, state="readonly")
        combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        combo.bind("<<ComboboxSelected>>", lambda _e: self.redraw())

    def add_color(self, parent, label, name, value):
        row = tk.Frame(parent, bg="#181820")
        row.pack(fill=tk.X, padx=10, pady=5)
        variable = self.var(name, tk.StringVar, value)
        tk.Label(row, text=label, bg="#181820", fg="#eeeeff", width=16, anchor="w").pack(side=tk.LEFT)
        button = tk.Button(row, text=value, bg=value, fg=self.contrast(value), relief=tk.FLAT, width=13)
        button.configure(command=lambda: self.pick_color(name, button))
        button.pack(side=tk.LEFT)
        self.color_buttons[name] = button

    def pick_color(self, name, button):
        color = colorchooser.askcolor(self.vars[name].get(), parent=self.root)[1]
        if color:
            self.vars[name].set(color)
            button.configure(text=color, bg=color, fg=self.contrast(color))
            self.redraw()

    @staticmethod
    def contrast(color):
        try:
            r, g, b = (int(color[i:i+2], 16) for i in (1, 3, 5))
            return "black" if r*299 + g*587 + b*114 > 150000 else "white"
        except Exception:
            return "white"

    def load_image(self):
        path = filedialog.askopenfilename(title="Load multi-image page", filetypes=[("Images", "*.png *.jpg *.jpeg *.webp *.bmp *.tif *.tiff"), ("All files", "*")])
        if not path:
            return
        try:
            self.source = Image.open(path).convert("RGBA")
            self.source_path = path
            self.panels.clear()
            self.selected_index = None
            self.status.set(f"Loaded {os.path.basename(path)} — {self.source.width}×{self.source.height}")
            self.redraw()
        except Exception as error:
            messagebox.showerror(APP_TITLE, f"Could not load image:\n{error}")

    def clear_panels(self):
        self.panels.clear()
        self.selected_index = None
        self.redraw()

    def auto_grid(self):
        if self.source is None:
            return
        cols = max(1, self.vars["grid_cols"].get())
        rows = max(1, self.vars["grid_rows"].get())
        gx = self.vars["gutter_x"].get()
        gy = self.vars["gutter_y"].get()
        trim = self.vars["trim_edge"].get()
        width = self.source.width - trim*2
        height = self.source.height - trim*2
        cell_w = width / cols
        cell_h = height / rows
        self.panels.clear()
        for row in range(rows):
            for col in range(cols):
                x1 = int(trim + col*cell_w + gx/2)
                y1 = int(trim + row*cell_h + gy/2)
                x2 = int(trim + (col+1)*cell_w - gx/2)
                y2 = int(trim + (row+1)*cell_h - gy/2)
                if x2 > x1 and y2 > y1:
                    self.panels.append(PanelBox(x1, y1, x2, y2))
        self.status.set(f"Auto grid made {len(self.panels)} panels.")
        self.redraw()

    def auto_detect_panels(self):
        if self.source is None:
            return
        # Lightweight gutter detector: finds long dark horizontal/vertical bands.
        gray = ImageOps.grayscale(self.source).resize((min(900, self.source.width), min(900, self.source.height)))
        w, h = gray.size
        threshold = self.vars["detect_threshold"].get()
        pixels = gray.load()
        dark_cols = []
        dark_rows = []
        for x in range(w):
            dark = sum(1 for y in range(h) if pixels[x, y] < threshold)
            if dark > h * 0.72:
                dark_cols.append(x)
        for y in range(h):
            dark = sum(1 for x in range(w) if pixels[x, y] < threshold)
            if dark > w * 0.72:
                dark_rows.append(y)
        x_cuts = self.cluster_cuts(dark_cols, w)
        y_cuts = self.cluster_cuts(dark_rows, h)
        sx = self.source.width / w
        sy = self.source.height / h
        min_size = self.vars["min_panel"].get()
        trim = self.vars["trim_edge"].get()
        panels = []
        for y1, y2 in zip(y_cuts[:-1], y_cuts[1:]):
            for x1, x2 in zip(x_cuts[:-1], x_cuts[1:]):
                box = PanelBox(int(x1*sx)+trim, int(y1*sy)+trim, int(x2*sx)-trim, int(y2*sy)-trim).normalized()
                bw, bh = box.size()
                if bw >= min_size and bh >= min_size:
                    panels.append(box)
        self.panels = panels
        self.status.set(f"Auto detect found {len(self.panels)} panels. Adjust threshold if weird.")
        self.redraw()

    @staticmethod
    def cluster_cuts(values, maximum):
        if not values:
            return [0, maximum]
        groups = []
        start = previous = values[0]
        for value in values[1:]:
            if value <= previous + 2:
                previous = value
            else:
                groups.append((start, previous))
                start = previous = value
        groups.append((start, previous))
        cuts = [0]
        for start, end in groups:
            center = (start + end) // 2
            if 10 < center < maximum - 10:
                cuts.append(center)
        cuts.append(maximum)
        return sorted(set(cuts))

    def canvas_to_image(self, cx, cy):
        if self.source is None or self.scale == 0:
            return 0, 0
        return int((cx - self.offset_x) / self.scale), int((cy - self.offset_y) / self.scale)

    def image_to_canvas(self, ix, iy):
        return int(ix * self.scale + self.offset_x), int(iy * self.scale + self.offset_y)

    def panel_at(self, cx, cy):
        ix, iy = self.canvas_to_image(cx, cy)
        for index in reversed(range(len(self.panels))):
            box = self.panels[index].normalized()
            if box.x1 <= ix <= box.x2 and box.y1 <= iy <= box.y2:
                return index
        return None

    def on_down(self, event):
        if self.source is None:
            return
        hit = self.panel_at(event.x, event.y)
        if hit is not None:
            self.selected_index = hit
            self.drag_start_canvas = None
            self.redraw()
            return
        self.selected_index = None
        self.drag_start_canvas = (event.x, event.y)
        self.temp_rect = self.canvas.create_rectangle(event.x, event.y, event.x, event.y, outline="#63f6ff", width=3, dash=(5, 4))

    def on_drag(self, event):
        if self.drag_start_canvas and self.temp_rect:
            x0, y0 = self.drag_start_canvas
            self.canvas.coords(self.temp_rect, x0, y0, event.x, event.y)

    def on_up(self, event):
        if self.source is None or not self.drag_start_canvas:
            return
        x0, y0 = self.drag_start_canvas
        x1, y1 = self.canvas_to_image(x0, y0)
        x2, y2 = self.canvas_to_image(event.x, event.y)
        box = PanelBox(x1, y1, x2, y2).normalized()
        bw, bh = box.size()
        if bw > 20 and bh > 20:
            box.x1 = max(0, min(self.source.width, box.x1))
            box.x2 = max(0, min(self.source.width, box.x2))
            box.y1 = max(0, min(self.source.height, box.y1))
            box.y2 = max(0, min(self.source.height, box.y2))
            self.panels.append(box)
            self.selected_index = len(self.panels) - 1
            self.status.set(f"Added panel {len(self.panels)}.")
        self.drag_start_canvas = None
        self.temp_rect = None
        self.redraw()

    def delete_at_pointer(self, event):
        hit = self.panel_at(event.x, event.y)
        if hit is not None:
            del self.panels[hit]
            self.selected_index = None
            self.status.set("Panel deleted.")
            self.redraw()

    def redraw(self):
        self.canvas.delete("all")
        if self.source is None:
            self.canvas.create_text(self.canvas.winfo_width()//2, self.canvas.winfo_height()//2,
                                    text="LOAD A BIG IMAGE\nthen Auto Grid, Auto Detect, or draw boxes",
                                    fill="#77778c", font=("TkDefaultFont", 22, "bold"), justify=tk.CENTER)
            return
        view = self.source.copy()
        cw, ch = max(1, self.canvas.winfo_width()), max(1, self.canvas.winfo_height())
        self.scale = min((cw-30)/view.width, (ch-30)/view.height, 1.0)
        preview = view.resize((int(view.width*self.scale), int(view.height*self.scale)), Image.Resampling.LANCZOS)
        self.offset_x = (cw - preview.width) // 2
        self.offset_y = (ch - preview.height) // 2
        self.preview_photo = ImageTk.PhotoImage(preview)
        self.canvas.create_image(self.offset_x, self.offset_y, image=self.preview_photo, anchor="nw")
        for index, panel in enumerate(self.panels):
            box = panel.normalized()
            x1, y1 = self.image_to_canvas(box.x1, box.y1)
            x2, y2 = self.image_to_canvas(box.x2, box.y2)
            color = "#fff36d" if index == self.selected_index else "#63f6ff"
            self.canvas.create_rectangle(x1, y1, x2, y2, outline=color, width=3)
            self.canvas.create_rectangle(x1, y1, x1+54, y1+24, fill="#000000", outline=color)
            self.canvas.create_text(x1+27, y1+12, text=str(index+1), fill=color, font=("TkDefaultFont", 11, "bold"))
        self.status.set(f"Panels: {len(self.panels)} | Style: {self.vars['style'].get()}")

    def export_selected(self):
        if self.selected_index is None:
            messagebox.showinfo(APP_TITLE, "Select a panel first.")
            return
        folder = filedialog.askdirectory(title="Choose export folder")
        if folder:
            self.export_indices(folder, [self.selected_index])

    def export_all(self):
        if not self.panels:
            messagebox.showinfo(APP_TITLE, "No panels to export yet.")
            return
        folder = filedialog.askdirectory(title="Choose export folder")
        if folder:
            self.export_indices(folder, list(range(len(self.panels))))

    def export_indices(self, folder, indices):
        if self.source is None:
            return
        stem = os.path.splitext(os.path.basename(self.source_path or "panel"))[0]
        made = 0
        for number, index in enumerate(indices, start=1):
            box = self.panels[index].normalized()
            crop = self.source.crop((box.x1, box.y1, box.x2, box.y2))
            framed = self.frame_image(crop, index)
            path = os.path.join(folder, f"{stem}_panel_{index+1:02d}.png")
            framed.save(path)
            made += 1
        self.status.set(f"Exported {made} framed panel image(s) to {folder}")

    def frame_image(self, image: Image.Image, index: int) -> Image.Image:
        style = self.vars["style"].get()
        if style == "Random Per Panel":
            style = random.choice(["Chaos Neon", "Comic Ink", "Polaroid Stack", "Walnut Relic", "Sky Glass", "Science Snap", "System Card"])
        old_style = self.vars["style"].get()
        # Use style rules without mutating visible controls.
        settings = self.style_settings(style)
        outer = settings.get("outer", self.vars["outer"].get())
        inner = settings.get("inner", self.vars["inner"].get())
        mat = settings.get("mat", self.vars["mat"].get())
        radius = settings.get("radius", self.vars["radius"].get())
        bevel = settings.get("bevel", self.vars["bevel"].get())
        jitter = settings.get("jitter", self.vars["jitter"].get())
        glow = settings.get("glow", self.vars["glow"].get())
        shadow = settings.get("shadow", self.vars["shadow"].get())
        texture = settings.get("texture", self.vars["texture"].get())
        boost = settings.get("boost", self.vars["boost"].get())
        outer_color = settings.get("outer_color", self.vars["outer_color"].get())
        inner_color = settings.get("inner_color", self.vars["inner_color"].get())
        mat_color = settings.get("mat_color", self.vars["mat_color"].get())
        glow_color = settings.get("glow_color", self.vars["glow_color"].get())

        image = ImageEnhance.Color(image).enhance(boost / 100)
        image = ImageEnhance.Contrast(image).enhance(1.05)
        image = ImageOps.expand(image, mat, mat_color)
        image = ImageOps.expand(image, inner, inner_color)
        image = self.rough_expand(image, outer, outer_color, jitter)
        image = self.add_texture(image, outer, texture)
        image = self.add_bevel(image, bevel)
        if radius:
            image = self.rounded(image, radius)
        return self.add_shadow_glow(image, shadow, glow, glow_color)

    def rough_expand(self, image, border, color, jitter):
        if border <= 0:
            return image
        result = ImageOps.expand(image, border, color)
        if jitter <= 0:
            return result
        draw = ImageDraw.Draw(result)
        for _ in range(max(20, int((result.width + result.height) / 18))):
            side = random.choice(["top", "bottom", "left", "right"])
            if side in {"top", "bottom"}:
                y = random.randint(0, border-1) if side == "top" else random.randint(result.height-border, result.height-1)
                x1 = random.randint(0, result.width)
                x2 = min(result.width, x1 + random.randint(10, 90))
            else:
                x1 = random.randint(0, border-1) if side == "left" else random.randint(result.width-border, result.width-1)
                y = random.randint(0, result.height)
                x2 = x1
                y2 = min(result.height, y + random.randint(10, 90))
                draw.line((x1, y, x2, y2), fill=(255,255,255,90), width=random.randint(1, max(1, jitter//3)))
                continue
            draw.line((x1, y, x2, y + random.randint(-jitter, jitter)), fill=(0,0,0,120), width=random.randint(1, max(1, jitter//3)))
        return result

    def add_texture(self, image, border, amount):
        if amount <= 0 or border <= 0:
            return image
        overlay = Image.new("RGBA", image.size, (0,0,0,0))
        draw = ImageDraw.Draw(overlay)
        alpha = int(amount * 1.4)
        for x in range(-image.height, image.width, 18):
            draw.line((x, 0, x+image.height, image.height), fill=(255,255,255,alpha), width=1)
        mask = Image.new("L", image.size, 255)
        ImageDraw.Draw(mask).rectangle((border, border, image.width-border, image.height-border), fill=0)
        overlay.putalpha(ImageChops.multiply(overlay.getchannel("A"), mask))
        return Image.alpha_composite(image, overlay)

    @staticmethod
    def add_bevel(image, bevel):
        if bevel <= 0:
            return image
        overlay = Image.new("RGBA", image.size, (0,0,0,0))
        draw = ImageDraw.Draw(overlay)
        for i in range(bevel):
            alpha = int(90 * (1 - i / max(1, bevel)))
            draw.line((i, i, image.width-i-1, i), fill=(255,255,255,alpha))
            draw.line((i, i, i, image.height-i-1), fill=(255,255,255,alpha))
            draw.line((i, image.height-i-1, image.width-i-1, image.height-i-1), fill=(0,0,0,alpha))
            draw.line((image.width-i-1, i, image.width-i-1, image.height-i-1), fill=(0,0,0,alpha))
        return Image.alpha_composite(image, overlay)

    @staticmethod
    def rounded(image, radius):
        mask = Image.new("L", image.size, 0)
        ImageDraw.Draw(mask).rounded_rectangle((0,0,image.width-1,image.height-1), radius=radius, fill=255)
        image = image.copy()
        image.putalpha(mask)
        return image

    @staticmethod
    def add_shadow_glow(image, shadow, glow, glow_color):
        margin = max(20, shadow + glow + 24)
        canvas = Image.new("RGBA", (image.width+margin*2, image.height+margin*2), (0,0,0,0))
        alpha = image.getchannel("A")
        if glow > 0:
            glow_alpha = alpha.filter(ImageFilter.MaxFilter(max(3, glow*2+1))).filter(ImageFilter.GaussianBlur(glow))
            glow_layer = Image.new("RGBA", image.size, glow_color)
            glow_layer.putalpha(glow_alpha.point(lambda p: int(p*0.75)))
            canvas.alpha_composite(glow_layer, (margin, margin))
        if shadow > 0:
            shadow_alpha = alpha.filter(ImageFilter.MaxFilter(max(3, shadow+1))).filter(ImageFilter.GaussianBlur(max(1, shadow//2)))
            shadow_layer = Image.new("RGBA", image.size, "#000000")
            shadow_layer.putalpha(shadow_alpha.point(lambda p: int(p*0.65)))
            canvas.alpha_composite(shadow_layer, (margin+shadow//3, margin+shadow//3))
        canvas.alpha_composite(image, (margin, margin))
        return canvas

    def style_settings(self, style):
        styles = {
            "Chaos Neon": dict(outer=44, inner=10, mat=18, radius=16, bevel=7, jitter=7, glow=25, shadow=30, texture=35, boost=120, outer_color="#101018", inner_color="#ff4fd8", mat_color="#08080d", glow_color="#5cf3ff"),
            "Comic Ink": dict(outer=28, inner=8, mat=8, radius=0, bevel=0, jitter=16, glow=0, shadow=20, texture=15, boost=115, outer_color="#050505", inner_color="#f4e04d", mat_color="#ffffff", glow_color="#ffffff"),
            "Polaroid Stack": dict(outer=8, inner=0, mat=70, radius=2, bevel=2, jitter=0, glow=0, shadow=45, texture=4, boost=105, outer_color="#ffffff", inner_color="#ffffff", mat_color="#ffffff", glow_color="#ffffff"),
            "Walnut Relic": dict(outer=90, inner=7, mat=26, radius=8, bevel=18, jitter=4, glow=0, shadow=38, texture=75, boost=108, outer_color="#4a2818", inner_color="#bc8a5f", mat_color="#e8dcc4", glow_color="#ffffff"),
            "Sky Glass": dict(outer=34, inner=3, mat=14, radius=46, bevel=12, jitter=0, glow=28, shadow=18, texture=18, boost=116, outer_color="#0a1020", inner_color="#9be7ff", mat_color="#101827", glow_color="#84f7ff"),
            "Science Snap": dict(outer=20, inner=4, mat=40, radius=8, bevel=3, jitter=3, glow=8, shadow=30, texture=10, boost=110, outer_color="#f1e7cf", inner_color="#7c5cff", mat_color="#fff6dc", glow_color="#7c5cff"),
            "System Card": dict(outer=36, inner=2, mat=18, radius=4, bevel=6, jitter=2, glow=12, shadow=25, texture=25, boost=112, outer_color="#16181d", inner_color="#62f2a4", mat_color="#101214", glow_color="#62f2a4"),
        }
        return styles.get(style, {})

    def apply_style(self, style):
        self.vars["style"].set(style)
        for key, value in self.style_settings(style).items():
            if key in self.vars:
                self.vars[key].set(value)
        for name, button in self.color_buttons.items():
            value = self.vars[name].get()
            button.configure(text=value, bg=value, fg=self.contrast(value))
        self.redraw()


if __name__ == "__main__":
    root = tk.Tk()
    BloomPanelBreaker(root)
    root.mainloop()
