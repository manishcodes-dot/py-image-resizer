import os
import io
import re
import ctypes
import threading
import urllib.request
from datetime import datetime
from PIL import Image, ImageTk
import customtkinter as ctk
from tkinter import filedialog, messagebox

from components.theme import THEME_COLORS, FONTS
from core.providers.grok_provider import GrokProvider
from services.history_service import HistoryService

class ZoomableCanvas(ctk.CTkCanvas):
    def __init__(self, master, **kwargs):
        super().__init__(master, highlightthickness=0, bg="#141517", **kwargs)
        self.image_path = None
        self.pil_image = None
        self.tk_image = None
        self.zoom_level = 1.0
        self.pan_x = 0
        self.pan_y = 0
        self._drag_start_x = 0
        self._drag_start_y = 0

        # Bind events
        self.bind("<MouseWheel>", self._on_zoom)
        self.bind("<ButtonPress-1>", self._on_drag_start)
        self.bind("<B1-Motion>", self._on_drag_move)
        self.bind("<Configure>", lambda e: self.show_image())

    def set_image(self, image_path: str):
        self.image_path = image_path
        if image_path and os.path.exists(image_path):
            self.pil_image = Image.open(image_path)
            self.fit_to_window()
        else:
            self.pil_image = None
            self.tk_image = None
            self.delete("all")

    def fit_to_window(self):
        if not self.pil_image:
            return
        
        canvas_w = self.winfo_width() or 400
        canvas_h = self.winfo_height() or 400
        img_w, img_h = self.pil_image.size

        # Calculate fit scale
        scale_w = canvas_w / img_w
        scale_h = canvas_h / img_h
        self.zoom_level = min(scale_w, scale_h, 1.5)  # Cap at 1.5x for fit
        
        # Center the image
        self.pan_x = (canvas_w - (img_w * self.zoom_level)) / 2
        self.pan_y = (canvas_h - (img_h * self.zoom_level)) / 2
        
        self.show_image()

    def set_actual_size(self):
        if not self.pil_image:
            return
        self.zoom_level = 1.0
        canvas_w = self.winfo_width()
        canvas_h = self.winfo_height()
        img_w, img_h = self.pil_image.size
        
        self.pan_x = (canvas_w - img_w) / 2
        self.pan_y = (canvas_h - img_h) / 2
        self.show_image()

    def show_image(self):
        if not self.pil_image:
            return
        
        self.delete("all")
        
        # Calculate new dimensions
        w = int(self.pil_image.width * self.zoom_level)
        h = int(self.pil_image.height * self.zoom_level)
        
        if w <= 0 or h <= 0:
            return
            
        # Resize image for display
        resized = self.pil_image.resize((w, h), Image.Resampling.LANCZOS)
        self.tk_image = ImageTk.PhotoImage(resized)
        
        # Draw on canvas
        self.create_image(self.pan_x, self.pan_y, anchor="nw", image=self.tk_image)

    def _on_zoom(self, event):
        if not self.pil_image:
            return
        
        # Get mouse position on canvas
        mx = event.x
        my = event.y
        
        # Zoom factor
        zoom_factor = 1.1 if event.delta > 0 else 0.9
        new_zoom = self.zoom_level * zoom_factor
        
        # Clamp zoom level between 0.1x and 5x
        if new_zoom < 0.1 or new_zoom > 5.0:
            return
            
        # Adjust pan so the zoom is centered on the cursor
        self.pan_x = mx - (mx - self.pan_x) * zoom_factor
        self.pan_y = my - (my - self.pan_y) * zoom_factor
        self.zoom_level = new_zoom
        
        self.show_image()

    def _on_drag_start(self, event):
        self._drag_start_x = event.x
        self._drag_start_y = event.y

    def _on_drag_move(self, event):
        if not self.pil_image:
            return
        dx = event.x - self._drag_start_x
        dy = event.y - self._drag_start_y
        self.pan_x += dx
        self.pan_y += dy
        self._drag_start_x = event.x
        self._drag_start_y = event.y
        self.show_image()


