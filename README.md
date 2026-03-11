# Professional Background Remover Pro v2.1

🖼️ **AI-powered professional background removal tool** — rembg (U2-Net) asosida rasmlardan fonni avtomatik olib tashlash, tahrirlash, va eksport qilish.

## ✨ Features

### Core
- 🤖 **AI Background Removal** — U2-Net modeli orqali yuqori sifatli fon olib tashlash
- 📦 **Batch Processing** — bir nechta rasmni ketma-ket qayta ishlash (cancel bilan)
- 📋 **Clipboard Support** — clipboard'dan rasm yuklash

### Editing
- ↩️ **Undo / Redo** — cheksiz bekor qilish va qaytarish (limit=20)
- ✂️ **Crop** — interaktiv rasm kesish
- 🔄 **Rotate** — 0-360° aylantirish
- 🔀 **Flip** — gorizontal va vertikal aks ettirish
- 💧 **Watermark** — matnli watermark (5 pozitsiya, opacity, font size)

### Filters
- ☀️ Brightness / 🔲 Contrast / 🎭 Saturation / 🔍 Sharpness
- Blur / Sharpen / Edge Enhance / Emboss
- 🎨 **Grayscale** — qora-oq rejim
- 🔄 **Invert Colors** — ranglarni teskari qilish
- ✨ **Auto Enhance** — avtomatik rasm optimallash

### Export
- 📤 **Export Presets**: Web (72 DPI), Print (300 DPI), Social (1080px), Thumbnail (256px)
- PNG / JPEG / WEBP / BMP formatlar
- Sifat sozlash (1-100%)

### UI
- 🌓 **Dark / Light Mode** — professional tema tizimi
- 📜 **History Panel** — amallar tarixi
- ⌨️ **Shortcuts Panel** — tezkor tugmalar
- 📊 **Image Info** — o'lcham, format, EXIF ma'lumotlari
- 📂 **Recent Files** — oxirgi 10 fayl

---

## 🏗️ Architecture (MVC)

```
Professional-Background-Remover-Pro/
├── main.py                 ← Entry point
├── requirements.txt
├── .gitignore
├── core/                   ← Business Logic
│   ├── image_processor.py   (AI removal, lazy rembg, cancel, batch)
│   ├── image_editor.py      (Undo/Redo deque, 12+ filters, watermark)
│   └── export_manager.py    (Multi-format, presets, DPI)
├── ui/                     ← Presentation Layer
│   ├── main_window.py       (Main coordinator)
│   ├── themes.py            (Dark/Light theme system)
│   ├── panels.py            (Input, Settings, Filter, Actions, Display)
│   ├── dialogs.py           (Rotate, Flip, Crop, Compare, Export, Watermark, Info)
│   └── history_panel.py     (History + Shortcuts panels)
├── config/                 ← Configuration
│   └── config_manager.py    (JSON config, validation, recent files)
├── utils/                  ← Utilities
│   ├── helpers.py           (EXIF, debounce, file ops)
│   └── logger.py            (Singleton logger, file+console)
└── tests/                  ← Test Suite (90+ tests)
    ├── test_image_editor.py
    ├── test_config.py
    ├── test_export.py
    ├── test_helpers.py
    └── test_logger.py
```

---

## 🚀 Quick Start

```bash
# Clone
git clone https://github.com/mpython77/Professional-Background-Remover-Pro.git
cd Professional-Background-Remover-Pro

# Install
pip install -r requirements.txt

# Run
python main.py
```

## ⌨️ Shortcuts

| Key | Action |
|-----|--------|
| `Ctrl+O` | Open Image |
| `Ctrl+S` | Save |
| `Ctrl+P` | Remove Background |
| `Ctrl+Z` | Undo |
| `Ctrl+Y` | Redo |
| `Ctrl+±` | Zoom In/Out |
| `Ctrl+0` | Reset Zoom |
| `Esc` | Cancel Processing |

## 📋 Requirements

- Python 3.8+
- Pillow
- rembg
- numpy

## 📄 License

MIT License — see [LICENSE](LICENSE)
