import os
from typing import Dict, Any
import customtkinter as ctk
from components.theme import THEME_COLORS, FONTS
from utils.file_helpers import format_size

class FileListFrame(ctk.CTkFrame):
    def __init__(self, master, state_manager, **kwargs):
        super().__init__(
            master,
            fg_color=THEME_COLORS["bg_card"],
            border_color=THEME_COLORS["border"],
            border_width=1,
            corner_radius=12,
            **kwargs
        )
        self.state_manager = state_manager
        
        # Configure layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)  # Table Header
        self.grid_rowconfigure(1, weight=1)  # Table Body (Scrollable)
        
        # Create Table Headers
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent", height=32)
        self.header_frame.grid(row=0, column=0, padx=12, pady=(8, 4), sticky="ew")
        
        # Grid column configuration for headers (must match the rows)
        self.header_frame.grid_columnconfigure(0, weight=5)  # Name / Badge
        self.header_frame.grid_columnconfigure(1, weight=2)  # Resolution
        self.header_frame.grid_columnconfigure(2, weight=2)  # Size
        self.header_frame.grid_columnconfigure(3, weight=2)  # Status
        self.header_frame.grid_columnconfigure(4, weight=1)  # Action (delete)
        
        # Header labels
        headers = ["File Name", "Resolution", "Size", "Status", ""]
        for idx, text in enumerate(headers):
            weight = [5, 2, 2, 2, 1][idx]
            lbl = ctk.CTkLabel(
                self.header_frame,
                text=text,
                font=FONTS["small"],
                text_color=THEME_COLORS["text_muted"],
                anchor="w" if idx < 4 else "center"
            )
            lbl.grid(row=0, column=idx, sticky="ew" if idx < 4 else "", padx=4)

        # Divider line
        self.divider = ctk.CTkFrame(self, height=1, fg_color=THEME_COLORS["border"])
        self.divider.grid(row=0, column=0, sticky="ews", padx=8)

        # Scrollable container for rows
        self.scroll_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=THEME_COLORS["border"],
            scrollbar_button_hover_color=THEME_COLORS["text_muted"]
        )
        self.scroll_frame.grid(row=1, column=0, padx=4, pady=4, sticky="nsew")
        self.scroll_frame.grid_columnconfigure(0, weight=1)

        # Map to store row widgets: file_id -> row components dictionary
        self.rows: Dict[str, Dict[str, Any]] = {}
        
        # Bind state manager events
        self.state_manager.on_file_added(self._add_row)
        self.state_manager.on_file_updated(self._update_row)
        self.state_manager.on_file_removed(self._remove_row)
        self.state_manager.on_queue_cleared(self._clear_all_rows)
        
        # Populate table with any files already in state
        for file_entry in self.state_manager.files:
            self._add_row(file_entry)

    def _add_row(self, file_entry: Dict[str, Any]) -> None:
        """Adds a new row to the scrollable table."""
        file_id = file_entry["id"]
        filepath = file_entry["path"]
        name = file_entry["name"]
        
        # Row container frame
        row_frame = ctk.CTkFrame(
            self.scroll_frame,
            fg_color="transparent",
            height=38,
            corner_radius=6
        )
        row_frame.pack(fill="x", pady=2, padx=4)
        
        row_frame.grid_columnconfigure(0, weight=5)
        row_frame.grid_columnconfigure(1, weight=2)
        row_frame.grid_columnconfigure(2, weight=2)
        row_frame.grid_columnconfigure(3, weight=2)
        row_frame.grid_columnconfigure(4, weight=1)
        
        # Format Badge (e.g. JPG, PNG)
        _, ext = os.path.splitext(name.lower())
        badge_text = ext[1:].upper()
        if badge_text == "JPEG":
            badge_text = "JPG"
            
        badge_color = ("#3B82F6", "#2563EB") if badge_text == "PNG" else ("#F59E0B", "#D97706")
        
        # Pack badge and name inside a sub-frame
        name_container = ctk.CTkFrame(row_frame, fg_color="transparent")
        name_container.grid(row=0, column=0, sticky="ew", padx=4, pady=4)
        
        badge_lbl = ctk.CTkLabel(
            name_container,
            text=badge_text,
            font=(FONTS["small"][0], 9, "bold"),
            text_color="#FFFFFF",
            fg_color=badge_color,
            corner_radius=4,
            width=36,
            height=18
        )
        
        # File Name Label (truncated if too long)
        name_lbl = ctk.CTkLabel(
            name_container,
            text=name,
            font=FONTS["body"],
            text_color=THEME_COLORS["text_main"],
            anchor="w"
        )
        
        badge_lbl.pack(side="left", padx=(0, 8))
        name_lbl.pack(side="left", fill="x", expand=True)
        
        # Resolution Label
        res_lbl = ctk.CTkLabel(
            row_frame,
            text=file_entry["resolution"],
            font=FONTS["small"],
            text_color=THEME_COLORS["text_muted"],
            anchor="w"
        )
        res_lbl.grid(row=0, column=1, sticky="ew", padx=4)
        
        # Size Label
        size_lbl = ctk.CTkLabel(
            row_frame,
            text=format_size(file_entry["size"]),
            font=FONTS["small"],
            text_color=THEME_COLORS["text_muted"],
            anchor="w"
        )
        size_lbl.grid(row=0, column=2, sticky="ew", padx=4)
        
        # Status Label
        status_lbl = ctk.CTkLabel(
            row_frame,
            text=file_entry["status"],
            font=FONTS["small"],
            text_color=self._get_status_color(file_entry["status"]),
            anchor="w"
        )
        status_lbl.grid(row=0, column=3, sticky="ew", padx=4)
        
        # Delete Button (Action)
        del_btn = ctk.CTkButton(
            row_frame,
            text="✕",
            font=("Outfit", 12, "bold"),
            text_color=THEME_COLORS["text_muted"],
            fg_color="transparent",
            hover_color=("#F3F4F6", "#2D323A"),
            width=24,
            height=24,
            corner_radius=12,
            command=lambda fid=file_id: self.state_manager.remove_file(fid)
        )
        del_btn.grid(row=0, column=4, padx=4)

        # Store widgets for live updates
        self.rows[file_id] = {
            "frame": row_frame,
            "size_lbl": size_lbl,
            "res_lbl": res_lbl,
            "status_lbl": status_lbl,
            "del_btn": del_btn
        }

    def _update_row(self, file_entry: Dict[str, Any]) -> None:
        """Updates the status and details of an existing row in-place."""
        file_id = file_entry["id"]
        if file_id not in self.rows:
            return
            
        row_widgets = self.rows[file_id]
        
        # Update Resolution
        row_widgets["res_lbl"].configure(text=file_entry["resolution"])
        
        # Update Status
        status = file_entry["status"]
        row_widgets["status_lbl"].configure(
            text=status,
            text_color=self._get_status_color(status)
        )
        
        # Update Size (if converted, show old -> new)
        if status == "Completed" and file_entry["new_size"] > 0:
            old_str = format_size(file_entry["size"])
            new_str = format_size(file_entry["new_size"])
            row_widgets["size_lbl"].configure(text=f"{old_str} → {new_str}")
        else:
            row_widgets["size_lbl"].configure(text=format_size(file_entry["size"]))
            
        # Disable/Enable delete button based on conversion status
        if status in ("Converting", "Completed"):
            row_widgets["del_btn"].configure(state="disabled")
        else:
            row_widgets["del_btn"].configure(state="normal")

    def _remove_row(self, file_id: str) -> None:
        """Removes a row from the list UI."""
        if file_id in self.rows:
            self.rows[file_id]["frame"].destroy()
            del self.rows[file_id]

    def _clear_all_rows(self) -> None:
        """Destroys all rows in the UI."""
        for file_id in list(self.rows.keys()):
            self._remove_row(file_id)
        self.rows.clear()

    def _get_status_color(self, status: str) -> tuple:
        """Helper to get corresponding theme status color."""
        key = f"status_{status.lower()}"
        return THEME_COLORS.get(key, THEME_COLORS["text_muted"])
