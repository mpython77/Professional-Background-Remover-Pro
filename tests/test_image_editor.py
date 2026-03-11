"""ImageEditor unit tests — crop, rotate, flip, filters, undo/redo, history."""

import pytest
from PIL import Image

from core.image_editor import ImageEditor, HistoryEntry


@pytest.fixture
def sample_image() -> Image.Image:
    """Create a 100x100 red test image."""
    return Image.new("RGB", (100, 100), (255, 0, 0))


@pytest.fixture
def editor(sample_image: Image.Image) -> ImageEditor:
    """Create an ImageEditor instance with the sample image."""
    return ImageEditor(sample_image, undo_limit=5)


class TestImageEditorInit:
    """Initialization tests."""

    def test_init_with_image(self, sample_image: Image.Image) -> None:
        editor = ImageEditor(sample_image)
        assert editor.image is not None
        assert editor.image.size == (100, 100)

    def test_init_without_image(self) -> None:
        editor = ImageEditor()
        assert editor.image is None
        assert not editor.can_undo
        assert not editor.can_redo

    def test_set_image_clears_stacks(self, editor: ImageEditor) -> None:
        editor.rotate(90)
        assert editor.can_undo
        editor.image = Image.new("RGB", (50, 50))
        assert not editor.can_undo
        assert not editor.can_redo


class TestHistoryEntry:
    """HistoryEntry tests."""

    def test_create_entry(self) -> None:
        img = Image.new("RGB", (10, 10))
        entry = HistoryEntry(img, "Test Action")
        assert entry.action == "Test Action"
        assert entry.timestamp > 0
        assert entry.image is img

    def test_repr(self) -> None:
        img = Image.new("RGB", (10, 10))
        entry = HistoryEntry(img, "Rotate 90°")
        assert "Rotate 90°" in repr(entry)


class TestUndo:
    """Undo system tests."""

    def test_undo_empty_stack(self) -> None:
        editor = ImageEditor()
        assert not editor.undo()

    def test_undo_after_rotate(self, editor: ImageEditor) -> None:
        original_size = editor.image.size
        editor.rotate(90)
        assert editor.can_undo
        editor.undo()
        assert editor.image.size == original_size

    def test_undo_count(self, editor: ImageEditor) -> None:
        assert editor.undo_count == 0
        editor.rotate(90)
        assert editor.undo_count == 1
        editor.flip_horizontal()
        assert editor.undo_count == 2

    def test_undo_limit(self) -> None:
        editor = ImageEditor(Image.new("RGB", (10, 10)), undo_limit=3)
        for i in range(5):
            editor.rotate(90)
        assert editor.undo_count == 3


class TestRedo:
    """Redo system tests."""

    def test_redo_empty(self) -> None:
        editor = ImageEditor()
        assert not editor.redo()
        assert not editor.can_redo

    def test_redo_after_undo(self, editor: ImageEditor) -> None:
        editor.rotate(90)
        assert editor.can_undo
        assert not editor.can_redo
        editor.undo()
        assert editor.can_redo
        assert editor.redo_count == 1

    def test_redo_restores(self, editor: ImageEditor) -> None:
        editor.rotate(90)
        size_after_rotate = editor.image.size
        editor.undo()
        assert editor.image.size != size_after_rotate or editor.image.size == (100, 100)
        editor.redo()
        assert editor.image.size == size_after_rotate

    def test_new_action_clears_redo(self, editor: ImageEditor) -> None:
        editor.rotate(90)
        editor.undo()
        assert editor.can_redo
        editor.flip_horizontal()  # New action — redo is cleared
        assert not editor.can_redo

    def test_multiple_undo_redo(self, editor: ImageEditor) -> None:
        editor.rotate(90)
        editor.flip_horizontal()
        editor.adjust_brightness(1.5)
        assert editor.undo_count == 3
        editor.undo()
        editor.undo()
        assert editor.redo_count == 2
        editor.redo()
        assert editor.redo_count == 1
        assert editor.undo_count == 2


class TestHistory:
    """History log tests."""

    def test_history_empty(self) -> None:
        editor = ImageEditor()
        assert editor.history == []

    def test_history_tracks_actions(self, editor: ImageEditor) -> None:
        editor.rotate(90)
        editor.flip_horizontal()
        history = editor.history
        assert len(history) == 2
        assert "Rotate 90" in history[0]
        assert "Flip Horizontal" in history[1]

    def test_history_cleared_on_new_image(self, editor: ImageEditor) -> None:
        editor.rotate(90)
        editor.image = Image.new("RGB", (50, 50))
        assert editor.history == []

    def test_history_undo_removes(self, editor: ImageEditor) -> None:
        editor.rotate(90)
        editor.flip_horizontal()
        editor.undo()
        assert len(editor.history) == 1


class TestRotate:
    """Rotate tests."""

    def test_rotate_90(self, editor: ImageEditor) -> None:
        editor.rotate(90)
        assert editor.image is not None

    def test_rotate_no_image(self) -> None:
        editor = ImageEditor()
        assert not editor.rotate(90)

    def test_rotate_360(self, editor: ImageEditor) -> None:
        original_size = editor.image.size
        editor.rotate(360)
        assert editor.image.size == original_size


class TestFlip:
    """Flip tests."""

    def test_flip_horizontal(self, editor: ImageEditor) -> None:
        assert editor.flip_horizontal()
        assert editor.image.size == (100, 100)

    def test_flip_vertical(self, editor: ImageEditor) -> None:
        assert editor.flip_vertical()
        assert editor.image.size == (100, 100)

    def test_flip_no_image(self) -> None:
        editor = ImageEditor()
        assert not editor.flip_horizontal()
        assert not editor.flip_vertical()

    def test_double_flip_restores(self, editor: ImageEditor) -> None:
        original = editor.image.tobytes()
        editor.flip_horizontal()
        editor.flip_horizontal()
        assert editor.image.tobytes() == original


