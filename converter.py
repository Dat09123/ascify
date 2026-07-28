"""
converter.py - Chuyển đổi ảnh → ASCII Art (Ascify-CLI)
Core orchestrator: xử lý ảnh qua pipeline resize → grayscale → map ký tự → màu
"""

from PIL import Image
from config import IMAGE_CONFIG, CHARSET_CONFIG, COLOR_CONFIG, UNICODE_CONFIG
from resize import resize_image
from grayscale import to_grayscale, get_pixels
from charset import get_char
from color import colorize
from unicode_mode import to_braille_art, to_block_art


def image_to_ascii(
    image: Image.Image,
    width: int | None = None,
    height: int | None = None,
    charset_name: str | None = None,
    invert: bool | None = None,
    enable_color: bool | None = None,
    braille_mode: bool | None = None,
    block_mode: bool | None = None,
) -> str:
    """Chuyển đổi ảnh Pillow thành ASCII Art.

    Pipeline:
        1. Resize ảnh
        2. Chuyển grayscale
        3. Map pixel → ký tự theo charset
        4. (Tuỳ chọn) Thêm màu ANSI

    Args:
        image: Ảnh Pillow đầu vào
        width: Chiều rộng ASCII (ký tự)
        height: Chiều cao ASCII (ký tự)
        charset_name: Tên bộ ký tự
        invert: Đảo ngược màu
        enable_color: Bật màu ANSI
        braille_mode: Dùng Braille Unicode
        block_mode: Dùng block Unicode

    Returns:
        Chuỗi ASCII Art (có thể chứa escape codes ANSI)
    """
    # Resize
    image = resize_image(image, width, height)
    w, h = image.size

    # Kiểm tra Unicode mode — chỉ kích hoạt khi được yêu cầu rõ ràng
    if enable_color is None:
        enable_color = COLOR_CONFIG.get("enable", True)

    if braille_mode or UNICODE_CONFIG.get("braille_mode", False):
        return _convert_braille(image, enable_color)
    elif block_mode or UNICODE_CONFIG.get("block_mode", False):
        return _convert_block(image, enable_color)

    # Chuẩn: ASCII
    gray = to_grayscale(image)
    pixels = get_pixels(gray)

    lines = []
    for y in range(len(pixels)):
        line_chars = []
        for x in range(len(pixels[y])):
            value = pixels[y][x] / 255.0
            char = get_char(value, charset_name, invert)

            if enable_color and image.mode == "RGB":
                r, g, b = image.getpixel((x, y))[:3]
                char = colorize(char, r, g, b)

            line_chars.append(char)
        lines.append("".join(line_chars))

    return "\n".join(lines)


def image_to_ascii_with_pixels(
    image: Image.Image,
    width: int | None = None,
    height: int | None = None,
    charset_name: str | None = None,
    invert: bool | None = None,
) -> tuple[list[list[str]], list[list[tuple[int, int, int]]] | None]:
    """Chuyển ảnh thành grid ASCII và pixel map (cho exporter).

    Returns:
        Tuple (grid_ascii, grid_colors)
    """
    image = resize_image(image, width, height)
    w, h = image.size
    gray = to_grayscale(image)
    pixels = get_pixels(gray)

    grid = []
    colors = []

    for y in range(len(pixels)):
        row_chars = []
        row_colors = []
        for x in range(len(pixels[y])):
            value = pixels[y][x] / 255.0
            char = get_char(value, charset_name, invert)
            row_chars.append(char)
            if image.mode == "RGB":
                row_colors.append(image.getpixel((x, y))[:3])
            else:
                row_colors.append((255, 255, 255))
        grid.append(row_chars)
        colors.append(row_colors)

    return grid, colors


def _convert_braille(image: Image.Image, enable_color: bool) -> str:
    """Chuyển ảnh sang Braille art."""
    gray = to_grayscale(image)
    pixels = get_pixels(gray)

    if enable_color and image.mode == "RGB":
        braille_grid = to_braille_art(pixels)
        lines = []
        for y, row in enumerate(braille_grid):
            line_chars = []
            for x, char in enumerate(row):
                # Lấy màu trung bình từ block 4x2
                r, g, b = _avg_block_color(image, y * 4, x * 2, 4, 2)
                line_chars.append(colorize(char, r, g, b))
            lines.append("".join(line_chars))
        return "\n".join(lines)

    braille_grid = to_braille_art(pixels)
    return "\n".join("".join(row) for row in braille_grid)


def _convert_block(image: Image.Image, enable_color: bool) -> str:
    """Chuyển ảnh sang block art."""
    gray = to_grayscale(image)
    pixels = get_pixels(gray)

    if enable_color and image.mode == "RGB":
        block_grid = to_block_art(pixels)
        lines = []
        for y, row in enumerate(block_grid):
            line_chars = []
            for x, char in enumerate(row):
                r, g, b = _avg_block_color(image, y * 2, x, 2, 1)
                line_chars.append(colorize(char, r, g, b))
            lines.append("".join(line_chars))
        return "\n".join(lines)

    block_grid = to_block_art(pixels)
    return "\n".join("".join(row) for row in block_grid)


def _avg_block_color(image: Image.Image, y: int, x: int, bh: int, bw: int) -> tuple[int, int, int]:
    """Tính màu trung bình của block ảnh."""
    r_total, g_total, b_total, count = 0, 0, 0, 0
    img_w, img_h = image.size
    for dy in range(bh):
        for dx in range(bw):
            px, py = x + dx, y + dy
            if px < img_w and py < img_h:
                pr, pg, pb = image.getpixel((px, py))[:3]
                r_total += pr
                g_total += pg
                b_total += pb
                count += 1
    if count == 0:
        return (0, 0, 0)
    return (r_total // count, g_total // count, b_total // count)
