import os
import re
from typing import List
import customtkinter as ctk
from tkinter import filedialog
from tkinterdnd2 import DND_FILES
from components.theme import THEME_COLORS, FONTS
from utils.file_helpers import scan_file_or_directory, get_image_info

class DragDropFrame(ctk.CTkFrame):
    def __init__(self, master, state_manager, logger_service, **kwargs):
        super().__init__(
            master,
            fg_color=THEME_COLORS["bg_card"],
            border_color=THEME_COLORS["border"],
            border_width=2,
            corner_radius=16,
            **kwargs
        )
        self.state_manager = state_manager
        self.logger = logger_service
        
        # Configure layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Container frame to center elements
        self.inner_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.inner_frame.grid(row=0, column=0, padx=24, pady=24, sticky="nsew")
        
        self.inner_frame.grid_columnconfigure(0, weight=1)
        
        # Big Icon/Glyph
        self.icon_label = ctk.CTkLabel(
            self.inner_frame,
            text="📥",
            font=("Outfit", 48, "normal")
        )
        self.icon_label.grid(row=0, column=0, pady=(16, 8))
        
        # Main text
        self.text_label = ctk.CTkLabel(
            self.inner_frame,
            text="Drag & Drop images or folders here",
            font=FONTS["header"],
            text_color=THEME_COLORS["text_main"]
        )
        self.text_label.grid(row=1, column=0, pady=4)
        
        # Sub text
        self.subtext_label = ctk.CTkLabel(
            self.inner_frame,
            text="Supports JPG, JPEG, PNG (recursively scans folders)",
            font=FONTS["small"],
            text_color=THEME_COLORS["text_muted"]
        )
        self.subtext_label.grid(row=2, column=0, pady=(0, 16))
        
        # OR label
        self.or_label = ctk.CTkLabel(
            self.inner_frame,
            text="— or —",
            font=FONTS["small"],
            text_color=THEME_COLORS["text_muted"]
        )
        self.or_label.grid(row=3, column=0, pady=(0, 12))
        
        # Buttons container
        self.btn_frame = ctk.CTkFrame(self.inner_frame, fg_color="transparent")
        self.btn_frame.grid(row=4, column=0, pady=(0, 16))
        
        self.browse_files_btn = ctk.CTkButton(
            self.btn_frame,
            text="Browse Files",
            font=FONTS["body_bold"],
            fg_color=THEME_COLORS["primary"],
            hover_color=THEME_COLORS["primary_hover"],
            command=self._browse_files
        )
        self.browse_files_btn.pack(side="left", padx=8)
        
        self.browse_folder_btn = ctk.CTkButton(
            self.btn_frame,
            text="Browse Folder",
            font=FONTS["body_bold"],
            fg_color=THEME_COLORS["bg_hover"],
            text_color=THEME_COLORS["text_main"],
            border_color=THEME_COLORS["border"],
            border_width=1,
            hover_color=THEME_COLORS["border"],
            command=self._browse_folder
        )
        self.browse_folder_btn.pack(side="left", padx=8)
        
        # Register Drag & Drop
        self.drop_target_register(DND_FILES)
        self.dnd_bind("<<DragEnter>>", self._on_drag_enter)
        self.dnd_bind("<<DragLeave>>", self._on_drag_leave)
        self.dnd_bind("<<Drop>>", self._on_drop)
        
        # Make inner labels forward clicks to file browser for a better UX
        self.icon_label.bind("<Button-1>", lambda e: self._browse_files())
        self.text_label.bind("<Button-1>", lambda e: self._browse_files())
        self.subtext_label.bind("<Button-1>", lambda e: self._browse_files())

    def _on_drag_enter(self, event) -> None:
        """Visual feedback when dragging files over the area."""
        self.configure(border_color=THEME_COLORS["border_active"])

    def _on_drag_leave(self, event) -> None:
        """Restore default border when drag leaves."""
        self.configure(border_color=THEME_COLORS["border"])

    def _on_drop(self, event) -> None:
        """Processes dropped files/folders."""
        self.configure(border_color=THEME_COLORS["border"])
        
        raw_data = event.data
        if not raw_data:
            return
            
        # Parse dropped files/folders
        paths = self._parse_dnd_paths(raw_data)
        self._process_paths(paths)

    def _parse_dnd_paths(self, raw_data: str) -> List[str]:
        """
        Parses the path list from tkinterdnd2 drop event.
        Handles curly-brace wrapped paths with spaces.
        """
        # Matches content in curly braces {C:/Path with Space/img.png} or normal space-separated strings
        pattern = r'\{([^}]+)\}|(\S+)'
        matches = re.findall(pattern, raw_data)
        paths = []
        for m in matches:
            path = m[0] if m[0] else m[1]
            paths.append(path.strip())
        return paths

    def _process_paths(self, paths: List[str]) -> None:
        """Scans the paths and adds valid images to the queue."""
        added_count = 0
        duplicate_count = 0
        
        for path in paths:
            # Check if it is a directory or file and scan
            scanned_files = scan_file_or_directory(path, recursive=True)
            for filepath in scanned_files:
                size = os.path.getsize(filepath)
                # Read dimensions without loading into memory
                _, res_str = get_image_info(filepath)
                
                success = self.state_manager.add_file(filepath, size, res_str)
                if success:
                    added_count += 1
                else:
                    duplicate_count += 1

        if added_count > 0:
            self.logger.info(f"Added {added_count} image(s) to queue.")
        if duplicate_count > 0:
            self.logger.warning(f"Skipped {duplicate_count} duplicate image(s) already in queue.")
        if added_count == 0 and duplicate_count == 0:
            self.logger.warning("No supported images found in dropped files.")

    def _browse_files(self) -> None:
        """Opens a file dialog to choose image files."""
        files = filedialog.askopenfilenames(
            title="Select Images",
            filetypes=[
                ("Supported Images", "*.jpg;*.jpeg;*.png"),
                ("JPEG Images", "*.jpg;*.jpeg"),
                ("PNG Images", "*.png")
            ]
        )
        if files:
            self._process_paths(list(files))

    def _browse_folder(self) -> None:
        """Opens a directory dialog to choose a folder."""
        folder = filedialog.askdirectory(title="Select Folder to Scan")
        if folder:
            self._process_paths([folder])
