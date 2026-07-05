import os
import customtkinter as ctk
from tkinter import messagebox, Menu
from tkinterdnd2 import TkinterDnD

# Import custom modules
from config.settings import SettingsManager
from utils.asset_generator import generate_app_assets
from utils.file_helpers import get_resource_path, format_size, scan_file_or_directory
from services.state_manager import StateManager
from services.logger_service import LoggerService
from core.converter import ImageConverter
from core.processor import BatchProcessor

# Import components
from components.theme import THEME_COLORS, FONTS
from components.header import HeaderFrame
from components.welcome_frame import WelcomeFrame
from components.file_list import FileListFrame
from components.settings_panel import SettingsPanelFrame
from components.progress_panel import ProgressPanelFrame
from components.log_panel import LogPanelFrame
from components.resizer_frame import ResizerFrame
from components.ugc_workspace import UgcWorkspaceFrame

class SettingsDialog(ctk.CTkToplevel):
    def __init__(self, parent, settings_manager):
        super().__init__(parent)
        self.settings = settings_manager
        
        self.title("Conversion Settings")
        self.geometry("740x480")
        self.resizable(False, False)
        
        # Center on parent window
        self.update_idletasks()
        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()
        parent_w = parent.winfo_width()
        parent_h = parent.winfo_height()
        
        x = parent_x + (parent_w - 740) // 2
        y = parent_y + (parent_h - 480) // 2
        self.geometry(f"+{x}+{y}")
        
        self.transient(parent)
        self.grab_set()
        
        # Top banner
        header_lbl = ctk.CTkLabel(
            self,
            text="Settings Options",
            font=("Outfit", 18, "bold"),
            text_color=THEME_COLORS["text_main"]
        )
        header_lbl.pack(pady=(16, 8))
        
        # Wrap settings panel inside the dialog
        self.panel = SettingsPanelFrame(self, self.settings)
        self.panel.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Close button
        self.close_btn = ctk.CTkButton(
            self,
            text="Save & Close",
            font=FONTS["body_bold"],
            fg_color=THEME_COLORS["primary"],
            hover_color=THEME_COLORS["primary_hover"],
            command=self.destroy
        )
        self.close_btn.pack(pady=16)


