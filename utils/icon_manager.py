import os
import customtkinter as ctk
from PIL import Image, ImageDraw, ImageFont

class IconManager:
    _cache = {}
    _font_path = None

    @classmethod
    def initialize(cls):
        """Initialize the font path."""
        if cls._font_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            cls._font_path = os.path.join(base_dir, "assets", "fonts", "fa-solid-900.ttf")
            if not os.path.exists(cls._font_path):
                print(f"[Warning] FontAwesome not found at {cls._font_path}")

    @classmethod
    def get_icon(cls, unicode_char: str, color: str = "#ffffff", size: int = 20) -> ctk.CTkImage:
        """
        Generate a CTkImage from a FontAwesome unicode character.
        Caches the image to prevent memory leaks and improve performance.
        """
        if cls._font_path is None:
            cls.initialize()

        cache_key = f"{unicode_char}_{color}_{size}"
        if cache_key in cls._cache:
            return cls._cache[cache_key]

        try:
            # We render the font at a slightly larger size for better anti-aliasing
            render_size = size * 2
            font = ImageFont.truetype(cls._font_path, render_size)
            
            # Determine the bounding box of the glyph
            left, top, right, bottom = font.getbbox(unicode_char)
            width = right - left
            height = bottom - top

            # Create a square image to fit the icon (padding handled naturally)
            img_size = max(width, height)
            
            # Create a transparent image
            img = Image.new("RGBA", (img_size, img_size), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            
            # Draw text centered
            x = (img_size - width) / 2 - left
            y = (img_size - height) / 2 - top
            draw.text((x, y), unicode_char, font=font, fill=color)

            # Resize down to the target size for smooth edges (Anti-alias)
            img = img.resize((size, size), Image.Resampling.LANCZOS)

            # Create CTkImage
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(size, size))
            cls._cache[cache_key] = ctk_img
            return ctk_img

        except Exception as e:
            print(f"[IconManager] Error rendering icon {unicode_char}: {e}")
            # Return empty transparent image on failure
            empty_img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
            return ctk.CTkImage(light_image=empty_img, dark_image=empty_img, size=(size, size))
