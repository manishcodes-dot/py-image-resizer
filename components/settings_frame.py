import os
import customtkinter as ctk
from tkinter import filedialog
from components.theme import THEME_COLORS, FONTS
from components.settings_panel import SettingsPanelFrame

class UgcSettingsFrame(ctk.CTkScrollableFrame):
    def __init__(self, master, settings_manager, show_toast_callback, **kwargs):
        super().__init__(
            master,
            fg_color="transparent",
            **kwargs
        )
        self.settings = settings_manager
        self.show_toast = show_toast_callback

        # 1. Embed the existing converter settings panel
        lbl_conv_header = ctk.CTkLabel(
            self,
            text="Image Converter Settings",
            font=("Outfit", 20, "bold"),
            text_color=THEME_COLORS["text_main"],
            anchor="w"
        )
        lbl_conv_header.pack(fill="x", padx=10, pady=(10, 10))

        self.conv_settings_panel = SettingsPanelFrame(self, self.settings)
        # Note: SettingsPanelFrame has a border and bg_color built-in. Let's pack it cleanly.
        self.conv_settings_panel.pack(fill="x", padx=10, pady=(0, 20))

        # 2. Build the AI Generator settings card
        lbl_ai_header = ctk.CTkLabel(
            self,
            text="AI Image Generator Settings",
            font=("Outfit", 20, "bold"),
            text_color=THEME_COLORS["text_main"],
            anchor="w"
        )
        lbl_ai_header.pack(fill="x", padx=10, pady=(10, 10))

        self.ai_card = ctk.CTkFrame(
            self,
            fg_color=THEME_COLORS["bg_card"],
            border_color=THEME_COLORS["border"],
            border_width=1,
            corner_radius=12
        )
        self.ai_card.pack(fill="x", padx=10, pady=(0, 20))
        self.ai_card.grid_columnconfigure((0, 1), weight=1, uniform="equal")

        self._build_ai_settings()

    def _build_ai_settings(self):
        # API Key (Left Column)
        left_col = ctk.CTkFrame(self.ai_card, fg_color="transparent")
        left_col.grid(row=0, column=0, padx=16, pady=16, sticky="nsew")
        left_col.grid_columnconfigure(0, weight=1)

        lbl_api = ctk.CTkLabel(left_col, text="Grok API Key", font=FONTS["body_bold"], text_color=THEME_COLORS["text_main"], anchor="w")
        lbl_api.pack(fill="x", pady=(0, 2))
        
        self.api_entry = ctk.CTkEntry(
            left_col,
            placeholder_text="Enter your xAI Grok API Key...",
            font=FONTS["body"],
            fg_color=THEME_COLORS["bg_window"],
            border_color=THEME_COLORS["border"],
            show="*",
            height=36
        )
        self.api_entry.insert(0, self.settings.get("ai_api_key"))
        self.api_entry.bind("<KeyRelease>", lambda e: self._save_ai_setting("ai_api_key", self.api_entry.get()))
        self.api_entry.pack(fill="x", pady=(0, 12))

        # Output Folder
        lbl_folder = ctk.CTkLabel(left_col, text="AI Output Directory", font=FONTS["body_bold"], text_color=THEME_COLORS["text_main"], anchor="w")
        lbl_folder.pack(fill="x", pady=(0, 2))
        
        folder_frame = ctk.CTkFrame(left_col, fg_color="transparent")
        folder_frame.pack(fill="x", pady=(0, 12))
        
        self.folder_entry = ctk.CTkEntry(
            folder_frame,
            placeholder_text="Default (output/generated)",
            font=FONTS["small"],
            fg_color=THEME_COLORS["bg_window"],
            border_color=THEME_COLORS["border"],
            height=36
        )
        self.folder_entry.insert(0, self.settings.get("ai_output_folder"))
        self.folder_entry.bind("<KeyRelease>", lambda e: self._save_ai_setting("ai_output_folder", self.folder_entry.get()))
        self.folder_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        btn_browse = ctk.CTkButton(
            folder_frame,
            text="Browse",
            width=70,
            font=FONTS["small"],
            fg_color=THEME_COLORS["bg_hover"],
            text_color=THEME_COLORS["text_main"],
            border_color=THEME_COLORS["border"],
            border_width=1,
            hover_color=THEME_COLORS["border"],
            command=self._browse_ai_folder,
            height=36
        )
        btn_browse.pack(side="right")

        # Provider Selection
        lbl_prov = ctk.CTkLabel(left_col, text="AI Provider", font=FONTS["body_bold"], text_color=THEME_COLORS["text_main"], anchor="w")
        lbl_prov.pack(fill="x", pady=(0, 2))
        self.prov_var = ctk.StringVar(value=self.settings.get("ai_provider"))
        self.prov_sel = ctk.CTkOptionMenu(
            left_col,
            values=["Grok"],
            variable=self.prov_var,
            font=FONTS["body"],
            fg_color=THEME_COLORS["bg_window"],
            button_color=THEME_COLORS["border"],
            button_hover_color=THEME_COLORS["bg_hover"],
            dropdown_fg_color=THEME_COLORS["bg_card"],
            command=lambda v: self._save_ai_setting("ai_provider", v),
            height=36
        )
        self.prov_sel.pack(fill="x", pady=(0, 12))

        # Right Column (Defaults & Toggles)
        right_col = ctk.CTkFrame(self.ai_card, fg_color="transparent")
        right_col.grid(row=0, column=1, padx=16, pady=16, sticky="nsew")
        right_col.grid_columnconfigure(0, weight=1)

        # Default Size
        lbl_size = ctk.CTkLabel(right_col, text="Default Image Size", font=FONTS["body_bold"], text_color=THEME_COLORS["text_main"], anchor="w")
        lbl_size.pack(fill="x", pady=(0, 2))
        self.size_var = ctk.StringVar(value=self.settings.get("ai_image_size"))
        self.size_sel = ctk.CTkOptionMenu(
            right_col,
            values=["512x512", "768x768", "1024x1024", "1024x768", "768x1024"],
            variable=self.size_var,
            font=FONTS["body"],
            fg_color=THEME_COLORS["bg_window"],
            button_color=THEME_COLORS["border"],
            button_hover_color=THEME_COLORS["bg_hover"],
            dropdown_fg_color=THEME_COLORS["bg_card"],
            command=lambda v: self._save_ai_setting("ai_image_size", v),
            height=36
        )
        self.size_sel.pack(fill="x", pady=(0, 12))

        # Default Quality
        lbl_qual = ctk.CTkLabel(right_col, text="Generation Quality", font=FONTS["body_bold"], text_color=THEME_COLORS["text_main"], anchor="w")
        lbl_qual.pack(fill="x", pady=(0, 2))
        self.qual_var = ctk.StringVar(value=self.settings.get("ai_quality"))
        self.qual_sel = ctk.CTkOptionMenu(
            right_col,
            values=["Standard", "HD"],
            variable=self.qual_var,
            font=FONTS["body"],
            fg_color=THEME_COLORS["bg_window"],
            button_color=THEME_COLORS["border"],
            button_hover_color=THEME_COLORS["bg_hover"],
            dropdown_fg_color=THEME_COLORS["bg_card"],
            command=lambda v: self._save_ai_setting("ai_quality", v),
            height=36
        )
        self.qual_sel.pack(fill="x", pady=(0, 16))

        # Checkboxes (Save History, Auto Save)
        self.history_var = ctk.BooleanVar(value=self.settings.get("ai_save_history"))
        self.history_cb = ctk.CTkCheckBox(
            right_col,
            text="Save Generation History locally",
            variable=self.history_var,
            command=lambda: self._save_ai_setting("ai_save_history", self.history_var.get()),
            fg_color=THEME_COLORS["primary"],
            hover_color=THEME_COLORS["primary_hover"],
            font=FONTS["body"]
        )
        self.history_cb.pack(fill="x", pady=6)

        self.autosave_var = ctk.BooleanVar(value=self.settings.get("ai_auto_save"))
        self.autosave_cb = ctk.CTkCheckBox(
            right_col,
            text="Auto-save images to output directory",
            variable=self.autosave_var,
            command=lambda: self._save_ai_setting("ai_auto_save", self.autosave_var.get()),
            fg_color=THEME_COLORS["primary"],
            hover_color=THEME_COLORS["primary_hover"],
            font=FONTS["body"]
        )
        self.autosave_cb.pack(fill="x", pady=6)

    def _browse_ai_folder(self):
        folder = filedialog.askdirectory(title="Select AI Output Folder")
        if folder:
            self.folder_entry.delete(0, "end")
            self.folder_entry.insert(0, folder)
            self._save_ai_setting("ai_output_folder", folder)

    def _save_ai_setting(self, key, value):
        self.settings.set(key, value)
