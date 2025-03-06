# Professional Background Remover Pro

## Overview
Professional Background Remover Pro is a Python-based desktop application for removing image backgrounds with additional editing features. It provides a user-friendly interface with functionalities such as cropping, rotating, flipping, zooming, and batch processing. The application is built using `rembg` for AI-powered background removal and `tkinter` for the graphical interface.

## Features
- **AI-powered background removal** for images
- **Editing tools**: Crop, rotate, flip, zoom
- **Undo last action** (Ctrl+Z)
- **Batch processing** for multiple images
- **Clipboard support**: Load images directly from clipboard
- **Save options**: PNG or JPEG with adjustable quality
- **Compare original and processed images**
- **Custom background color selection**

## Installation
### Clone the Repository:
```bash
git clone https://github.com/mpython77/Professional-Background-Remover-Pro.git
cd Professional-Background-Remover-Pro
```
### Install Python (if not installed)
Ensure you have Python 3.7+ installed. [Download Python](https://www.python.org/downloads/).

### Install Dependencies
Install required libraries:
```bash
pip install Pillow rembg numpy
```
Or use `requirements.txt`:
```bash
pip install -r requirements.txt
```

### Clipboard Support (Linux - Optional)
If you are using Linux, install `python3-xlib` for clipboard functionality:
```bash
sudo apt-get install python3-xlib
```

## Usage
### Run the Application
```bash
python Remove Background.py
```
### Steps to Use:
1. **Open an image**: "File" > "Open Image..." (Ctrl+O) or load from clipboard
2. **Remove background**: "Edit" > "Remove Background" (Ctrl+P)
3. **Edit the image**: Crop, rotate, flip via the "Edit" menu
4. **Zoom options**: "View" > Zoom In/Out/Reset
5. **Undo changes**: "Edit" > "Undo" (Ctrl+Z)
6. **Save the processed image**: "File" > "Save..." (Ctrl+S)
7. **Batch process multiple images**: "Batch" > "Process Multiple Images..."
8. **Customize background**: Set format/quality in "Settings" or choose a background color via "Edit" > "Select Background Color..."

## Code Overview
### `Remove Background.py` Structure
The application is managed by the `EnhancedBackgroundRemover` class, which handles the GUI and image processing.
#### Key Functions:
- **`process_image()`**: Removes the background using `rembg`
- **`crop_image()`**: Allows interactive cropping
- **`rotate_image(angle)`**: Rotates the image
- **`flip_image()`**: Flips image horizontally or vertically
- **`undo()`**: Reverts the last edit
- **`batch_process()`**: Processes multiple images at once
- **`display_*()`**: Updates the GUI canvas with images

## Requirements
- **Python 3.7+**
- **Libraries**: Pillow, rembg, numpy
- **Optional**: `python3-xlib` (for clipboard support on Linux)

## Troubleshooting
- **Module not found (`rembg`)**: Run `pip install rembg`
- **Clipboard issues**: Ensure Pillow supports `ImageGrab`
- **Slow performance**: Check system resources and restart the application



## License
This project is licensed under the **MIT License** (see LICENSE file).

## Acknowledgments
- `rembg` for AI-powered background removal
- `Pillow` for image processing
- `tkinter` for the GUI