class TestCrop:
    """Crop tests."""

    def test_crop_valid(self, editor: ImageEditor) -> None:
        assert editor.crop(10, 10, 50, 50)
        assert editor.image.size == (40, 40)

    def test_crop_invalid_coords(self, editor: ImageEditor) -> None:
        """Reversed coordinates get swapped — still a valid crop."""
        result = editor.crop(50, 10, 10, 50)
        assert result is True
        assert editor.image.size == (40, 40)

    def test_crop_bounds_clamped(self, editor: ImageEditor) -> None:
        assert editor.crop(-10, -10, 200, 200)
        assert editor.image.size == (100, 100)

    def test_crop_no_image(self) -> None:
        editor = ImageEditor()
        assert not editor.crop(0, 0, 50, 50)


class TestEnhanceFilters:
    """Enhancement filter tests."""

    def test_brightness(self, editor: ImageEditor) -> None:
        assert editor.adjust_brightness(1.5)
        assert editor.can_undo

    def test_contrast(self, editor: ImageEditor) -> None:
        assert editor.adjust_contrast(0.8)
        assert editor.can_undo

    def test_saturation(self, editor: ImageEditor) -> None:
        assert editor.adjust_saturation(2.0)
        assert editor.can_undo

    def test_sharpness(self, editor: ImageEditor) -> None:
        assert editor.adjust_sharpness(1.5)
        assert editor.can_undo

    def test_filters_no_image(self) -> None:
        editor = ImageEditor()
        assert not editor.adjust_brightness(1.5)
        assert not editor.adjust_contrast(1.5)
        assert not editor.adjust_saturation(1.5)
        assert not editor.adjust_sharpness(1.5)


class TestEffectFilters:
    """Effect filter tests."""

    def test_blur(self, editor: ImageEditor) -> None:
        assert editor.apply_blur(3)
        assert editor.can_undo

    def test_sharpen(self, editor: ImageEditor) -> None:
        assert editor.apply_sharpen()
        assert editor.can_undo

    def test_edge_enhance(self, editor: ImageEditor) -> None:
        assert editor.apply_edge_enhance()
        assert editor.can_undo

    def test_emboss(self, editor: ImageEditor) -> None:
        assert editor.apply_emboss()
        assert editor.can_undo

    def test_effects_no_image(self) -> None:
        editor = ImageEditor()
        assert not editor.apply_blur()
        assert not editor.apply_sharpen()
        assert not editor.apply_edge_enhance()
        assert not editor.apply_emboss()


class TestNewFilters:
    """New filter tests — grayscale, invert, auto-enhance."""

    def test_grayscale(self, editor: ImageEditor) -> None:
        assert editor.apply_grayscale()
        assert editor.can_undo
        # Should be converted back to RGB for subsequent filters
        assert editor.image.mode == "RGB"

    def test_grayscale_no_image(self) -> None:
        editor = ImageEditor()
        assert not editor.apply_grayscale()

    def test_invert_rgb(self, editor: ImageEditor) -> None:
        assert editor.apply_invert()
        assert editor.can_undo
        # Red (255,0,0) -> inverted (0,255,255)
        pixel = editor.image.getpixel((50, 50))
        assert pixel == (0, 255, 255)

    def test_invert_rgba(self) -> None:
        img = Image.new("RGBA", (50, 50), (255, 0, 0, 128))
        editor = ImageEditor(img)
        assert editor.apply_invert()
        pixel = editor.image.getpixel((25, 25))
        assert pixel[0] == 0  # R inverted
        assert pixel[3] == 128  # Alpha preserved

    def test_invert_no_image(self) -> None:
        editor = ImageEditor()
        assert not editor.apply_invert()

    def test_auto_enhance_rgb(self, editor: ImageEditor) -> None:
        assert editor.apply_auto_enhance()
        assert editor.can_undo

    def test_auto_enhance_rgba(self) -> None:
        img = Image.new("RGBA", (50, 50), (100, 100, 100, 200))
        editor = ImageEditor(img)
        assert editor.apply_auto_enhance()
        assert editor.image.mode == "RGBA"

    def test_auto_enhance_no_image(self) -> None:
        editor = ImageEditor()
        assert not editor.apply_auto_enhance()


class TestWatermark:
    """Watermark tests."""

    def test_watermark_default(self, editor: ImageEditor) -> None:
        assert editor.add_watermark("Test")
        assert editor.can_undo
        assert editor.image.mode == "RGBA"

    def test_watermark_positions(self, editor: ImageEditor) -> None:
        for pos in ["top-left", "top-right", "bottom-left", "bottom-right", "center"]:
            ed = ImageEditor(Image.new("RGB", (200, 200)))
            assert ed.add_watermark("Test", position=pos)

    def test_watermark_no_image(self) -> None:
        editor = ImageEditor()
        assert not editor.add_watermark("Test")


class TestResize:
    """Resize tests."""

    def test_resize(self, editor: ImageEditor) -> None:
        assert editor.resize(50, 50, maintain_aspect=False)
        assert editor.image.size == (50, 50)

    def test_resize_maintain_aspect(self, editor: ImageEditor) -> None:
        assert editor.resize(50, 50, maintain_aspect=True)
        assert editor.image.width <= 50
        assert editor.image.height <= 50

    def test_resize_no_image(self) -> None:
        editor = ImageEditor()
        assert not editor.resize(50, 50)
