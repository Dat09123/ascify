"""
unicode_mode.py - Hỗ trợ Unicode/Braille cho Ascify-CLI
Braille: mỗi ký tự đại diện cho 4x2 pixel (8 điểm)
Block: mỗi ký tự đại diện cho 2x1 pixel (4 mức)
"""

from .config import UNICODE_CONFIG

# Braille patterns cho 4 hàng x 2 cột
# Mỗi Braille char có 8 dot positions:
#   dot1 (0x01) dot4 (0x08)
#   dot2 (0x02) dot5 (0x10)
#   dot3 (0x04) dot6 (0x20)
#   dot7 (0x40) dot8 (0x80)

BRAILLE_BASE = 0x2800


def pixels_to_braille(pixels_4x2: list[list[int]], invert: bool = False, threshold: int = 128) -> str:
    """Chuyển block 4x2 pixel thành ký tự Braille.

    Args:
        pixels_4x2: List 4 hàng, mỗi hàng 2 giá trị (0–255)
        invert: True = dot khi pixel tối (phong cách negative, nền đậm → ⣿)
        threshold: Ngưỡng bật/tắt dot (0–255)

    Returns:
        Ký tự Braille Unicode tương ứng
    """
    dots = 0
    # Dot mapping: (hàng, cột) -> bit position
    # Braille dot layout:
    #   0 3
    #   1 4
    #   2 5
    #   6 7

    def dot_on(v: int) -> bool:
        return v < threshold if invert else v > threshold

    if dot_on(pixels_4x2[0][0]): dots |= 0x01
    if dot_on(pixels_4x2[1][0]): dots |= 0x02
    if dot_on(pixels_4x2[2][0]): dots |= 0x04
    if dot_on(pixels_4x2[0][1]): dots |= 0x08
    if dot_on(pixels_4x2[1][1]): dots |= 0x10
    if dot_on(pixels_4x2[2][1]): dots |= 0x20
    if dot_on(pixels_4x2[3][0]): dots |= 0x40
    if dot_on(pixels_4x2[3][1]): dots |= 0x80

    return chr(BRAILLE_BASE + dots)


def to_braille_art(
    pixels: list[list[int]],
    invert: bool = False,
    threshold: int = 128,
    dither: bool = False,
) -> list[list[str]]:
    """Chuyển ma trận pixel thành ma trận ký tự Braille.

    Kết quả có kích thước (h//4) x (w//2)

    Args:
        pixels: Ma trận pixel 2D (h x w)
        invert: Đảo ngược (tối → dot)
        threshold: Ngưỡng bật/tắt dot (0–255)
        dither: Dithering Floyd-Steinberg để giữ chi tiết gradient

    Returns:
        Ma trận ký tự Braille
    """
    if dither:
        pixels = _floyd_steinberg(pixels, threshold)

    h = len(pixels)
    w = len(pixels[0]) if h > 0 else 0
    result = []

    for y in range(0, h - 3, 4):
        row = []
        for x in range(0, w - 1, 2):
            block = [
                [pixels[y][x], pixels[y][x + 1]],
                [pixels[y + 1][x], pixels[y + 1][x + 1]],
                [pixels[y + 2][x], pixels[y + 2][x + 1]],
                [pixels[y + 3][x], pixels[y + 3][x + 1]],
            ]
            row.append(pixels_to_braille(block, invert, threshold))
        result.append(row)

    return result


def _floyd_steinberg(pixels: list[list[int]], threshold: int = 128) -> list[list[int]]:
    """Dithering Floyd-Steinberg: chuyển gradient mượt → chấm nhị phân rõ chi tiết.

    Vì dot braille chỉ bật/tắt, dithering phân tán sai số lượng tử hóa sang
    pixel lân cận giúp ảnh chi tiết (manga, wallpaper) hiển thị rõ hơn nhiều.

    Args:
        pixels: Ma trận pixel 2D (h x w)
        threshold: Ngưỡng bật/tắt (0–255)

    Returns:
        Ma trận pixel nhị phân 0/255
    """
    h = len(pixels)
    w = len(pixels[0]) if h > 0 else 0
    if h == 0 or w == 0:
        return pixels

    out = [row[:] for row in pixels]
    for y in range(h):
        for x in range(w):
            old = out[y][x]
            new = 255 if old > threshold else 0
            out[y][x] = new
            err = old - new
            if x + 1 < w:
                out[y][x + 1] += _diffuse(err, 7)
            if y + 1 < h:
                if x > 0:
                    out[y + 1][x - 1] += _diffuse(err, 3)
                out[y + 1][x] += _diffuse(err, 5)
                if x + 1 < w:
                    out[y + 1][x + 1] += _diffuse(err, 1)
    return out


def _diffuse(err: int, weight: int) -> int:
    """Phân tán sai số theo trọng số Floyd-Steinberg, làm tròn thay vì floor.

    // với số âm thiên về âm (floor), gây lệch nhẹ; round về 0 đúng hơn.
    """
    v = err * weight
    if v >= 0:
        return (v + 8) // 16
    return -((-v + 8) // 16)


def to_block_art(pixels: list[list[int]], invert: bool = False) -> list[list[str]]:
    """Chuyển ma trận pixel thành ký tự block Unicode.

    Blocks: ' ░▒▓█' (4 levels cho 2x1 block)

    Args:
        pixels: Ma trận pixel 2D (h x w)
        invert: Đảo ngược thang độ đậm

    Returns:
        Ma trận ký tự block
    """
    blocks = "█▓▒░ " if invert else " ░▒▓█"
    h = len(pixels)
    w = len(pixels[0]) if h > 0 else 0
    result = []

    for y in range(0, h - 1, 2):
        row = []
        for x in range(w):
            if y + 1 < h:
                avg = (pixels[y][x] + pixels[y + 1][x]) // 2
            else:
                avg = pixels[y][x]
            idx = int(avg / 255 * (len(blocks) - 1))
            row.append(blocks[idx])
        result.append(row)

    return result
