"""
benchmark.py - Đo hiệu năng (FPS) cho Ascify-CLI
Benchmark các cấu hình khác nhau để tối ưu tốc độ
"""

import time
from PIL import Image

from .converter import image_to_ascii


def benchmark_fps(
    image_path: str,
    width: int = 80,
    charset_name: str = "standard",
    enable_color: bool = False,
    duration: float = 5.0,
    iterations: int | None = None,
) -> float:
    """Đo FPS ổn định trong khoảng thời gian (hoặc số lần lặp).

    Args:
        image_path: Đường dẫn ảnh
        width: Chiều rộng ASCII
        charset_name: Tên bộ ký tự
        enable_color: Bật màu
        duration: Thời gian chạy (giây) — bỏ qua nếu có `iterations`
        iterations: Số lần lặp cố định (ưu tiên hơn `duration`)

    Returns:
        FPS trung bình
    """
    try:
        image = Image.open(image_path)
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        return 0.0

    start = time.perf_counter()
    count = 0

    if iterations is not None:
        for _ in range(iterations):
            image_to_ascii(
                image,
                width=width,
                charset_name=charset_name,
                enable_color=enable_color,
            )
        count = iterations
    else:
        while time.perf_counter() - start < duration:
            image_to_ascii(
                image,
                width=width,
                charset_name=charset_name,
                enable_color=enable_color,
            )
            count += 1

    elapsed = time.perf_counter() - start
    fps = count / elapsed if elapsed > 0 else 0.0

    mode = f"{iterations} iterations" if iterations is not None else f"{duration}s"
    print(f"\n⏱ Benchmark: {mode}, {count} conversions")
    print(f"   Width={width}, Charset={charset_name}, Color={enable_color}")
    print(f"   ⚡ {fps:.1f} FPS ({elapsed / max(1, count) * 1000:.3f}ms/op)")

    return fps
