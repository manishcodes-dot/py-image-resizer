import customtkinter as ctk
from components.theme import THEME_COLORS, FONTS
from utils.file_helpers import format_size

class ProgressPanelFrame(ctk.CTkFrame):
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
        
        # Grid layout: two main columns separated by a vertical line
        self.grid_columnconfigure(0, weight=6)  # Left: Progress
        self.grid_columnconfigure(1, weight=0)  # Center: Separator
        self.grid_columnconfigure(2, weight=5)  # Right: Stats
        self.grid_rowconfigure(0, weight=1)

        self._build_progress_column()
        self._build_separator()
        self._build_stats_column()

        # Listen to State Manager for stats updates
        self.state_manager.on_stats_updated(self._update_compression_stats)
        self.state_manager.on_file_updated(self._update_current_file)
        self.state_manager.on_queue_cleared(self.reset_ui)

    def _build_progress_column(self) -> None:
        self.progress_col = ctk.CTkFrame(self, fg_color="transparent")
        self.progress_col.grid(row=0, column=0, padx=16, pady=16, sticky="nsew")
        self.progress_col.grid_columnconfigure(0, weight=1)

        # Title
        self.title_lbl = ctk.CTkLabel(
            self.progress_col,
            text="Conversion Progress",
            font=FONTS["header"],
            text_color=THEME_COLORS["text_main"],
            anchor="w"
        )
        self.title_lbl.pack(fill="x", pady=(0, 8))

        # Stats counts line
        self.count_lbl = ctk.CTkLabel(
            self.progress_col,
            text="0 / 0 Images Processed (0%)",
            font=FONTS["body_bold"],
            text_color=THEME_COLORS["text_main"],
            anchor="w"
        )
        self.count_lbl.pack(fill="x", pady=2)

        # Progress Bar
        self.progress_bar = ctk.CTkProgressBar(
            self.progress_col,
            progress_color=THEME_COLORS["primary"],
            border_color=THEME_COLORS["border"],
            height=12
        )
        self.progress_bar.set(0.0)
        self.progress_bar.pack(fill="x", pady=8)

        # Sub-stats (Speed, ETA)
        self.meta_frame = ctk.CTkFrame(self.progress_col, fg_color="transparent")
        self.meta_frame.pack(fill="x", pady=2)
        
        self.speed_lbl = ctk.CTkLabel(
            self.meta_frame,
            text="Speed: --",
            font=FONTS["small"],
            text_color=THEME_COLORS["text_muted"],
            anchor="w"
        )
        self.speed_lbl.pack(side="left", fill="x", expand=True)

        self.eta_lbl = ctk.CTkLabel(
            self.meta_frame,
            text="ETA: --",
            font=FONTS["small"],
            text_color=THEME_COLORS["text_muted"],
            anchor="e"
        )
        self.eta_lbl.pack(side="right")

        # Current converting file name
        self.curr_file_lbl = ctk.CTkLabel(
            self.progress_col,
            text="Current: Idle",
            font=FONTS["small"],
            text_color=THEME_COLORS["text_muted"],
            anchor="w"
        )
        self.curr_file_lbl.pack(fill="x", pady=(8, 0))

    def _build_separator(self) -> None:
        self.sep = ctk.CTkFrame(self, width=1, fg_color=THEME_COLORS["border"])
        self.sep.grid(row=0, column=1, sticky="ns", pady=12)

    def _build_stats_column(self) -> None:
        self.stats_col = ctk.CTkFrame(self, fg_color="transparent")
        self.stats_col.grid(row=0, column=2, padx=16, pady=16, sticky="nsew")
        self.stats_col.grid_columnconfigure(0, weight=1)
        self.stats_col.grid_columnconfigure(1, weight=1)

        # Title
        self.stats_title = ctk.CTkLabel(
            self.stats_col,
            text="Compression Stats",
            font=FONTS["header"],
            text_color=THEME_COLORS["text_main"],
            anchor="w"
        )
        self.stats_title.grid(row=0, column=0, columnspan=2, pady=(0, 10), sticky="ew")

        # Size Grid: Original Size & Converted Size
        self.lbl_orig_title = ctk.CTkLabel(self.stats_col, text="Original Size", font=FONTS["small"], text_color=THEME_COLORS["text_muted"], anchor="w")
        self.lbl_orig_title.grid(row=1, column=0, sticky="ew", pady=1)
        
        self.lbl_orig_val = ctk.CTkLabel(self.stats_col, text="0.00 B", font=FONTS["body_bold"], text_color=THEME_COLORS["text_main"], anchor="w")
        self.lbl_orig_val.grid(row=2, column=0, sticky="ew", pady=(0, 6))

        self.lbl_conv_title = ctk.CTkLabel(self.stats_col, text="Converted Size", font=FONTS["small"], text_color=THEME_COLORS["text_muted"], anchor="w")
        self.lbl_conv_title.grid(row=1, column=1, sticky="ew", pady=1)
        
        self.lbl_conv_val = ctk.CTkLabel(self.stats_col, text="0.00 B", font=FONTS["body_bold"], text_color=THEME_COLORS["text_main"], anchor="w")
        self.lbl_conv_val.grid(row=2, column=1, sticky="ew", pady=(0, 6))

        # Size Grid: Space Saved & Compression ratio
        self.lbl_saved_title = ctk.CTkLabel(self.stats_col, text="Space Saved", font=FONTS["small"], text_color=THEME_COLORS["text_muted"], anchor="w")
        self.lbl_saved_title.grid(row=3, column=0, sticky="ew", pady=1)
        
        self.lbl_saved_val = ctk.CTkLabel(self.stats_col, text="0.00 B", font=FONTS["body_bold"], text_color=THEME_COLORS["primary"], anchor="w")
        self.lbl_saved_val.grid(row=4, column=0, sticky="ew", pady=(0, 4))

        self.lbl_pct_title = ctk.CTkLabel(self.stats_col, text="Reduction Ratio", font=FONTS["small"], text_color=THEME_COLORS["text_muted"], anchor="w")
        self.lbl_pct_title.grid(row=3, column=1, sticky="ew", pady=1)
        
        self.lbl_pct_val = ctk.CTkLabel(self.stats_col, text="0.0%", font=FONTS["body_bold"], text_color=THEME_COLORS["primary"], anchor="w")
        self.lbl_pct_val.grid(row=4, column=1, sticky="ew", pady=(0, 4))

    # Real-time updates
    def update_progress_state(self, progress_data: dict) -> None:
        """Called by BatchProcessor to update progress bar, counts, speed and ETA."""
        processed = progress_data["processed"]
        total = progress_data["total"]
        pct = progress_data["percentage"]
        
        self.count_lbl.configure(text=f"{processed} / {total} Images Processed ({int(pct * 100)}%)")
        self.progress_bar.set(pct)
        self.speed_lbl.configure(text=f"Speed: {progress_data['speed']}")
        self.eta_lbl.configure(text=f"ETA: {progress_data['eta']}")

    def _update_current_file(self, file_entry: dict) -> None:
        """Updates the name of the file currently converting."""
        if file_entry["status"] == "Converting":
            self.curr_file_lbl.configure(text=f"Converting: {file_entry['name']}", text_color=THEME_COLORS["status_converting"])
        elif file_entry["status"] == "Completed" and self.state_manager.get_compression_stats()["remaining_files"] == 0:
            self.curr_file_lbl.configure(text="Finished processing.", text_color=THEME_COLORS["status_completed"])

    def _update_compression_stats(self) -> None:
        """Called automatically when StateManager recalculates sizes."""
        stats = self.state_manager.get_compression_stats()
        
        self.lbl_orig_val.configure(text=format_size(stats["original_size"]))
        self.lbl_conv_val.configure(text=format_size(stats["converted_size"]))
        self.lbl_saved_val.configure(text=format_size(stats["saved_size"]))
        
        ratio = stats["compression_percent"]
        self.lbl_pct_val.configure(text=f"{ratio:.1f}%")

    def reset_ui(self) -> None:
        """Resets all fields to their default state."""
        self.count_lbl.configure(text="0 / 0 Images Processed (0%)")
        self.progress_bar.set(0.0)
        self.speed_lbl.configure(text="Speed: --")
        self.eta_lbl.configure(text="ETA: --")
        self.curr_file_lbl.configure(text="Current: Idle", text_color=THEME_COLORS["text_muted"])
        
        self.lbl_orig_val.configure(text="0.00 B")
        self.lbl_conv_val.configure(text="0.00 B")
        self.lbl_saved_val.configure(text="0.00 B")
        self.lbl_pct_val.configure(text="0.0%")
