import os
import uuid
from typing import List, Dict, Any, Callable

class StateManager:
    def __init__(self):
        # File list structure:
        # {
        #    'id': str,
        #    'path': str,
        #    'name': str,
        #    'size': int,  # bytes
        #    'resolution': str,  # "W x H"
        #    'status': str,  # "Waiting", "Converting", "Completed", "Skipped", "Failed"
        #    'new_size': int,  # bytes
        #    'saved_percent': float,
        #    'error_msg': str
        # }
        self.files: List[Dict[str, Any]] = []
        self.files_by_id: Dict[str, Dict[str, Any]] = {}
        self.files_by_path: Dict[str, Dict[str, Any]] = {}
        
        # Statistics
        self.total_files = 0
        self.processed_files = 0
        self.completed_files = 0
        self.failed_files = 0
        self.skipped_files = 0
        
        self.total_original_bytes = 0
        self.total_converted_bytes = 0
        
        # Callbacks
        self.file_added_callbacks: List[Callable[[Dict[str, Any]], None]] = []
        self.file_updated_callbacks: List[Callable[[Dict[str, Any]], None]] = []
        self.stats_updated_callbacks: List[Callable[[], None]] = []
        self.queue_cleared_callbacks: List[Callable[[], None]] = []
        self.file_removed_callbacks: List[Callable[[str], None]] = []

    # Observer Registering
    def on_file_added(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        self.file_added_callbacks.append(callback)

    def on_file_updated(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        self.file_updated_callbacks.append(callback)

    def on_stats_updated(self, callback: Callable[[], None]) -> None:
        self.stats_updated_callbacks.append(callback)

    def on_queue_cleared(self, callback: Callable[[], None]) -> None:
        self.queue_cleared_callbacks.append(callback)

    def on_file_removed(self, callback: Callable[[str], None]) -> None:
        self.file_removed_callbacks.append(callback)

    # State Actions
    def add_file(self, filepath: str, size: int, resolution: str) -> bool:
        """Adds a file to the queue. Returns True if successfully added, False if duplicate."""
        norm_path = os.path.abspath(filepath)
        if norm_path in self.files_by_path:
            return False
            
        file_id = str(uuid.uuid4())
        file_entry = {
            "id": file_id,
            "path": norm_path,
            "name": os.path.basename(filepath),
            "size": size,
            "resolution": resolution,
            "status": "Waiting",
            "new_size": 0,
            "saved_percent": 0.0,
            "error_msg": ""
        }
        
        self.files.append(file_entry)
        self.files_by_id[file_id] = file_entry
        self.files_by_path[norm_path] = file_entry
        
        self.total_files = len(self.files)
        self.total_original_bytes += size
        
        # Notify
        for cb in self.file_added_callbacks:
            try:
                cb(file_entry)
            except Exception as e:
                print(f"Error in file_added callback: {e}")
                
        self.update_stats()
        return True

    def remove_file(self, file_id: str) -> None:
        """Removes a single file from the queue by ID."""
        if file_id not in self.files_by_id:
            return
            
        entry = self.files_by_id[file_id]
        self.files.remove(entry)
        del self.files_by_id[file_id]
        if entry["path"] in self.files_by_path:
            del self.files_by_path[entry["path"]]
            
        self.total_files = len(self.files)
        
        # Recompute totals and stats from remaining files
        self.recalculate_all_stats()
        
        # Notify
        for cb in self.file_removed_callbacks:
            try:
                cb(file_id)
            except Exception as e:
                print(f"Error in file_removed callback: {e}")
                
        self.update_stats()

    def clear_queue(self) -> None:
        """Clears all files and resets stats."""
        self.files.clear()
        self.files_by_id.clear()
        self.files_by_path.clear()
        
        self.total_files = 0
        self.processed_files = 0
        self.completed_files = 0
        self.failed_files = 0
        self.skipped_files = 0
        self.total_original_bytes = 0
        self.total_converted_bytes = 0
        
        for cb in self.queue_cleared_callbacks:
            try:
                cb()
            except Exception as e:
                print(f"Error in queue_cleared callback: {e}")
                
        self.update_stats()

    def update_file_status(
        self, 
        file_id: str, 
        status: str, 
        new_size: int = 0, 
        error_msg: str = ""
    ) -> None:
        """Updates the status and results of a file, then recalculates statistics."""
        if file_id not in self.files_by_id:
            return
            
        entry = self.files_by_id[file_id]
        old_status = entry["status"]
        entry["status"] = status
        entry["error_msg"] = error_msg
        
        if status == "Completed" and new_size > 0:
            entry["new_size"] = new_size
            saved = entry["size"] - new_size
            entry["saved_percent"] = (saved / entry["size"] * 100.0) if entry["size"] > 0 else 0.0
        elif status in ("Failed", "Skipped"):
            entry["new_size"] = 0
            entry["saved_percent"] = 0.0

        # Notify UI about file change
        for cb in self.file_updated_callbacks:
            try:
                cb(entry)
            except Exception as e:
                print(f"Error in file_updated callback: {e}")
                
        self.recalculate_all_stats()
        self.update_stats()

    def recalculate_all_stats(self) -> None:
        """Recalculates counts and sizes from the current queue state."""
        self.processed_files = 0
        self.completed_files = 0
        self.failed_files = 0
        self.skipped_files = 0
        
        # We only count bytes for files that are Completed.
        # For original size of completed files, we sum them up.
        completed_orig_bytes = 0
        completed_conv_bytes = 0
        
        for f in self.files:
            status = f["status"]
            if status != "Waiting":
                self.processed_files += 1
                
            if status == "Completed":
                self.completed_files += 1
                completed_orig_bytes += f["size"]
                completed_conv_bytes += f["new_size"]
            elif status == "Failed":
                self.failed_files += 1
            elif status == "Skipped":
                self.skipped_files += 1

        self.total_original_bytes = completed_orig_bytes
        self.total_converted_bytes = completed_conv_bytes

    def reset_for_conversion(self) -> None:
        """Resets status of Failed or Converting files back to Waiting to run them again, preserves Completed ones."""
        for f in self.files:
            if f["status"] in ("Failed", "Converting"):
                f["status"] = "Waiting"
                f["new_size"] = 0
                f["saved_percent"] = 0.0
                f["error_msg"] = ""
                for cb in self.file_updated_callbacks:
                    try:
                        cb(f)
                    except Exception as e:
                        print(f"Error in file_updated callback: {e}")
        self.recalculate_all_stats()
        self.update_stats()

    def update_stats(self) -> None:
        """Triggers stats update event."""
        for cb in self.stats_updated_callbacks:
            try:
                cb()
            except Exception as e:
                print(f"Error in stats_updated callback: {e}")

    def get_compression_stats(self) -> Dict[str, Any]:
        """Calculates and returns total compression statistics."""
        saved_bytes = self.total_original_bytes - self.total_converted_bytes
        if saved_bytes < 0:
            saved_bytes = 0
            
        ratio = 0.0
        if self.total_original_bytes > 0:
            ratio = (saved_bytes / self.total_original_bytes) * 100.0
            
        return {
            "original_size": self.total_original_bytes,
            "converted_size": self.total_converted_bytes,
            "saved_size": saved_bytes,
            "compression_percent": ratio,
            "total_files": self.total_files,
            "processed_files": self.processed_files,
            "completed_files": self.completed_files,
            "failed_files": self.failed_files,
            "skipped_files": self.skipped_files,
            "remaining_files": self.total_files - self.processed_files
        }
