"""Utils helpers unit tests."""

import os
from PIL import Image

from utils.helpers import rgb_to_hex, get_image_info, clamp


class TestRgbToHex:
    """rgb_to_hex tests."""

    def test_black(self) -> None:
        assert rgb_to_hex((0, 0, 0)) == "#000000"

    def test_white(self) -> None:
        assert rgb_to_hex((255, 255, 255)) == "#ffffff"

    def test_red(self) -> None:
        assert rgb_to_hex((255, 0, 0)) == "#ff0000"

    def test_custom_color(self) -> None:
        assert rgb_to_hex((67, 97, 238)) == "#4361ee"


class TestClamp:
    """clamp tests."""

    def test_within_range(self) -> None:
        assert clamp(5.0, 0.0, 10.0) == 5.0

    def test_below_min(self) -> None:
        assert clamp(-5.0, 0.0, 10.0) == 0.0

    def test_above_max(self) -> None:
        assert clamp(15.0, 0.0, 10.0) == 10.0

    def test_at_boundary(self) -> None:
        assert clamp(0.0, 0.0, 10.0) == 0.0
        assert clamp(10.0, 0.0, 10.0) == 10.0


class TestGetImageInfo:
    """get_image_info tests."""

    def test_basic_info(self) -> None:
        img = Image.new("RGB", (200, 150))
        info = get_image_info(img)
        assert info["width"] == 200
        assert info["height"] == 150
        assert info["mode"] == "RGB"
        assert info["pixels"] == 30000

    def test_with_file_path(self, tmp_path) -> None:
        img = Image.new("RGB", (100, 100))
        path = str(tmp_path / "test.png")
        img.save(path)

        info = get_image_info(img, path)
        assert "file_size_bytes" in info
        assert info["file_size_kb"] > 0

    def test_rgba_mode(self) -> None:
        img = Image.new("RGBA", (50, 50))
        info = get_image_info(img)
        assert info["mode"] == "RGBA"

    def test_exif_key_exists(self) -> None:
        img = Image.new("RGB", (10, 10))
        info = get_image_info(img)
        assert "exif" in info
