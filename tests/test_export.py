"""ExportManager unit tests — saving, presets, format conversion."""

import os
import tempfile

import pytest
from PIL import Image

from core.export_manager import ExportManager, EXPORT_PRESETS


@pytest.fixture
def temp_dir() -> str:
    """Temporary directory."""
    d = tempfile.mkdtemp()
    yield d
    # Cleanup
    for f in os.listdir(d):
        os.remove(os.path.join(d, f))
    os.rmdir(d)


@pytest.fixture
def exporter() -> ExportManager:
    return ExportManager()


@pytest.fixture
def rgba_image() -> Image.Image:
    """RGBA test image."""
    return Image.new("RGBA", (100, 100), (255, 0, 0, 128))


@pytest.fixture
def rgb_image() -> Image.Image:
    """RGB test image."""
    return Image.new("RGB", (100, 100), (0, 255, 0))


class TestSavePNG:
    """PNG saving tests."""

    def test_save_png(self, exporter: ExportManager, rgba_image: Image.Image, temp_dir: str) -> None:
        path = os.path.join(temp_dir, "test.png")
        assert exporter.save(rgba_image, path, "png")
        assert os.path.exists(path)

    def test_save_png_preserves_alpha(self, exporter: ExportManager, rgba_image: Image.Image, temp_dir: str) -> None:
        path = os.path.join(temp_dir, "test.png")
        exporter.save(rgba_image, path, "png")
        loaded = Image.open(path)
        assert loaded.mode == "RGBA"


class TestSaveJPEG:
    """JPEG saving tests."""

    def test_save_jpeg_from_rgb(self, exporter: ExportManager, rgb_image: Image.Image, temp_dir: str) -> None:
        path = os.path.join(temp_dir, "test.jpg")
        assert exporter.save(rgb_image, path, "jpeg")
        assert os.path.exists(path)

    def test_save_jpeg_from_rgba(self, exporter: ExportManager, rgba_image: Image.Image, temp_dir: str) -> None:
        """RGBA image should be converted to RGB when saved as JPEG."""
        path = os.path.join(temp_dir, "test.jpg")
        assert exporter.save(rgba_image, path, "jpeg")
        loaded = Image.open(path)
        assert loaded.mode == "RGB"

    def test_save_jpeg_quality(self, exporter: ExportManager, rgb_image: Image.Image, temp_dir: str) -> None:
        low_q = os.path.join(temp_dir, "low.jpg")
        high_q = os.path.join(temp_dir, "high.jpg")
        exporter.save(rgb_image, low_q, "jpeg", quality=10)
        exporter.save(rgb_image, high_q, "jpeg", quality=100)
        assert os.path.getsize(low_q) < os.path.getsize(high_q)


class TestSaveWEBP:
    """WEBP saving tests."""

    def test_save_webp(self, exporter: ExportManager, rgb_image: Image.Image, temp_dir: str) -> None:
        path = os.path.join(temp_dir, "test.webp")
        assert exporter.save(rgb_image, path, "webp")
        assert os.path.exists(path)


class TestPresets:
    """Export preset tests."""

    def test_presets_exist(self) -> None:
        presets = ExportManager.get_presets()
        assert "web" in presets
        assert "print" in presets
        assert "social" in presets
        assert "thumbnail" in presets
        assert "original" in presets

    def test_save_with_web_preset(self, exporter: ExportManager, rgb_image: Image.Image, temp_dir: str) -> None:
        path = os.path.join(temp_dir, "web_test.png")
        assert exporter.save_with_preset(rgb_image, path, "web")
        assert os.path.exists(path)

    def test_save_with_thumbnail_preset(self, exporter: ExportManager, temp_dir: str) -> None:
        big_img = Image.new("RGB", (1000, 1000))
        path = os.path.join(temp_dir, "thumb.png")
        exporter.save_with_preset(big_img, path, "thumbnail")
        # Filename should be .jpeg (preset format)
        jpeg_path = os.path.join(temp_dir, "thumb.jpeg")
        assert os.path.exists(jpeg_path)

    def test_invalid_preset(self, exporter: ExportManager, rgb_image: Image.Image, temp_dir: str) -> None:
        path = os.path.join(temp_dir, "test.png")
        assert not exporter.save_with_preset(rgb_image, path, "nonexistent")


class TestFilename:
    """Output filename generation tests."""

    def test_default_suffix(self) -> None:
        result = ExportManager.generate_output_filename("photo.jpg")
        assert result == "photo_nobg.png"

    def test_custom_suffix(self) -> None:
        result = ExportManager.generate_output_filename("photo.jpg", suffix="_edited", file_format="jpeg")
        assert result == "photo_edited.jpeg"

    def test_path_with_dirs(self) -> None:
        result = ExportManager.generate_output_filename("/home/user/photos/image.png")
        assert result == "image_nobg.png"
