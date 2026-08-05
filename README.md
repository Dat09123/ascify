# 🖼 Ascify-CLI

**Chuyển đổi ảnh, video, webcam thành ASCII Art trên terminal — nhanh, nhiều chế độ, tự động chọn kiểu phù hợp.**

> ✨ Tự động: icon → ASCII · ảnh lớn → Unicode/Braille · ảnh chụp nhiều màu → true color · dithering giữ chi tiết gradient

---

## ✨ Tính năng chính

| Tính năng | Mô tả |
|---|---|
| 🧠 **Auto-mode** | Tự chọn chế độ theo ảnh: icon/logo nhỏ → ASCII, ảnh lớn → Braille, không cần flag |
| 🎨 **True color** | ANSI 24-bit RGB, tự bật cho ảnh chụp nhiều màu (chuẩn chafa/viu) |
| ⣿ **Dithering** | Floyd-Steinberg (mặc định ON cho braille) — giữ chi tiết gradient, hết nhiễu |
| 🕶️ **3 chế độ render** | ASCII · Unicode Braille (2×4px) · Unicode Block (1×2px) |
| 🖥️ **Fit-to-terminal** | Tự vừa khít chiều rộng lẫn chiều cao màn hình, không tràn |
| 🎬 **Video/Webcam** | Chuyển video → ASCII frames, phát realtime, webcam live |
| 💾 **Export** | txt, html, png, ansi |

---

## 📦 Cài đặt

### Từ GitHub (khuyến nghị)

```bash
# Cài đặt cơ bản (chỉ ảnh)
pip install git+https://github.com/Dat09123/ascify.git

# Cài đặt đầy đủ (bao gồm video/webcam: OpenCV + NumPy)
pip install "ascify-cli[full] @ git+https://github.com/Dat09123/ascify.git"
```

Sau đó chạy:

```bash
ascify image input.jpg
```

### Chạy từ source (development mode)

```bash
git clone https://github.com/Dat09123/ascify.git
cd ascify
pip install -e .                     # cài đầy đủ deps (Pillow, colorama, ...)
python main.py image input.jpg        # hoặc: python -m ascify_cli image input.jpg
```

> 💡 **Gợi ý:** dùng terminal hỗ trợ màu 24-bit (Windows Terminal, iTerm2, GNOME Terminal, VS Code) để xem đúng màu.

### 🪟 Chạy trên Windows

Ascify hỗ trợ Windows (10/11) — màu ANSI tự bật qua `colorama` khi khởi động, không cần cấu hình gì thêm.

```powershell
# PowerShell / cmd — cài từ GitHub
pip install git+https://github.com/Dat09123/ascify.git
ascify image photo.jpg
```

**Mẹo cho Windows:**
- Dùng **Windows Terminal** (thay vì cmd cũ) để hiển thị đúng màu 24-bit + braille Unicode.
- Font nên là **Cascadia Mono** hoặc **Consolas** (hỗ trợ braille/block Unicode).
- Nếu text bị lỗi font trên cmd cũ: đổi font sang TrueType (`Cascadia Mono`) và gõ `chcp 65001` để dùng UTF-8.
- Video/webcam: cài với `[full]` extra (OpenCV tương thích Windows).

---

## 🚀 Bắt đầu nhanh

```bash
ascify image icon.png                 # icon nhỏ → ASCII
ascify image photo.jpg                # ảnh chụp → Braille + màu + dither, tự fit màn hình
ascify image anime.png                # line-art/anime → negative style
ascify image input.jpg -w 120         # chỉ định chiều rộng (số cột ký tự)
ascify image input.jpg -o output      # xuất ra file (mặc định .txt)
ascify image input.jpg --bg           # tô màu nền (kiểu mosaic)
ascify video video.mp4 --play         # phát video ASCII realtime
ascify webcam                         # webcam ASCII realtime
ascify benchmark input.jpg            # benchmark FPS
ascify --version                      # xem phiên bản
```

---

## 🧠 Auto-mode (tự động chọn chế độ)

Không cần nhớ flag — Ascify tự quyết định theo ảnh:

| Loại ảnh | Chế độ mặc định |
|---|---|
| Icon, logo, meme nhỏ (< 400px) | **ASCII** (6 bộ ký tự) |
| Ảnh chụp, art lớn (≥ 400px) | **Braille** + dithering |
| Ảnh chụp **nhiều màu** | Braille + **true color** (HSV hue-diversity classifier) |
| Line-art/anime (palette hạn chế) | Negative monochrome style |
| Ảnh lớn không truyền `-w` | Tự fit vừa khít terminal (cả 2 chiều) |

### Ép chế độ khi cần

