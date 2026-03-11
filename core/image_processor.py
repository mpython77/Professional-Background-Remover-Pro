"""AI-powered background removal using rembg (U2-Net model)."""

import os
import time
import threading
from typing import Optional, Callable, List

import numpy as np
from PIL import Image

from utils.logger import setup_logger

logger = setup_logger(__name__)

# Lazy import — only load rembg when first needed
_rembg_remove = None


def _get_rembg_remove():
    """Lazy import — loads the rembg module on first use."""
    global _rembg_remove
    if _rembg_remove is None:
        from rembg import remove
        _rembg_remove = remove
        logger.info("rembg module loaded.")
    return _rembg_remove


class ImageProcessor:
    """AI-powered background removal.

    Uses the rembg library (U2-Net model) to automatically remove
    backgrounds from images. Thread-safe with cancel support.

    Attributes:
        is_processing: Whether a processing job is currently running.
        last_processing_time: Duration of the last processing job (seconds).
    """

    def __init__(self) -> None:
        self.is_processing: bool = False
        self.last_processing_time: float = 0.0
        self._lock = threading.Lock()
        self._cancel_event = threading.Event()

    def cancel(self) -> None:
        """Request cancellation of the current processing job."""
        self._cancel_event.set()
        logger.info("Processing cancellation requested.")

    @property
    def is_cancelled(self) -> bool:
        """Check whether cancellation has been requested."""
        return self._cancel_event.is_set()

    def remove_background(
        self,
        image: Image.Image,
        on_progress: Optional[Callable[[float], None]] = None,
    ) -> Optional[Image.Image]:
        """Remove the background from an image.

        Args:
            image: Input image (PIL Image).
            on_progress: Progress callback (0.0 - 1.0).

        Returns:
            Image with background removed, or None on error/cancel.
        """
        with self._lock:
            if self.is_processing:
                logger.warning("Already processing an image.")
                return None
            self.is_processing = True
            self._cancel_event.clear()

        start_time = time.time()

        try:
            if on_progress:
                on_progress(0.1)

            logger.info(
                "Background removal started: %dx%d, mode=%s",
                image.width, image.height, image.mode,
            )

            # Check for cancellation
            if self._cancel_event.is_set():
                logger.info("Processing cancelled (before conversion).")
                return None

            # Convert to RGBA or RGB
            convert_mode = "RGBA" if image.mode == "RGBA" else "RGB"
            img_array = np.array(image.convert(convert_mode))

            if on_progress:
                on_progress(0.2)

            # Check for cancellation
            if self._cancel_event.is_set():
                logger.info("Processing cancelled (after conversion).")
                return None

            # Remove background via rembg (lazy import)
            remove_fn = _get_rembg_remove()
            result_array = remove_fn(img_array)

            if on_progress:
                on_progress(0.7)

            # Check for cancellation
            if self._cancel_event.is_set():
                logger.info("Processing cancelled (after removal).")
                return None

            result_image = Image.fromarray(result_array)

            if on_progress:
                on_progress(0.9)

            elapsed = time.time() - start_time
            self.last_processing_time = elapsed

            logger.info(
                "Background removal complete: %dx%d, mode=%s, time=%.2fs",
                result_image.width, result_image.height, result_image.mode, elapsed,
            )

            if on_progress:
                on_progress(1.0)

            return result_image

        except Exception as e:
            logger.error("Background removal error: %s", e)
            return None
        finally:
            with self._lock:
                self.is_processing = False

    def remove_background_async(
        self,
        image: Image.Image,
        on_complete: Callable[[Optional[Image.Image]], None],
        on_progress: Optional[Callable[[float], None]] = None,
        on_error: Optional[Callable[[str], None]] = None,
    ) -> threading.Thread:
        """Remove the background asynchronously in a separate thread.

        Args:
            image: Input image.
            on_complete: Callback when finished.
            on_progress: Progress callback.
            on_error: Error callback.

        Returns:
            The started Thread object.
        """
        def _worker() -> None:
            result = self.remove_background(image, on_progress)
            if self._cancel_event.is_set():
                if on_error:
                    on_error("Processing was cancelled.")
                return
            if result is not None:
                on_complete(result)
            elif on_error:
                on_error("Background removal failed.")

        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()
        return thread

    def batch_process(
        self,
        file_paths: List[str],
        output_dir: str,
        on_progress: Optional[Callable[[int, int, str], None]] = None,
        on_complete: Optional[Callable[[int, int], None]] = None,
        on_error: Optional[Callable[[str, str], None]] = None,
    ) -> threading.Thread:
        """Process multiple images sequentially.

        Args:
            file_paths: List of input file paths.
            output_dir: Output directory.
            on_progress: Progress callback (current, total, filename).
            on_complete: Completion callback (success_count, total).
            on_error: Error callback (filename, error_message).

        Returns:
            The started Thread object.
        """
        def _batch_worker() -> None:
            total = len(file_paths)
            success_count = 0

            for i, file_path in enumerate(file_paths):
                # Check for cancellation
                if self._cancel_event.is_set():
                    logger.info("Batch processing cancelled: %d/%d", i, total)
                    break

                filename = os.path.basename(file_path)
                try:
                    img = Image.open(file_path)
                    result = self.remove_background(img)

                    if self._cancel_event.is_set():
                        break

                    if result is not None:
                        out_name = f"{os.path.splitext(filename)[0]}_nobg.png"
                        out_path = os.path.join(output_dir, out_name)
                        result.save(out_path, "PNG", optimize=True)
                        success_count += 1
                        logger.info("Batch: %s processed (%d/%d)", filename, i + 1, total)
                    else:
                        if on_error:
                            on_error(filename, "Processing failed")

                except Exception as e:
                    logger.error("Batch error [%s]: %s", filename, e)
                    if on_error:
                        on_error(filename, str(e))

                if on_progress:
                    on_progress(i + 1, total, filename)

            if on_complete:
                on_complete(success_count, total)

        self._cancel_event.clear()
        thread = threading.Thread(target=_batch_worker, daemon=True)
        thread.start()
        return thread