class OptiWebPApp(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self):
        # Initialize CustomTkinter window
        ctk.CTk.__init__(self)
        
        # Initialize Drag & Drop extensions
        self.TkdndVersion = TkinterDnD._require(self)
        
        # Generate assets if missing
        import sys
        if not getattr(sys, "frozen", False):
            generate_app_assets("assets")
        
        # Load Settings Manager
        self.settings = SettingsManager("config.json")
        
        # Set Appearance Mode
        theme = self.settings.get("theme")
        ctk.set_appearance_mode(theme)
        ctk.set_default_color_theme("blue")
        
        # Window setup
        self.title("OptiWebP — Offline Image to WebP Converter")
        ico_path = get_resource_path(os.path.join("assets", "logo.ico"))
        if os.path.exists(ico_path):
            try:
                self.iconbitmap(ico_path)
            except Exception as e:
                print(f"Error setting iconbitmap: {e}")
        
        # Geometry: Sleek compact utility dashboard
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        w, h = 880, 640
        x = (screen_w - w) // 2
        y = (screen_h - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")
        self.minsize(820, 580)
        
        # Grid layout
        self.grid_rowconfigure(0, weight=0)  # Header
        self.grid_rowconfigure(1, weight=0)  # Tab Selector
        self.grid_rowconfigure(2, weight=1)  # Main View area
        self.grid_columnconfigure(0, weight=1)
        
        # Initialize Services
        self.logger = LoggerService("logs")
        self.state_manager = StateManager()
        self.converter = ImageConverter(self.settings)
        self.processor = BatchProcessor(self.state_manager, self.logger, self.converter, self)
        
        # Build top header
        self._build_header()
        
        # Tab selector
        self.tab_var = ctk.StringVar(value="PNG Converter")
        self.tab_selector = ctk.CTkSegmentedButton(
            self,
            values=["PNG Converter", "Image Resizer"],
            variable=self.tab_var,
            font=FONTS["body_bold"],
            selected_color=THEME_COLORS["primary"][1],
            selected_hover_color=THEME_COLORS["primary_hover"][1],
            fg_color=THEME_COLORS["bg_card"],
            command=self._on_tab_changed
        )
        self.tab_selector.grid(row=1, column=0, padx=16, pady=(4, 8), sticky="ew")
        
        # Active view references
        self.welcome_view = None
        self.queue_view = None
        self.resizer_view = None
        self.ugc_workspace = None
        
        # Register processor callbacks
        self.processor.on_batch_start(self._on_batch_start)
        self.processor.on_batch_complete(self._on_batch_complete)
        
        # Decide starting view
        self._refresh_view()
        
        self.logger.info("OptiWebP started successfully. Ready for conversions.")

    def _build_header(self) -> None:
        self.header = HeaderFrame(
            master=self,
            settings_manager=self.settings,
            on_theme_toggle_callback=self._set_theme
        )
        self.header.grid(row=0, column=0, padx=16, pady=(16, 8), sticky="ew")

    def _on_tab_changed(self, selected_tab: str) -> None:
        if selected_tab == "PNG Converter":
            # Hide resizer
            if hasattr(self, "resizer_view") and self.resizer_view:
                self.resizer_view.grid_forget()
            # Show converter
            self._refresh_view()
        elif selected_tab == "Image Resizer":
            # Hide UGC workspace
            if hasattr(self, "ugc_workspace") and self.ugc_workspace:
                self.ugc_workspace.grid_forget()
            
            # Show resizer
            if not hasattr(self, "resizer_view") or not self.resizer_view:
                self.resizer_view = ResizerFrame(
                    self,
                    logger_service=self.logger,
                    show_toast_callback=self.show_toast
                )
            self.resizer_view.grid(row=2, column=0, padx=16, pady=(8, 16), sticky="nsew")

    def _refresh_view(self) -> None:
        """Toggles between welcome screen and queue screen based on queue state."""
        if self.tab_var.get() != "PNG Converter":
            return
            
        # Ensure UGC workspace exists
        if not hasattr(self, "ugc_workspace") or not self.ugc_workspace:
            self.ugc_workspace = UgcWorkspaceFrame(
                self,
                state_manager=self.state_manager,
                settings=self.settings,
                logger=self.logger,
                show_toast_callback=self.show_toast
            )
        self.ugc_workspace.grid(row=2, column=0, padx=16, pady=(8, 16), sticky="nsew")
        
        # Get active parent frame inside the UGC workspace
        parent = self.ugc_workspace.converter_page_container

        if not self.state_manager.files:
            # Hide queue if it exists
            if self.queue_view:
                self.queue_view.grid_forget()
            
            # Show welcome
            if not self.welcome_view:
                self.welcome_view = WelcomeFrame(
                    parent,
                    self.state_manager,
                    self.logger,
                    on_files_added=self._on_files_added
                )
            self.welcome_view.grid(row=0, column=0, padx=0, pady=0, sticky="nsew")
        else:
            # Hide welcome if it exists
            if self.welcome_view:
                self.welcome_view.grid_forget()
            
            # Build and show queue
            if not self.queue_view:
                self._build_queue_view()
            self.queue_view.grid(row=0, column=0, padx=0, pady=0, sticky="nsew")

    def _build_queue_view(self) -> None:
        parent = self.ugc_workspace.converter_page_container if (hasattr(self, "ugc_workspace") and self.ugc_workspace) else self
        self.queue_view = ctk.CTkFrame(parent, fg_color="transparent")
        # Row 0: File Queue List Table (Expands)
        # Row 1: Progress panel (Shown when converting)
        # Row 2: Bottom Control Bar (Fixed)
        self.queue_view.grid_columnconfigure(0, weight=1)
        self.queue_view.grid_rowconfigure(0, weight=1)
        self.queue_view.grid_rowconfigure(1, weight=0)
        self.queue_view.grid_rowconfigure(2, weight=0)
        
        # File Queue table
        self.file_list = FileListFrame(self.queue_view, self.state_manager)
        self.file_list.grid(row=0, column=0, pady=(0, 10), sticky="nsew")
        
        # Progress & Live Stats Dashboard (Initially packed, but hidden until conversion start)
        self.progress_panel = ProgressPanelFrame(self.queue_view, self.state_manager)
        self.progress_panel.grid(row=1, column=0, pady=(0, 10), sticky="ew")
        
        # Connect processor updates to progress panel
        self.processor.on_progress_update(self.progress_panel.update_progress_state)
        
        # Bottom Control toolbar
        self.control_bar = ctk.CTkFrame(self.queue_view, fg_color="transparent")
        self.control_bar.grid(row=2, column=0, pady=(0, 5), sticky="ew")
        
        # Left side controls
        self.add_btn = ctk.CTkButton(
            self.control_bar,
            text="Add Files",
            width=120,
            font=FONTS["body_bold"],
            fg_color=THEME_COLORS["primary"],
            hover_color=THEME_COLORS["primary_hover"],
            command=self._browse_files
        )
        self.add_btn.pack(side="left", padx=(0, 8))
        
        self.clear_queue_btn = ctk.CTkButton(
            self.control_bar,
            text="Clear Queue",
            width=100,
            font=FONTS["body_bold"],
            fg_color=THEME_COLORS["bg_card"],
            text_color=THEME_COLORS["text_main"],
            border_color=THEME_COLORS["border"],
            border_width=1,
            hover_color=THEME_COLORS["bg_hover"],
            command=self._clear_queue
        )
        self.clear_queue_btn.pack(side="left", padx=4)
        
        self.open_out_btn = ctk.CTkButton(
            self.control_bar,
            text="Open Folder 📁",
            width=110,
            font=FONTS["body_bold"],
            fg_color=THEME_COLORS["bg_card"],
            text_color=THEME_COLORS["text_main"],
            border_color=THEME_COLORS["border"],
            border_width=1,
            hover_color=THEME_COLORS["bg_hover"],
            command=self.open_explorer
        )
        self.open_out_btn.pack(side="left", padx=4)
 
        # Middle controls
        self.settings_btn = ctk.CTkButton(
            self.control_bar,
            text="Settings ⚙️",
            width=100,
            font=FONTS["body_bold"],
            fg_color=THEME_COLORS["bg_card"],
            text_color=THEME_COLORS["text_main"],
            border_color=THEME_COLORS["border"],
            border_width=1,
            hover_color=THEME_COLORS["bg_hover"],
            command=self._open_settings_dialog
        )
        self.settings_btn.pack(side="left", padx=4)
        
        # Right side action button (Convert)
        self.action_btn = ctk.CTkButton(
            self.control_bar,
            text="CONVERT QUEUE",
            width=150,
            height=34,
            font=FONTS["body_bold"],
            fg_color=THEME_COLORS["primary"],
            hover_color=THEME_COLORS["primary_hover"],
            command=self._start_conversion
        )
        self.action_btn.pack(side="right")

    def _on_add_files_click(self) -> None:
        """Shows menu to select files or folder."""
        menu = Menu(self, tearoff=0, bg=THEME_COLORS["bg_card"][1], fg=THEME_COLORS["text_main"][1], activebackground=THEME_COLORS["primary"][1])
        menu.add_command(label="Select Files...", command=self._browse_files)
        menu.add_command(label="Select Folder...", command=self._browse_folder)
        
        x = self.add_btn.winfo_rootx()
        y = self.add_btn.winfo_rooty() + self.add_btn.winfo_height()
        menu.post(x, y)

    def _browse_files(self) -> None:
        files = filedialog = ctk.filedialog.askopenfilenames(
            title="Select Images",
            filetypes=[
                ("Supported Images", "*.jpg;*.jpeg;*.png"),
                ("JPEG Images", "*.jpg;*.jpeg"),
                ("PNG Images", "*.png")
            ]
        )
        if files:
            self._welcome_process_paths(list(files))

    def _browse_folder(self) -> None:
        folder = ctk.filedialog.askdirectory(title="Select Folder to Scan")
        if folder:
            self._welcome_process_paths([folder])

    def _welcome_process_paths(self, paths: list) -> None:
        added_count = 0
        for path in paths:
            scanned_files = scan_file_or_directory(path, recursive=True)
            for filepath in scanned_files:
                size = os.path.getsize(filepath)
                from utils.file_helpers import get_image_info
                _, res_str = get_image_info(filepath)
                success = self.state_manager.add_file(filepath, size, res_str)
                if success:
                    added_count += 1
        if added_count > 0:
            self.logger.info(f"Added {added_count} image(s) to queue.")
            self._on_files_added()

    def _open_settings_dialog(self) -> None:
        """Launches the settings modal."""
        dialog = SettingsDialog(self, self.settings)
        dialog.focus()



    def _on_files_added(self) -> None:
        self._refresh_view()

    def _set_theme(self, new_theme: str) -> None:
        ctk.set_appearance_mode(new_theme)
        self.logger.info(f"Theme changed to {new_theme.capitalize()} Mode.")

    def _clear_queue(self) -> None:
        if not self.state_manager.files:
            return
        if messagebox.askyesno("Clear Queue", "Are you sure you want to remove all files from the queue?"):
            self.state_manager.clear_queue()
            self.logger.info("Conversion queue cleared.")
            # Destroy queue view to force rebuild next time files are added
            if self.queue_view:
                self.queue_view.destroy()
                self.queue_view = None
            self.logs_visible = False
            self._refresh_view()

    def open_explorer(self) -> None:
        mode = self.settings.get("output_mode")
        folder = ""
        
        if mode == "custom":
            folder = self.settings.get("custom_output_dir")
        else:
            if self.state_manager.files:
                folder = os.path.dirname(self.state_manager.files[0]["path"])
            else:
                folder = os.path.abspath(os.getcwd())
                
        if not folder or not os.path.exists(folder):
            if mode == "custom":
                self.logger.error(f"Destination folder is invalid or empty: '{folder}'")
                messagebox.showerror("Invalid Folder", "Custom destination folder does not exist or is empty.")
                return
            folder = os.path.abspath(os.getcwd())
            
        import platform
        import subprocess
        try:
            if platform.system() == "Windows":
                os.startfile(folder)
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", folder])
            else:
                subprocess.Popen(["xdg-open", folder])
            self.logger.info(f"Opened output folder: '{folder}'")
        except Exception as e:
            self.logger.error(f"Failed to open destination folder: {e}")

    def _start_conversion(self) -> None:
        files_to_convert = [f for f in self.state_manager.files if f["status"] in ("Waiting", "Failed")]
        
        if not self.state_manager.files:
            self.show_toast("The queue is empty. Drag and drop images to start.", type="error")
            return
            
        if not files_to_convert:
            self.show_toast("All files in the queue have already been converted.", type="info")
            return
            
        # UI controls locking
        self.add_btn.configure(state="disabled")
        self.clear_queue_btn.configure(state="disabled")
        self.settings_btn.configure(state="disabled")
        
        # Change Convert button to Cancel button
        self.action_btn.configure(
            text="CANCEL CONVERSION",
            fg_color=("#EF4444", "#DC2626"),
            hover_color=("#DC2626", "#B91C1C"),
            command=self._cancel_conversion
        )
        
        # Run conversion thread pool
        self.processor.start()

    def _cancel_conversion(self) -> None:
        self.processor.cancel()

    def show_toast(self, message: str, type: str = "success", duration_ms: int = 2000) -> None:
        """Displays a beautiful non-blocking Shadcn-UI styled notification toast at the top of the window."""
        # Clean up any existing toast first if it exists to avoid overlapping multiple toasts
        if hasattr(self, "_active_toast"):
            try:
                if self._active_toast.winfo_exists():
                    self._active_toast.destroy()
            except Exception:
                pass

        # Shadcn-UI style colors adapting to light and dark themes
        toast_bg = ("#FFFFFF", "#18181B")  # White in light mode, Dark Slate-900 in dark mode

        # Color code the border based on the message type (with light/dark mode support)
        if type == "error":
            border_color = ("#EF4444", "#F87171")  # red-500 / red-400
        elif type == "info":
            border_color = ("#3B82F6", "#60A5FA")  # blue-500 / blue-400
        else:
            border_color = ("#10B981", "#34D399")  # green-500 / green-400

        text_color = border_color

        # Toast frame positioned floating at the top center of the application window
        self._active_toast = ctk.CTkFrame(
            self,
            fg_color=toast_bg,
            border_color=border_color,
            border_width=2,
            corner_radius=6
        )
        self._active_toast.place(relx=0.5, rely=0.18, anchor="center")
        
        # Message Label
        lbl = ctk.CTkLabel(
            self._active_toast,
            text=message,
            font=("Outfit", 12, "bold"),
            text_color=text_color,
            padx=20,
            pady=10,
            justify="center"
        )
        lbl.pack()
        
        # Schedule auto-destruction after duration_ms
        self.after(duration_ms, lambda: self._destroy_toast(self._active_toast))

    def _destroy_toast(self, toast_widget) -> None:
        try:
            if toast_widget.winfo_exists():
                toast_widget.destroy()
        except Exception:
            pass

    def _on_batch_start(self) -> None:
        pass

    def _on_batch_complete(self, cancelled: bool) -> None:
        # Restore Main Action Button
        self.action_btn.configure(
            text="CONVERT QUEUE",
            fg_color=THEME_COLORS["primary"],
            hover_color=THEME_COLORS["primary_hover"],
            command=self._start_conversion
        )
        
        # Unlock UI controls
        self.add_btn.configure(state="normal")
        self.clear_queue_btn.configure(state="normal")
        self.settings_btn.configure(state="normal")
        
        if cancelled:
            self.show_toast("Conversion Stopped", type="error", duration_ms=2000)
        else:
            stats = self.state_manager.get_compression_stats()
            if stats["failed_files"] > 0:
                failed_files = [f for f in self.state_manager.files if f["status"] == "Failed"]
                error_list = []
                for f in failed_files:
                    error_list.append(f"{f['name']}: {f['error_msg']}")
                error_details = " | ".join(error_list)
                msg = f"Failed! {error_details}"
                self.show_toast(msg, type="error", duration_ms=4000)
            else:
                msg = f"Success! Converted: {stats['completed_files']} | Skipped: {stats['skipped_files']}"
                self.show_toast(msg, type="success", duration_ms=2000)
            
            if self.settings.get("open_after_complete"):
                self.open_explorer()


if __name__ == "__main__":
    app = OptiWebPApp()
    app.mainloop()
