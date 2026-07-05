import customtkinter as ctk
from tkinter import filedialog, messagebox
from components.theme import THEME_COLORS, FONTS

class LogPanelFrame(ctk.CTkFrame):
    def __init__(self, master, logger_service, **kwargs):
        super().__init__(
            master,
            fg_color=THEME_COLORS["bg_card"],
            border_color=THEME_COLORS["border"],
            border_width=1,
            corner_radius=12,
            **kwargs
        )
        self.logger = logger_service
        
        # Configure layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)  # Toolbar
        self.grid_rowconfigure(1, weight=1)  # Console Box
        
        # Toolbar Frame
        self.toolbar = ctk.CTkFrame(self, fg_color="transparent")
        self.toolbar.grid(row=0, column=0, padx=12, pady=(8, 4), sticky="ew")
        
        self.title_lbl = ctk.CTkLabel(
            self.toolbar,
            text="Event Logs",
            font=FONTS["header"],
            text_color=THEME_COLORS["text_main"]
        )
        self.title_lbl.pack(side="left")
        
        # Action Buttons
        self.btn_clear = ctk.CTkButton(
            self.toolbar,
            text="Clear",
            width=50,
            font=FONTS["small"],
            fg_color="transparent",
            text_color=THEME_COLORS["text_muted"],
            hover_color=("#E5E7EB", "#2D323A"),
            command=self._clear_logs
        )
        self.btn_clear.pack(side="right", padx=2)

        self.btn_save = ctk.CTkButton(
            self.toolbar,
            text="Save Log",
            width=70,
            font=FONTS["small"],
            fg_color="transparent",
            text_color=THEME_COLORS["text_muted"],
            hover_color=("#E5E7EB", "#2D323A"),
            command=self._save_logs
        )
        self.btn_save.pack(side="right", padx=2)

        self.btn_copy = ctk.CTkButton(
            self.toolbar,
            text="Copy Log",
            width=70,
            font=FONTS["small"],
            fg_color="transparent",
            text_color=THEME_COLORS["text_muted"],
            hover_color=("#E5E7EB", "#2D323A"),
            command=self._copy_logs
        )
        self.btn_copy.pack(side="right", padx=2)

        # Log Text Area (Read Only)
        self.log_text = ctk.CTkTextbox(
            self,
            font=FONTS["code"],
            fg_color=THEME_COLORS["bg_window"],
            border_color=THEME_COLORS["border"],
            border_width=1,
            text_color=THEME_COLORS["text_main"],
            activate_scrollbars=True
        )
        self.log_text.grid(row=1, column=0, padx=12, pady=(4, 12), sticky="nsew")
        self.log_text.configure(state="disabled")

        # Set up color-coding tags for the text area (using underlying Tkinter.Text methods)
        # Note: #10B981 (emerald), #EF4444 (red), #F59E0B (orange) are visible on both dark/light backgrounds
        self.log_text._textbox.tag_config("timestamp", foreground="#6B7280")
        self.log_text._textbox.tag_config("success", foreground="#10B981")
        self.log_text._textbox.tag_config("error", foreground="#EF4444")
        self.log_text._textbox.tag_config("warning", foreground="#F59E0B")
        self.log_text._textbox.tag_config("info", foreground=THEME_COLORS["text_main"][1]) # Fallback dark main, but let's override with dynamic
        
        # Register for log events
        self.logger.register_callback(self._on_log_added)

    def _on_log_added(self, log_entry: dict) -> None:
        """Appends a new log entry to the UI console, scroll to bottom."""
        # Ensure we mutate Tkinter widgets only on the main thread
        self.after(0, lambda: self._safe_log_added(log_entry))

    def _safe_log_added(self, log_entry: dict) -> None:
        timestamp = log_entry["timestamp"]
        message = log_entry["message"]
        level = log_entry["level"]
        
        self.log_text.configure(state="normal")
        
        # Add timestamp
        self.log_text.insert("end", f"[{timestamp}] ", "timestamp")
        
        # Add colored message body
        self.log_text.insert("end", f"{message}\n", level)
        
        # Scroll to bottom
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def _copy_logs(self) -> None:
        """Copies all logs to clipboard."""
        logs = self.logger.get_logs_text()
        if not logs:
            messagebox.showinfo("Copy Log", "Log console is empty.")
            return
            
        self.clipboard_clear()
        self.clipboard_append(logs)
        self.logger.info("Logs copied to clipboard.")
        messagebox.showinfo("Copy Log", "Logs successfully copied to clipboard.")

    def _save_logs(self) -> None:
        """Saves logs to a text file."""
        if not self.logger.in_memory_logs:
            messagebox.showinfo("Save Log", "Log console is empty.")
            return
            
        file_path = filedialog.asksaveasfilename(
            title="Save Log File",
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("Log Files", "*.log")]
        )
        if file_path:
            success = self.logger.save_logs_to_file(file_path)
            if success:
                messagebox.showinfo("Save Log", f"Logs successfully saved to:\n{file_path}")

    def _clear_logs(self) -> None:
        """Clears both log UI and in-memory log list."""
        self.logger.clear()
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")
        self.logger.info("Log console cleared.")