```bash
ascify image photo.jpg --ascii        # ép ASCII kể cả ảnh lớn
ascify image icon.png -b              # ép Braille kể cả ảnh nhỏ
ascify image input.jpg --block        # ép chế độ Block Unicode
ascify image input.jpg --charset detailed   # dùng charset tùy chỉnh (ngầm ép ASCII)
ascify image --list-charsets          # xem các bộ ký tự có sẵn
```

---

## 🎨 Dithering & màu cho ảnh chi tiết

Braille chỉ bật/tắt chấm (binary), nên ảnh gradient mượt dễ thành nhiễu. **Dithering Floyd-Steinberg** (mặc định BẬT) phân tán sai số sang pixel lân cận → chi tiết rõ ràng hơn nhiều.

```bash
ascify image manga.jpg                # dithering mặc định ON → chi tiết rõ
ascify image manga.jpg --no-dither    # tắt dithering (nếu muốn kiểu thuần)
ascify image manga.jpg --threshold 170    # chỉnh ngưỡng bật/tắt dot (0-255, mặc định 128)
ascify image photo.jpg -b --no-dither --threshold 150   # kết hợp tùy chỉnh
```

### Màu

```bash
ascify image photo.jpg                # ảnh chụp → TỰ bật màu true color
ascify image input.jpg -c             # ép bật màu
ascify image input.jpg --no-color     # tắt màu (đen trắng)
ascify image photo.jpg -i             # ép negative đen trắng
ascify image photo.jpg --no-invert    # bỏ auto-invert trên ảnh tối
```

> ⚙️ Có thể chỉnh ngưỡng trong `ascify_cli/config.py`: `auto_unicode_min_size`, `auto_color_min_saturation`, `auto_color_min_hue_buckets`, `braille_threshold`, `braille_dither`.

---

## 🖼 Lệnh `image`

```bash
ascify image <file> [options]
```

| Option | Mô tả |
|---|---|
| `-w, --width N` | Chiều rộng (số cột ký tự, mặc định 120) |
| `--height N` | Chiều cao ký tự (mặc định: auto theo tỷ lệ) |
| `-c, --color` | Bật màu ANSI 24-bit |
| `--no-color` | Tắt màu |
| `-b, --braille` | Chế độ Braille Unicode |
| `--block` | Chế độ Block Unicode |
| `--ascii` | Ép ASCII (bỏ auto Unicode) |
| `--charset NAME` | Chọn bộ ký tự (standard, detailed, block, braille, numbers, letters) |
| `-i, --invert` | Đảo ngược màu (negative) |
| `--no-invert` | Ép không đảo ngược |
| `--no-dither` | Tắt dithering braille |
| `--threshold N` | Ngưỡng dot braille 0-255 (mặc định 128) |
| `--bg` | Tô màu nền thay vì màu chữ (phù hợp block art kiểu mosaic) |
| `-o, --output FILE` | Xuất ra file (không cần extension) |
| `-f, --format FMT` | Định dạng xuất: `txt`, `html`, `png`, `ansi` |
| `--list-charsets` | Liệt kê bộ ký tự |

---

## 🎬 Video & Webcam

```bash
# Video → ASCII frames (thư mục output/)
ascify video input.mp4 -w 100 -c

# Phát video ASCII realtime trên terminal
ascify video input.mp4 --play
ascify video input.mp4 --play -b -c   # phát ở chế độ Braille + màu

# Webcam ASCII realtime
ascify webcam -w 100 -c -b            # webcam + braille + màu
```

**Phím tắt webcam:** nhấn `s` để chụp snapshot PNG (lưu vào `output/`), `q` để thoát (ngoài Ctrl+C).

> Video/webcam cũng hỗ trợ `--no-dither` và `--threshold` để tinh chỉnh chế độ Braille.

> Yêu cầu `opencv-python` + `numpy` (cài qua `[full]` extra).

---

## 📁 Cấu trúc dự án

```
ascify_cli/
├── main.py           # Entry point
├── cli.py            # Xử lý dòng lệnh
├── converter.py      # Pipeline chính + auto-color classifier
├── resize.py         # Resize theo mode (hệ số lấy mẫu ký tự)
├── unicode_mode.py   # Braille/Block + Floyd-Steinberg dithering
├── grayscale.py      # Grayscale
├── charset.py        # Bộ ký tự
├── color.py          # ANSI 24-bit
├── exporter.py       # Xuất txt/html/png/ansi
├── video.py          # Video → ASCII
├── webcam.py         # Webcam realtime
├── benchmark.py      # Đo FPS
└── config.py         # Cấu hình trung tâm
tests/                # Ảnh mẫu để test
```

---

## 🧰 Dependencies

- Python ≥ 3.10
- Pillow ≥ 10.0
- colorama
- OpenCV + NumPy (chỉ cho video/webcam, cài qua `[full]`)

---

## 📄 License

MIT
