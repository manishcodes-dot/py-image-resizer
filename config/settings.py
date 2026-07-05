import os
import json
from typing import Any, Dict

DEFAULT_SETTINGS = {
    "quality": 85,
    "lossless": False,
    "preserve_metadata": True,
    "overwrite": False,
    "delete_original": False,
    "open_after_complete": False,  # Auto-open output folder
    "output_mode": "same",  # "same" or "custom"
    "custom_output_dir": "",
    "resize_mode": "original",  # "original", "1920", "1080", "720", "custom_w", "custom_h"
    "custom_width": 1280,
    "custom_height": 720,
    "maintain_aspect": True,
    "theme": "dark",  # "dark" or "light"
    
    # AI Settings
    "ai_api_key": "",
    "ai_provider": "Grok",
    "ai_output_folder": "",
    "ai_image_size": "1024x1024",
    "ai_num_images": 1,
    "ai_quality": "Standard",
    "ai_save_history": True,
    "ai_auto_save": True
}

class SettingsManager:
    def __init__(self, config_filename: str = "config.json"):
        # Put config file in the user's home or local workspace directory
        # For simplicity and portability, we place it in the same directory as main.py
        self.config_path = os.path.abspath(config_filename)
        self.settings: Dict[str, Any] = DEFAULT_SETTINGS.copy()
        self.load()

    def load(self) -> None:
        """Loads configuration from JSON file. If it doesn't exist, creates it with defaults."""
        if not os.path.exists(self.config_path):
            self.save()
            return
        
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                # Merge defaults to handle cases where some fields might be missing from an older config
                for key, val in DEFAULT_SETTINGS.items():
                    self.settings[key] = loaded.get(key, val)
        except Exception as e:
            print(f"Error loading configuration: {e}. Reverting to defaults.")
            self.settings = DEFAULT_SETTINGS.copy()
            self.save()

    def save(self) -> None:
        """Saves current configuration to JSON file."""
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, indent=4)
        except Exception as e:
            print(f"Error saving configuration: {e}")

    def get(self, key: str) -> Any:
        """Retrieves a configuration value."""
        return self.settings.get(key, DEFAULT_SETTINGS.get(key))

    def set(self, key: str, value: Any) -> None:
        """Sets a configuration value and saves it."""
        if key in DEFAULT_SETTINGS:
            # Type casting to make sure we store correct types
            expected_type = type(DEFAULT_SETTINGS[key])
            if expected_type is bool and not isinstance(value, bool):
                value = bool(value)
            elif expected_type is int and not isinstance(value, int):
                try:
                    value = int(value)
                except ValueError:
                    value = DEFAULT_SETTINGS[key]
            elif expected_type is str and not isinstance(value, str):
                value = str(value)
            
            self.settings[key] = value
            self.save()
