"""Image editing — crop, rotate, flip, filters, watermark, undo/redo."""

import time
from collections import deque
from typing import Optional, List, Tuple, Deque

from PIL import Image, ImageDraw, ImageFilter, ImageEnhance, ImageFont, ImageOps

from utils.logger import setup_logger

logger = setup_logger(__name__)

# Default limit for the undo/redo stack
DEFAULT_UNDO_LIMIT = 20


class HistoryEntry:
    """An entry in the undo/redo stack.

    Attributes:
        image: The image state at this point.
        action: The name of the action performed.
        timestamp: The time the action was performed.
    """

    __slots__ = ("image", "action", "timestamp")

    def __init__(self, image: Image.Image, action: str) -> None:
        self.image = image
        self.action = action
        self.timestamp = time.time()

    def __repr__(self) -> str:
        return f"HistoryEntry({self.action!r})"


class ImageEditor:
    """Non-destructive image editing system with Undo/Redo support.

    Performs various operations on images: crop, rotate, flip,
    brightness, contrast, saturation, blur, sharpen, grayscale,
    invert, auto-enhance, watermark.

    Undo and Redo are implemented via ``collections.deque``
    (O(1) operations, memory-limited).

    Attributes:
        image: The current image state.
        undo_limit: Maximum number of entries in the undo stack.
    """

    def __init__(self, image: Optional[Image.Image] = None, undo_limit: int = DEFAULT_UNDO_LIMIT) -> None:
        self._image: Optional[Image.Image] = image
        self._undo_stack: Deque[HistoryEntry] = deque(maxlen=undo_limit)
        self._redo_stack: Deque[HistoryEntry] = deque(maxlen=undo_limit)
        self.undo_limit: int = undo_limit
        self._history_log: List[str] = []

    @property
    def image(self) -> Optional[Image.Image]:
        """Return the current image."""
        return self._image

    @image.setter
    def image(self, new_image: Optional[Image.Image]) -> None:
        """Set a new image and clear undo/redo stacks."""
        self._image = new_image
        self._undo_stack.clear()
        self._redo_stack.clear()
        self._history_log.clear()

    @property
    def can_undo(self) -> bool:
        """Check whether an undo operation is possible."""
        return len(self._undo_stack) > 0

    @property
    def can_redo(self) -> bool:
        """Check whether a redo operation is possible."""
        return len(self._redo_stack) > 0

    @property
    def undo_count(self) -> int:
        """Return the number of entries in the undo stack."""
        return len(self._undo_stack)

    @property
    def redo_count(self) -> int:
        """Return the number of entries in the redo stack."""
        return len(self._redo_stack)

    @property
    def history(self) -> List[str]:
        """Return a copy of the action history list."""
        return self._history_log.copy()

    def _push_undo(self, action_name: str) -> None:
        """Save the current state to the undo stack and clear redo.

        Args:
            action_name: Name of the action being performed.
        """
        if self._image is not None:
            self._undo_stack.append(HistoryEntry(self._image.copy(), action_name))
            self._redo_stack.clear()  # New action invalidates redo
            self._history_log.append(action_name)

    def undo(self) -> bool:
        """Undo the last action.

        Returns:
            True if the undo was successful, False otherwise.
        """
        if not self._undo_stack:
            logger.info("Undo stack is empty — nothing to undo.")
            return False

        # Push current state onto redo
        if self._image is not None:
            action = self._undo_stack[-1].action if self._undo_stack else "unknown"
            self._redo_stack.append(HistoryEntry(self._image.copy(), action))

        entry = self._undo_stack.pop()
        self._image = entry.image
        if self._history_log:
            self._history_log.pop()
        logger.info("Undo: '%s'. stack=%d, redo=%d", entry.action, len(self._undo_stack), len(self._redo_stack))
        return True

    def redo(self) -> bool:
        """Redo the last undone action.

        Returns:
            True if the redo was successful, False otherwise.
        """
        if not self._redo_stack:
            logger.info("Redo stack is empty — nothing to redo.")
            return False

        # Push current state onto undo
        if self._image is not None:
            entry_name = self._redo_stack[-1].action
            self._undo_stack.append(HistoryEntry(self._image.copy(), entry_name))

        entry = self._redo_stack.pop()
        self._image = entry.image
        self._history_log.append(entry.action)
        logger.info("Redo: '%s'. stack=%d, redo=%d", entry.action, len(self._undo_stack), len(self._redo_stack))
        return True

    # ==================== TRANSFORMATIONS ====================

    def rotate(self, angle: float, expand: bool = True) -> bool:
        """Rotate the image by a given angle.

        Args:
            angle: Rotation angle in degrees.
            expand: Whether to expand the canvas to fit the rotated image.

        Returns:
            True if successful.
        """
        if self._image is None:
            return False

        self._push_undo(f"Rotate {angle}°")
        self._image = self._image.rotate(angle, expand=expand, resample=Image.BICUBIC)
        logger.info("Image rotated by %s°.", angle)
        return True

    def flip_horizontal(self) -> bool:
        """Flip the image horizontally."""
        if self._image is None:
            return False

        self._push_undo("Flip Horizontal")
        self._image = self._image.transpose(Image.FLIP_LEFT_RIGHT)
        logger.info("Image flipped horizontally.")
        return True

    def flip_vertical(self) -> bool:
        """Flip the image vertically."""
        if self._image is None:
            return False

        self._push_undo("Flip Vertical")
        self._image = self._image.transpose(Image.FLIP_TOP_BOTTOM)
        logger.info("Image flipped vertically.")
        return True

    def crop(self, left: int, top: int, right: int, bottom: int) -> bool:
        """Crop the image.

        Args:
            left: Left boundary (pixels).
            top: Top boundary (pixels).
            right: Right boundary (pixels).
            bottom: Bottom boundary (pixels).

        Returns:
            True if successful.
        """
        if self._image is None:
            return False

        # Swap coordinates if reversed
        if left > right:
            left, right = right, left
        if top > bottom:
            top, bottom = bottom, top

        # Clamp coordinates to image bounds
        left = max(0, min(left, self._image.width))
        top = max(0, min(top, self._image.height))
        right = max(left + 1, min(right, self._image.width))
        bottom = max(top + 1, min(bottom, self._image.height))

        if right <= left or bottom <= top:
            logger.warning("Invalid crop coordinates: (%d,%d,%d,%d)", left, top, right, bottom)
            return False

        self._push_undo(f"Crop ({left},{top})-({right},{bottom})")
        self._image = self._image.crop((left, top, right, bottom))
        logger.info("Image cropped: (%d,%d) -> (%d,%d)", left, top, right, bottom)
        return True

    def resize(self, width: int, height: int, maintain_aspect: bool = True) -> bool:
        """Resize the image.

        Args:
            width: New width.
            height: New height.
            maintain_aspect: Whether to maintain the aspect ratio.

        Returns:
            True if successful.
        """
        if self._image is None:
            return False

        self._push_undo(f"Resize {width}x{height}")

        if maintain_aspect:
            self._image.thumbnail((width, height), Image.LANCZOS)
        else:
            self._image = self._image.resize((width, height), Image.LANCZOS)

        logger.info("Image resized to: %dx%d", self._image.width, self._image.height)
        return True

    # ==================== ENHANCEMENT FILTERS ====================

    def adjust_brightness(self, factor: float) -> bool:
        """Adjust the image brightness (1.0 = no change)."""
        if self._image is None:
            return False
        self._push_undo(f"Brightness x{factor:.2f}")
        self._image = ImageEnhance.Brightness(self._image).enhance(factor)
        return True

    def adjust_contrast(self, factor: float) -> bool:
        """Adjust the image contrast (1.0 = no change)."""
        if self._image is None:
            return False
        self._push_undo(f"Contrast x{factor:.2f}")
        self._image = ImageEnhance.Contrast(self._image).enhance(factor)
        return True

    def adjust_saturation(self, factor: float) -> bool:
        """Adjust the image saturation (0 = grayscale, 1.0 = no change)."""
        if self._image is None:
            return False
        self._push_undo(f"Saturation x{factor:.2f}")
        self._image = ImageEnhance.Color(self._image).enhance(factor)
        return True

    def adjust_sharpness(self, factor: float) -> bool:
        """Adjust the image sharpness (1.0 = no change)."""
        if self._image is None:
            return False
        self._push_undo(f"Sharpness x{factor:.2f}")
        self._image = ImageEnhance.Sharpness(self._image).enhance(factor)
        return True

    # ==================== FILTER EFFECTS ====================

    def apply_blur(self, radius: int = 2) -> bool:
        """Apply a Gaussian blur to the image."""
        if self._image is None:
            return False
        self._push_undo(f"Blur r={radius}")
        self._image = self._image.filter(ImageFilter.GaussianBlur(radius=radius))
        return True

    def apply_sharpen(self) -> bool:
        """Apply a sharpen filter to the image."""
        if self._image is None:
            return False
        self._push_undo("Sharpen")
        self._image = self._image.filter(ImageFilter.SHARPEN)
        return True

    def apply_edge_enhance(self) -> bool:
        """Apply edge enhancement to the image."""
        if self._image is None:
            return False
        self._push_undo("Edge Enhance")
        self._image = self._image.filter(ImageFilter.EDGE_ENHANCE)
        return True

    def apply_emboss(self) -> bool:
        """Apply an emboss effect to the image."""
        if self._image is None:
            return False
        self._push_undo("Emboss")
        self._image = self._image.filter(ImageFilter.EMBOSS)
        return True

    def apply_grayscale(self) -> bool:
        """Convert the image to grayscale."""
        if self._image is None:
            return False
        self._push_undo("Grayscale")
        gray = ImageOps.grayscale(self._image)
        # Convert back to RGB so subsequent filters work correctly
        self._image = gray.convert("RGB")
        logger.info("Grayscale applied.")
        return True

    def apply_invert(self) -> bool:
        """Invert the image colors."""
        if self._image is None:
            return False
        self._push_undo("Invert Colors")
        # For RGBA images, preserve the alpha channel
        if self._image.mode == "RGBA":
            r, g, b, a = self._image.split()
            rgb = Image.merge("RGB", (r, g, b))
            inverted = ImageOps.invert(rgb)
            ir, ig, ib = inverted.split()
            self._image = Image.merge("RGBA", (ir, ig, ib, a))
        else:
            img_rgb = self._image.convert("RGB")
            self._image = ImageOps.invert(img_rgb)
        logger.info("Invert applied.")
        return True

    def apply_auto_enhance(self) -> bool:
        """Auto-enhance the image (contrast + color + sharpness)."""
        if self._image is None:
            return False
        self._push_undo("Auto Enhance")
        # Auto contrast
        if self._image.mode in ("RGB", "L"):
            self._image = ImageOps.autocontrast(self._image, cutoff=1)
        elif self._image.mode == "RGBA":
            r, g, b, a = self._image.split()
            rgb = Image.merge("RGB", (r, g, b))
            rgb = ImageOps.autocontrast(rgb, cutoff=1)
            r2, g2, b2 = rgb.split()
            self._image = Image.merge("RGBA", (r2, g2, b2, a))
        # Boost color and sharpness
        self._image = ImageEnhance.Color(self._image).enhance(1.15)
        self._image = ImageEnhance.Sharpness(self._image).enhance(1.2)
        logger.info("Auto-enhance applied.")
        return True

    # ==================== WATERMARK ====================

    def add_watermark(
        self,
        text: str,
        position: str = "bottom-right",
        opacity: int = 128,
        font_size: int = 24,
        color: Tuple[int, int, int] = (255, 255, 255),
    ) -> bool:
        """Add a text watermark to the image.

        Args:
            text: Watermark text.
            position: One of 'top-left', 'top-right', 'bottom-left',
                      'bottom-right', 'center'.
            opacity: Opacity value (0-255).
            font_size: Font size in points.
            color: Text color as an RGB tuple.

        Returns:
            True if successful.
        """
        if self._image is None:
            return False

        self._push_undo(f"Watermark '{text}'")

        if self._image.mode != "RGBA":
            self._image = self._image.convert("RGBA")

        watermark_layer = Image.new("RGBA", self._image.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(watermark_layer)

        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except (IOError, OSError):
            font = ImageFont.load_default()

        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        padding = 20
        positions = {
            "top-left": (padding, padding),
            "top-right": (self._image.width - text_width - padding, padding),
            "bottom-left": (padding, self._image.height - text_height - padding),
            "bottom-right": (
                self._image.width - text_width - padding,
                self._image.height - text_height - padding,
            ),
            "center": (
                (self._image.width - text_width) // 2,
                (self._image.height - text_height) // 2,
            ),
        }

        pos = positions.get(position, positions["bottom-right"])
        draw.text(pos, text, font=font, fill=(*color, opacity))

        self._image = Image.alpha_composite(self._image, watermark_layer)
        logger.info("Watermark added: '%s' at %s", text, position)
        return True
