# bloomframe_studio.py
# run with: python3 bloomframe_studio.py
# path: /home/quarterbitgames/SkyCorePi/apps/BloomFrame/bloomframe_studio.py
# description: Raspberry Pi image framing studio with live preview, layered borders, knobs, sliders, procedural textures, glow, shadow, presets, and export.
# version: 0.1.0
# updated: 2026-06-25
# format: bloomcore/v1.3
# tags: bloomcore, skycorepi, tkinter, pillow, image, frame, editor, raspberrypi
# gpio: none
# dependencies: Pillow >= 9.0
# author: bloomcraft/sky
# license: MIT
# hardware: Raspberry Pi 5 or desktop Linux
# notes: Original image is never overwritten unless that output filename is explicitly selected.
# uuid: bc-app-bloomframe-20260625-001

from __future__ import annotations

import math
import os
import random
import tkinter as tk
from tkinter import colorchooser, filedialog, messagebox, ttk
from typing import Callable, Optional

from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter, ImageOps, ImageTk

APP_TITLE = "BloomFrame Studio"


class Knob(tk.Canvas):
    """Small mouse-wheel and vertical-drag rotary control."""

    def __init__(self, master, label: str, variable: tk.IntVar, low: int,
                 high: int, command: Callable[[], None], size: int = 78):
        super().__init__(master, width=size, height=size + 28,
                         bg="#181820", highlightthickness=0)
        self.label, self.variable = label, variable
        self.low, self.high, self.command, self.size = low, high, command, size
        self.drag_y: Optional[int] = None
        self.bind("<Button-1>", self.start_drag)
        self.bind("<B1-Motion>", self.drag)
        self.bind("<MouseWheel>", self.wheel)
        self.variable.trace_add("write", lambda *_: self.draw())
        self.draw()

    def start_drag(self, event):
        self.drag_y = event.y

    def drag(self, event):
        if self.drag_y is None:
            return
        delta = self.drag_y - event.y
        if delta:
            self.set_value(self.variable.get() + delta)
            self.drag_y = event.y

    def wheel(self, event):
        self.set_value(self.variable.get() + (1 if event.delta > 0 else -1))

    def set_value(self, value):
        value = max(self.low, min(self.high, int(value)))
        if value != self.variable.get():
            self.variable.set(value)
            self.command()

    def draw(self):
        self.delete("all")
        value = self.variable.get()
        ratio = (value - self.low) / max(1, self.high - self.low)
        angle = math.radians(225 - ratio * 270)
        center, radius = self.size / 2, self.size * 0.36
        self.create_oval(center-radius, center-radius, center+radius,
                         center+radius, fill="#2c2c38", outline="#68687a", width=2)
        self.create_arc(center-radius-4, center-radius-4, center+radius+4,
                        center+radius+4, start=-45, extent=ratio*270,
                        style="arc", outline="#b58cff", width=4)
        px = center + math.cos(angle) * radius * 0.72
        py = center - math.sin(angle) * radius * 0.72
        self.create_line(center, center, px, py, fill="#f7e7ff",
                         width=4, capstyle=tk.ROUND)
        self.create_text(center, center + radius + 13,
                         text=f"{self.label} {value}", fill="#eeeef5",
                         font=("TkDefaultFont", 8, "bold"))


