import os
import time
from concurrent.futures import ThreadPoolExecutor, Future
from typing import List, Dict, Any, Callable, Optional
from utils.file_helpers import format_size

class BatchProcessor:
    def __init__(self, state_manager, logger_service, image_converter, root_window):
        self.state_manager = state_manager
        self.logger = logger_service
        self.converter = image_converter
        self.root = root_window
        
        self.executor: Optional[ThreadPoolExecutor] = None
        self.futures: List[Future] = []
        
        # Batch status
        self.is_running = False
        self.is_cancelled = False
        
        # Timing & Speed statistics
        self.start_time = 0.0
        self.total_to_process = 0
        self.completed_in_batch = 0
        self.failed_in_batch = 0
        self.skipped_in_batch = 0
        
        # Callbacks
        self.on_batch_start_callbacks: List[Callable[[], None]] = []
        self.on_batch_complete_callbacks: List[Callable[[bool], None]] = []  # True if cancelled
        self.on_progress_update_callbacks: List[Callable[[Dict[str, Any]], None]] = []

    # Register callbacks
    def on_batch_start(self, callback: Callable[[], None]) -> None:
        self.on_batch_start_callbacks.append(callback)

    def on_batch_complete(self, callback: Callable[[bool], None]) -> None:
        self.on_batch_complete_callbacks.append(callback)

    def on_progress_update(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        self.on_progress_update_callbacks.append(callback)

    def start(self, max_workers: Optional[int] = None) -> None:
        """Starts the batch conversion process for all files in 'Waiting' status."""
        if self.is_running:
            return
            
        # Get files to process
        files_to_process = [f for f in self.state_manager.files if f["status"] in ("Waiting", "Failed")]
        if not files_to_process:
            self.logger.warning("No files in the queue to convert.")
            return
            
        self.is_running = True
        self.is_cancelled = False
        self.total_to_process = len(files_to_process)
        self.completed_in_batch = 0
        self.failed_in_batch = 0
        self.skipped_in_batch = 0
        
        # Reset failed files to waiting so they can be processed
        self.state_manager.reset_for_conversion()
        
        self.start_time = time.time()
        self.logger.info(f"Starting batch conversion of {self.total_to_process} images...")
        
        for cb in self.on_batch_start_callbacks:
            try:
                cb()
            except Exception as e:
                print(f"Error in on_batch_start callback: {e}")
                
        # Calculate optimal worker threads (default to CPU count minus 1, min 1, max 8 to prevent disk IO saturation)
        if max_workers is None:
            max_workers = min(8, max(1, (os.cpu_count() or 4) - 1))
            
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.futures = []
        
        # Submit tasks
        for file_entry in files_to_process:
            future = self.executor.submit(self._worker_task, file_entry)
            self.futures.append(future)
            
        # Trigger an initial progress update
        self._update_progress()

    def cancel(self) -> None:
        """Cancels the running batch conversion."""
        if not self.is_running:
            return
            
        self.is_cancelled = True
        self.logger.warning("Cancellation requested. Stopping queue...")
        
        # Shutdown executor but don't wait - we want to mark remaining files quickly
        if self.executor:
            self.executor.shutdown(wait=False, cancel_futures=True)
            
        # Cancel any futures that haven't run yet
        for f in self.futures:
            f.cancel()
            
        # If no threads are actually running or all completed, clean up
        self._check_batch_finished()

    def _worker_task(self, file_entry: Dict[str, Any]) -> None:
        """The worker thread routine."""
        file_id = file_entry["id"]
        filepath = file_entry["path"]
        
        if self.is_cancelled:
            # If cancelled before starting, keep as waiting or schedule cancellation status
            self.root.after(0, self._on_file_cancelled, file_id)
            return

        # Update status to Converting (run on UI thread)
        self.root.after(0, self.state_manager.update_file_status, file_id, "Converting")
        
        # Perform conversion (blocking IO)
        status, new_size, err_msg = self.converter.convert_image(filepath)
        
        # Report completion (run on UI thread)
        self.root.after(0, self._on_file_done, file_entry, status, new_size, err_msg)

    def _on_file_cancelled(self, file_id: str) -> None:
        # Keep status as Waiting since it was cancelled
        self._check_batch_finished()

    def _on_file_done(self, file_entry: Dict[str, Any], status: str, new_size: int, err_msg: str) -> None:
        """Runs on the main UI thread when a file conversion is complete."""
        file_id = file_entry["id"]
        filename = file_entry["name"]
        orig_size = file_entry["size"]
        
        # Update state manager
        self.state_manager.update_file_status(file_id, status, new_size, err_msg)
        
        # Log result
        if status == "Completed":
            self.completed_in_batch += 1
            savings = orig_size - new_size
            pct = (savings / orig_size * 100.0) if orig_size > 0 else 0.0
            size_diff = f"{format_size(orig_size)} → {format_size(new_size)} (-{pct:.1f}%)"
            self.logger.success(f"✓ {filename} converted successfully. {size_diff}")
        elif status == "Skipped":
            self.skipped_in_batch += 1
            self.logger.info(f"↷ {filename} skipped: {err_msg}")
        elif status == "Failed":
            self.failed_in_batch += 1
            self.logger.error(f"✗ {filename} failed: {err_msg}")

        # Update live progress & stats
        self._update_progress()
        
        # Check if the entire batch is completed
        self._check_batch_finished()

    def _update_progress(self) -> None:
        """Calculates and dispatches progress updates to the UI."""
        processed = self.completed_in_batch + self.failed_in_batch + self.skipped_in_batch
        
        elapsed = time.time() - self.start_time
        speed_fps = processed / elapsed if elapsed > 0 else 0.0
        speed_ms = (elapsed * 1000.0) / processed if processed > 0 else 0.0
        
        remaining = self.total_to_process - processed
        eta_seconds = remaining / speed_fps if speed_fps > 0 else 0.0
        
        # Format ETA
        if processed == 0:
            eta_str = "Calculating..."
        elif remaining == 0:
            eta_str = "0s"
        elif eta_seconds < 60:
            eta_str = f"{int(eta_seconds)}s"
        else:
            m = int(eta_seconds // 60)
            s = int(eta_seconds % 60)
            eta_str = f"{m}m {s}s"

        # Format Speed
        if processed == 0:
            speed_str = "Waiting..."
        elif speed_fps >= 1.0:
            speed_str = f"{speed_fps:.2f} img/s"
        else:
            speed_str = f"{int(speed_ms)} ms/img"

        progress_data = {
            "processed": processed,
            "total": self.total_to_process,
            "completed": self.completed_in_batch,
            "failed": self.failed_in_batch,
            "skipped": self.skipped_in_batch,
            "remaining": remaining,
            "elapsed": elapsed,
            "speed": speed_str,
            "eta": eta_str,
            "percentage": (processed / self.total_to_process) if self.total_to_process > 0 else 0.0
        }
        
        for cb in self.on_progress_update_callbacks:
            try:
                cb(progress_data)
            except Exception as e:
                print(f"Error in on_progress_update callback: {e}")

    def _check_batch_finished(self) -> None:
        """Checks if all futures have completed and cleans up the batch."""
        if not self.is_running:
            return
            
        # Check if all submitted tasks are done
        # (Since we run in the main thread, we can check futures or processed count)
        processed = self.completed_in_batch + self.failed_in_batch + self.skipped_in_batch
        
        # If all submitted tasks are finished, or if we cancelled and no active worker is remaining
        all_done = (processed >= self.total_to_process) or (self.is_cancelled and all(f.done() for f in self.futures))
        
        if all_done:
            self._finalize_batch()

    def _finalize_batch(self) -> None:
        self.is_running = False
        
        # Clean up executor
        if self.executor:
            self.executor.shutdown(wait=False)
            self.executor = None
            
        self.futures = []
        
        # Log final status
        elapsed_str = f"{time.time() - self.start_time:.2f}s"
        if self.is_cancelled:
            self.logger.warning(f"Batch conversion cancelled after {elapsed_str}.")
        else:
            self.logger.success(
                f"Batch conversion completed in {elapsed_str}! "
                f"Converted: {self.completed_in_batch}, "
                f"Skipped: {self.skipped_in_batch}, "
                f"Failed: {self.failed_in_batch}."
            )
            
        # Trigger completed callbacks
        for cb in self.on_batch_complete_callbacks:
            try:
                cb(self.is_cancelled)
            except Exception as e:
                print(f"Error in on_batch_complete callback: {e}")
