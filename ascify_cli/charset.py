"""
charset.py - Bộ ký tự cho Ascify-CLI
Quản lý và ánh xạ độ sáng → ký tự ASCII
"""

from .config import CHARSET_CONFIG


def get_charset(name: str | None = None) -> str:
    """Lấy bộ ký tự theo tên. Nếu None, dùng mặc định."""
    if name is None:
        name = CHARSET_CONFIG["default"]
    charsets = CHARSET_CONFIG["charset"]
    if name not in charsets:
        name = CHARSET_CONFIG["default"]
    return charsets[name]


def get_char(value: float, charset_name: str | None = None, invert: bool | None = None) -> str:
    """Ánh xạ giá trị 0.0–1.0 thành một ký tự trong bộ charset.

    Args:
        value: Giá trị độ sáng 0.0 (đen) → 1.0 (trắng)
        charset_name: Tên bộ ký tự
        invert: Đảo ngược (True = value càng cao → ký tự càng thưa)

    Returns:
        Ký tự ASCII tương ứng
    """
    charset = get_charset(charset_name)
    if invert is None:
        invert = CHARSET_CONFIG.get("invert", False)

    if invert:
        value = 1.0 - value

    # Clamp
    value = max(0.0, min(1.0, value))

    idx = int(value * (len(charset) - 1))
    return charset[idx]


def list_charsets() -> dict[str, str]:
    """Trả về dict {tên: charset}."""
    return dict(CHARSET_CONFIG["charset"])
