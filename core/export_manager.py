"""Export manager — save images in various formats and presets."""

import os
from typing import Optional, Tuple, Dict, Any

from PIL import Image

from utils.logger import setup_logger

logger = setup_logger(__name__)


# Export presets
EXPORT_PRESETS: Dict[str, Dict[str, Any]] = {
    "web": {
        "label": "Web (72 DPI, optimized)",
        "max_width": 1920,
        "max_height": 1080,
        "dpi": (72, 72),
        "quality": 85,
        "format": "png",
        "optimize": True,
    },
    "print": {
        "label": "Print (300 DPI, max quality)",
        "max_width": 4096,
        "max_height": 4096,
        "dpi": (300, 300),
        "quality": 100,
        "format": "png",
        "optimize": False,
    },
    "social": {
        "label": "Social Media (1080x1080, JPEG)",
        "max_width": 1080,
        "max_height": 1080,
        "dpi": (72, 72),
        "quality": 90,
        "format": "jpeg",
        "optimize": True,
    },
    "thumbnail": {
        "label": "Thumbnail (256x256)",
        "max_width": 256,
        "max_height": 256,
        "dpi": (72, 72),
        "quality": 80,
        "format": "jpeg",
        "optimize": True,
    },
    "original": {
        "label": "Original (unchanged)",
        "max_width": None,
        "max_height": None,
        "dpi": None,
        "quality": 100,
        "format": "png",
        "optimize": True,
    },
}


class ExportManager:
    """Image export manager.

    Handles saving images in various formats (PNG, JPEG, WEBP, BMP)
    and presets (Web, Print, Social Media).

    Attributes:
        default_bg_color: Default background color for JPEG exports.
    """

    def __init__(self, default_bg_color: Tuple[int, int, int] = (255, 255, 255)) -> None:
        self.default_bg_color = default_bg_color

    @staticmethod
    def get_presets() -> Dict[str, Dict[str, Any]]:
        """Return a copy of the available export presets."""
        return EXPORT_PRESETS.copy()

    def save(
        self,
        image: Image.Image,
        save_path: str,
        file_format: str = "png",
        quality: int = 90,
        bg_color: Optional[Tuple[int, int, int]] = None,
        optimize: bool = True,
        dpi: Optional[Tuple[int, int]] = None,
    ) -> bool:
        """Save an image with the given settings.

        Args:
            image: The image to save.
            save_path: File path to save to.
            file_format: Format ('png', 'jpeg', 'webp', 'bmp').
            quality: Quality (1-100, JPEG/WEBP only).
            bg_color: Background color for JPEG (for RGBA images).
            optimize: Whether to apply optimization.
            dpi: DPI value.

        Returns:
            True if the save was successful.
        """
        try:
            fmt = file_format.upper()
            if fmt == "JPG":
                fmt = "JPEG"

            save_image = image.copy()

            # Convert RGBA to RGB for JPEG
            if fmt == "JPEG" and save_image.mode in ("RGBA", "LA", "PA"):
                bg = Image.new("RGB", save_image.size, bg_color or self.default_bg_color)
                if save_image.mode == "RGBA":
                    bg.paste(save_image, mask=save_image.split()[3])
                elif save_image.mode == "LA":
                    bg.paste(save_image, mask=save_image.split()[1])
                else:
                    bg.paste(save_image)
                save_image = bg

            # BMP also requires RGB
            if fmt == "BMP" and save_image.mode in ("RGBA", "LA", "PA"):
                bg = Image.new("RGB", save_image.size, bg_color or self.default_bg_color)
                if save_image.mode == "RGBA":
                    bg.paste(save_image, mask=save_image.split()[3])
                else:
                    bg.paste(save_image)
                save_image = bg

            # Create the output directory if needed
            os.makedirs(os.path.dirname(save_path) or ".", exist_ok=True)

            # Build the save arguments
            save_kwargs: Dict[str, Any] = {"format": fmt}

            if fmt in ("JPEG", "WEBP"):
                save_kwargs["quality"] = max(1, min(quality, 100))
            if optimize and fmt in ("PNG", "JPEG"):
                save_kwargs["optimize"] = True
            if dpi:
                save_kwargs["dpi"] = dpi

            save_image.save(save_path, **save_kwargs)
            logger.info("Image saved: %s (format=%s, quality=%d)", save_path, fmt, quality)
            return True

        except Exception as e:
            logger.error("Error saving image: %s — %s", save_path, e)
            return False

    def save_with_preset(
        self,
        image: Image.Image,
        save_path: str,
        preset_name: str = "web",
        bg_color: Optional[Tuple[int, int, int]] = None,
    ) -> bool:
        """Save an image using a preset.

        Args:
            image: The image to save.
            save_path: File path to save to.
            preset_name: Preset name ('web', 'print', 'social', 'thumbnail', 'original').
            bg_color: Background color for JPEG.

        Returns:
            True if the save was successful.
        """
        preset = EXPORT_PRESETS.get(preset_name)
        if not preset:
            logger.error("Unknown preset: %s", preset_name)
            return False

        img = image.copy()

        # Resize according to preset limits
        max_w = preset.get("max_width")
        max_h = preset.get("max_height")
        if max_w and max_h:
            img.thumbnail((max_w, max_h), Image.LANCZOS)

        # Adjust file extension to match format
        fmt = preset.get("format", "png")
        if not save_path.lower().endswith(f".{fmt}"):
            base = os.path.splitext(save_path)[0]
            save_path = f"{base}.{fmt}"

        return self.save(
            image=img,
            save_path=save_path,
            file_format=fmt,
            quality=preset.get("quality", 90),
            bg_color=bg_color,
            optimize=preset.get("optimize", True),
            dpi=preset.get("dpi"),
        )

    @staticmethod
    def generate_output_filename(
        input_path: str,
        suffix: str = "_nobg",
        file_format: str = "png",
    ) -> str:
        """Generate an output filename based on the input file.

        Args:
            input_path: Input file path.
            suffix: Suffix to append.
            file_format: Output format.

        Returns:
            Generated filename string.
        """
        base_name = os.path.splitext(os.path.basename(input_path))[0]
        return f"{base_name}{suffix}.{file_format.lower()}"
