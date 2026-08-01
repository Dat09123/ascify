"""
cli.py - Xử lý dòng lệnh cho Ascify-CLI
Sử dụng argparse để parse arguments
"""

import argparse
import sys
from pathlib import Path

from .config import CHARSET_CONFIG, COLOR_CONFIG, VIDEO_CONFIG, EXPORT_CONFIG, IMAGE_CONFIG


def create_parser() -> argparse.ArgumentParser:
    """Tạo argument parser với tất cả options."""
    parser = argparse.ArgumentParser(
        prog="ascify",
        description="🖼 Ascify-CLI - Chuyển đổi ảnh/video/webcam thành ASCII Art",
        epilog="Ví dụ:\n"
               "  ascify image input.jpg              # Ảnh → ASCII\n"
               "  ascify image input.jpg -w 100 -c    # Màu sắc\n"
               "  ascify video input.mp4 --play       # Phát video\n"
               "  ascify webcam                       # Webcam realtime\n"
               "  ascify image input.jpg -o out.html  # Xuất HTML",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Lệnh")

    # ===== IMAGE =====
    img_parser = subparsers.add_parser("image", help="Chuyển ảnh → ASCII")
    img_parser.add_argument("input", help="Đường dẫn ảnh đầu vào")
    img_parser.add_argument("-o", "--output", help="Đường dẫn đầu ra (không extension)")
    img_parser.add_argument("-f", "--format", choices=EXPORT_CONFIG["format"], default=None,
                            help="Định dạng xuất (txt, html, png, ansi)")
    img_parser.add_argument("-w", "--width", type=int, default=None,
                            help=f"Chiều rộng ASCII (mặc định: {IMAGE_CONFIG['default_width']})")
    img_parser.add_argument("--height", type=int, default=None,
                            help=f"Chiều cao ASCII (mặc định: auto theo tỷ lệ)")
    img_parser.add_argument("-c", "--color", action="store_true", default=None,
                            help="Bật màu ANSI")
    img_parser.add_argument("--no-color", action="store_true", default=None,
                            help="Tắt màu")
    img_parser.add_argument("--charset", choices=list(CHARSET_CONFIG["charset"].keys()),
                            default=None, help="Bộ ký tự")
    img_parser.add_argument("-i", "--invert", action="store_true", default=None,
                            help="Đảo ngược màu")
    img_parser.add_argument("--no-invert", action="store_true", default=None,
                            help="Ép KHÔNG đảo ngược (bỏ auto-invert trên ảnh tối)")
    img_parser.add_argument("-b", "--braille", action="store_true",
                            help="Chế độ Braille Unicode")
    img_parser.add_argument("--block", action="store_true",
                            help="Chế độ Block Unicode")
    img_parser.add_argument("--ascii", action="store_true",
                            help="Ép dùng ASCII kể cả ảnh lớn (bỏ auto Unicode)")
    img_parser.add_argument("--no-dither", action="store_true",
                            help="Tắt dithering braille (mặc định bật)")
    img_parser.add_argument("--threshold", type=int, default=None,
                            help="Ngưỡng bật/tắt dot braille 0-255 (mặc định 128)")
    img_parser.add_argument("--list-charsets", action="store_true",
                            help="Liệt kê các bộ ký tự có sẵn")

    # ===== VIDEO =====
    vid_parser = subparsers.add_parser("video", help="Chuyển video → ASCII")
    vid_parser.add_argument("input", help="Đường dẫn video đầu vào")
    vid_parser.add_argument("--play", action="store_true",
                            help="Phát video ASCII realtime trên terminal")
    vid_parser.add_argument("-o", "--output-dir", default="output",
                            help="Thư mục xuất frames")
    vid_parser.add_argument("-f", "--format", choices=EXPORT_CONFIG["format"],
                            default="txt", help="Định dạng xuất")
    vid_parser.add_argument("-w", "--width", type=int, default=80,
                            help="Chiều rộng ASCII")
    vid_parser.add_argument("-c", "--color", action="store_true", default=None,
                            help="Bật màu")
    vid_parser.add_argument("--no-color", action="store_true", default=None,
                            help="Tắt màu")
    vid_parser.add_argument("--charset", choices=list(CHARSET_CONFIG["charset"].keys()),
                            default=None, help="Bộ ký tự")
    vid_parser.add_argument("--max-frames", type=int, default=None,
                            help="Số frame tối đa")
    vid_parser.add_argument("--frame-skip", type=int, default=None,
                            help="Bỏ qua N frame giữa mỗi lần xử lý")

    # ===== WEBCAM =====
    webcam_parser = subparsers.add_parser("webcam", help="Webcam ASCII realtime")
    webcam_parser.add_argument("--camera-id", type=int, default=None,
                               help=f"ID webcam (mặc định: {VIDEO_CONFIG.get('webcam_id', 0)})")
    webcam_parser.add_argument("-w", "--width", type=int, default=80,
                               help="Chiều rộng ASCII")
    webcam_parser.add_argument("-c", "--color", action="store_true", default=None,
                               help="Bật màu")
    webcam_parser.add_argument("--no-color", action="store_true", default=None,
                               help="Tắt màu")
    webcam_parser.add_argument("--charset", choices=list(CHARSET_CONFIG["charset"].keys()),
                               default=None, help="Bộ ký tự")
    webcam_parser.add_argument("-b", "--braille", action="store_true",
                               help="Chế độ Braille Unicode")
    webcam_parser.add_argument("--block", action="store_true",
                               help="Chế độ Block Unicode")

    # ===== BENCHMARK =====
    bench_parser = subparsers.add_parser("benchmark", help="Benchmark hiệu năng")
    bench_parser.add_argument("input", help="Đường dẫn ảnh benchmark")
    bench_parser.add_argument("-n", "--iterations", type=int, default=None,
                              help="Số lần lặp")
    bench_parser.add_argument("--duration", type=float, default=5.0,
                              help="Thời gian chạy benchmark (giây)")

    return parser


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    """Parse arguments và validate.

    Returns:
        Namespace đã parse
    """
    parser = create_parser()
    parsed = parser.parse_args(args)

    if parsed.command is None:
        parser.print_help()
        sys.exit(1)

    return parsed


def resolve_color(args: argparse.Namespace) -> bool:
    """Xác định có bật màu không dựa trên args và config."""
    if hasattr(args, 'color') and args.color:
        return True
    if hasattr(args, 'no_color') and args.no_color:
        return False
    return COLOR_CONFIG.get("enable", True)
