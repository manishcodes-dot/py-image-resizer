import os
import datetime
from typing import Callable, List, Dict

class LoggerService:
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = os.path.abspath(log_dir)
        os.makedirs(self.log_dir, exist_ok=True)
        self.log_file = os.path.join(self.log_dir, "converter.log")
        self.in_memory_logs: List[Dict[str, str]] = []
        self.callbacks: List[Callable[[Dict[str, str]], None]] = []

        # Create log file if it doesn't exist
        if not os.path.exists(self.log_file):
            self.write_to_file("=== Logger Initialized ===")

    def register_callback(self, callback: Callable[[Dict[str, str]], None]) -> None:
        """Register a callback to be notified when a new log event is added."""
        self.callbacks.append(callback)

    def write_to_file(self, message: str) -> None:
        """Appends a raw log message to the log file."""
        try:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(f"[{timestamp}] {message}\n")
        except Exception as e:
            print(f"Failed to write to log file: {e}")

    def log(self, message: str, level: str = "info") -> None:
        """
        Logs a message with a specific level ('info', 'success', 'error', 'warning').
        """
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        log_entry = {
            "timestamp": timestamp,
            "message": message,
            "level": level.lower()
        }
        self.in_memory_logs.append(log_entry)
        
        # Write to persistent file
        self.write_to_file(f"[{level.upper()}] {message}")
        
        # Trigger callbacks
        for callback in self.callbacks:
            try:
                callback(log_entry)
            except Exception as e:
                print(f"Error in logger callback: {e}")

    def info(self, message: str) -> None:
        self.log(message, "info")

    def success(self, message: str) -> None:
        self.log(message, "success")

    def error(self, message: str) -> None:
        self.log(message, "error")

    def warning(self, message: str) -> None:
        self.log(message, "warning")

    def get_logs_text(self) -> str:
        """Returns all in-memory logs formatted as a single string."""
        return "\n".join([f"[{entry['timestamp']}] {entry['message']}" for entry in self.in_memory_logs])

    def clear(self) -> None:
        """Clears in-memory logs."""
        self.in_memory_logs.clear()

    def save_logs_to_file(self, target_path: str) -> bool:
        """Saves current session logs to a custom file location."""
        try:
            with open(target_path, "w", encoding="utf-8") as f:
                f.write("=== Image to WebP Converter Session Logs ===\n")
                f.write(f"Saved At: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                for entry in self.in_memory_logs:
                    f.write(f"[{entry['timestamp']}] [{entry['level'].upper()}] {entry['message']}\n")
            return True
        except Exception as e:
            self.error(f"Failed to save log to file {target_path}: {e}")
            return False
