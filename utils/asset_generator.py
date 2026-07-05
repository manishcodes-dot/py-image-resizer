import os
from PIL import Image, ImageDraw, ImageFilter

def generate_app_assets(assets_dir: str = "assets") -> None:
    """Generates default graphic assets for the application if they do not exist."""
    assets_path = os.path.abspath(assets_dir)
    os.makedirs(assets_path, exist_ok=True)
    
    logo_path = os.path.join(assets_path, "logo.png")
    # Always generate to apply theme changes
    _create_logo_image(logo_path)
        
    logo_ico_path = os.path.join(assets_path, "logo.ico")
    try:
        img = Image.open(logo_path)
        img.save(logo_ico_path, format="ICO", sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    except Exception as e:
        print(f"Error generating ICO asset: {e}")

def _create_logo_image(path: str) -> None:
    """Draws a premium 256x256 modern logo for the application."""
    # Create high-res canvas (256x256)
    size = 256
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw rounded rectangle background (Emerald-mint gradient approximation)
    # Base emerald: (16, 185, 129)
    draw.rounded_rectangle(
        [16, 16, size - 16, size - 16],
        radius=48,
        fill=(16, 185, 129, 255)
    )
    
    # Draw a subtle inner glow (Lighter mint glow)
    draw.rounded_rectangle(
        [24, 24, size - 24, size - 24],
        radius=40,
        outline=(110, 231, 183, 80),  # Mint glow, semi-transparent
        width=4
    )
    
    # Draw overlapping image layers
    # Card 1: PNG (representing source)
    draw.rounded_rectangle(
        [60, 60, 160, 160],
        radius=12,
        fill=(255, 255, 255, 240)
    )
    # Simulating image contents: blue mountain & sun in card 1
    # Mountain
    draw.polygon([(75, 140), (105, 95), (120, 120), (135, 105), (150, 140)], fill=(59, 130, 246, 255))
    # Sun
    draw.ellipse([125, 75, 145, 95], fill=(245, 158, 11, 255))
    
    # Card 2: WebP (representing target) offset and overlapping
    # Draw shadow for overlapping card
    shadow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    sh_draw = ImageDraw.Draw(shadow)
    sh_draw.rounded_rectangle(
        [110, 110, 210, 210],
        radius=12,
        fill=(0, 0, 0, 80)
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(8))
    img = Image.alpha_composite(img, shadow)
    
    draw = ImageDraw.Draw(img)
    # The actual WebP card
    draw.rounded_rectangle(
        [110, 110, 210, 210],
        radius=12,
        fill=(31, 41, 55, 255),  # Dark gray card
        outline=(16, 185, 129, 255),  # Emerald border
        width=3
    )
    
    # Draw transfer arrow from PNG card to WebP card
    # Arrow line
    draw.line([95, 80, 135, 120], fill=(255, 255, 255, 255), width=6)
    # Arrow head
    draw.polygon([(122, 120), (135, 120), (135, 107)], fill=(255, 255, 255, 255))
    
    # Inside the WebP card, draw "W" symbol using thick lines
    w_pts = [
        (135, 145),  # Top-left of W
        (147, 175),  # Bottom-left
        (160, 155),  # Mid peak
        (173, 175),  # Bottom-right
        (185, 145)   # Top-right
    ]
    draw.line(w_pts[:2], fill=(16, 185, 129, 255), width=5, joint="round")
    draw.line(w_pts[1:3], fill=(16, 185, 129, 255), width=5, joint="round")
    draw.line(w_pts[2:4], fill=(16, 185, 129, 255), width=5, joint="round")
    draw.line(w_pts[3:], fill=(16, 185, 129, 255), width=5, joint="round")
    
    img.save(path, "PNG")
