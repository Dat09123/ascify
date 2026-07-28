"""
resize.py - Resize ảnh cho Ascify-CLI
Sử dụng Pillow để resize giữ/gỡ bỏ tỷ lệ khung hình
"""

from PIL import Image
from .config import IMAGE_CONFIG


def resize_image(
    image: Image.Image,
    width: int | None = None,
    height: int | None = None,
    keep_aspect_ratio: bool | None = None,
) -> Image.Image:
    """Resize ảnh về kích thước mong muốn.

    Nếu giữ tỷ lệ, chỉ dùng width để tính height tự động.
    ASCII art thường cần height = width // 2 vì ký tự cao hơn rộng.

    Args:
        image: Ảnh Pillow đầu vào
        width: Chiều rộng mong muốn (pixel)
        height: Chiều cao mong muốn (pixel)
        keep_aspect_ratio: Giữ tỷ lệ khung hình

    Returns:
        Ảnh đã resize
    """
    if keep_aspect_ratio is None:
        keep_aspect_ratio = IMAGE_CONFIG.get("keep_aspect_ratio", True)

    orig_w, orig_h = image.size

    if width is None and height is None:
        width = IMAGE_CONFIG["default_width"]
        height = IMAGE_CONFIG["default_height"]

    if keep_aspect_ratio:
        if width and not height:
            # Tự động tính height từ width với hệ số bù chiều cao ký tự
            ratio = width / orig_w
            height = int(orig_h * ratio * 0.45)  # 0.45 để bù chiều cao ký tự
        elif height and not width:
            # Tự động tính width từ height
            ratio = height / orig_h
            width = int(orig_w * ratio / 0.45)
        # else: cả width và height đều có — dùng nguyên, không override
    else:
        if width is None:
            width = orig_w
        if height is None:
            height = orig_h

    width = max(IMAGE_CONFIG["min_width"], min(width, IMAGE_CONFIG["max_width"]))
    height = max(IMAGE_CONFIG["min_height"], min(height, IMAGE_CONFIG["max_height"]))

    return image.resize((int(width), int(height)), Image.LANCZOS)
