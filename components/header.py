import os
import customtkinter as ctk
from PIL import Image
from components.theme import THEME_COLORS, FONTS
from utils.file_helpers import get_resource_path

class HeaderFrame(ctk.CTkFrame):
    def __init__(self, master, settings_manager, on_theme_toggle_callback, **kwargs):
        super().__init__(
            master, 
            fg_color=THEME_COLORS["bg_card"],
            border_color=THEME_COLORS["border"],
            border_width=1,
            corner_radius=12,
            **kwargs
        )
        self.settings = settings_manager
        self.on_theme_toggle = on_theme_toggle_callback
        
        # Configure layout grid
        self.grid_columnconfigure(0, weight=1)  # Left (Logo + Title)
        self.grid_columnconfigure(1, weight=0)  # Right (Theme Toggle)
        self.grid_rowconfigure(0, weight=1)
        
        # Left side: Container for Logo and Title
        self.brand_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.brand_frame.grid(row=0, column=0, padx=16, pady=8, sticky="w")
        
        # Load and set application logo
        logo_path = get_resource_path(os.path.join("assets", "logo.png"))
        if os.path.exists(logo_path):
            try:
                pil_img = Image.open(logo_path)
                # CTkImage handles high-DPI scaling automatically
                self.logo_image = ctk.CTkImage(
                    light_image=pil_img,
                    dark_image=pil_img,
                    size=(36, 36)
                )
                self.logo_label = ctk.CTkLabel(self.brand_frame, image=self.logo_image, text="")
                self.logo_label.grid(row=0, column=0, padx=(0, 12), sticky="w")
            except Exception as e:
                print(f"Error loading logo in header: {e}")
                self.logo_image = None
        
        # App Title and Subtitle
        self.title_container = ctk.CTkFrame(self.brand_frame, fg_color="transparent")
        self.title_container.grid(row=0, column=1, sticky="w")
        
        self.title_label = ctk.CTkLabel(
            self.title_container, 
            text="OptiWebP", 
            font=FONTS["title"], 
            text_color=THEME_COLORS["text_main"]
        )
        self.title_label.grid(row=0, column=0, sticky="w")
        
        self.subtitle_label = ctk.CTkLabel(
            self.title_container, 
            text="Professional Image to WebP Converter", 
            font=FONTS["small"], 
            text_color=THEME_COLORS["text_muted"]
        )
        self.subtitle_label.grid(row=1, column=0, sticky="w")

        # Right side: Theme Toggle Frame
        self.toggle_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.toggle_frame.grid(row=0, column=1, padx=16, pady=8, sticky="e")
        
        # Label next to switch
        self.theme_label = ctk.CTkLabel(
            self.toggle_frame, 
            text="Dark Mode", 
            font=FONTS["body_bold"], 
            text_color=THEME_COLORS["text_main"]
        )
        self.theme_label.pack(side="left", padx=(0, 8))
        
        # Switch
        current_theme = self.settings.get("theme")
        self.switch_var = ctk.IntVar(value=1 if current_theme == "dark" else 0)
        self.theme_switch = ctk.CTkSwitch(
            self.toggle_frame,
            text="",
            variable=self.switch_var,
            onvalue=1,
            offvalue=0,
            command=self._toggle_theme,
            progress_color=THEME_COLORS["primary"][1], # Always use emerald for toggled state
            button_color=THEME_COLORS["primary"],
            button_hover_color=THEME_COLORS["primary_hover"]
        )
        self.theme_switch.pack(side="left")
        
        # Initialize text label
        self._update_theme_label(current_theme)

    def _toggle_theme(self) -> None:
        """Toggles the theme based on switch value."""
        is_dark = self.switch_var.get() == 1
        new_theme = "dark" if is_dark else "light"
        
        # Save to settings
        self.settings.set("theme", new_theme)
        
        # Trigger external callback (which calls ctk.set_appearance_mode)
        self.on_theme_toggle(new_theme)
        
        # Update header labels
        self._update_theme_label(new_theme)

    def _update_theme_label(self, theme: str) -> None:
        if theme == "dark":
            self.theme_label.configure(text="Dark Mode")
        else:
            self.theme_label.configure(text="Light Mode")
