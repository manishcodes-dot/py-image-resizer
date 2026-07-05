import os
import customtkinter as ctk
from datetime import datetime
from components.theme import THEME_COLORS, FONTS

class DashboardFrame(ctk.CTkFrame):
    def __init__(self, master, state_manager, history_service, on_navigate_callback, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.state_manager = state_manager
        self.history_service = history_service
        self.navigate = on_navigate_callback

        # Grid config
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)  # Title
        self.grid_rowconfigure(1, weight=0)  # Stats Cards Row
        self.grid_rowconfigure(2, weight=1)  # Recent activity / Quick start

        # Title
        title_lbl = ctk.CTkLabel(
            self,
            text="Studio Dashboard",
            font=("Outfit", 24, "bold"),
            text_color=THEME_COLORS["text_main"]
        )
        title_lbl.grid(row=0, column=0, padx=20, pady=(20, 15), sticky="w")

        # Container for cards
        self.cards_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.cards_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        self.cards_frame.grid_columnconfigure((0, 1, 2), weight=1, uniform="equal")

        self.update_dashboard()

    def update_dashboard(self) -> None:
        # Clear existing card widgets
        for widget in self.cards_frame.winfo_children():
            widget.destroy()

        # Fetch stats
        queue_size = len(self.state_manager.files)
        completed_convs = getattr(self.state_manager, "completed_count", 0)  # fallback
        # Let's count files in state_manager that are "Completed"
        completed_convs = sum(1 for f in self.state_manager.files if f.get("status") == "Completed")
        
        total_generated = len(self.history_service.history)
        last_gen_str = "None"
        if total_generated > 0:
            last_gen_str = self.history_service.history[0]["date"]

        # Card 1: Batch Converter Status
        self._create_stat_card(
            self.cards_frame, 
            col=0, 
            title="Image Converter Queue", 
            value=f"{queue_size} File(s)", 
            subtext="Ready for processing", 
            accent_color="#10B981"  # Emerald
        )

        # Card 2: AI Image Generator Status
        self._create_stat_card(
            self.cards_frame, 
            col=1, 
            title="AI Image Generations", 
            value=f"{total_generated} Image(s)", 
            subtext=f"Last: {last_gen_str}", 
            accent_color="#6366F1"  # Indigo
        )

        # Card 3: Quick Overview / Theme Status
        self._create_stat_card(
            self.cards_frame, 
            col=2, 
            title="System Mode", 
            value="Active", 
            subtext="Ready to convert & generate", 
            accent_color=THEME_COLORS["primary"][1]
        )

        # Row 2: Quick Start Container
        qs_frame = ctk.CTkFrame(self, fg_color=THEME_COLORS["bg_card"], border_color=THEME_COLORS["border"], border_width=1, corner_radius=10)
        qs_frame.grid(row=2, column=0, padx=20, pady=(20, 20), sticky="nsew")
        qs_frame.grid_columnconfigure((0, 1), weight=1, uniform="equal")
        qs_frame.grid_rowconfigure(0, weight=1)

        # Left Column: UGC Image Converter Quick Start
        conv_qs = ctk.CTkFrame(qs_frame, fg_color="transparent")
        conv_qs.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        
        lbl_conv = ctk.CTkLabel(conv_qs, text="UGC Converter", font=("Outfit", 18, "bold"), text_color=THEME_COLORS["text_main"])
        lbl_conv.pack(anchor="w", pady=(0, 5))
        lbl_conv_desc = ctk.CTkLabel(
            conv_qs, 
            text="Batch convert JPG, JPEG, and PNG images directly to WebP and other formats offline with multi-threading.",
            font=FONTS["body"],
            text_color=THEME_COLORS["text_muted"],
            wraplength=320,
            justify="left"
        )
        lbl_conv_desc.pack(anchor="w", pady=(0, 15))
        
        btn_go_conv = ctk.CTkButton(
            conv_qs,
            text="Open Converter",
            font=FONTS["body_bold"],
            fg_color=THEME_COLORS["primary"],
            hover_color=THEME_COLORS["primary_hover"],
            command=lambda: self.navigate("Image Converter")
        )
        btn_go_conv.pack(anchor="w")

        # Right Column: AI Generator Quick Start
        ai_qs = ctk.CTkFrame(qs_frame, fg_color="transparent")
        ai_qs.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        
        lbl_ai = ctk.CTkLabel(ai_qs, text="AI Image Generator", font=("Outfit", 18, "bold"), text_color=THEME_COLORS["text_main"])
        lbl_ai.pack(anchor="w", pady=(0, 5))
        lbl_ai_desc = ctk.CTkLabel(
            ai_qs, 
            text="Generate images from text prompts using Grok-2. Fully threaded, non-blocking UI with complete local history.",
            font=FONTS["body"],
            text_color=THEME_COLORS["text_muted"],
            wraplength=320,
            justify="left"
        )
        lbl_ai_desc.pack(anchor="w", pady=(0, 15))
        
        btn_go_ai = ctk.CTkButton(
            ai_qs,
            text="Start AI Generation",
            font=FONTS["body_bold"],
            fg_color="#6366F1",
            hover_color="#4F46E5",
            command=lambda: self.navigate("AI Image Generator")
        )
        btn_go_ai.pack(anchor="w")

    def _create_stat_card(self, parent, col: int, title: str, value: str, subtext: str, accent_color: str):
        card = ctk.CTkFrame(parent, fg_color=THEME_COLORS["bg_card"], border_color=THEME_COLORS["border"], border_width=1, corner_radius=10, height=120)
        card.grid(row=0, column=col, padx=8, sticky="ew")
        card.grid_propagate(False)
        
        # Color bar on the left
        bar = ctk.CTkFrame(card, width=4, fg_color=accent_color)
        bar.pack(side="left", fill="y", padx=(0, 12))

        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(side="left", fill="both", expand=True, pady=12)

        lbl_title = ctk.CTkLabel(content, text=title, font=("Outfit", 11, "bold"), text_color=THEME_COLORS["text_muted"])
        lbl_title.pack(anchor="w")

        lbl_val = ctk.CTkLabel(content, text=value, font=("Outfit", 18, "bold"), text_color=THEME_COLORS["text_main"])
        lbl_val.pack(anchor="w", pady=(2, 0))

        lbl_sub = ctk.CTkLabel(content, text=subtext, font=FONTS["caption"], text_color=THEME_COLORS["text_muted"])
        lbl_sub.pack(anchor="w", pady=(2, 0))