class BloomFrameStudio:
    def __init__(self, root: tk.Tk):
        self.root = root
        root.title(APP_TITLE)
        root.geometry("1380x860")
        root.minsize(1100, 700)
        root.configure(bg="#111118")
        self.original: Optional[Image.Image] = None
        self.rendered: Optional[Image.Image] = None
        self.preview_photo = None
        self.current_path = None
        self.pending_after = None
        self.vars = {}
        self.color_buttons = {}
        self.build_style()
        self.build_ui()
        self.apply_preset("Bloom Shrine")

    def build_style(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TFrame", background="#181820")
        style.configure("TLabel", background="#181820", foreground="#efeff7")
        style.configure("TNotebook", background="#111118", borderwidth=0)
        style.configure("TNotebook.Tab", padding=(12, 7))
        style.configure("TScale", background="#181820")

    def var(self, name, kind, value):
        result = kind(value=value)
        self.vars[name] = result
        return result

    def build_ui(self):
        toolbar = tk.Frame(self.root, bg="#20202a", padx=8, pady=8)
        toolbar.pack(fill=tk.X)
        for text, command in (("Load Image", self.load_image),
                              ("Save As", self.save_image),
                              ("Reset", lambda: self.apply_preset("Bloom Shrine")),
                              ("Randomize", self.randomize_frame)):
            tk.Button(toolbar, text=text, command=command, bg="#343445",
                      fg="white", activebackground="#4d3f66", relief=tk.FLAT,
                      padx=14, pady=7).pack(side=tk.LEFT, padx=3)
        self.status = tk.StringVar(value="Load an image to begin.")
        tk.Label(toolbar, textvariable=self.status, bg="#20202a",
                 fg="#c9c9d8").pack(side=tk.RIGHT, padx=12)

        body = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, sashwidth=7,
                              bg="#0d0d12")
        body.pack(fill=tk.BOTH, expand=True)
        controls = tk.Frame(body, bg="#181820", width=405)
        preview = tk.Frame(body, bg="#0b0b10")
        body.add(controls, minsize=365)
        body.add(preview, minsize=620)

        book = ttk.Notebook(controls)
        book.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)
        tabs = {name: ttk.Frame(book) for name in ("Frame", "Image", "Effects", "Presets")}
        for name, tab in tabs.items():
            book.add(tab, text=name)
        self.build_frame_tab(tabs["Frame"])
        self.build_image_tab(tabs["Image"])
        self.build_effects_tab(tabs["Effects"])
        self.build_presets_tab(tabs["Presets"])

        self.preview_canvas = tk.Canvas(preview, bg="#0b0b10", highlightthickness=0)
        self.preview_canvas.pack(fill=tk.BOTH, expand=True)
        self.preview_canvas.bind("<Configure>", lambda _e: self.schedule_render())

    def scrollable(self, parent):
        canvas = tk.Canvas(parent, bg="#181820", highlightthickness=0, width=375)
        bar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=canvas.yview)
        inner = tk.Frame(canvas, bg="#181820")
        inner.bind("<Configure>", lambda _e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw", width=370)
        canvas.configure(yscrollcommand=bar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        bar.pack(side=tk.RIGHT, fill=tk.Y)
        return inner

    def add_slider(self, parent, label, name, low, high, value):
        row = tk.Frame(parent, bg="#181820")
        row.pack(fill=tk.X, padx=10, pady=4)
        variable = self.var(name, tk.IntVar, value)
        tk.Label(row, text=label, bg="#181820", fg="#efeff7",
                 width=17, anchor="w").pack(side=tk.LEFT)
        ttk.Scale(row, from_=low, to=high, variable=variable,
                  command=lambda _v: self.schedule_render()).pack(side=tk.LEFT, fill=tk.X, expand=True)
        tk.Spinbox(row, from_=low, to=high, textvariable=variable, width=5,
                   command=self.schedule_render, bg="#262632", fg="white",
                   buttonbackground="#343445", insertbackground="white").pack(side=tk.RIGHT, padx=(6, 0))

    def add_color(self, parent, label, name, value):
        row = tk.Frame(parent, bg="#181820")
        row.pack(fill=tk.X, padx=10, pady=5)
        variable = self.var(name, tk.StringVar, value)
        tk.Label(row, text=label, bg="#181820", fg="#efeff7",
                 width=17, anchor="w").pack(side=tk.LEFT)
        button = tk.Button(row, text=value, bg=value, fg=self.contrast_text(value),
                           relief=tk.FLAT, width=14)
        button.configure(command=lambda: self.pick_color(name, button))
        button.pack(side=tk.LEFT)
        self.color_buttons[name] = button

    def add_combo(self, parent, label, name, values, value):
        row = tk.Frame(parent, bg="#181820")
        row.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(row, text=label, bg="#181820", fg="#efeff7",
                 width=17, anchor="w").pack(side=tk.LEFT)
        variable = self.var(name, tk.StringVar, value)
        combo = ttk.Combobox(row, textvariable=variable, values=values,
                             state="readonly", width=20)
        combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        combo.bind("<<ComboboxSelected>>", lambda _e: self.schedule_render())

    def build_frame_tab(self, parent):
        panel = self.scrollable(parent)
        specs = (("Outer width", "outer_width", 0, 300, 70),
                 ("Inner width", "inner_width", 0, 100, 10),
                 ("Gap width", "gap_width", 0, 100, 8),
                 ("Mat padding", "mat_padding", 0, 250, 24),
                 ("Corner radius", "corner_radius", 0, 220, 18),
                 ("Bevel size", "bevel_size", 0, 40, 8))
        for spec in specs:
            self.add_slider(panel, *spec)
        ttk.Separator(panel).pack(fill=tk.X, padx=10, pady=8)
        for spec in (("Outer color", "outer_color", "#241438"),
                     ("Inner color", "inner_color", "#d9b85f"),
                     ("Gap color", "gap_color", "#08080d"),
                     ("Mat color", "mat_color", "#f1eee6")):
            self.add_color(panel, *spec)
        ttk.Separator(panel).pack(fill=tk.X, padx=10, pady=8)
        self.add_combo(panel, "Texture", "texture",
                       ["None", "Stripes", "Dots", "Crosshatch", "Noise", "Wood"], "None")
        self.add_slider(panel, "Texture amount", "texture_strength", 0, 100, 18)
        self.add_slider(panel, "Pattern width", "stripe_width", 1, 80, 14)
        self.add_slider(panel, "Pattern spacing", "stripe_spacing", 4, 100, 18)

    def build_image_tab(self, parent):
        panel = self.scrollable(parent)
        knobs = tk.Frame(panel, bg="#181820")
        knobs.pack(fill=tk.X, padx=5, pady=8)
        for index, spec in enumerate((("Bright", "brightness", 0, 200, 100),
                                      ("Contrast", "contrast", 0, 200, 100),
                                      ("Color", "saturation", 0, 200, 100),
                                      ("Sharp", "sharpness", 0, 250, 100))):
            label, name, low, high, value = spec
            variable = self.var(name, tk.IntVar, value)
            Knob(knobs, label, variable, low, high, self.schedule_render).grid(
                row=index // 2, column=index % 2, padx=12, pady=5)
        self.add_slider(panel, "Rotation", "rotation", -180, 180, 0)
        self.add_slider(panel, "Image scale", "scale", 25, 200, 100)
        self.add_slider(panel, "Vignette", "vignette", 0, 100, 0)
        row = tk.Frame(panel, bg="#181820")
        row.pack(fill=tk.X, padx=10, pady=12)
        for text, command in (("Rotate L", lambda: self.bump("rotation", -90)),
                              ("Rotate R", lambda: self.bump("rotation", 90)),
                              ("Flip H", self.flip_horizontal),
                              ("Flip V", self.flip_vertical)):
            ttk.Button(row, text=text, command=command).pack(side=tk.LEFT, padx=2)

    def build_effects_tab(self, parent):
        panel = self.scrollable(parent)
        for spec in (("Shadow size", "shadow_size", 0, 150, 24),
                     ("Shadow blur", "shadow_blur", 0, 80, 18),
                     ("Shadow X", "shadow_offset_x", -100, 100, 10),
                     ("Shadow Y", "shadow_offset_y", -100, 100, 10)):
            self.add_slider(panel, *spec)
        self.add_color(panel, "Shadow color", "shadow_color", "#000000")
        ttk.Separator(panel).pack(fill=tk.X, padx=10, pady=8)
        for spec in (("Glow size", "glow_size", 0, 100, 12),
                     ("Glow blur", "glow_blur", 0, 80, 18),
                     ("Glow strength", "glow_strength", 0, 255, 80)):
            self.add_slider(panel, *spec)
        self.add_color(panel, "Glow color", "glow_color", "#8b5cf6")

    def build_presets_tab(self, parent):
        panel = self.scrollable(parent)
        tk.Label(panel, text="One-click frame recipes", bg="#181820",
                 fg="#d7c4ff", font=("TkDefaultFont", 12, "bold")).pack(pady=12)
        for name in ("Bloom Shrine", "Classic Gold", "Polaroid", "Neon Portal",
                     "Comic Ink", "Walnut", "Pixel Block", "Soft Gallery", "Void Glass"):
            tk.Button(panel, text=name, command=lambda n=name: self.apply_preset(n),
                      bg="#2c2c38", fg="white", activebackground="#4d3f66",
                      relief=tk.FLAT, pady=9).pack(fill=tk.X, padx=18, pady=4)

    def pick_color(self, name, button):
        color = colorchooser.askcolor(self.vars[name].get(), parent=self.root)[1]
        if color:
            self.vars[name].set(color)
            button.configure(text=color, bg=color, fg=self.contrast_text(color))
            self.schedule_render()

    @staticmethod
    def contrast_text(color):
        try:
            red, green, blue = (int(color[i:i+2], 16) for i in (1, 3, 5))
            return "black" if red*299 + green*587 + blue*114 > 150000 else "white"
        except Exception:
            return "white"

    def load_image(self):
        path = filedialog.askopenfilename(
            title="Load image",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.webp *.bmp *.tif *.tiff"),
                       ("All files", "*")])
        if not path:
            return
        try:
            self.original = Image.open(path).convert("RGBA")
            self.current_path = path
            self.status.set(f"Loaded: {os.path.basename(path)} — {self.original.width}×{self.original.height}")
            self.schedule_render()
        except Exception as error:
            messagebox.showerror(APP_TITLE, f"Could not load image:\n{error}")

    def save_image(self):
        if self.rendered is None:
            messagebox.showinfo(APP_TITLE, "Load an image first.")
            return
        stem = os.path.splitext(os.path.basename(self.current_path or "bloomframe"))[0]
        path = filedialog.asksaveasfilename(
            title="Save framed image", defaultextension=".png",
            initialfile=f"{stem}_framed.png",
            filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg *.jpeg"), ("WebP", "*.webp")])
        if not path:
            return
        try:
            image = self.rendered
            if os.path.splitext(path)[1].lower() in {".jpg", ".jpeg"}:
                background = Image.new("RGB", image.size, "white")
                background.paste(image, mask=image.getchannel("A"))
                image = background
            image.save(path, quality=95)
            self.status.set(f"Saved: {path}")
        except Exception as error:
            messagebox.showerror(APP_TITLE, f"Could not save image:\n{error}")

    def schedule_render(self):
        if self.pending_after:
            self.root.after_cancel(self.pending_after)
        self.pending_after = self.root.after(70, self.render)

    def render(self):
        self.pending_after = None
        self.preview_canvas.delete("all")
        if self.original is None:
            self.preview_canvas.create_text(
                self.preview_canvas.winfo_width() // 2,
                self.preview_canvas.winfo_height() // 2,
                text="LOAD AN IMAGE\nthen turn every knob", fill="#77778b",
                font=("TkDefaultFont", 22, "bold"), justify=tk.CENTER)
            return
        try:
            self.rendered = self.compose(self.original)
            preview = self.rendered.copy()
            available = (max(200, self.preview_canvas.winfo_width()-30),
                         max(200, self.preview_canvas.winfo_height()-30))
            preview.thumbnail(available, Image.Resampling.LANCZOS)
            self.preview_photo = ImageTk.PhotoImage(preview)
            self.preview_canvas.create_image(
                self.preview_canvas.winfo_width() // 2,
                self.preview_canvas.winfo_height() // 2,
                image=self.preview_photo, anchor="center")
        except Exception as error:
            self.status.set(f"Render error: {error}")

    def compose(self, source):
        image = source.copy()
        image = ImageEnhance.Brightness(image).enhance(self.vars["brightness"].get()/100)
        image = ImageEnhance.Contrast(image).enhance(self.vars["contrast"].get()/100)
        image = ImageEnhance.Color(image).enhance(self.vars["saturation"].get()/100)
        image = ImageEnhance.Sharpness(image).enhance(self.vars["sharpness"].get()/100)
        if self.vars["rotation"].get():
            image = image.rotate(-self.vars["rotation"].get(), expand=True,
                                 resample=Image.Resampling.BICUBIC)
        scale = self.vars["scale"].get()/100
        if scale != 1:
            image = image.resize((max(1, int(image.width*scale)),
                                  max(1, int(image.height*scale))), Image.Resampling.LANCZOS)
        image = self.apply_vignette(image)
        for width, color in ((self.vars["mat_padding"].get(), self.vars["mat_color"].get()),
                             (self.vars["gap_width"].get(), self.vars["gap_color"].get()),
                             (self.vars["inner_width"].get(), self.vars["inner_color"].get()),
                             (self.vars["outer_width"].get(), self.vars["outer_color"].get())):
            image = ImageOps.expand(image, border=width, fill=color)
        image = self.apply_texture(image, self.vars["outer_width"].get())
        image = self.apply_bevel(image)
        image = self.round_image(image)
        return self.shadow_and_glow(image)

    def apply_vignette(self, image):
        amount = self.vars["vignette"].get()
        if amount <= 0:
            return image
        mask = Image.new("L", image.size, 0)
        inset = int(min(image.size)*0.08)
        ImageDraw.Draw(mask).ellipse((-inset, -inset, image.width+inset,
                                      image.height+inset), fill=255)
        mask = mask.filter(ImageFilter.GaussianBlur(max(8, int(min(image.size)*0.18))))
        dark = Image.new("RGBA", image.size, (0, 0, 0, int(255*amount/100)))
        clear = Image.new("RGBA", image.size, (0, 0, 0, 0))
        return Image.alpha_composite(image, Image.composite(clear, dark, mask))

    def apply_texture(self, image, outer):
        mode = self.vars["texture"].get()
        strength = self.vars["texture_strength"].get()
        if mode == "None" or strength <= 0 or outer <= 0:
            return image
        overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        spacing = max(4, self.vars["stripe_spacing"].get())
        width = max(1, self.vars["stripe_width"].get())
        alpha = int(255*strength/100*0.45)
        color = (255, 255, 255, alpha)
        if mode in {"Stripes", "Wood"}:
            line_width = width if mode == "Stripes" else max(1, width//5)
            for x in range(-image.height, image.width, spacing):
                draw.line((x, 0, x+image.height, image.height), fill=color, width=line_width)
        elif mode == "Dots":
            for y in range(0, image.height, spacing):
                for x in range(0, image.width, spacing):
                    draw.ellipse((x, y, x+width, y+width), fill=color)
        elif mode == "Crosshatch":
            for x in range(-image.height, image.width, spacing):
                draw.line((x, 0, x+image.height, image.height), fill=color, width=max(1, width//4))
                draw.line((x+image.height, 0, x, image.height), fill=color, width=max(1, width//4))
        elif mode == "Noise":
            noise = Image.effect_noise(image.size, max(1, strength)).convert("L")
            overlay = Image.merge("RGBA", (noise, noise, noise,
                                  noise.point(lambda p: int(p*strength/300))))
        mask = Image.new("L", image.size, 255)
        if outer < min(image.size)//2:
            ImageDraw.Draw(mask).rectangle((outer, outer, image.width-outer-1,
                                            image.height-outer-1), fill=0)
        overlay.putalpha(ImageChops.multiply(overlay.getchannel("A"), mask))
        return Image.alpha_composite(image, overlay)

    def apply_bevel(self, image):
        size = self.vars["bevel_size"].get()
        if size <= 0:
            return image
        overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        for i in range(size):
            alpha = int(80*(1-i/max(1, size)))
            draw.line((i, i, image.width-i-1, i), fill=(255,255,255,alpha))
            draw.line((i, i, i, image.height-i-1), fill=(255,255,255,alpha))
            draw.line((i, image.height-i-1, image.width-i-1,
                       image.height-i-1), fill=(0,0,0,alpha))
            draw.line((image.width-i-1, i, image.width-i-1,
                       image.height-i-1), fill=(0,0,0,alpha))
        return Image.alpha_composite(image, overlay)

    def round_image(self, image):
        radius = self.vars["corner_radius"].get()
        if radius <= 0:
            return image
        mask = Image.new("L", image.size, 0)
        ImageDraw.Draw(mask).rounded_rectangle(
            (0, 0, image.width-1, image.height-1), radius=radius, fill=255)
        result = image.copy()
        result.putalpha(mask)
        return result

    def shadow_and_glow(self, image):
        shadow_size = self.vars["shadow_size"].get()
        glow_size = self.vars["glow_size"].get()
        blur = max(self.vars["shadow_blur"].get(), self.vars["glow_blur"].get())
        margin = max(2, shadow_size+glow_size+blur+20)
        canvas = Image.new("RGBA", (image.width+margin*2,
                                     image.height+margin*2), (0,0,0,0))
        alpha = image.getchannel("A")
        if glow_size > 0 and self.vars["glow_strength"].get() > 0:
            kernel = glow_size*2+1
            glow_alpha = alpha.filter(ImageFilter.MaxFilter(max(3, kernel)))
            glow_alpha = glow_alpha.filter(ImageFilter.GaussianBlur(self.vars["glow_blur"].get()))
            glow_alpha = glow_alpha.point(lambda p: int(p*self.vars["glow_strength"].get()/255))
            glow = Image.new("RGBA", image.size, self.vars["glow_color"].get())
            glow.putalpha(glow_alpha)
            canvas.alpha_composite(glow, (margin, margin))
        if shadow_size > 0:
            kernel = shadow_size*2+1
            shadow_alpha = alpha.filter(ImageFilter.MaxFilter(max(3, kernel)))
            shadow_alpha = shadow_alpha.filter(ImageFilter.GaussianBlur(self.vars["shadow_blur"].get()))
            shadow = Image.new("RGBA", image.size, self.vars["shadow_color"].get())
            shadow.putalpha(shadow_alpha.point(lambda p: int(p*0.72)))
            canvas.alpha_composite(shadow,
                (margin+self.vars["shadow_offset_x"].get(),
                 margin+self.vars["shadow_offset_y"].get()))
        canvas.alpha_composite(image, (margin, margin))
        return canvas

    def bump(self, name, amount):
        self.vars[name].set(self.vars[name].get()+amount)
        self.schedule_render()

    def flip_horizontal(self):
        if self.original is not None:
            self.original = ImageOps.mirror(self.original)
            self.schedule_render()

    def flip_vertical(self):
        if self.original is not None:
            self.original = ImageOps.flip(self.original)
            self.schedule_render()

    def randomize_frame(self):
        colors = ["#11131f", "#241438", "#512b58", "#143642",
                  "#5b2b22", "#123524", "#e9e1d0", "#1a1a1a"]
        accents = ["#d9b85f", "#8b5cf6", "#4de0ff", "#ff5fa2",
                   "#f4f1de", "#66ff99"]
        for name, value in (("outer_width", random.randint(20,150)),
                            ("inner_width", random.randint(2,30)),
                            ("gap_width", random.randint(0,20)),
                            ("corner_radius", random.randint(0,80)),
                            ("outer_color", random.choice(colors)),
                            ("inner_color", random.choice(accents)),
                            ("glow_color", random.choice(accents)),
                            ("texture", random.choice(["None", "Stripes", "Dots", "Crosshatch", "Wood"]))):
            self.vars[name].set(value)
        self.refresh_color_buttons()
        self.schedule_render()

    def refresh_color_buttons(self):
        for name, button in self.color_buttons.items():
            value = self.vars[name].get()
            button.configure(text=value, bg=value, fg=self.contrast_text(value))

    def apply_preset(self, name):
        presets = {
            "Bloom Shrine": dict(outer_width=70, inner_width=10, gap_width=8, mat_padding=24, corner_radius=18, bevel_size=8, outer_color="#241438", inner_color="#d9b85f", gap_color="#08080d", mat_color="#f1eee6", glow_size=12, glow_blur=18, glow_strength=80, glow_color="#8b5cf6", texture="None"),
            "Classic Gold": dict(outer_width=90, inner_width=16, gap_width=6, mat_padding=35, corner_radius=6, bevel_size=14, outer_color="#3b2415", inner_color="#d4af37", gap_color="#24150c", mat_color="#eee7d5", glow_size=0, texture="Wood"),
            "Polaroid": dict(outer_width=8, inner_width=0, gap_width=0, mat_padding=55, corner_radius=2, bevel_size=1, outer_color="#ffffff", inner_color="#ffffff", gap_color="#ffffff", mat_color="#ffffff", shadow_size=18, glow_size=0, texture="None"),
            "Neon Portal": dict(outer_width=38, inner_width=12, gap_width=5, mat_padding=8, corner_radius=55, bevel_size=4, outer_color="#090914", inner_color="#32f6ff", gap_color="#18002b", mat_color="#090914", glow_size=28, glow_blur=28, glow_strength=190, glow_color="#bd48ff", texture="Stripes"),
            "Comic Ink": dict(outer_width=30, inner_width=10, gap_width=4, mat_padding=14, corner_radius=0, bevel_size=0, outer_color="#111111", inner_color="#f4d35e", gap_color="#111111", mat_color="#f7f4e8", glow_size=0, texture="Dots"),
            "Walnut": dict(outer_width=110, inner_width=5, gap_width=8, mat_padding=30, corner_radius=10, bevel_size=16, outer_color="#4a2818", inner_color="#bc8a5f", gap_color="#24140c", mat_color="#e6dcc8", glow_size=0, texture="Wood"),
            "Pixel Block": dict(outer_width=48, inner_width=14, gap_width=8, mat_padding=8, corner_radius=0, bevel_size=0, outer_color="#202020", inner_color="#63d471", gap_color="#101010", mat_color="#d8f3dc", glow_size=4, glow_blur=3, glow_strength=80, glow_color="#63d471", texture="Crosshatch"),
            "Soft Gallery": dict(outer_width=18, inner_width=2, gap_width=2, mat_padding=70, corner_radius=14, bevel_size=2, outer_color="#ebe7df", inner_color="#c8bfb0", gap_color="#ffffff", mat_color="#f8f6f2", glow_size=0, shadow_size=20, shadow_blur=30, texture="None"),
            "Void Glass": dict(outer_width=42, inner_width=3, gap_width=12, mat_padding=6, corner_radius=35, bevel_size=10, outer_color="#06070a", inner_color="#7a7f91", gap_color="#14151b", mat_color="#05060a", glow_size=16, glow_blur=30, glow_strength=90, glow_color="#6770ff", texture="Noise")
        }
        for key, value in presets[name].items():
            if key in self.vars:
                self.vars[key].set(value)
        self.refresh_color_buttons()
        self.status.set(f"Preset: {name}")
        self.schedule_render()


if __name__ == "__main__":
    root = tk.Tk()
    BloomFrameStudio(root)
    root.mainloop()
