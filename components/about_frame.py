import customtkinter as ctk
from components.theme import THEME_COLORS, FONTS

class AboutFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        card = ctk.CTkFrame(
            self,
            fg_color=THEME_COLORS["bg_card"],
            border_color=THEME_COLORS["border"],
            border_width=1,
            corner_radius=12
        )
        card.grid(row=0, column=0, padx=40, pady=40, sticky="nsew")
        
        # Title & Branding
        brand_lbl = ctk.CTkLabel(
            card,
            text="OptiWebP Image Studio",
            font=("Outfit", 26, "bold"),
            text_color=THEME_COLORS["text_main"]
        )
        brand_lbl.pack(pady=(40, 5))
        
        ver_lbl = ctk.CTkLabel(
            card,
            text="Version 2.0.0 — Offline & AI Suite",
            font=FONTS["body_bold"],
            text_color=THEME_COLORS["primary"][1]
        )
        ver_lbl.pack(pady=(0, 20))
        
        # Details
        desc_lbl = ctk.CTkLabel(
            card,
            text="A high-performance image processing studio combining offline multi-threaded batch conversion, responsive custom preview resizing, and cutting-edge AI image generation powered by Grok-2.",
            font=FONTS["body"],
            text_color=THEME_COLORS["text_muted"],
            wraplength=480,
            justify="center"
        )
        desc_lbl.pack(pady=10)
        
        features_lbl = ctk.CTkLabel(
            card,
            text="• UGC Converter: Fast PNG/JPG/JPEG to WebP\n"
                 "• Custom Image Resizer: Product/Feature banner presets\n"
                 "• AI Image Generator: Powered by xAI Grok API\n"
                 "• Local History DB: Browse and regenerate past prompts",
            font=FONTS["body_bold"],
            text_color=THEME_COLORS["text_main"],
            justify="left",
            pady=15
        )
        features_lbl.pack()
        
        footer_lbl = ctk.CTkLabel(
            card,
            text="Developed by Pair Programming. All rights reserved.",
            font=FONTS["caption"],
            text_color=THEME_COLORS["text_muted"]
        )
        footer_lbl.pack(side="bottom", pady=30)
