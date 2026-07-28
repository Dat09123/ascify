# 🖼 Ascify-CLI

**Chuyển đổi ảnh, video, webcam thành ASCII Art trên terminal.**

## Install

### 📦 Từ GitHub (không cần PyPI)

```bash
pip install git+https://github.com/Dat09123/ascify.git[full]
```

Sau đó chạy:

```bash
ascify image input.jpg
```

### 🏃 Chạy trực tiếp (không cần cài đặt)

```bash
git clone https://github.com/Dat09123/ascify.git
cd ascify
pip install Pillow
python main.py image input.jpg
```

## Usage

```bash
ascify image input.jpg                    # Ảnh → ASCII
ascify image input.jpg -w 100 -c          # Với màu sắc
ascify image input.jpg -o out.html        # Xuất HTML
ascify image input.jpg --braille          # Chế độ Braille
ascify video input.mp4 --play             # Phát video ASCII
ascify webcam -w 80 -c                    # Webcam realtime
ascify benchmark input.jpg                # Benchmark FPS
```

## Features

- 🖼 Ảnh → ASCII với 6 bộ ký tự
- 🎨 ANSI 24-bit true color
- 🕶️ Unicode Braille & Block mode
- 🎬 Video → ASCII frames + phát realtime
- 📷 Webcam ASCII realtime
- 💾 Export: txt, html, png, ansi
- ⚡ Benchmark hiệu năng

## Dependencies

- Python ≥ 3.10
- Pillow (built-in)
- OpenCV + NumPy (cho video/webcam)

## License

MIT
