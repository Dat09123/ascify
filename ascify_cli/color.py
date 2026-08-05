"""
color.py - Màu ANSI RGB cho Ascify-CLI
Hỗ trợ 24-bit true color trong terminal
"""

import os
import re
import sys

from .config import COLOR_CONFIG


def supports_truecolor() -> bool:
    """Kiểm tra terminal có hỗ trợ màu 24-bit (truecolor) hay không.

    Heuristic an toàn (tránh báo động giả trên terminal hiện đại):
      - `NO_COLOR` được set hoặc `TERM=dumb` → chắc chắn không hỗ trợ.
      - `COLORTERM=truecolor|24bit` hoặc TERM chứa truecolor/direct/24bit → có.
      - `COLORTERM` set nhưng là giá trị không phải 256-color (vd "16color") → coi là không.
      - Còn lại mặc định True (hầu hết terminal hiện đại đều hỗ trợ truecolor).
    """
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("TERM") == "dumb":
        return False

    colorterm = os.environ.get("COLORTERM", "").lower()
    term = os.environ.get("TERM", "").lower()
    if colorterm in ("truecolor", "24bit"):
        return True
    if "truecolor" in term or "direct" in term or "24bit" in term:
        return True
    if colorterm and colorterm not in ("", "8bit", "256color"):
        return False  # COLORTERM lạ → không chắc hỗ trợ truecolor
    return True


def init_ansi() -> None:
    """Bật hỗ trợ ANSI escape codes trên Windows (cmd.exe/PowerShell cũ).

    Linux/macOS và Windows Terminal mới đã hỗ trợ ANSI mặc định nên hàm này
    là no-op. Trên Windows cũ, dùng colorama (đã là dependency trong
    pyproject.toml) để bật VT processing — không có màu sẽ vỡ/ra ký tự rác.

    safe: không raise lỗi nếu colorama không cài.
    """
    if sys.platform != "win32":
        return
    try:
        import colorama

        # colorama >= 0.4.6 có just_fix_windows_console (không wrap streams)
        fix = getattr(colorama, "just_fix_windows_console", None)
        if fix:
            fix()
        else:
            colorama.init()
    except ImportError:
        pass  # Không có colorama → giữ nguyên hành vi cũ, không crash


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
