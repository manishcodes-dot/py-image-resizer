import os
import customtkinter as ctk
from PIL import Image, ImageTk
from tkinter import messagebox
from components.theme import THEME_COLORS, FONTS

class HistoryFrame(ctk.CTkFrame):
    def __init__(self, master, history_service, on_load_to_generator_callback, show_toast_callback, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.history_service = history_service
        self.load_to_generator = on_load_to_generator_callback
        self.show_toast = show_toast_callback
        self._thumbnails = {}  # Keeps image references alive

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)  # Title/Action bar
        self.grid_rowconfigure(1, weight=1)  # Scrollable List

        self._build_header()
        self._build_list()

    def _build_header(self):
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        header_frame.grid_columnconfigure(0, weight=1)

        lbl = ctk.CTkLabel(
            header_frame,
            text="Generation History",
            font=("Outfit", 24, "bold"),
            text_color=THEME_COLORS["text_main"]
        )
        lbl.grid(row=0, column=0, sticky="w")

        self.clear_all_btn = ctk.CTkButton(
            header_frame,
            text="Clear All History",
            font=FONTS["body_bold"],
            fg_color="#EF4444",
            hover_color="#DC2626",
            command=self._clear_all_history
        )
        self.clear_all_btn.grid(row=0, column=1, sticky="e")

    def _build_list(self):
        self.scroll_list = ctk.CTkScrollableFrame(
            self,
            fg_color=THEME_COLORS["bg_card"],
            border_color=THEME_COLORS["border"],
            border_width=1,
            corner_radius=12
        )
        self.scroll_list.grid(row=1, column=0, padx=20, pady=(10, 20), sticky="nsew")
        self.scroll_list.grid_columnconfigure(0, weight=1)
        
        self.refresh_history()

    def refresh_history(self):
        # Clear list
        for widget in self.scroll_list.winfo_children():
            widget.destroy()
        self._thumbnails.clear()

        history_items = self.history_service.history
        if not history_items:
            empty_lbl = ctk.CTkLabel(
                self.scroll_list,
                text="No generation history found. Start creating images in the Generator tab!",
                font=FONTS["body"],
                text_color=THEME_COLORS["text_muted"]
            )
            empty_lbl.pack(pady=40)
            self.clear_all_btn.configure(state="disabled")
            return
            
        self.clear_all_btn.configure(state="normal")

        for idx, entry in enumerate(history_items):
            # Create a card for each item
            card = ctk.CTkFrame(
                self.scroll_list,
                fg_color=THEME_COLORS["bg_window"],
                border_color=THEME_COLORS["border"],
                border_width=1,
                corner_radius=8
            )
            card.pack(fill="x", padx=10, pady=6)
            card.grid_columnconfigure(0, weight=0)  # Thumbnail
            card.grid_columnconfigure(1, weight=1)  # Meta/Prompt details
            card.grid_columnconfigure(2, weight=0)  # Actions

            # Load thumbnail image
            img_path = entry.get("image_path")
            thumbnail_loaded = False
            
            if img_path and os.path.exists(img_path):
                try:
                    # Open and scale down to 80x80 thumbnail
                    img = Image.open(img_path)
                    img.thumbnail((80, 80))
                    tk_img = ImageTk.PhotoImage(img)
                    
                    # Store reference to prevent garbage collection
                    self._thumbnails[entry["id"]] = tk_img
                    
                    lbl_thumb = ctk.CTkLabel(card, image=tk_img, text="")
                    lbl_thumb.grid(row=0, column=0, padx=12, pady=12)
                    thumbnail_loaded = True
                except Exception as e:
                    print(f"Error loading thumbnail for history entry {entry['id']}: {e}")
            
            if not thumbnail_loaded:
                # Placeholder box
                lbl_thumb = ctk.CTkLabel(
                    card,
                    text="No Image",
                    font=FONTS["caption_bold"],
                    width=80,
                    height=80,
                    fg_color=THEME_COLORS["bg_card"],
                    text_color=THEME_COLORS["text_muted"],
                    corner_radius=4
                )
                lbl_thumb.grid(row=0, column=0, padx=12, pady=12)

            # Details
            details_frame = ctk.CTkFrame(card, fg_color="transparent")
            details_frame.grid(row=0, column=1, pady=12, sticky="nsew")
            
            # Row 1: Date | Size | Provider
            meta_str = f"{entry.get('date')}  •  {entry.get('size')}  •  {entry.get('provider')}"
            lbl_meta = ctk.CTkLabel(
                details_frame,
                text=meta_str,
                font=FONTS["caption_bold"],
                text_color=THEME_COLORS["primary"][1]
            )
            lbl_meta.pack(anchor="w")

            # Row 2: Prompt
            lbl_prompt = ctk.CTkLabel(
                details_frame,
                text=entry.get("prompt"),
                font=FONTS["body_bold"],
                text_color=THEME_COLORS["text_main"],
                justify="left",
                wraplength=380
            )
            lbl_prompt.pack(anchor="w", pady=(4, 0))

            if entry.get("negative_prompt"):
                lbl_neg = ctk.CTkLabel(
                    details_frame,
                    text=f"Avoid: {entry.get('negative_prompt')}",
                    font=FONTS["caption"],
                    text_color=THEME_COLORS["text_muted"],
                    justify="left",
                    wraplength=380
                )
                lbl_neg.pack(anchor="w", pady=(2, 0))

            # Actions
            actions_frame = ctk.CTkFrame(card, fg_color="transparent")
            actions_frame.grid(row=0, column=2, padx=12, pady=12, sticky="e")
            
            # Open Image button
            btn_open = ctk.CTkButton(
                actions_frame,
                text="View",
                width=65,
                height=28,
                font=FONTS["caption_bold"],
                fg_color=THEME_COLORS["bg_card"],
                border_color=THEME_COLORS["border"],
                border_width=1,
                text_color=THEME_COLORS["text_main"],
                hover_color=THEME_COLORS["bg_hover"],
                command=lambda p=img_path: self._open_image(p)
            )
            btn_open.pack(side="left", padx=4)

            # Regenerate button
            btn_regen = ctk.CTkButton(
                actions_frame,
                text="Regen",
                width=65,
                height=28,
                font=FONTS["caption_bold"],
                fg_color="#6366F1",
                hover_color="#4F46E5",
                command=lambda e=entry: self.load_to_generator(e)
            )
            btn_regen.pack(side="left", padx=4)

            # Delete button
            btn_del = ctk.CTkButton(
                actions_frame,
                text="🗑️",
                width=28,
                height=28,
                font=FONTS["caption"],
                fg_color="#EF4444",
                hover_color="#DC2626",
                command=lambda eid=entry["id"]: self._delete_entry(eid)
            )
            btn_del.pack(side="left", padx=4)

    def _open_image(self, path):
        if not path or not os.path.exists(path):
            self.show_toast("Image file does not exist on disk.", type="error")
            return
        try:
            os.startfile(path)
        except Exception as e:
            self.show_toast(f"Failed to open image: {e}", type="error")

    def _delete_entry(self, entry_id):
        if messagebox.askyesno("Delete Entry", "Remove this generation from history? (This will not delete the file on disk)"):
            if self.history_service.delete_entry(entry_id):
                self.refresh_history()
                self.show_toast("History entry removed.", type="info")

    def _clear_all_history(self):
        if messagebox.askyesno("Clear All History", "Are you sure you want to clear all generation history?"):
            self.history_service.clear_all()
            self.refresh_history()
            self.show_toast("All history cleared.", type="success")
