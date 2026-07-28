"""
benchmark.py - Đo hiệu năng (FPS) cho Ascify-CLI
Benchmark các cấu hình khác nhau để tối ưu tốc độ
"""

import time
from PIL import Image

from .config import PERFORMANCE_CONFIG
from .converter import image_to_ascii


def benchmark_image(
    image_path: str,
    iterations: int | None = None,
    widths: list[int] | None = None,
    charset_names: list[str] | None = None,
    color_modes: list[bool] | None = None,
) -> dict:
    """Benchmark hiệu năng chuyển đổi ảnh → ASCII.

    Args:
        image_path: Đường dẫn ảnh test
        iterations: Số lần lặp cho mỗi cấu hình
        widths: List chiều rộng cần test
        charset_names: List charset cần test
        color_modes: List chế độ màu cần test

    Returns:
        Dict kết quả benchmark
    """
    if iterations is None:
        iterations = PERFORMANCE_CONFIG.get("benchmark_iterations", 100)

    if widths is None:
        widths = [40, 80, 120]

    if charset_names is None:
        charset_names = ["standard", "detailed"]

    if color_modes is None:
        color_modes = [False, True]

    try:
        image = Image.open(image_path)
    except Exception as e:
        print(f"❌ Không thể mở ảnh: {e}")
        return {"error": str(e)}

    results = {}
    image.load()

    print(f"\n📊 Benchmark: {image_path} ({image.size[0]}x{image.size[1]})")
    print(f"   Iterations per config: {iterations}")
    print("-" * 60)
    print(f"{'Width':<8} {'Charset':<12} {'Color':<8} {'FPS':<10} {'Time/op':<10}")
    print("-" * 60)

    for width in widths:
        for charset in charset_names:
            for color in color_modes:
                times = []
                for _ in range(iterations):
                    start = time.perf_counter()
                    image_to_ascii(
                        image,
                        width=width,
                        charset_name=charset,
                        enable_color=color,
                    )
                    elapsed = time.perf_counter() - start
                    times.append(elapsed)

                avg_time = sum(times) / len(times)
                fps = 1.0 / avg_time

                key = f"w={width},charset={charset},color={color}"
                results[key] = {
                    "width": width,
                    "charset": charset,
                    "color": color,
                    "avg_time_ms": avg_time * 1000,
                    "fps": fps,
                    "min_ms": min(times) * 1000,
                    "max_ms": max(times) * 1000,
                }

                print(f"{width:<8} {charset:<12} {str(color):<8} {fps:<10.1f} {avg_time*1000:<10.3f}ms")

    print("-" * 60)

    # So sánh nhanh nhất
    best = min(results.values(), key=lambda r: r["avg_time_ms"])
    print(f"\n⚡ Nhanh nhất: width={best['width']}, charset={best['charset']}, color={best['color']}")
    print(f"   {best['fps']:.1f} FPS ({best['avg_time_ms']:.3f}ms mỗi lần)")

    return results


def benchmark_fps(
    image_path: str,
    width: int = 80,
    charset_name: str = "standard",
    enable_color: bool = False,
    duration: float = 5.0,
) -> float:
    """Đo FPS ổn định trong khoảng thời gian.

    Args:
        image_path: Đường dẫn ảnh
        width: Chiều rộng ASCII
        charset_name: Tên bộ ký tự
        enable_color: Bật màu
        duration: Thời gian chạy (giây)

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

    while time.perf_counter() - start < duration:
        image_to_ascii(
            image,
            width=width,
            charset_name=charset_name,
            enable_color=enable_color,
        )
        count += 1

    elapsed = time.perf_counter() - start
    fps = count / elapsed

    print(f"\n⏱ Benchmark: {duration}s, {count} iterations")
    print(f"   Width={width}, Charset={charset_name}, Color={enable_color}")
    print(f"   ⚡ {fps:.1f} FPS ({elapsed/count*1000:.3f}ms/op)")

    return fps
