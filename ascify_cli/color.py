"""
color.py - Màu ANSI RGB cho Ascify-CLI
Hỗ trợ 24-bit true color trong terminal
"""

import re

from .config import COLOR_CONFIG


def rgb_to_ansi(r: int, g: int, b: int, background: bool = False) -> str:
    """Tạo escape sequence ANSI 24-bit cho màu RGB.

    Args:
        r: Đỏ (0–255)
        g: Xanh lá (0–255)
        b: Xanh dương (0–255)
        background: True = màu nền, False = màu chữ

    Returns:
        Escape sequence ANSI
    """
    if background:
        return f"\033[48;2;{r};{g};{b}m"
    return f"\033[38;2;{r};{g};{b}m"


def colorize(char: str, r: int, g: int, b: int, bg: bool = False) -> str:
    """Bọc ký tự với màu ANSI.

    Args:
        char: Ký tự ASCII
        r, g, b: Giá trị màu RGB
        bg: True = tô màu nền

    Returns:
        Chuỗi đã có escape code màu
    """
    if not COLOR_CONFIG.get("enable", True):
        return char
    ansi = rgb_to_ansi(r, g, b, background=bg or COLOR_CONFIG.get("background", False))
    return f"{ansi}{char}\033[0m"


def strip_ansi(text: str) -> str:
    """Xoá tất cả escape sequences ANSI khỏi chuỗi."""
    return re.sub(r'\033\[[0-9;]*m', '', text)


def iter_colored_chars(text: str):
    """Duyệt chuỗi ASCII có màu, trả về (char, r, g, b) cho từng ký tự.

    Giữ current color khi gặp reset code, parse 24-bit ANSI.
    Default color: (255, 255, 255).

    Yields:
        (char, r, g, b) tuples
    """
    current_color = (255, 255, 255)
    i = 0
    while i < len(text):
        if text[i] == '\033':
            # Tìm đến 'm'
            end = text.find('m', i)
            if end == -1:
                break
            seq = text[i:end + 1]
            # Reset
            if seq == '\033[0m':
                current_color = (255, 255, 255)
            # 24-bit foreground
            elif seq.startswith('\033[38;2;'):
                parts = seq[7:-1].split(';')  # bỏ '\033[38;2;' và 'm'
                if len(parts) == 3:
                    try:
                        current_color = (int(parts[0]), int(parts[1]), int(parts[2]))
                    except ValueError:
                        pass
            # 24-bit background — bỏ qua cho PNG
            i = end + 1
        else:
            yield (text[i], *current_color)
            i += 1


def get_color_map(key: str) -> tuple[int, int, int]:
    """Lấy màu từ color map (cho thông báo đặc biệt)."""
    return COLOR_CONFIG.get("color_map", {}).get(key, (255, 255, 255))
