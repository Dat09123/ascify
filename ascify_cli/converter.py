"""
converter.py - Chuyển đổi ảnh → ASCII Art (Ascify-CLI)
Core orchestrator: xử lý ảnh qua pipeline resize → grayscale → map ký tự → màu
"""

from PIL import Image
from .config import IMAGE_CONFIG, CHARSET_CONFIG, COLOR_CONFIG, UNICODE_CONFIG
from .resize import resize_image
from .grayscale import to_grayscale, get_pixels
from .charset import get_char
from .color import colorize
from .unicode_mode import to_braille_art, to_block_art


def image_to_ascii(
    image: Image.Image,
    width: int | None = None,
    height: int | None = None,
    charset_name: str | None = None,
    invert: bool | None = None,
    enable_color: bool | None = None,
    braille_mode: bool | None = None,
    block_mode: bool | None = None,
    force_color: bool = False,
    dither: bool | None = None,
    threshold: int | None = None,
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
        invert: Đảo ngược màu (None = tự đảo nếu ảnh tối chiếm đa số)
        enable_color: Bật màu ANSI
        braille_mode: Dùng Braille Unicode
        block_mode: Dùng block Unicode
        force_color: Ép bật màu kể cả khi đang ở kiểu negative (invert)
        dither: Dithering Floyd-Steinberg cho braille (None = theo config)
        threshold: Ngưỡng dot braille (None = theo config)

    Returns:
        Chuỗi ASCII Art (có thể chứa escape codes ANSI)
    """
    # Kiểm tra Unicode mode — chỉ kích hoạt khi được yêu cầu rõ ràng
    if enable_color is None:
        enable_color = COLOR_CONFIG.get("enable", True)

    use_braille = braille_mode or UNICODE_CONFIG.get("braille_mode", False)
    use_block = block_mode or UNICODE_CONFIG.get("block_mode", False)

    # Resize với hệ số bù chiều cao theo chế độ (ASCII khác Braille/Block)
    mode = "braille" if use_braille else ("block" if use_block else "ascii")
    # Braille: 1 ký tự = block 2x4 px → -w tính theo SỐ CỘT ký tự,
    # nên nhân đôi chiều rộng pixel để grid ra đúng W cột.
    # Clamp trong miền ký tự TRƯỚC khi nhân, tránh resize cắt lén
    # (vd -w 300 → 600px bị clamp 500 → mất cột).
    if use_braille:
        # Clamp trong miền ký tự; resize đã scale clamp theo hệ số lấy mẫu
        # (2x4) nên -w 300 thực sự cho 300 cột, --height 60 cho 60 hàng.
        if width is not None:
            width = max(IMAGE_CONFIG["min_width"], min(width, IMAGE_CONFIG["max_width"]))
        if height is not None:
            height = max(IMAGE_CONFIG["min_height"], min(height, IMAGE_CONFIG["max_height"]))
        resize_w = width * 2 if width is not None else None
        resize_h = height * 4 if height is not None else None
    else:
        resize_w = width
        resize_h = height
    image = resize_image(image, resize_w, resize_h, mode=mode)
    w, h = image.size

    if use_braille:
        return _convert_braille(image, enable_color, invert, force_color, dither, threshold)
    elif use_block:
        return _convert_block(image, enable_color, invert, force_color)

    # Chuẩn: ASCII — giữ polarity gốc (không auto-invert như braille),
    # ảnh tối vẫn hiển thị bình thường; dùng -i nếu muốn đảo.
    gray = to_grayscale(image)
    raw_pixels = get_pixels(gray)
    if invert is None:
        invert = False
    pixels = _stretch_contrast(raw_pixels)

    use_color = enable_color and image.mode in ("RGB", "RGBA") and (force_color or not invert)
    lines = []
    for y in range(len(pixels)):
        line_chars = []
        for x in range(len(pixels[y])):
            value = pixels[y][x] / 255.0
            char = get_char(value, charset_name, invert)

            if use_color:
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
    raw_pixels = get_pixels(gray)
    if invert is None:
        invert = False
    pixels = _stretch_contrast(raw_pixels)

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


def _convert_braille(
    image: Image.Image,
    enable_color: bool,
    invert: bool | None = None,
    force_color: bool = False,
    dither: bool | None = None,
    threshold: int | None = None,
) -> str:
    """Chuyển ảnh sang Braille art.

    Ảnh tối chiếm đa số → tự đảo ngược (nền đậm → ⣿, như kiểu negative)
    để output rõ nét trên terminal tối, giống ảnh ví dụ.
    Dithering mặc định BẬT để giữ chi tiết gradient (ảnh manga/wallpaper).
    """
    if dither is None:
        dither = UNICODE_CONFIG.get("braille_dither", True)
    if threshold is None:
        threshold = UNICODE_CONFIG.get("braille_threshold", 128)

    gray = to_grayscale(image)
    raw_pixels = get_pixels(gray)
    if invert is None:
        invert = _is_dark_dominant(raw_pixels)
    pixels = _stretch_contrast(raw_pixels)

    # Kiểu negative là monochrome: màu per-cell làm ⣿ tối mờ trên terminal tối.
    # Tôn trọng `-c` nếu user chủ động yêu cầu màu.
    use_color = enable_color and image.mode in ("RGB", "RGBA") and (force_color or not invert)
    if use_color:
        braille_grid = to_braille_art(pixels, invert, threshold, dither)
        lines = []
        for y, row in enumerate(braille_grid):
            line_chars = []
            for x, char in enumerate(row):
                # Lấy màu trung bình từ block 4x2
                r, g, b = _avg_block_color(image, y * 4, x * 2, 4, 2)
                line_chars.append(colorize(char, r, g, b))
            lines.append("".join(line_chars))
        return "\n".join(lines)

    braille_grid = to_braille_art(pixels, invert, threshold, dither)
    return "\n".join("".join(row) for row in braille_grid)


def _convert_block(
    image: Image.Image,
    enable_color: bool,
    invert: bool | None = None,
    force_color: bool = False,
) -> str:
    """Chuyển ảnh sang block art."""
    gray = to_grayscale(image)
    raw_pixels = get_pixels(gray)
    if invert is None:
        invert = _is_dark_dominant(raw_pixels)
    pixels = _stretch_contrast(raw_pixels)

    use_color = enable_color and image.mode in ("RGB", "RGBA") and (force_color or not invert)
    if use_color:
        block_grid = to_block_art(pixels, invert)
        lines = []
        for y, row in enumerate(block_grid):
            line_chars = []
            for x, char in enumerate(row):
                r, g, b = _avg_block_color(image, y * 2, x, 2, 1)
                line_chars.append(colorize(char, r, g, b))
            lines.append("".join(line_chars))
        return "\n".join(lines)

    block_grid = to_block_art(pixels, invert)
    return "\n".join("".join(row) for row in block_grid)


def _stretch_contrast(pixels: list[list[int]], low_pct: float = 2.0, high_pct: float = 98.0) -> list[list[int]]:
    """Kéo giãn tương phản (contrast stretch) cho ma trận pixel grayscale.

    Map khoảng pixel [p_low, p_high] → [0, 255] để ảnh rõ nét hơn,
    tránh output mờ khi ảnh gốc thiếu tương phản.

    Args:
        pixels: Ma trận pixel 2D (h x w)
        low_pct: Phân vị dưới (mặc định 2%)
        high_pct: Phân vị trên (mặc định 98%)

    Returns:
        Ma trận pixel đã kéo giãn
    """
    flat = [v for row in pixels for v in row]
    if not flat:
        return pixels
    flat.sort()
    n = len(flat)
    lo = flat[int((n - 1) * low_pct / 100.0)]
    hi = flat[int((n - 1) * high_pct / 100.0)]
    span = hi - lo
    if span <= 0:
        return pixels

    def remap(v: int) -> int:
        return max(0, min(255, int((v - lo) * 255 / span)))

    return [[remap(v) for v in row] for row in pixels]


def _is_colorful(image: Image.Image) -> bool:
    """Kiểm tra ảnh có phải photo nhiều màu hay không (chuẩn chafa/viu).

    Dùng HSV trên mẫu pixel:
      - Ảnh chụp thật (wallpaper, ảnh máy ảnh): gradient màu mượt →
        bão hoà trung bình CAO và NHIỀU hue riêng biệt → render true color.
      - Anime/manga/line-art: dù có màu nhưng palette giới hạn (ít hue
        buckets) → giữ negative style.

    Args:
        image: Ảnh Pillow

    Returns:
        True nếu là ảnh nhiều màu (photo)
    """
    min_sat = IMAGE_CONFIG.get("auto_color_min_saturation", 40)
    min_buckets = IMAGE_CONFIG.get("auto_color_min_hue_buckets", 12)
    img = image.convert("RGB")
    # Downscale trước khi phân tích: chỉ cần thống kê hue/saturation,
    # không cần chi tiết → nhanh hơn nhiều với ảnh chụp hàng triệu pixel.
    img.thumbnail((200, 200))
    w, h = img.size
    hsv = img.convert("HSV")
    step = max(1, min(w, h) // 50)
    sat_sum = 0
    hue_buckets = set()
    count = 0
    for y in range(0, h, step):
        for x in range(0, w, step):
            hh, ss, _ = hsv.getpixel((x, y))
            sat_sum += ss
            if ss > 30:  # pixel thật sự có màu
                hue_buckets.add(hh // 8)
            count += 1
    if count == 0:
        return False
    mean_sat = sat_sum / count
    return mean_sat >= min_sat and len(hue_buckets) >= min_buckets


def _is_dark_dominant(pixels: list[list[int]], threshold: int = 128) -> bool:
    """Kiểm tra ảnh có thiên về tối (mean < threshold) hay không."""
    total = 0
    count = 0
    for row in pixels:
        for v in row:
            total += v
            count += 1
    if count == 0:
        return False
    return (total / count) < threshold


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
