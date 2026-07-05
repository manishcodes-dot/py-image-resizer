import os
import re
from typing import List
import customtkinter as ctk
from tkinter import filedialog, Menu
from tkinterdnd2 import DND_FILES
from components.theme import THEME_COLORS, FONTS
from utils.file_helpers import scan_file_or_directory, get_image_info

class WelcomeFrame(ctk.CTkFrame):
    def __init__(self, master, state_manager, logger_service, on_files_added, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.state_manager = state_manager
        self.logger = logger_service
        self.on_files_added = on_files_added  # Callback when files are successfully added
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Center container
        self.center_container = ctk.CTkFrame(self, fg_color="transparent")
        self.center_container.grid(row=0, column=0, pady=(20, 20), sticky="ns")
        self.center_container.grid_columnconfigure(0, weight=1)
        
        # 1. Main Title
        self.title_lbl = ctk.CTkLabel(
            self.center_container,
            text="PNG to WEBP Converter",
            font=("Outfit", 32, "bold"),
            text_color=THEME_COLORS["text_main"]
        )
        self.title_lbl.grid(row=0, column=0, pady=(10, 8), sticky="w")
        
        # 2. Description
        self.desc_lbl = ctk.CTkLabel(
            self.center_container,
            text="OptiWebP converts your image files offline. We support PNG, JPG, and JPEG.\nYou can use the settings to control image resolution, quality, and file size.",
            font=FONTS["body"],
            text_color=THEME_COLORS["text_muted"],
            justify="left",
            anchor="w"
        )
        self.desc_lbl.grid(row=1, column=0, pady=(0, 20), sticky="w")
        
        # 3. Visual Row (PNG to WEBP graphic)
        self.visual_frame = ctk.CTkFrame(self.center_container, fg_color="transparent")
        self.visual_frame.grid(row=0, rowspan=2, column=1, padx=(40, 0), pady=(10, 20), sticky="ne")
        
        # Box 1: PNG File Icon
        self.png_box = ctk.CTkFrame(
            self.visual_frame,
            width=90,
            height=100,
            fg_color="#1E1F22",
            border_color="#2D2E32",
            border_width=1,
            corner_radius=12
        )
        self.png_box.pack(side="left", padx=8)
        self.png_box.pack_propagate(False)
        
        self.png_icon = ctk.CTkLabel(self.png_box, text="📄", font=("Outfit", 28, "normal"))
        self.png_icon.pack(pady=(16, 2))
        self.png_lbl = ctk.CTkLabel(self.png_box, text="PNG", font=("Outfit", 12, "bold"), text_color=THEME_COLORS["text_muted"])
        self.png_lbl.pack()
        
        # Middle: TO arrow
        self.to_frame = ctk.CTkFrame(self.visual_frame, fg_color="transparent")
        self.to_frame.pack(side="left", padx=12)
        
        self.to_circle = ctk.CTkFrame(
            self.to_frame,
            width=32,
            height=32,
            fg_color="#2D2E32",
            corner_radius=16
        )
        self.to_circle.pack(pady=(0, 2))
        self.to_circle.pack_propagate(False)
        self.to_arrow = ctk.CTkLabel(self.to_circle, text="⇆", font=("Outfit", 14, "bold"), text_color=THEME_COLORS["primary"])
        self.to_arrow.pack(pady=2)
        
        self.to_lbl = ctk.CTkLabel(self.to_frame, text="TO", font=("Outfit", 9, "bold"), text_color=THEME_COLORS["text_muted"])
        self.to_lbl.pack()
        
        # Box 2: WEBP File Icon (glowing red border)
        self.webp_box = ctk.CTkFrame(
            self.visual_frame,
            width=90,
            height=100,
            fg_color="#1E1F22",
            border_color=THEME_COLORS["primary"],
            border_width=1.5,
            corner_radius=12
        )
        self.webp_box.pack(side="left", padx=8)
        self.webp_box.pack_propagate(False)
        
        self.webp_icon = ctk.CTkLabel(self.webp_box, text="📄", font=("Outfit", 28, "normal"), text_color=THEME_COLORS["primary"])
        self.webp_icon.pack(pady=(16, 2))
        self.webp_lbl = ctk.CTkLabel(self.webp_box, text="WEBP", font=("Outfit", 12, "bold"), text_color=THEME_COLORS["primary"])
        self.webp_lbl.pack()
        
        # 4. Central Upload Card
        self.upload_card = ctk.CTkFrame(
            self.center_container,
            width=580,
            height=260,
            fg_color=THEME_COLORS["bg_card"],
            border_color=THEME_COLORS["border"],
            border_width=1,
            corner_radius=16
        )
        self.upload_card.grid(row=2, column=0, columnspan=2, pady=10, sticky="ew")
        self.upload_card.grid_propagate(False)
        
        self.upload_card.grid_columnconfigure(0, weight=1)
        self.upload_card.grid_rowconfigure(0, weight=1)
        
        # Inner content container
        self.card_inner = ctk.CTkFrame(self.upload_card, fg_color="transparent")
        self.card_inner.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        self.card_inner.grid_columnconfigure(0, weight=1)
        
        # Red cloud icon
        self.cloud_lbl = ctk.CTkLabel(
            self.card_inner,
            text="☁",
            font=("Outfit", 48, "normal"),
            text_color=THEME_COLORS["primary"],
            anchor="center",
            justify="center"
        )
        self.cloud_lbl.grid(row=0, column=0, pady=(15, 8), sticky="")
        
        # Heading
        self.card_head = ctk.CTkLabel(
            self.card_inner,
            text="Select your files here to get started",
            font=("Outfit", 18, "bold"),
            text_color=THEME_COLORS["text_main"]
        )
        self.card_head.grid(row=1, column=0, pady=2)
        
        # Subheading
        self.card_sub = ctk.CTkLabel(
            self.card_inner,
            text="or drop your files here.",
            font=FONTS["body"],
            text_color=THEME_COLORS["text_muted"]
        )
        self.card_sub.grid(row=2, column=0, pady=(0, 16))
        
        # Red Select Button (Select Files directly)
        self.select_btn = ctk.CTkButton(
            self.card_inner,
            text="Select File",
            width=160,
            height=38,
            font=FONTS["body_bold"],
            fg_color=THEME_COLORS["primary"],
            hover_color=THEME_COLORS["primary_hover"],
            corner_radius=6,
            command=self._browse_files
        )
        self.select_btn.grid(row=3, column=0, pady=(0, 15))
        
        # Drag & Drop bindings
        self.drop_target_register(DND_FILES)
        self.dnd_bind("<<DragEnter>>", self._on_drag_enter)
        self.dnd_bind("<<DragLeave>>", self._on_drag_leave)
        self.dnd_bind("<<Drop>>", self._on_drop)
        
        # Clicking background opens files too
        self.upload_card.bind("<Button-1>", lambda e: self._browse_files())
        self.card_inner.bind("<Button-1>", lambda e: self._browse_files())
        self.cloud_lbl.bind("<Button-1>", lambda e: self._browse_files())
        self.card_head.bind("<Button-1>", lambda e: self._browse_files())
        self.card_sub.bind("<Button-1>", lambda e: self._browse_files())

    def _on_drag_enter(self, event) -> None:
        self.upload_card.configure(border_color=THEME_COLORS["border_active"])

    def _on_drag_leave(self, event) -> None:
        self.upload_card.configure(border_color=THEME_COLORS["border"])

    def _on_drop(self, event) -> None:
        self.upload_card.configure(border_color=THEME_COLORS["border"])
        raw_data = event.data
        if not raw_data:
            return
        paths = self._parse_dnd_paths(raw_data)
        self._process_paths(paths)

    def _parse_dnd_paths(self, raw_data: str) -> List[str]:
        pattern = r'\{([^}]+)\}|(\S+)'
        matches = re.findall(pattern, raw_data)
        paths = []
        for m in matches:
            path = m[0] if m[0] else m[1]
            paths.append(path.strip())
        return paths

    def _process_paths(self, paths: List[str]) -> None:
        added_count = 0
        duplicate_count = 0
        
        for path in paths:
            scanned_files = scan_file_or_directory(path, recursive=True)
            for filepath in scanned_files:
                size = os.path.getsize(filepath)
                _, res_str = get_image_info(filepath)
                success = self.state_manager.add_file(filepath, size, res_str)
                if success:
                    added_count += 1
                else:
                    duplicate_count += 1

        if added_count > 0:
            self.logger.info(f"Added {added_count} image(s) to queue.")
            self.on_files_added()
        if duplicate_count > 0:
            self.logger.warning(f"Skipped {duplicate_count} duplicate image(s) already in queue.")

    def _on_select_click(self) -> None:
        """Shows selection menu to choose Files or Folder."""
        # Simple Tkinter menu for dropdown
        menu = Menu(self, tearoff=0, bg=THEME_COLORS["bg_card"][1], fg=THEME_COLORS["text_main"][1], activebackground=THEME_COLORS["primary"][1])
        menu.add_command(label="Select Files...", command=self._browse_files)
        menu.add_command(label="Select Folder...", command=self._browse_folder)
        
        # Position menu below the button
        x = self.select_btn.winfo_rootx()
        y = self.select_btn.winfo_rooty() + self.select_btn.winfo_height()
        menu.post(x, y)

    def _browse_files(self) -> None:
        files = filedialog.askopenfilenames(
            title="Select Images",
            filetypes=[
                ("Supported Images", "*.jpg *.jpeg *.png"),
                ("JPEG Images", "*.jpg *.jpeg"),
                ("PNG Images", "*.png")
            ]
        )
        if files:
            self._process_paths(list(files))

    def _browse_folder(self) -> None:
        folder = filedialog.askdirectory(title="Select Folder to Scan")
        if folder:
            self._process_paths([folder])
