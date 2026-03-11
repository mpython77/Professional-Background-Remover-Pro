"""Core module — image processing, editing, and export."""


def __getattr__(name):
    """Lazy imports — only load rembg when ImageProcessor is used."""
    if name == "ImageProcessor":
        from core.image_processor import ImageProcessor
        return ImageProcessor
    if name == "ImageEditor":
        from core.image_editor import ImageEditor
        return ImageEditor
    if name == "ExportManager":
        from core.export_manager import ExportManager
        return ExportManager
    raise AttributeError(f"module 'core' has no attribute {name!r}")


__all__ = ["ImageProcessor", "ImageEditor", "ExportManager"]
