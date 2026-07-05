import os
import shutil
import io
from typing import Dict, Any, Tuple
from PIL import Image
from utils.file_helpers import calculate_new_dimensions, get_image_info

class ImageConverter:
    def __init__(self, settings_manager):
        self.settings = settings_manager

    def convert_image(self, filepath: str) -> Tuple[str, int, str]:
        """
        Converts a single image file to WebP based on configuration.
        Returns a tuple: (status, new_file_size, error_message)
        
        status can be: "Completed", "Skipped", "Failed"
        """
        if not os.path.exists(filepath):
            return "Failed", 0, "Source file does not exist"

        # Read configuration values
        quality = self.settings.get("quality")
        lossless = self.settings.get("lossless")
        preserve_metadata = self.settings.get("preserve_metadata")
        overwrite = self.settings.get("overwrite")
        delete_original = self.settings.get("delete_original")
        output_mode = self.settings.get("output_mode")
        custom_output_dir = self.settings.get("custom_output_dir")
        
        resize_mode = self.settings.get("resize_mode")
        custom_width = self.settings.get("custom_width")
        custom_height = self.settings.get("custom_height")
        maintain_aspect = self.settings.get("maintain_aspect")

        # Determine target output folder
        src_dir = os.path.dirname(filepath)
        filename = os.path.basename(filepath)
        name_without_ext, _ = os.path.splitext(filename)
        dest_filename = f"{name_without_ext}.webp"

        if output_mode == "custom" and custom_output_dir:
            dest_dir = os.path.abspath(custom_output_dir)
            os.makedirs(dest_dir, exist_ok=True)
        else:
            dest_dir = src_dir

        dest_path = os.path.join(dest_dir, dest_filename)

        # Check for overwrite/skip
        # If original and destination are in the same folder and have the same base name,
        # but original is .webp, (we filter webp out in scanning, so this is unlikely,
        # but we should prevent overwriting original files if they have different paths but same name)
        if os.path.exists(dest_path):
            # If we're not overwriting, skip the file
            if not overwrite:
                return "Skipped", 0, "File already exists in destination"

        temp_dest_path = dest_path + ".tmp"

        try:
            with Image.open(filepath) as img:
                orig_w, orig_h = img.size
                
                # Metadata extraction
                exif_data = None
                icc_profile = None
                if preserve_metadata:
                    try:
                        exif_data = img.info.get("exif")
                    except Exception:
                        pass
                    try:
                        icc_profile = img.info.get("icc_profile")
                    except Exception:
                        pass

                # Convert palette/transparency mode cleanly
                if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
                    img = img.convert("RGBA")
                else:
                    img = img.convert("RGB")

                # Resizing
                target_w, target_h = calculate_new_dimensions(
                    orig_w, orig_h, resize_mode, custom_width, custom_height, maintain_aspect
                )
                
                if (target_w, target_h) != (orig_w, orig_h):
                    img = img.resize((target_w, target_h), Image.Resampling.LANCZOS)

                # Save arguments
                save_args: Dict[str, Any] = {
                    "quality": quality,
                    "lossless": lossless
                }
                
                if preserve_metadata:
                    if exif_data is not None:
                        save_args["exif"] = exif_data
                    if icc_profile is not None:
                        save_args["icc_profile"] = icc_profile

                # Try saving to a buffer and lowering quality if it's over 100kb
                max_size_bytes = 100 * 1024
                
                if save_args.get("lossless"):
                    buffer = io.BytesIO()
                    img.save(buffer, "WEBP", **save_args)
                    if buffer.tell() > max_size_bytes:
                        # Fallback to lossy if it exceeds 100kb
                        save_args["lossless"] = False
                        if "quality" not in save_args or save_args["quality"] is None:
                            save_args["quality"] = 90
                    else:
                        with open(temp_dest_path, "wb") as f:
                            f.write(buffer.getvalue())
                
                if not save_args.get("lossless"):
                    current_quality = save_args.get("quality", 90)
                    while current_quality >= 5:
                        save_args["quality"] = current_quality
                        buffer = io.BytesIO()
                        img.save(buffer, "WEBP", **save_args)
                        if buffer.tell() <= max_size_bytes or current_quality == 5:
                            with open(temp_dest_path, "wb") as f:
                                f.write(buffer.getvalue())
                            break
                        current_quality -= 5

            # Move temp file to final destination
            if os.path.exists(dest_path):
                os.remove(dest_path)
            shutil.move(temp_dest_path, dest_path)

            new_size = os.path.getsize(dest_path)

            # Delete original if requested
            if delete_original:
                try:
                    # Double check we are not deleting the output file (in case they somehow match)
                    if os.path.abspath(filepath) != os.path.abspath(dest_path):
                        os.remove(filepath)
                except Exception as e:
                    # Log but don't fail conversion because the output was created successfully
                    return "Completed", new_size, f"Converted, but failed to delete original: {e}"

            return "Completed", new_size, ""

        except Exception as e:
            # Clean up temp file if exists
            if os.path.exists(temp_dest_path):
                try:
                    os.remove(temp_dest_path)
                except Exception:
                    pass
            return "Failed", 0, str(e)