class GeneratorFrame(ctk.CTkFrame):
    def __init__(self, master, settings, logger, history_service, show_toast_callback, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.settings = settings
        self.logger = logger
        self.history_service = history_service
        self.show_toast = show_toast_callback
        self.provider = GrokProvider()
        
        # Active generation state
        self.is_generating = False
        self.generated_files = []
        self.active_file_idx = 0

        self.grid_columnconfigure(0, weight=4)  # Left controls
        self.grid_columnconfigure(1, weight=6)  # Right preview
        self.grid_rowconfigure(0, weight=1)

        self._build_ui()

    def _build_ui(self):
        # Left Panel (Controls)
        left_panel = ctk.CTkScrollableFrame(
            self,
            fg_color=THEME_COLORS["bg_card"],
            border_color=THEME_COLORS["border"],
            border_width=1,
            corner_radius=12
        )
        left_panel.grid(row=0, column=0, padx=(0, 10), pady=0, sticky="nsew")
        left_panel.grid_columnconfigure(0, weight=1)

        # Title
        title_lbl = ctk.CTkLabel(left_panel, text="AI Image Studio", font=("Outfit", 20, "bold"), text_color=THEME_COLORS["text_main"])
        title_lbl.pack(anchor="w", padx=16, pady=(16, 12))

        # Prompt Entry
        lbl_prompt = ctk.CTkLabel(left_panel, text="Prompt", font=FONTS["body_bold"], text_color=THEME_COLORS["text_main"])
        lbl_prompt.pack(anchor="w", padx=16, pady=(6, 2))
        
        self.prompt_text = ctk.CTkTextbox(
            left_panel,
            font=FONTS["body"],
            fg_color=THEME_COLORS["bg_window"],
            border_color=THEME_COLORS["border"],
            border_width=1,
            height=100,
            corner_radius=6
        )
        self.prompt_text.pack(fill="x", padx=16, pady=(0, 10))

        # Negative Prompt Entry
        lbl_neg_prompt = ctk.CTkLabel(left_panel, text="Negative Prompt (Optional)", font=FONTS["body_bold"], text_color=THEME_COLORS["text_main"])
        lbl_neg_prompt.pack(anchor="w", padx=16, pady=(6, 2))
        
        self.neg_prompt_text = ctk.CTkTextbox(
            left_panel,
            font=FONTS["body"],
            fg_color=THEME_COLORS["bg_window"],
            border_color=THEME_COLORS["border"],
            border_width=1,
            height=60,
            corner_radius=6
        )
        self.neg_prompt_text.pack(fill="x", padx=16, pady=(0, 12))

        # Model Selector
        lbl_model = ctk.CTkLabel(left_panel, text="Model", font=FONTS["body_bold"], text_color=THEME_COLORS["text_main"])
        lbl_model.pack(anchor="w", padx=16, pady=(6, 2))
        self.model_var = ctk.StringVar(value="Pollinations (Free)")
        self.model_sel = ctk.CTkOptionMenu(
            left_panel,
            values=["Pollinations (Free)", "Grok 2 (xAI Key)"],
            variable=self.model_var,
            font=FONTS["body"],
            fg_color=THEME_COLORS["bg_window"],
            button_color=THEME_COLORS["border"],
            button_hover_color=THEME_COLORS["bg_hover"],
            dropdown_fg_color=THEME_COLORS["bg_card"],
            dropdown_hover_color=THEME_COLORS["bg_hover"],
            height=36
        )
        self.model_sel.pack(fill="x", padx=16, pady=(0, 10))

        # Image Size Selector
        lbl_size = ctk.CTkLabel(left_panel, text="Image Size", font=FONTS["body_bold"], text_color=THEME_COLORS["text_main"])
        lbl_size.pack(anchor="w", padx=16, pady=(6, 2))
        self.size_var = ctk.StringVar(value=self.settings.get("ai_image_size"))
        self.size_sel = ctk.CTkOptionMenu(
            left_panel,
            values=["512x512", "768x768", "1024x1024", "1024x768", "768x1024"],
            variable=self.size_var,
            font=FONTS["body"],
            fg_color=THEME_COLORS["bg_window"],
            button_color=THEME_COLORS["border"],
            button_hover_color=THEME_COLORS["bg_hover"],
            dropdown_fg_color=THEME_COLORS["bg_card"],
            dropdown_hover_color=THEME_COLORS["bg_hover"],
            height=36
        )
        self.size_sel.pack(fill="x", padx=16, pady=(0, 10))

        # Number of Images Selector
        lbl_num = ctk.CTkLabel(left_panel, text="Number of Images", font=FONTS["body_bold"], text_color=THEME_COLORS["text_main"])
        lbl_num.pack(anchor="w", padx=16, pady=(6, 2))
        self.num_var = ctk.StringVar(value=str(self.settings.get("ai_num_images")))
        self.num_sel = ctk.CTkOptionMenu(
            left_panel,
            values=["1", "2", "3", "4"],
            variable=self.num_var,
            font=FONTS["body"],
            fg_color=THEME_COLORS["bg_window"],
            button_color=THEME_COLORS["border"],
            button_hover_color=THEME_COLORS["bg_hover"],
            dropdown_fg_color=THEME_COLORS["bg_card"],
            dropdown_hover_color=THEME_COLORS["bg_hover"],
            height=36
        )
        self.num_sel.pack(fill="x", padx=16, pady=(0, 15))

        # Actions Buttons Row
        btn_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
        btn_frame.pack(fill="x", padx=16, pady=10)
        btn_frame.grid_columnconfigure((0, 1), weight=1, uniform="equal")

        self.clear_btn = ctk.CTkButton(
            btn_frame,
            text="Clear",
            font=FONTS["body_bold"],
            fg_color=THEME_COLORS["bg_card"],
            border_color=THEME_COLORS["border"],
            border_width=1,
            text_color=THEME_COLORS["text_main"],
            hover_color=THEME_COLORS["bg_hover"],
            command=self._clear_inputs,
            height=36
        )
        self.clear_btn.grid(row=0, column=0, padx=(0, 4), sticky="ew")

        self.gen_btn = ctk.CTkButton(
            btn_frame,
            text="Generate",
            font=FONTS["body_bold"],
            fg_color="#6366F1",
            hover_color="#4F46E5",
            command=self._start_generation,
            height=36
        )
        self.gen_btn.grid(row=0, column=1, padx=(4, 0), sticky="ew")

        # Loading / Status Panel
        self.status_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
        self.status_lbl = ctk.CTkLabel(self.status_frame, text="", font=FONTS["caption"], text_color=THEME_COLORS["text_muted"])
        self.status_lbl.pack(pady=4)
        self.progress_bar = ctk.CTkProgressBar(self.status_frame, progress_color="#6366F1", height=4)
        self.progress_bar.pack(fill="x")
        self.progress_bar.set(0)

        # Right Panel (Preview Area)
        self.right_panel = ctk.CTkFrame(
            self,
            fg_color=THEME_COLORS["bg_card"],
            border_color=THEME_COLORS["border"],
            border_width=1,
            corner_radius=12
        )
        self.right_panel.grid(row=0, column=1, padx=(10, 0), pady=0, sticky="nsew")
        self.right_panel.grid_rowconfigure(0, weight=0)  # Toolbar
        self.right_panel.grid_rowconfigure(1, weight=1)  # Zoomable Canvas
        self.right_panel.grid_rowconfigure(2, weight=0)  # Thumbnail Carousel / Info
        self.right_panel.grid_columnconfigure(0, weight=1)

        # Toolbar
        self.toolbar = ctk.CTkFrame(self.right_panel, fg_color="transparent", height=44)
        self.toolbar.grid(row=0, column=0, padx=10, pady=5, sticky="ew")

        # Left tools (Navigation / Zoom / Fit)
        self.fit_btn = ctk.CTkButton(self.toolbar, text="Fit Window", width=90, font=FONTS["caption_bold"], fg_color=THEME_COLORS["bg_window"], border_color=THEME_COLORS["border"], border_width=1, text_color=THEME_COLORS["text_main"], hover_color=THEME_COLORS["bg_hover"], command=self._fit_image)
        self.fit_btn.pack(side="left", padx=4)

        self.actual_btn = ctk.CTkButton(self.toolbar, text="100%", width=60, font=FONTS["caption_bold"], fg_color=THEME_COLORS["bg_window"], border_color=THEME_COLORS["border"], border_width=1, text_color=THEME_COLORS["text_main"], hover_color=THEME_COLORS["bg_hover"], command=self._actual_size)
        self.actual_btn.pack(side="left", padx=4)

        # Right tools (Copy / Save / Folder / Delete)
        self.delete_btn = ctk.CTkButton(self.toolbar, text="🗑️", width=40, font=FONTS["caption"], fg_color="#EF4444", hover_color="#DC2626", command=self._delete_active_image)
        self.delete_btn.pack(side="right", padx=4)

        self.save_as_btn = ctk.CTkButton(self.toolbar, text="💾 Save As...", width=90, font=FONTS["caption_bold"], fg_color=THEME_COLORS["primary"], hover_color=THEME_COLORS["primary_hover"], command=self._save_active_image_as)
        self.save_as_btn.pack(side="right", padx=4)

        self.copy_btn = ctk.CTkButton(self.toolbar, text="📋 Copy", width=70, font=FONTS["caption_bold"], fg_color=THEME_COLORS["bg_window"], border_color=THEME_COLORS["border"], border_width=1, text_color=THEME_COLORS["text_main"], hover_color=THEME_COLORS["bg_hover"], command=self._copy_active_image)
        self.copy_btn.pack(side="right", padx=4)

        self.copy_prompt_btn = ctk.CTkButton(self.toolbar, text="📄 Prompt", width=75, font=FONTS["caption_bold"], fg_color=THEME_COLORS["bg_window"], border_color=THEME_COLORS["border"], border_width=1, text_color=THEME_COLORS["text_main"], hover_color=THEME_COLORS["bg_hover"], command=self._copy_prompt_text)
        self.copy_prompt_btn.pack(side="right", padx=4)

        self.folder_btn = ctk.CTkButton(self.toolbar, text="📁 Folder", width=75, font=FONTS["caption_bold"], fg_color=THEME_COLORS["bg_window"], border_color=THEME_COLORS["border"], border_width=1, text_color=THEME_COLORS["text_main"], hover_color=THEME_COLORS["bg_hover"], command=self._open_output_folder)
        self.folder_btn.pack(side="right", padx=4)

        # Zoomable Canvas Preview
        self.canvas = ZoomableCanvas(self.right_panel)
        self.canvas.grid(row=1, column=0, padx=16, pady=(5, 10), sticky="nsew")

        # Bottom Carousel Container
        self.carousel_frame = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        self.carousel_frame.grid(row=2, column=0, padx=16, pady=(0, 16), sticky="ew")

        # Initial view
        self._update_toolbar_states()

    def _clear_inputs(self):
        self.prompt_text.delete("1.0", "end")
        self.neg_prompt_text.delete("1.0", "end")

    def _update_toolbar_states(self):
        has_active = len(self.generated_files) > 0
        state = "normal" if has_active else "disabled"
        
        self.fit_btn.configure(state=state)
        self.actual_btn.configure(state=state)
        self.copy_btn.configure(state=state)
        self.save_as_btn.configure(state=state)
        self.delete_btn.configure(state=state)
        self.copy_prompt_btn.configure(state=state)

    def _fit_image(self):
        self.canvas.fit_to_window()

    def _actual_size(self):
        self.canvas.set_actual_size()

    def _copy_prompt_text(self):
        prompt = self.prompt_text.get("1.0", "end").strip()
        if prompt:
            self.clipboard_clear()
            self.clipboard_append(prompt)
            self.show_toast("Prompt copied to clipboard!", type="success")

    def _open_output_folder(self):
        out_dir = self.settings.get("ai_output_folder")
        if not out_dir or not os.path.exists(out_dir):
            out_dir = os.path.abspath(os.path.join("output", "generated"))
            os.makedirs(out_dir, exist_ok=True)
            
        import platform
        import subprocess
        try:
            if platform.system() == "Windows":
                os.startfile(out_dir)
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", out_dir])
            else:
                subprocess.Popen(["xdg-open", out_dir])
        except Exception as e:
            self.show_toast(f"Failed to open folder: {e}", type="error")

    def _copy_active_image(self):
        if not self.generated_files:
            return
        active_path = self.generated_files[self.active_file_idx]
        
        # Call ctypes clipboard copier
        success = self._copy_image_to_clipboard_win(active_path)
        if success:
            self.show_toast("Image copied to clipboard!", type="success")
        else:
            self.show_toast("Copy failed.", type="error")

    def _copy_image_to_clipboard_win(self, image_path: str) -> bool:
        try:
            image = Image.open(image_path)
            output = io.BytesIO()
            image.convert("RGB").save(output, "BMP")
            data = output.getvalue()[14:]  # Strip BMP header
            output.close()
            
            if ctypes.windll.user32.OpenClipboard(None):
                ctypes.windll.user32.EmptyClipboard()
                h_mem = ctypes.windll.kernel32.GlobalAlloc(2, len(data))
                p_mem = ctypes.windll.kernel32.GlobalLock(h_mem)
                ctypes.memmove(p_mem, data, len(data))
                ctypes.windll.kernel32.GlobalUnlock(h_mem)
                ctypes.windll.user32.SetClipboardData(8, h_mem)  # CF_DIB = 8
                ctypes.windll.user32.CloseClipboard()
                return True
        except Exception as e:
            self.logger.error(f"Copy image error: {e}")
        return False

    def _save_active_image_as(self):
        if not self.generated_files:
            return
        active_path = self.generated_files[self.active_file_idx]
        
        save_path = filedialog.asksaveasfilename(
            title="Save Image As",
            initialfile=os.path.basename(active_path),
            filetypes=[("PNG Image", "*.png"), ("All Files", "*.*")],
            defaultextension=".png"
        )
        
        if save_path:
            try:
                import shutil
                shutil.copy2(active_path, save_path)
                self.show_toast("Image saved successfully!", type="success")
            except Exception as e:
                self.show_toast(f"Save failed: {e}", type="error")

    def _delete_active_image(self):
        if not self.generated_files:
            return
        
        if messagebox.askyesno("Delete Image", "Are you sure you want to delete this generated image?"):
            active_path = self.generated_files[self.active_file_idx]
            try:
                # Remove file from disk
                if os.path.exists(active_path):
                    os.remove(active_path)
                
                # Remove from local list
                self.generated_files.pop(self.active_file_idx)
                
                # Update indices and preview
                if not self.generated_files:
                    self.active_file_idx = 0
                    self.canvas.set_image(None)
                else:
                    self.active_file_idx = max(0, self.active_file_idx - 1)
                    self.canvas.set_image(self.generated_files[self.active_file_idx])
                
                self._update_carousel()
                self._update_toolbar_states()
                self.show_toast("Image deleted.", type="info")
            except Exception as e:
                self.show_toast(f"Delete failed: {e}", type="error")

    def _start_generation(self):
        if self.is_generating:
            return
            
        model_name = self.model_var.get()
        api_key = self.settings.get("ai_api_key")
        if model_name != "Pollinations (Free)" and not api_key:
            self.show_toast("API Key missing! Please set it in Settings.", type="error")
            return
            
        prompt = self.prompt_text.get("1.0", "end").strip()
        if not prompt:
            self.show_toast("Prompt cannot be empty.", type="error")
            return

        try:
            neg_prompt = self.neg_prompt_text.get("1.0", "end").strip()
            size = self.size_var.get()
            num_images = int(self.num_var.get() or 1)
            quality = self.settings.get("ai_quality") or "Standard"
        except Exception as e:
            self.show_toast(f"Invalid input parameters: {e}", type="error")
            return

        # Start loading state
        self.is_generating = True
        self.gen_btn.configure(state="disabled")
        self.clear_btn.configure(state="disabled")
        self.status_frame.pack(fill="x", padx=16, pady=8)
        self.status_lbl.configure(text=f"Connecting to {model_name}...")
        self.progress_bar.set(0.1)

        # Run background thread
        thread = threading.Thread(
            target=self._generation_thread,
            args=(model_name, prompt, neg_prompt, size, num_images, quality, api_key),
            daemon=True
        )
        thread.start()

    def _generation_thread(self, model_name, prompt, neg_prompt, size, num_images, quality, api_key):
        try:
            # Generate URL list from provider
            self.logger.info(f"AI Generation started. Model: {model_name}, Prompt: {prompt}")
            
            if model_name == "Pollinations (Free)":
                provider = PollinationsProvider()
            else:
                provider = GrokProvider()

            image_urls = provider.generate_image(prompt, neg_prompt, size, num_images, quality, api_key)
            
            # Setup output folder structure: output/generated/YYYY-MM-DD/
            out_base = self.settings.get("ai_output_folder")
            if not out_base:
                out_base = os.path.join("output", "generated")
            
            today_str = datetime.now().strftime("%Y-%m-%d")
            out_dir = os.path.join(out_base, today_str)
            os.makedirs(out_dir, exist_ok=True)

            self.after(0, lambda: self.status_lbl.configure(text=f"Downloading {len(image_urls)} generated image(s)..."))
            self.after(0, lambda: self.progress_bar.set(0.6))
            
            downloaded_paths = []
            for i, url in enumerate(image_urls):
                # Count current files to format filename: image001.png, image002.png...
                existing_count = len([f for f in os.listdir(out_dir) if f.startswith("image") and f.endswith(".png")])
                filename = f"image{existing_count + 1:03d}.png"
                save_path = os.path.join(out_dir, filename)

                if url.startswith("data:image/png;base64,"):
                    # Decode base64 data
                    import base64
                    b64_data = url.split(",")[1]
                    with open(save_path, "wb") as f:
                        f.write(base64.b64decode(b64_data))
                else:
                    # Download URL
                    urllib.request.urlretrieve(url, save_path)
                
                downloaded_paths.append(save_path)
                
                # Add history entry
                if self.settings.get("ai_save_history"):
                    self.history_service.add_entry(
                        prompt=prompt,
                        negative_prompt=neg_prompt,
                        provider="Grok",
                        size=size,
                        image_path=save_path
                    )
            
            # Update UI on main thread
            self.after(0, lambda: self._on_generation_success(downloaded_paths))
            
        except Exception as e:
            err_str = str(e)
            self.logger.error(f"AI Generation failed: {err_str}")
            self.after(0, lambda: self._on_generation_failure(err_str))

    def _on_generation_success(self, file_paths):
        self.is_generating = False
        self.gen_btn.configure(state="normal")
        self.clear_btn.configure(state="normal")
        self.status_frame.pack_forget()
        
        self.generated_files = file_paths
        self.active_file_idx = 0
        
        # Display first image
        if self.generated_files:
            self.canvas.set_image(self.generated_files[0])
            
        self._update_carousel()
        self._update_toolbar_states()
        self.show_toast("Generation completed!", type="success")

    def _on_generation_failure(self, err_msg):
        self.is_generating = False
        self.gen_btn.configure(state="normal")
        self.clear_btn.configure(state="normal")
        self.status_frame.pack_forget()
        self.update_idletasks()  # Force UI refresh to hide loading state immediately
        
        messagebox.showerror("Generation Error", f"Failed to generate image:\n{err_msg}", parent=self)
        self.show_toast("Generation failed.", type="error")

    def load_from_history(self, prompt, negative_prompt, image_path):
        """Used to display historical generation items directly in the generator view."""
        self.prompt_text.delete("1.0", "end")
        self.prompt_text.insert("1.0", prompt)
        
        self.neg_prompt_text.delete("1.0", "end")
        self.neg_prompt_text.insert("1.0", negative_prompt)
        
        self.generated_files = [image_path]
        self.active_file_idx = 0
        self.canvas.set_image(image_path)
        
        self._update_carousel()
        self._update_toolbar_states()

    def _update_carousel(self):
        for widget in self.carousel_frame.winfo_children():
            widget.destroy()
            
        if not self.generated_files:
            return
            
        # Draw thumbnails for files
        lbl = ctk.CTkLabel(self.carousel_frame, text="Select Image:", font=FONTS["caption_bold"], text_color=THEME_COLORS["text_muted"])
        lbl.pack(side="left", padx=(0, 10))
        
        for idx, path in enumerate(self.generated_files):
            # Show number button for selection
            is_active = idx == self.active_file_idx
            btn = ctk.CTkButton(
                self.carousel_frame,
                text=str(idx + 1),
                width=32,
                height=32,
                font=FONTS["caption_bold"],
                fg_color=THEME_COLORS["primary"] if is_active else THEME_COLORS["bg_window"],
                text_color=THEME_COLORS["text_main"] if is_active else THEME_COLORS["text_muted"],
                border_color=THEME_COLORS["border"],
                border_width=1 if not is_active else 0,
                command=lambda i=idx: self._set_active_carousel_image(i)
            )
            btn.pack(side="left", padx=4)

    def _set_active_carousel_image(self, idx):
        self.active_file_idx = idx
        self.canvas.set_image(self.generated_files[idx])
        self._update_carousel()
