"""
grayscale.py - Chuyển đổi ảnh sang grayscale (Ascify-CLI)
"""

from PIL import Image


def to_grayscale(image: Image.Image) -> Image.Image:
    """Chuyển ảnh màu sang grayscale.

    Args:
        image: Ảnh Pillow đầu vào (RGB hoặc RGBA)

    Returns:
        Ảnh grayscale (mode 'L')
    """
    if image.mode == "L":
        return image
    if image.mode == "RGBA":
        # Convert RGBA → RGB → L
        background = Image.new("RGB", image.size, (0, 0, 0))
        background.paste(image, mask=image.split()[3])
        return background.convert("L")
    return image.convert("L")


def get_pixels(image: Image.Image) -> list[list[int]]:
    """Lấy ma trận pixel grayscale 2D từ ảnh.

    Returns:
        List 2D các giá trị 0–255
    """
    gray = to_grayscale(image)
    w, h = gray.size
    pixels = list(gray.getdata())
    return [pixels[i * w:(i + 1) * w] for i in range(h)]
