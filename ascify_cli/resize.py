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
    mode: str = "ascii",
) -> Image.Image:
    """Resize ảnh về kích thước mong muốn.

    Nếu giữ tỷ lệ, chỉ dùng width để tính height tự động.
    Hệ số bù chiều cao ký tự phụ thuộc chế độ render:
      - "ascii": mỗi ký tự ~1 pixel, ký tự cao hơn rộng → 0.45
      - "braille"/"block": ký tự lấy mẫu 2x4 / 2x1 pixel → 1.0

    Args:
        image: Ảnh Pillow đầu vào
        width: Chiều rộng mong muốn (pixel)
        height: Chiều cao mong muốn (pixel)
        keep_aspect_ratio: Giữ tỷ lệ khung hình
        mode: Chế độ render ("ascii", "braille", "block")

    Returns:
        Ảnh đã resize
    """
    if keep_aspect_ratio is None:
        keep_aspect_ratio = IMAGE_CONFIG.get("keep_aspect_ratio", True)

    orig_w, orig_h = image.size

    if width is None and height is None:
        if mode in ("braille", "block"):
            # Unicode mode: chỉ lấy width mặc định, height tính theo tỷ lệ
            # (vì ký tự braille/block lấy mẫu 2x4/2x1 px, không nên ép 120x40)
            width = IMAGE_CONFIG["default_width"]
            height = None
        else:
            width = IMAGE_CONFIG["default_width"]
            height = IMAGE_CONFIG["default_height"]

    factor = 1.0 if mode in ("braille", "block") else 0.45

    # Mỗi ký tự lấy mẫu bao nhiêu pixel theo chế độ:
    #   ascii:   1x1 (1 char = 1px)
    #   braille: 2x4 (1 char = block 2 cột x 4 hàng pixel)
    #   block:   1x2 (1 char = 1 cột x 2 hàng pixel)
    char_w = 2 if mode == "braille" else 1
    char_h = 4 if mode == "braille" else (2 if mode == "block" else 1)

    if keep_aspect_ratio:
        if width and not height:
            # Tự động tính height từ width với hệ số bù chiều cao ký tự
            ratio = width / orig_w
            height = int(orig_h * ratio * factor)
        elif height and not width:
            # Tự động tính width từ height
            ratio = height / orig_h
            width = int(orig_w * ratio / factor)
        # else: cả width và height đều có — dùng nguyên, không override
    else:
        if width is None:
            width = orig_w
        if height is None:
            height = orig_h

    # Clamp theo mode: clamp được thiết kế cho ASCII (1 char = 1px), nên
    # nhân với hệ số lấy mẫu. Trước đây braille bị bẹp vì max_height 200px
    # = chỉ 50 hàng braille — ảnh landscape mất tỷ lệ và chi tiết.
    width = max(
        IMAGE_CONFIG["min_width"] * char_w,
        min(width, IMAGE_CONFIG["max_width"] * char_w),
    )
    height = max(
        IMAGE_CONFIG["min_height"] * char_h,
        min(height, IMAGE_CONFIG["max_height"] * char_h),
    )

    return image.resize((int(width), int(height)), Image.LANCZOS)
