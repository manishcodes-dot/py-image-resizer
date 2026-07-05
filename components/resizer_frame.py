import os
import re
from typing import List, Tuple
import customtkinter as ctk
from tkinter import filedialog, messagebox
from tkinter.colorchooser import askcolor
from PIL import Image
import tkinter as tk
from components.theme import THEME_COLORS, FONTS
from tkinterdnd2 import DND_FILES

def create_checkerboard(width: int, height: int, cell_size: int = 12) -> Image.Image:
    """Generates a high-quality checkerboard pattern PIL image for transparent background previews."""
    cb = Image.new("RGBA", (width, height), (15, 15, 17, 255))
    pixels = cb.load()
    for y in range(height):
        for x in range(width):
            if ((x // cell_size) + (y // cell_size)) % 2 == 0:
                pixels[x, y] = (28, 28, 30, 255)
    return cb

def resize_and_pad(img: Image.Image, target_width: int, target_height: int, bg_mode: str, bg_color: str) -> Image.Image:
    """Resizes a PIL image to fit inside target dimensions keeping aspect ratio, padding the rest."""
    img_rgba = img.convert("RGBA")
    
    # Calculate aspect-ratio preserving dimensions
    scale = min(target_width / img_rgba.width, target_height / img_rgba.height)
    new_w = max(1, int(img_rgba.width * scale))
    new_h = max(1, int(img_rgba.height * scale))
    
    resized = img_rgba.resize((new_w, new_h), Image.Resampling.LANCZOS)
    
    # Generate background frame
    if bg_mode == "transparent":
        bg = Image.new("RGBA", (target_width, target_height), (0, 0, 0, 0))
    else:
        try:
            h = bg_color.lstrip('#')
            rgb = tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
            bg = Image.new("RGBA", (target_width, target_height), rgb + (255,))
        except Exception:
            bg = Image.new("RGBA", (target_width, target_height), (20, 21, 23, 255))
            
    # Composite the resized image in the center
    x = (target_width - new_w) // 2
    y = (target_height - new_h) // 2
    bg.paste(resized, (x, y), resized)
    return bg

class ResizerFrame(ctk.CTkFrame):
    def __init__(self, master, logger_service, show_toast_callback, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.logger = logger_service
        self.show_toast = show_toast_callback
        
        self.source_image = None
        self.source_filename = ""
        self.source_filepath = ""
        self.picker_tooltip = None
        
        # Grid layout to expand nicely
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Build views
        self.upload_view = None
        self.workshop_view = None
        
        self._show_upload_view()
        
    def _show_upload_view(self) -> None:
        """Renders the drag and drop dropzone for file upload."""
        if self.workshop_view:
            self.workshop_view.grid_forget()
            
        if not self.upload_view:
            self.upload_view = ctk.CTkFrame(self, fg_color="transparent")
            self.upload_view.grid_columnconfigure(0, weight=1)
            self.upload_view.grid_rowconfigure(0, weight=1)
            
            # Central Container
            center = ctk.CTkFrame(self.upload_view, fg_color="transparent")
            center.grid(row=0, column=0, pady=(20, 20), sticky="ns")
            center.grid_columnconfigure(0, weight=1)
            
            # Title
            title_lbl = ctk.CTkLabel(
                center,
                text="Cover & Banner Resizer",
                font=("Outfit", 32, "bold"),
                text_color=THEME_COLORS["text_main"]
            )
            title_lbl.grid(row=0, column=0, pady=(10, 8), sticky="w")
            
            # Description
            desc_lbl = ctk.CTkLabel(
                center,
                text="Resize, crop, and pad images to social media card specifications.\nPresets: 500x500 (Cover) and 960x502 (Banner), automatically converting to WebP.",
                font=FONTS["body"],
                text_color=THEME_COLORS["text_muted"],
                justify="left",
                anchor="w"
            )
            desc_lbl.grid(row=1, column=0, pady=(0, 20), sticky="w")
            
            # Upload Card Box
            self.upload_card = ctk.CTkFrame(
                center,
                width=580,
                height=280,
                fg_color=THEME_COLORS["bg_card"],
                border_color=THEME_COLORS["border"],
                border_width=1,
                corner_radius=16
            )
            self.upload_card.grid(row=2, column=0, pady=10, sticky="ew")
            self.upload_card.grid_propagate(False)
            self.upload_card.grid_columnconfigure(0, weight=1)
            self.upload_card.grid_rowconfigure(0, weight=1)
            
            inner = ctk.CTkFrame(self.upload_card, fg_color="transparent")
            inner.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
            inner.grid_columnconfigure(0, weight=1)
            
            cloud_lbl = ctk.CTkLabel(
                inner,
                text="🖼",
                font=("Outfit", 48, "normal"),
                text_color=THEME_COLORS["primary"],
                anchor="center",
                justify="center"
            )
            cloud_lbl.grid(row=0, column=0, pady=(20, 8), sticky="")
            
            card_head = ctk.CTkLabel(
                inner,
                text="Drag & drop your PNG/JPG image here",
                font=("Outfit", 18, "bold"),
                text_color=THEME_COLORS["text_main"]
            )
            card_head.grid(row=1, column=0, pady=2)
            
            card_sub = ctk.CTkLabel(
                inner,
                text="or click to browse from your computer.",
                font=FONTS["body"],
                text_color=THEME_COLORS["text_muted"]
            )
            card_sub.grid(row=2, column=0, pady=(0, 20))
            
            select_btn = ctk.CTkButton(
                inner,
                text="Select Image File",
                width=180,
                height=38,
                font=FONTS["body_bold"],
                fg_color=THEME_COLORS["primary"],
                hover_color=THEME_COLORS["primary_hover"],
                corner_radius=6,
                command=self._browse_image
            )
            select_btn.grid(row=3, column=0, pady=(0, 15))
            
            # Drag & drop setup
            self.upload_card.drop_target_register(DND_FILES)
            self.upload_card.dnd_bind("<<DragEnter>>", self._on_drag_enter)
            self.upload_card.dnd_bind("<<DragLeave>>", self._on_drag_leave)
            self.upload_card.dnd_bind("<<Drop>>", self._on_drop)
            
            # Clicking opens file selector
            self.upload_card.bind("<Button-1>", lambda e: self._browse_image())
            inner.bind("<Button-1>", lambda e: self._browse_image())
            cloud_lbl.bind("<Button-1>", lambda e: self._browse_image())
            card_head.bind("<Button-1>", lambda e: self._browse_image())
            card_sub.bind("<Button-1>", lambda e: self._browse_image())
            
        self.upload_view.grid(row=0, column=0, padx=16, pady=16, sticky="nsew")

    def _on_drag_enter(self, event) -> None:
        self.upload_card.configure(border_color=THEME_COLORS["border_active"])

    def _on_drag_leave(self, event) -> None:
        self.upload_card.configure(border_color=THEME_COLORS["border"])

    def _on_drop(self, event) -> None:
        self.upload_card.configure(border_color=THEME_COLORS["border"])
        raw_data = event.data
        if not raw_data:
            return
        
        # Handle curly braces from tkinterDnD paths containing spaces
        pattern = r'\{([^}]+)\}|(\S+)'
        matches = re.findall(pattern, raw_data)
        paths = []
        for m in matches:
            path = m[0] if m[0] else m[1]
            paths.append(path.strip())
            
        if paths:
            self._load_image_file(paths[0])

    def _browse_image(self) -> None:
        file_path = filedialog.askopenfilename(
            title="Select Image to Resize",
            filetypes=[
                ("Image Files", "*.jpg;*.jpeg;*.png"),
                ("PNG Images", "*.png"),
                ("JPEG Images", "*.jpg;*.jpeg")
            ]
        )
        if file_path:
            self._load_image_file(file_path)

    def _load_image_file(self, filepath: str) -> None:
        """Loads the image into memory and initializes workshop interface."""
        if not os.path.exists(filepath):
            return
        try:
            self.source_image = Image.open(filepath)
            self.source_filepath = filepath
            self.source_filename = os.path.basename(filepath)
            self.logger.info(f"Loaded image for resizer: {self.source_filename}")
            
            # Switch view
            self._show_workshop_view()
        except Exception as e:
            self.logger.error(f"Failed to open image file: {e}")
            messagebox.showerror("Error", f"Could not load image: {e}")

    def _show_workshop_view(self) -> None:
        """Renders the main customization studio layout."""
        if self.upload_view:
            self.upload_view.grid_forget()
            
        if self.workshop_view:
            self.workshop_view.destroy()
            
        self.workshop_view = ctk.CTkFrame(self, fg_color="transparent")
        self.workshop_view.grid_columnconfigure(0, weight=0, minsize=310)  # Settings pane
        self.workshop_view.grid_columnconfigure(1, weight=1)  # Preview Cards pane
        self.workshop_view.grid_rowconfigure(0, weight=1)
        
        # Pre-populate settings variables
        name_without_ext, _ = os.path.splitext(self.source_filename)
        self.output_name_var = ctk.StringVar(value=name_without_ext)
        self.bg_mode_var = ctk.StringVar(value="transparent")
        self.bg_color_var = ctk.StringVar(value="#141517")
        
        # 1. Left Side Control Panel
        self.settings_card = ctk.CTkFrame(
            self.workshop_view,
            fg_color=THEME_COLORS["bg_card"],
            border_color=THEME_COLORS["border"],
            border_width=1,
            corner_radius=12
        )
        self.settings_card.grid(row=0, column=0, padx=(0, 16), pady=4, sticky="nsew")
        self.settings_card.grid_columnconfigure(0, weight=1)
        
        # Title of settings
        hdr_frame = ctk.CTkFrame(self.settings_card, fg_color="transparent")
        hdr_frame.pack(fill="x", padx=16, pady=(16, 8))
        
        lbl_title = ctk.CTkLabel(
            hdr_frame,
            text="Studio Controls",
            font=FONTS["header"],
            text_color=THEME_COLORS["text_main"]
        )
        lbl_title.pack(side="left")
        
        btn_change = ctk.CTkButton(
            hdr_frame,
            text="Remove",
            width=65,
            height=24,
            font=FONTS["small"],
            fg_color=THEME_COLORS["bg_hover"],
            text_color=THEME_COLORS["text_muted"],
            hover_color=("#E5E7EB", "#2D2E32"),
            border_color=THEME_COLORS["border"],
            border_width=1,
            command=self._clear_loaded_image
        )
        btn_change.pack(side="right")
        
        # Divider
        div = ctk.CTkFrame(self.settings_card, height=1, fg_color=THEME_COLORS["border"])
        div.pack(fill="x", padx=16, pady=8)
        
        # Rename Input
        lbl_rename = ctk.CTkLabel(
            self.settings_card,
            text="Output File Name",
            font=FONTS["body_bold"],
            text_color=THEME_COLORS["text_main"]
        )
        lbl_rename.pack(anchor="w", padx=16, pady=(8, 2))
        
        self.name_entry = ctk.CTkEntry(
            self.settings_card,
            textvariable=self.output_name_var,
            font=FONTS["body"],
            fg_color=THEME_COLORS["bg_window"],
            border_color=THEME_COLORS["border"],
            height=36
        )
        self.name_entry.pack(fill="x", padx=16, pady=(0, 12))
        self.output_name_var.trace_add("write", lambda *args: self._update_previews())
        
        # Background Padding Mode
        lbl_bg = ctk.CTkLabel(
            self.settings_card,
            text="Background Mode",
            font=FONTS["body_bold"],
            text_color=THEME_COLORS["text_main"]
        )
        lbl_bg.pack(anchor="w", padx=16, pady=(8, 2))
        
        self.bg_mode_select = ctk.CTkSegmentedButton(
            self.settings_card,
            values=["Transparent", "Solid Color"],
            font=FONTS["small"],
            selected_color=THEME_COLORS["primary"][1],
            selected_hover_color=THEME_COLORS["primary_hover"][1],
            fg_color=THEME_COLORS["bg_window"],
            command=self._on_bg_mode_changed
        )
        self.bg_mode_select.set("Transparent")
        self.bg_mode_select.pack(fill="x", padx=16, pady=(0, 16))
        
        # Solid Color Options Wrapper (Hidden initially)
        self.color_section = ctk.CTkFrame(self.settings_card, fg_color="transparent")
        
        # Row 1 of color options: Custom Color Selector
        lbl_color_pick = ctk.CTkLabel(
            self.color_section,
            text="Custom Background Color",
            font=FONTS["small"],
            text_color=THEME_COLORS["text_muted"]
        )
        lbl_color_pick.pack(anchor="w", pady=(0, 2))
        
        color_input_frame = ctk.CTkFrame(self.color_section, fg_color="transparent")
        color_input_frame.pack(fill="x", pady=(0, 12))
        
        # Small colored preview box
        self.color_preview_box = ctk.CTkFrame(
            color_input_frame,
            width=28,
            height=28,
            fg_color="#141517",
            border_width=1,
            border_color=THEME_COLORS["border"]
        )
        self.color_preview_box.pack(side="left", padx=(0, 8))
        self.color_preview_box.pack_propagate(False)
        self.color_preview_box.bind("<Button-1>", lambda e: self._choose_custom_color())
        
        self.color_hex_entry = ctk.CTkEntry(
            color_input_frame,
            textvariable=self.bg_color_var,
            font=FONTS["code"],
            height=30
        )
        self.color_hex_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.bg_color_var.trace_add("write", self._on_hex_color_changed)
        
        btn_pick = ctk.CTkButton(
            color_input_frame,
            text="Pick 🎨",
            width=55,
            height=30,
            font=FONTS["small"],
            fg_color=THEME_COLORS["bg_window"],
            text_color=THEME_COLORS["text_main"],
            border_color=THEME_COLORS["border"],
            border_width=1,
            hover_color=THEME_COLORS["bg_hover"],
            command=self._choose_custom_color
        )
        btn_pick.pack(side="right")
        
        # Preset color circles/boxes
        lbl_presets = ctk.CTkLabel(
            self.color_section,
            text="Color Presets",
            font=FONTS["small"],
            text_color=THEME_COLORS["text_muted"]
        )
        lbl_presets.pack(anchor="w", pady=(4, 4))
        
        presets_grid = ctk.CTkFrame(self.color_section, fg_color="transparent")
        presets_grid.pack(fill="x", pady=(0, 10))
        
        color_presets = [
            ("#141517", "Dark"),
            ("#000000", "Black"),
            ("#FFFFFF", "White"),
            ("#10B981", "Green"),
            ("#8B5CF6", "Purple"),
            ("#EF4444", "Red"),
            ("#3B82F6", "Blue")
        ]
        
        for hex_val, label in color_presets:
            p_btn = ctk.CTkButton(
                presets_grid,
                text="",
                width=24,
                height=24,
                corner_radius=12,
                fg_color=hex_val,
                hover_color=hex_val,
                border_width=1,
                border_color="#FFFFFF" if hex_val.lower() == "#000000" else "#2D2E32",
                command=lambda val=hex_val: self.bg_color_var.set(val)
            )
            p_btn.pack(side="left", padx=4)

        # 2. Right Side Preview and Export Columns
        self.previews_container = ctk.CTkFrame(self.workshop_view, fg_color="transparent")
        self.previews_container.grid(row=0, column=1, sticky="nsew")
        self.previews_container.grid_columnconfigure(0, weight=1)
        self.previews_container.grid_columnconfigure(1, weight=1)
        self.previews_container.grid_rowconfigure(0, weight=1)
        self.previews_container.grid_rowconfigure(1, weight=0) # Bottom dual-action bar
        
        # Cover Card (500x500)
        self.cover_card = ctk.CTkFrame(
            self.previews_container,
            fg_color=THEME_COLORS["bg_card"],
            border_color=THEME_COLORS["border"],
            border_width=1,
            corner_radius=12
        )
        self.cover_card.grid(row=0, column=0, padx=(0, 8), pady=4, sticky="nsew")
        self.cover_card.grid_columnconfigure(0, weight=1)
        self.cover_card.grid_rowconfigure(2, weight=1) # preview box center
        
        lbl_cov_title = ctk.CTkLabel(
            self.cover_card,
            text="Product Image",
            font=FONTS["header"],
            text_color=THEME_COLORS["text_main"]
        )
        lbl_cov_title.grid(row=0, column=0, padx=16, pady=(16, 2), sticky="w")
        
        lbl_cov_sub = ctk.CTkLabel(
            self.cover_card,
            text="500 x 500 (1:1 Ratio) WebP",
            font=FONTS["small"],
            text_color=THEME_COLORS["text_muted"]
        )
        lbl_cov_sub.grid(row=1, column=0, padx=16, pady=(0, 10), sticky="w")
        
        # Live Preview Frame
        self.preview_frame_500 = ctk.CTkFrame(
            self.cover_card,
            fg_color=("#E5E7EB", "#09090b"),
            corner_radius=8,
            border_width=1,
            border_color=THEME_COLORS["border"]
        )
        self.preview_frame_500.grid(row=2, column=0, padx=16, pady=10, sticky="nsew")
        self.preview_frame_500.grid_columnconfigure(0, weight=1)
        self.preview_frame_500.grid_rowconfigure(0, weight=1)
        
        self.preview_lbl_500 = ctk.CTkLabel(self.preview_frame_500, text="", cursor="crosshair")
        self.preview_lbl_500.grid(row=0, column=0)
        self.preview_lbl_500.bind("<Button-1>", lambda event: self._on_preview_click(event, "cover"))
        self.preview_lbl_500.bind("<Enter>", lambda event: self._on_preview_enter(event, "cover"))
        self.preview_lbl_500.bind("<Motion>", lambda event: self._on_preview_motion(event, "cover"))
        self.preview_lbl_500.bind("<Leave>", self._on_preview_leave)
        
        btn_exp_500 = ctk.CTkButton(
            self.cover_card,
            text="Export 500x500 WebP",
            font=FONTS["body_bold"],
            fg_color=THEME_COLORS["primary"],
            hover_color=THEME_COLORS["primary_hover"],
            height=36,
            command=lambda: self._export_image("cover")
        )
        btn_exp_500.grid(row=3, column=0, padx=16, pady=16, sticky="ew")
        
        # Banner Card (960x502)
        self.banner_card = ctk.CTkFrame(
            self.previews_container,
            fg_color=THEME_COLORS["bg_card"],
            border_color=THEME_COLORS["border"],
            border_width=1,
            corner_radius=12
        )
        self.banner_card.grid(row=0, column=1, padx=(8, 0), pady=4, sticky="nsew")
        self.banner_card.grid_columnconfigure(0, weight=1)
        self.banner_card.grid_rowconfigure(2, weight=1) # preview box center
        
        lbl_ban_title = ctk.CTkLabel(
            self.banner_card,
            text="Feature Image",
            font=FONTS["header"],
            text_color=THEME_COLORS["text_main"]
        )
        lbl_ban_title.grid(row=0, column=0, padx=16, pady=(16, 2), sticky="w")
        
        lbl_ban_sub = ctk.CTkLabel(
            self.banner_card,
            text="960 x 502 (1.91:1 Ratio) WebP",
            font=FONTS["small"],
            text_color=THEME_COLORS["text_muted"]
        )
        lbl_ban_sub.grid(row=1, column=0, padx=16, pady=(0, 10), sticky="w")
        
        # Live Preview Frame
        self.preview_frame_960 = ctk.CTkFrame(
            self.banner_card,
            fg_color=("#E5E7EB", "#09090b"),
            corner_radius=8,
            border_width=1,
            border_color=THEME_COLORS["border"]
        )
        self.preview_frame_960.grid(row=2, column=0, padx=16, pady=10, sticky="nsew")
        self.preview_frame_960.grid_columnconfigure(0, weight=1)
        self.preview_frame_960.grid_rowconfigure(0, weight=1)
        
        self.preview_lbl_960 = ctk.CTkLabel(self.preview_frame_960, text="", cursor="crosshair")
        self.preview_lbl_960.grid(row=0, column=0)
        self.preview_lbl_960.bind("<Button-1>", lambda event: self._on_preview_click(event, "banner"))
        self.preview_lbl_960.bind("<Enter>", lambda event: self._on_preview_enter(event, "banner"))
        self.preview_lbl_960.bind("<Motion>", lambda event: self._on_preview_motion(event, "banner"))
        self.preview_lbl_960.bind("<Leave>", self._on_preview_leave)
        
        btn_exp_960 = ctk.CTkButton(
            self.banner_card,
            text="Export 960x502 WebP",
            font=FONTS["body_bold"],
            fg_color=THEME_COLORS["primary"],
            hover_color=THEME_COLORS["primary_hover"],
            height=36,
            command=lambda: self._export_image("banner")
        )
        btn_exp_960.grid(row=3, column=0, padx=16, pady=16, sticky="ew")
        
        # Bottom Export Both Bar
        self.export_both_bar = ctk.CTkFrame(self.previews_container, fg_color="transparent")
        self.export_both_bar.grid(row=1, column=0, columnspan=2, pady=(10, 4), sticky="ew")
        
        btn_exp_both = ctk.CTkButton(
            self.export_both_bar,
            text="Export Both Presets in WebP 🚀",
            font=FONTS["body_bold"],
            fg_color=THEME_COLORS["primary"],
            hover_color=THEME_COLORS["primary_hover"],
            height=38,
            command=self._export_both
        )
        btn_exp_both.pack(fill="x")
        
        # Render initial previews
        self._update_previews()
        self.workshop_view.grid(row=0, column=0, padx=16, pady=16, sticky="nsew")

    def _clear_loaded_image(self) -> None:
        self.source_image = None
        self.source_filepath = ""
        self.source_filename = ""
        self._show_upload_view()

    def _on_bg_mode_changed(self, mode: str) -> None:
        """Handles background padding mode toggle."""
        if mode == "Solid Color":
            self.bg_mode_var.set("color")
            self.color_section.pack(fill="x", padx=16, pady=(0, 10))
        else:
            self.bg_mode_var.set("transparent")
            self.color_section.pack_forget()
        self._update_previews()

    def _choose_custom_color(self) -> None:
        color_code = askcolor(color=self.bg_color_var.get(), title="Select Background Color")
        if color_code and color_code[1]:
            self.bg_color_var.set(color_code[1])

    def _on_hex_color_changed(self, *args) -> None:
        hex_val = self.bg_color_var.get()
        # Verify valid hex format
        if re.match(r'^#[0-9a-fA-F]{6}$', hex_val):
            # Update background colored square
            self.color_preview_box.configure(fg_color=hex_val)
            self._update_previews()

    def _on_hex_color_entry_unfocus(self, event) -> None:
        # Pad with hex if incorrect length
        pass

    def _update_previews(self) -> None:
        """Regenerates intermediate pillow representations and sets CTkImages."""
        if not self.source_image:
            return
            
        bg_mode = self.bg_mode_var.get()
        bg_color = self.bg_color_var.get()
        
        # 1. Generate core resized images (Product Image 500x500 is always transparent)
        self.img_500 = resize_and_pad(self.source_image, 500, 500, "transparent", bg_color)
        self.img_960 = resize_and_pad(self.source_image, 960, 502, bg_mode, bg_color)
        
        # 2. Prepare visual previews (layered on top of dark checkerboards if transparent)
        cb_500 = create_checkerboard(500, 500)
        cb_500.paste(self.img_500, (0, 0), self.img_500)
        preview_500_source = cb_500
        
        if bg_mode == "transparent":
            cb_960 = create_checkerboard(960, 502)
            cb_960.paste(self.img_960, (0, 0), self.img_960)
            preview_960_source = cb_960
        else:
            preview_960_source = self.img_960
            
        # 3. Create CTkImages sized for the labels
        self.preview_image_500 = ctk.CTkImage(
            light_image=preview_500_source,
            dark_image=preview_500_source,
            size=(140, 140)
        )
        self.preview_lbl_500.configure(image=self.preview_image_500)
        
        self.preview_image_960 = ctk.CTkImage(
            light_image=preview_960_source,
            dark_image=preview_960_source,
            size=(220, 115)
        )
        self.preview_lbl_960.configure(image=self.preview_image_960)

    def _export_image(self, preset: str) -> None:
        """Prompts user for save location and saves the resized WebP image."""
        if not self.source_image:
            return
            
        # Select appropriate image and suffix
        if preset == "cover":
            target_img = self.img_500
            suffix = ""
            width, height = 500, 500
        else:
            target_img = self.img_960
            suffix = "."
            width, height = 960, 502
        
        # Format initial filename suggestion
        clean_name = self.output_name_var.get().strip()
        if not clean_name:
            clean_name = "resized_image"
        # Sanitize filename
        clean_name = re.sub(r'[\\/*?:"<>|]', "", clean_name)
        suggested_name = f"{clean_name}{suffix}.webp"
        
        # Save File Dialog
        save_path = filedialog.asksaveasfilename(
            title=f"Export {width}x{height} WebP",
            initialfile=suggested_name,
            filetypes=[("WebP Image", "*.webp")],
            defaultextension=".webp"
        )
        
        if save_path:
            try:
                # Save as WebP
                target_img.save(save_path, "WEBP", quality=90)
                self.logger.info(f"Successfully exported WebP: {os.path.basename(save_path)}")
                self.show_toast(f"Export Success! Saved {os.path.basename(save_path)}.", type="success")
            except Exception as e:
                self.logger.error(f"Failed to export image: {e}")
                self.show_toast(f"Export Failed: {e}", type="error")

    def _export_both(self) -> None:
        """Saves both sizes directly into the output folder or same directory as the source image without prompting."""
        if not self.source_image:
            return
            
        # Determine destination folder (use custom output if configured, otherwise same as source file)
        dest_dir = ""
        if hasattr(self.master, "settings"):
            mode = self.master.settings.get("output_mode")
            if mode == "custom":
                dest_dir = self.master.settings.get("custom_output_dir")
        
        if not dest_dir or not os.path.exists(dest_dir):
            dest_dir = os.path.dirname(self.source_filepath)
            
        if not dest_dir or not os.path.exists(dest_dir):
            dest_dir = os.getcwd()
            
        clean_name = self.output_name_var.get().strip()
        if not clean_name:
            clean_name = "resized_image"
        clean_name = re.sub(r'[\\/*?:"<>|]', "", clean_name)
        
        path_500 = os.path.join(dest_dir, f"{clean_name}.webp")
        path_960 = os.path.join(dest_dir, f"{clean_name}..webp")
        
        try:
            self.img_500.save(path_500, "WEBP", quality=90)
            self.img_960.save(path_960, "WEBP", quality=90)
            
            self.logger.info(f"Batch exported: {os.path.basename(path_500)} and {os.path.basename(path_960)} to {dest_dir}")
            self.show_toast("Success! Saved both presets directly.", type="success")
        except Exception as e:
            self.logger.error(f"Failed to export both images: {e}")
            self.show_toast(f"Export Failed: {e}", type="error")

    def _on_preview_click(self, event, preset: str) -> None:
        if not self.source_image:
            return
            
        x, y = event.x, event.y
        
        if preset == "cover":
            width_preview, height_preview = 140, 140
            img_width, img_height = 500, 500
            source_img = self.img_500
        else:
            width_preview, height_preview = 220, 115
            img_width, img_height = 960, 502
            source_img = self.img_960
            
        # Ensure coordinates are within bounds
        x = max(0, min(x, width_preview - 1))
        y = max(0, min(y, height_preview - 1))
        
        # Map to actual image coordinates
        img_x = int(x * (img_width / width_preview))
        img_y = int(y * (img_height / height_preview))
        
        # Ensure mapped coordinates are within bounds of the image
        img_x = max(0, min(img_x, img_width - 1))
        img_y = max(0, min(img_y, img_height - 1))
        
        try:
            pixel = source_img.getpixel((img_x, img_y))
            # Check if transparent
            if len(pixel) == 4 and pixel[3] < 10:
                return
                
            r, g, b = pixel[:3]
            hex_color = f"#{r:02x}{g:02x}{b:02x}"
            self.bg_color_var.set(hex_color)
            
            # Switch background mode to Solid Color if it is transparent
            if self.bg_mode_var.get() == "transparent":
                self.bg_mode_select.set("Solid Color")
                self._on_bg_mode_changed("Solid Color")
                
            self.logger.info(f"Picked color {hex_color} from preview image")
            self.show_toast(f"Picked color {hex_color} from image!", type="success")
        except Exception as e:
            self.logger.error(f"Error picking color: {e}")

    def _create_picker_tooltip(self) -> None:
        if self.picker_tooltip:
            try:
                self.picker_tooltip.destroy()
            except Exception:
                pass
        
        self.picker_tooltip = tk.Toplevel(self)
        self.picker_tooltip.overrideredirect(True)
        self.picker_tooltip.attributes("-topmost", True)
        self.picker_tooltip.geometry("32x32")
        
        outer_frame = tk.Frame(self.picker_tooltip, bg="#1E1E24", bd=1)
        outer_frame.pack(fill="both", expand=True)
        
        inner_frame = tk.Frame(outer_frame, bg="#FFFFFF", bd=1)
        inner_frame.pack(fill="both", expand=True, padx=1, pady=1)
        
        self.tooltip_color_box = tk.Frame(inner_frame, bg="#000000")
        self.tooltip_color_box.pack(fill="both", expand=True, padx=1, pady=1)

    def _on_preview_enter(self, event, preset: str) -> None:
        if not self.source_image:
            return
        self._create_picker_tooltip()
        self._on_preview_motion(event, preset)

    def _on_preview_motion(self, event, preset: str) -> None:
        if not self.source_image or not self.picker_tooltip:
            return
            
        x, y = event.x, event.y
        
        if preset == "cover":
            width_preview, height_preview = 140, 140
            img_width, img_height = 500, 500
            source_img = self.img_500
        else:
            width_preview, height_preview = 220, 115
            img_width, img_height = 960, 502
            source_img = self.img_960
            
        x = max(0, min(x, width_preview - 1))
        y = max(0, min(y, height_preview - 1))
        
        img_x = int(x * (img_width / width_preview))
        img_y = int(y * (img_height / height_preview))
        
        img_x = max(0, min(img_x, img_width - 1))
        img_y = max(0, min(img_y, img_height - 1))
        
        try:
            pixel = source_img.getpixel((img_x, img_y))
            if len(pixel) == 4 and pixel[3] < 10:
                hex_color = "#1E1E24"
            else:
                r, g, b = pixel[:3]
                hex_color = f"#{r:02x}{g:02x}{b:02x}"
                
            self.tooltip_color_box.configure(bg=hex_color)
            self.picker_tooltip.geometry(f"32x32+{event.x_root + 15}+{event.y_root + 15}")
        except Exception:
            pass

    def _on_preview_leave(self, event) -> None:
        if self.picker_tooltip:
            try:
                self.picker_tooltip.destroy()
            except Exception:
                pass
            self.picker_tooltip = None
