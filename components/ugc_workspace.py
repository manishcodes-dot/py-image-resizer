import customtkinter as ctk

class UgcWorkspaceFrame(ctk.CTkFrame):
    def __init__(self, master, state_manager, settings, logger, show_toast_callback, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.state_manager = state_manager
        self.settings = settings
        self.logger = logger
        self.show_toast = show_toast_callback
        
        # Grid setup: Column 0 is content
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Initialize Image Converter Container Page
        self.converter_page_container = ctk.CTkFrame(self, fg_color="transparent")
        self.converter_page_container.grid(row=0, column=0, sticky="nsew")
        self.converter_page_container.grid_columnconfigure(0, weight=1)
        self.converter_page_container.grid_rowconfigure(0, weight=1)

