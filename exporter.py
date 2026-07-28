"""
exporter.py - Xuất ASCII Art ra các định dạng (Ascify-CLI)
Hỗ trợ: txt, html, png, ansi
"""

from pathlib import Path

from config import EXPORT_CONFIG


def export_ascii(
    ascii_art: str,
    output_path: str | Path,
    fmt: str | None = None,
    **kwargs,
) -> str | None:
    """Xuất ASCII Art ra file.

    Args:
        ascii_art: Chuỗi ASCII Art
        output_path: Đường dẫn file (không cần extension)
        fmt: Định dạng (txt, html, png, ansi)
        **kwargs: Tham số riêng cho từng định dạng

    Returns:
        Đường dẫn file đã xuất (None nếu lỗi)
    """
    if fmt is None:
        fmt = EXPORT_CONFIG.get("default_format", "txt")

    output_path = Path(output_path)
    exporters = {
        "txt": _export_txt,
        "html": _export_html,
        "ansi": _export_ansi,
        "png": _export_png,
    }

    exporter = exporters.get(fmt)
    if exporter is None:
        print(f"❌ Định dạng không hỗ trợ: {fmt}")
        return None

    return exporter(ascii_art, output_path, **kwargs)


def _export_txt(ascii_art: str, output_path: Path, **kwargs) -> str:
    """Xuất ra file .txt thuần."""
    from color import strip_ansi

    encoding = EXPORT_CONFIG["txt"].get("encoding", "utf-8")
    newline = EXPORT_CONFIG["txt"].get("newline", "\n")

    output_path = output_path.with_suffix(".txt")
    text = strip_ansi(ascii_art)
    text = text.replace("\n", newline)

    with open(output_path, "w", encoding=encoding) as f:
        f.write(text)

    print(f"📄 Đã xuất TXT: {output_path}")
    return str(output_path)


def _export_ansi(ascii_art: str, output_path: Path, **kwargs) -> str:
    """Xuất ra file .ansi giữ nguyên escape codes."""
    encoding = EXPORT_CONFIG["txt"].get("encoding", "utf-8")

    output_path = output_path.with_suffix(".ansi")
    with open(output_path, "w", encoding=encoding) as f:
        f.write(ascii_art)

    print(f"🎨 Đã xuất ANSI: {output_path}")
    return str(output_path)


def _export_html(ascii_art: str, output_path: Path, **kwargs) -> str:
    """Xuất ra file .html với màu sắc."""
    from color import strip_ansi

    html_config = {**EXPORT_CONFIG["html"], **kwargs}

    font_family = html_config.get("font_family", "monospace")
    font_size = html_config.get("font_size", "12px")
    bg = html_config.get("background", "#000000")
    color = html_config.get("color", "#00ff00")

    # Parse ANSI escape codes → HTML spans
    html_content = _ansi_to_html(ascii_art)
    plain_text = strip_ansi(ascii_art)
    lines = plain_text.count("\n") + 1
    line_height_px = int(font_size.replace("px", "")) + 2

    html = f"""<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<title>ASCII Art</title>
<style>
  body {{
    background: {bg};
    margin: 0;
    padding: 20px;
    min-height: 100vh;
  }}
  pre {{
    font-family: '{font_family}', monospace;
    font-size: {font_size};
    line-height: 1;
    color: {color};
    background: {bg};
    display: inline-block;
    padding: 10px;
    margin: 0;
    white-space: pre;
    overflow: auto;
  }}
</style>
</head>
<body>
<pre>{html_content}</pre>
</body>
</html>"""

    output_path = output_path.with_suffix(".html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"🌐 Đã xuất HTML: {output_path}")
    return str(output_path)


def _ansi_to_html(text: str) -> str:
    """Chuyển ANSI escape codes thành HTML spans.

    Xử lý các escape: \033[38;2;R;G;Bm (foreground)
    và \033[0m (reset)
    """
    import re

    # Escape HTML entities
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    def replace_fg(m):
        r, g, b = m.group(1), m.group(2), m.group(3)
        return f'<span style="color:rgb({r},{g},{b})">'

    def replace_bg(m):
        r, g, b = m.group(1), m.group(2), m.group(3)
        return f'<span style="background:rgb({r},{g},{b})">'

    # Foreground
    text = re.sub(r'\033\[38;2;(\d+);(\d+);(\d+)m', replace_fg, text)
    # Background
    text = re.sub(r'\033\[48;2;(\d+);(\d+);(\d+)m', replace_bg, text)
    # Reset
    text = text.replace('\033[0m', '</span>')

    # Đóng các span chưa đóng
    open_spans = text.count('<span')
    close_spans = text.count('</span>')
    if open_spans > close_spans:
        text += '</span>' * (open_spans - close_spans)

    return text


def _export_png(ascii_art: str, output_path: Path, **kwargs) -> str:
    """Xuất ra file .png sử dụng Pillow, giữ nguyên màu sắc."""
    from color import iter_colored_chars, strip_ansi
    from PIL import Image, ImageDraw, ImageFont

    png_config = {**EXPORT_CONFIG["png"], **kwargs}
    font_size = png_config.get("font_size", 14)
    font_path = png_config.get("font_path")
    bg_color = png_config.get("background_color", (0, 0, 0))

    # Dùng font monospace mặc định hoặc tìm font
    try:
        if font_path:
            font = ImageFont.truetype(font_path, font_size)
        else:
            font = ImageFont.load_default()
    except Exception:
        font = ImageFont.load_default()

    # Tính kích thước từng ký tự
    try:
        bbox_a = font.getbbox("A")
        char_w = bbox_a[2] - bbox_a[0]
        char_h = bbox_a[3] - bbox_a[1] + 2
    except Exception:
        char_w = font_size
        char_h = font_size + 2

    # Đếm số dòng từ ASCII art (strip ANSI codes để đếm chính xác)
    plain = strip_ansi(ascii_art)
    lines = plain.split("\n")
    max_line_len = max(len(line) for line in lines) if lines else 1
    img_w = max_line_len * char_w + 20
    img_h = len(lines) * char_h + 20

    img = Image.new("RGB", (img_w, img_h), bg_color)
    draw = ImageDraw.Draw(img)

    # Duyệt từng ký tự với màu tương ứng, vẽ từng ký tự một
    x, y = 10, 10
    for char, r, g, b in iter_colored_chars(ascii_art):
        if char == "\n":
            x = 10
            y += char_h
            continue
        draw.text((x, y), char, fill=(r, g, b), font=font)
        x += char_w

    output_path = output_path.with_suffix(".png")
    img.save(output_path)
    print(f"🖼 Đã xuất PNG: {output_path}")
    return str(output_path)
