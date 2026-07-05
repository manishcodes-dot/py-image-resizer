import os
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any

class HistoryService:
    def __init__(self, filename: str = "history.json"):
        # Store in the same directory as config.json/main.py for consistency
        self.filepath = os.path.abspath(filename)
        self.history: List[Dict[str, Any]] = []
        self.load()

    def load(self) -> None:
        """Loads generation history from file."""
        if not os.path.exists(self.filepath):
            self.save()
            return
        
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                self.history = json.load(f)
        except Exception as e:
            print(f"Error loading history: {e}")
            self.history = []

    def save(self) -> None:
        """Saves generation history to file."""
        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(self.history, f, indent=4)
        except Exception as e:
            print(f"Error saving history: {e}")

    def add_entry(
        self, 
        prompt: str, 
        negative_prompt: str, 
        provider: str, 
        size: str, 
        image_path: str
    ) -> Dict[str, Any]:
        """Creates and appends a new history entry."""
        entry = {
            "id": str(uuid.uuid4()),
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "provider": provider,
            "size": size,
            "image_path": os.path.abspath(image_path)
        }
        # Insert at the beginning so newer items appear first
        self.history.insert(0, entry)
        self.save()
        return entry

    def delete_entry(self, entry_id: str) -> bool:
        """Deletes a history entry by ID."""
        for i, entry in enumerate(self.history):
            if entry["id"] == entry_id:
                # Optional: Delete file if wanted? We should keep the file but delete from history as per standard,
                # or delete the file if it exists. Let's delete from history only, but we can also check if we want to delete file.
                self.history.pop(i)
                self.save()
                return True
        return False

    def clear_all(self) -> None:
        """Clears all history entries."""
        self.history = []
        self.save()
