import os
import customtkinter as ctk
from tkinter import filedialog
from components.theme import THEME_COLORS, FONTS

class SettingsPanelFrame(ctk.CTkFrame):
    def __init__(self, master, settings_manager, **kwargs):
        super().__init__(
            master,
            fg_color=THEME_COLORS["bg_card"],
            border_color=THEME_COLORS["border"],
            border_width=1,
            corner_radius=12,
            **kwargs
        )
        self.settings = settings_manager

        # Configure layout: two columns for balanced layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=0)  # Section Headers
        self.grid_rowconfigure(1, weight=1)  # Content

        # LEFT COLUMN: Conversion & Output Settings
        self.left_col = ctk.CTkFrame(self, fg_color="transparent")
        self.left_col.grid(row=0, column=0, rowspan=2, padx=16, pady=16, sticky="nsew")
        self.left_col.grid_columnconfigure(0, weight=1)

        # Right Column: Resizing & Behavior Checkboxes
        self.right_col = ctk.CTkFrame(self, fg_color="transparent")
        self.right_col.grid(row=0, column=1, rowspan=2, padx=16, pady=16, sticky="nsew")
        self.right_col.grid_columnconfigure(0, weight=1)

        self._build_left_column()
        self._build_right_column()
        
        # Trigger initial reactive state checks
        self._on_lossless_toggle()
        self._on_output_mode_change(self.settings.get("output_mode"))
        self._on_resize_mode_change(self.settings.get("resize_mode"))

    def _build_left_column(self) -> None:
        # Title: Image Settings
        lbl_img_settings = ctk.CTkLabel(
            self.left_col, text="Compression Settings", font=FONTS["header"], text_color=THEME_COLORS["text_main"], anchor="w"
        )
        lbl_img_settings.pack(fill="x", pady=(0, 12))

        # Quality Slider container
        self.slider_frame = ctk.CTkFrame(self.left_col, fg_color="transparent")
        self.slider_frame.pack(fill="x", pady=6)
        
        self.quality_lbl = ctk.CTkLabel(
            self.slider_frame, text="Quality: 85%", font=FONTS["body_bold"], text_color=THEME_COLORS["text_main"], anchor="w"
        )
        self.quality_lbl.pack(fill="x")
        
        initial_quality = self.settings.get("quality")
        self.quality_slider = ctk.CTkSlider(
            self.slider_frame,
            from_=1,
            to=100,
            number_of_steps=100,
            command=self._on_quality_slider_move,
            button_color=THEME_COLORS["primary"],
            button_hover_color=THEME_COLORS["primary_hover"]
        )
        self.quality_slider.set(initial_quality)
        self.quality_slider.pack(fill="x", pady=4)
        self.quality_lbl.configure(text=f"Quality: {initial_quality}%")

        # Lossless Mode Checkbox
        self.lossless_var = ctk.BooleanVar(value=self.settings.get("lossless"))
        self.lossless_cb = ctk.CTkCheckBox(
            self.left_col,
            text="Lossless Mode (Ignores Quality)",
            variable=self.lossless_var,
            command=self._on_lossless_toggle,
            fg_color=THEME_COLORS["primary"],
            hover_color=THEME_COLORS["primary_hover"],
            font=FONTS["body"]
        )
        self.lossless_cb.pack(fill="x", pady=8)

        # Separator line
        sep = ctk.CTkFrame(self.left_col, height=1, fg_color=THEME_COLORS["border"])
        sep.pack(fill="x", pady=12)

        # Title: Output Settings
        lbl_out_settings = ctk.CTkLabel(
            self.left_col, text="Destination Folder", font=FONTS["header"], text_color=THEME_COLORS["text_main"], anchor="w"
        )
        lbl_out_settings.pack(fill="x", pady=(0, 8))

        # Output Mode Select
        self.out_mode_var = ctk.StringVar(value=self.settings.get("output_mode"))
        
        self.radio_same = ctk.CTkRadioButton(
            self.left_col,
            text="Same Folder as Original",
            variable=self.out_mode_var,
            value="same",
            command=lambda: self._on_output_mode_change("same"),
            fg_color=THEME_COLORS["primary"],
            hover_color=THEME_COLORS["primary_hover"],
            font=FONTS["body"]
        )
        self.radio_same.pack(fill="x", pady=4)

        self.radio_custom = ctk.CTkRadioButton(
            self.left_col,
            text="Custom Destination Directory",
            variable=self.out_mode_var,
            value="custom",
            command=lambda: self._on_output_mode_change("custom"),
            fg_color=THEME_COLORS["primary"],
            hover_color=THEME_COLORS["primary_hover"],
            font=FONTS["body"]
        )
        self.radio_custom.pack(fill="x", pady=4)

        # Custom Path input & Browse button container
        self.path_container = ctk.CTkFrame(self.left_col, fg_color="transparent")
        self.path_container.pack(fill="x", pady=8)
        
        self.path_entry = ctk.CTkEntry(
            self.path_container,
            placeholder_text="Choose destination folder...",
            font=FONTS["small"],
            border_color=THEME_COLORS["border"],
            text_color=THEME_COLORS["text_main"]
        )
        self.path_entry.insert(0, self.settings.get("custom_output_dir"))
        # Bind typing to save path
        self.path_entry.bind("<KeyRelease>", lambda e: self._on_custom_dir_typing())
        self.path_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        
        self.browse_btn = ctk.CTkButton(
            self.path_container,
            text="Browse",
            width=70,
            font=FONTS["small"],
            fg_color=THEME_COLORS["bg_hover"],
            text_color=THEME_COLORS["text_main"],
            border_color=THEME_COLORS["border"],
            border_width=1,
            hover_color=THEME_COLORS["border"],
            command=self._browse_custom_dir
        )
        self.browse_btn.pack(side="right")

    def _build_right_column(self) -> None:
        # Title: Resize Settings
        lbl_resize = ctk.CTkLabel(
            self.right_col, text="Resize Settings", font=FONTS["header"], text_color=THEME_COLORS["text_main"], anchor="w"
        )
        lbl_resize.pack(fill="x", pady=(0, 12))

        # Dropdown options
        resize_options = {
            "Original Resolution": "original",
            "Fit Width: 1920px": "1920",
            "Fit Width: 1080px": "1080",
            "Fit Width: 720px": "720",
            "Custom Width (px)": "custom_w",
            "Custom Height (px)": "custom_h"
        }
        self.option_mapping = resize_options  # save mapping
        
        # Find current option text
        current_mode = self.settings.get("resize_mode")
        current_opt_text = "Original Resolution"
        for k, v in resize_options.items():
            if v == current_mode:
                current_opt_text = k
                break

        self.resize_menu = ctk.CTkOptionMenu(
            self.right_col,
            values=list(resize_options.keys()),
            command=self._on_resize_menu_select,
            font=FONTS["body"],
            fg_color=THEME_COLORS["bg_card"],
            button_color=THEME_COLORS["border"],
            button_hover_color=THEME_COLORS["text_muted"],
            dropdown_fg_color=THEME_COLORS["bg_card"],
            dropdown_text_color=THEME_COLORS["text_main"],
            text_color=THEME_COLORS["text_main"]
        )
        self.resize_menu.set(current_opt_text)
        self.resize_menu.pack(fill="x", pady=4)

        # Custom Dimensions container
        self.dim_frame = ctk.CTkFrame(self.right_col, fg_color="transparent")
        self.dim_frame.pack(fill="x", pady=6)
        
        self.dim_lbl = ctk.CTkLabel(
            self.dim_frame, text="Custom Dimension Value (px):", font=FONTS["small"], text_color=THEME_COLORS["text_muted"], anchor="w"
        )
        self.dim_lbl.grid(row=0, column=0, columnspan=2, sticky="ew")
        
        # Single input field for custom size based on whether Width or Height is chosen
        self.dim_entry = ctk.CTkEntry(
            self.dim_frame,
            width=100,
            font=FONTS["small"],
            border_color=THEME_COLORS["border"]
        )
        current_custom_val = self.settings.get("custom_width") if current_mode == "custom_w" else self.settings.get("custom_height")
        self.dim_entry.insert(0, str(current_custom_val))
        self.dim_entry.bind("<KeyRelease>", lambda e: self._on_custom_dim_typing())
        self.dim_entry.grid(row=1, column=0, sticky="w", pady=4)

        # Aspect Ratio check
        self.aspect_var = ctk.BooleanVar(value=self.settings.get("maintain_aspect"))
        self.aspect_cb = ctk.CTkCheckBox(
            self.right_col,
            text="Maintain Aspect Ratio",
            variable=self.aspect_var,
            command=self._on_aspect_toggle,
            fg_color=THEME_COLORS["primary"],
            hover_color=THEME_COLORS["primary_hover"],
            font=FONTS["small"]
        )
        self.aspect_cb.pack(fill="x", pady=4)

        # Separator line
        sep2 = ctk.CTkFrame(self.right_col, height=1, fg_color=THEME_COLORS["border"])
        sep2.pack(fill="x", pady=12)

        # Behavior Checkboxes Section
        lbl_behavior = ctk.CTkLabel(
            self.right_col, text="File Options", font=FONTS["header"], text_color=THEME_COLORS["text_main"], anchor="w"
        )
        lbl_behavior.pack(fill="x", pady=(0, 8))

        # Checkboxes
        self.meta_var = ctk.BooleanVar(value=self.settings.get("preserve_metadata"))
        self.meta_cb = ctk.CTkCheckBox(
            self.right_col,
            text="Preserve Metadata (EXIF/ICC)",
            variable=self.meta_var,
            command=self._on_metadata_toggle,
            fg_color=THEME_COLORS["primary"],
            font=FONTS["body"]
        )
        self.meta_cb.pack(fill="x", pady=4)

        self.overwrite_var = ctk.BooleanVar(value=self.settings.get("overwrite"))
        self.overwrite_cb = ctk.CTkCheckBox(
            self.right_col,
            text="Overwrite Existing Files",
            variable=self.overwrite_var,
            command=self._on_overwrite_toggle,
            fg_color=THEME_COLORS["primary"],
            font=FONTS["body"]
        )
        self.overwrite_cb.pack(fill="x", pady=4)

        self.delete_var = ctk.BooleanVar(value=self.settings.get("delete_original"))
        self.delete_cb = ctk.CTkCheckBox(
            self.right_col,
            text="Delete Original After Conversion",
            variable=self.delete_var,
            command=self._on_delete_toggle,
            fg_color=THEME_COLORS["primary"],
            font=FONTS["body"]
        )
        self.delete_cb.pack(fill="x", pady=4)

        self.open_complete_var = ctk.BooleanVar(value=self.settings.get("open_after_complete"))
        self.open_complete_cb = ctk.CTkCheckBox(
            self.right_col,
            text="Open Destination Folder When Done",
            variable=self.open_complete_var,
            command=self._on_open_complete_toggle,
            fg_color=THEME_COLORS["primary"],
            font=FONTS["body"]
        )
        self.open_complete_cb.pack(fill="x", pady=4)

    # Event handlers & sync with settings
    def _on_quality_slider_move(self, value) -> None:
        val = int(value)
        self.quality_lbl.configure(text=f"Quality: {val}%")
        self.settings.set("quality", val)

    def _on_lossless_toggle(self) -> None:
        lossless_enabled = self.lossless_var.get()
        self.settings.set("lossless", lossless_enabled)
        # Disable/Enable quality slider based on lossless setting
        if lossless_enabled:
            self.quality_slider.configure(state="disabled")
            self.quality_lbl.configure(text="Quality: Locked (Lossless)")
        else:
            self.quality_slider.configure(state="normal")
            self.quality_lbl.configure(text=f"Quality: {int(self.quality_slider.get())}%")

    def _on_output_mode_change(self, mode: str) -> None:
        self.settings.set("output_mode", mode)
        if mode == "same":
            self.path_entry.configure(state="disabled")
            self.browse_btn.configure(state="disabled")
        else:
            self.path_entry.configure(state="normal")
            self.browse_btn.configure(state="normal")

    def _browse_custom_dir(self) -> None:
        initial = self.settings.get("custom_output_dir") or os.path.expanduser("~")
        folder = filedialog.askdirectory(title="Choose Destination Folder", initialdir=initial)
        if folder:
            self.path_entry.configure(state="normal")
            self.path_entry.delete(0, "end")
            self.path_entry.insert(0, folder)
            self.settings.set("custom_output_dir", folder)
            # Recheck mode state
            self._on_output_mode_change(self.out_mode_var.get())

    def _on_custom_dir_typing(self) -> None:
        path = self.path_entry.get()
        self.settings.set("custom_output_dir", path)

    def _on_resize_menu_select(self, option_text: str) -> None:
        mode = self.option_mapping.get(option_text, "original")
        self.settings.set("resize_mode", mode)
        self._on_resize_mode_change(mode)

    def _on_resize_mode_change(self, mode: str) -> None:
        # Control aspect ratio and entry boxes visibility
        if mode == "original":
            self.dim_lbl.configure(text="Dimensions: Locked")
            self.dim_entry.configure(state="disabled")
            self.aspect_cb.configure(state="disabled")
        elif mode in ("1920", "1080", "720"):
            self.dim_lbl.configure(text=f"Preset Aspect Lock ({mode}px)")
            self.dim_entry.configure(state="disabled")
            self.aspect_cb.configure(state="disabled")
        else:
            # Custom width or height
            if mode == "custom_w":
                self.dim_lbl.configure(text="Custom Width (px):")
                self.dim_entry.configure(state="normal")
                self.dim_entry.delete(0, "end")
                self.dim_entry.insert(0, str(self.settings.get("custom_width")))
            elif mode == "custom_h":
                self.dim_lbl.configure(text="Custom Height (px):")
                self.dim_entry.configure(state="normal")
                self.dim_entry.delete(0, "end")
                self.dim_entry.insert(0, str(self.settings.get("custom_height")))
            self.aspect_cb.configure(state="normal")

    def _on_custom_dim_typing(self) -> None:
        mode = self.settings.get("resize_mode")
        val_str = self.dim_entry.get()
        try:
            val = int(val_str)
            if mode == "custom_w":
                self.settings.set("custom_width", val)
            elif mode == "custom_h":
                self.settings.set("custom_height", val)
        except ValueError:
            pass  # Ignore invalid integer inputs during typing

    def _on_aspect_toggle(self) -> None:
        self.settings.set("maintain_aspect", self.aspect_var.get())

    def _on_metadata_toggle(self) -> None:
        self.settings.set("preserve_metadata", self.meta_var.get())

    def _on_overwrite_toggle(self) -> None:
        self.settings.set("overwrite", self.overwrite_var.get())

    def _on_delete_toggle(self) -> None:
        self.settings.set("delete_original", self.delete_var.get())

    def _on_open_complete_toggle(self) -> None:
        self.settings.set("open_after_complete", self.open_complete_var.get())

    def set_enabled(self, enabled: bool) -> None:
        """Enables or disables all input controls in the settings panel."""
        state = "normal" if enabled else "disabled"
        
        self.quality_slider.configure(state=state)
        self.lossless_cb.configure(state=state)
        self.radio_same.configure(state=state)
        self.radio_custom.configure(state=state)
        self.path_entry.configure(state=state)
        self.browse_btn.configure(state=state)
        self.resize_menu.configure(state=state)
        self.dim_entry.configure(state=state)
        self.aspect_cb.configure(state=state)
        self.meta_cb.configure(state=state)
        self.overwrite_cb.configure(state=state)
        self.delete_cb.configure(state=state)
        self.open_complete_cb.configure(state=state)
        
        # If enabling, restore sub-component constraints
        if enabled:
            self._on_lossless_toggle()
            self._on_output_mode_change(self.out_mode_var.get())
            self._on_resize_mode_change(self.settings.get("resize_mode"))
