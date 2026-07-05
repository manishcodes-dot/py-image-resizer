# Design tokens for the application

# Modern harmonized color palettes using HSL-based mappings
# Format: (Light Mode Color, Dark Mode Color)

THEME_COLORS = {
    "bg_window": ("#F3F4F6", "#141517"),       # Window background
    "bg_card": ("#FFFFFF", "#1E1F22"),         # Panel cards
    "bg_hover": ("#F9FAFB", "#2A2B30"),        # Button/list hover states
    
    "border": ("#E5E7EB", "#2D2E32"),          # Card/divider borders
    "border_active": ("#10B981", "#10B981"),   # Highlights/focus
    
    "primary": ("#10B981", "#10B981"),         # Emerald Green Accent
    "primary_hover": ("#059669", "#059669"),
    
    "text_main": ("#111827", "#F9FAFB"),       # Main labels
    "text_muted": ("#6B7280", "#9CA3AF"),      # Secondary details
    
    # Status indicators
    "status_waiting": ("#2563EB", "#3B82F6"),
    "status_converting": ("#D97706", "#F59E0B"),
    "status_completed": ("#10B981", "#10B981"), # Matched to primary green
    "status_skipped": ("#4B5563", "#9CA3AF"),
    "status_failed": ("#DC2626", "#EF4444")
}

FONT_FAMILY = "Outfit"  # Premium modern look, falls back to Arial/Inter if Outfit isn't installed

FONTS = {
    "title": (FONT_FAMILY, 20, "bold"),
    "header": (FONT_FAMILY, 15, "bold"),
    "body_bold": (FONT_FAMILY, 13, "bold"),
    "body": (FONT_FAMILY, 13, "normal"),
    "small": (FONT_FAMILY, 11, "normal"),
    "caption": (FONT_FAMILY, 10, "normal"),
    "caption_bold": (FONT_FAMILY, 10, "bold"),
    "code": ("Consolas", 11, "normal")
}
