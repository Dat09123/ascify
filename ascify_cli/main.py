"""
main.py - Điểm bắt đầu của Ascify-CLI
Entry point: CLI + các chức năng chính
"""

import sys
import os
from pathlib import Path

from .config import IMAGE_CONFIG, EXPORT_CONFIG
from .cli import parse_args, resolve_color


def main() -> None:
    """Entry point chính."""
    args = parse_args()

    if args.command == "image":
        cmd_image(args)
    elif args.command == "video":
        cmd_video(args)
    elif args.command == "webcam":
        cmd_webcam(args)
    elif args.command == "benchmark":
        cmd_benchmark(args)
    else:
        from .cli import create_parser
        create_parser().print_help()


def cmd_image(args) -> None:
    """Xử lý lệnh 'image'."""
    from PIL import Image
    from .converter import image_to_ascii
    from .exporter import export_ascii
    from .charset import list_charsets

    # Kiểm tra file
    input_path = args.input
    if not os.path.exists(input_path):
        print(f"❌ File không tồn tại: {input_path}")
        sys.exit(1)

    # List charsets
    if args.list_charsets:
        print("\n📖 Các bộ ký tự có sẵn:\n")
        for name, charset in list_charsets().items():
            print(f"  {name:<12} {charset}")
        print()
        return

    # Load ảnh
    try:
        image = Image.open(input_path)
        print(f"📷 Ảnh: {input_path} ({image.size[0]}x{image.size[1]})")
    except Exception as e:
        print(f"❌ Lỗi đọc ảnh: {e}")
        sys.exit(1)

    # Xác định màu
    enable_color = resolve_color(args)

    # Convert
    ascii_art = image_to_ascii(
        image,
        width=args.width,
        height=args.height,
        charset_name=args.charset,
        invert=args.invert,
        enable_color=enable_color,
        braille_mode=args.braille,
        block_mode=args.block,
        force_color=bool(args.color),
    )

    # Output
    if args.output:
        fmt = args.format or EXPORT_CONFIG.get("default_format", "txt")
        export_ascii(ascii_art, args.output, fmt)
    else:
        # Print ra terminal
        print()
        print(ascii_art)
        if enable_color:
            print("\033[0m", end="")  # Reset màu
        print()


def cmd_video(args) -> None:
    """Xử lý lệnh 'video'."""
    from .video import video_to_ascii, play_video_ascii

    input_path = args.input
    if not os.path.exists(input_path):
        print(f"❌ File không tồn tại: {input_path}")
        sys.exit(1)

    enable_color = resolve_color(args)

    if args.play:
        # Phát realtime
        play_video_ascii(
            input_path,
            width=args.width,
            charset_name=args.charset,
            invert=None,
            enable_color=enable_color,
        )
    else:
        # Xuất frames
        video_to_ascii(
            input_path,
            width=args.width,
            charset_name=args.charset,
            invert=None,
            enable_color=enable_color,
            max_frames=args.max_frames,
            frame_skip=args.frame_skip,
            export_format=args.format,
            output_dir=args.output_dir,
        )


def cmd_webcam(args) -> None:
    """Xử lý lệnh 'webcam'."""
    from .webcam import run_webcam_interactive

    enable_color = resolve_color(args)

    run_webcam_interactive(
        camera_id=args.camera_id,
        width=args.width,
        charset_name=args.charset,
        invert=None,
        enable_color=enable_color,
        braille_mode=args.braille,
        block_mode=args.block,
        force_color=bool(args.color),
    )


def cmd_benchmark(args) -> None:
    """Xử lý lệnh 'benchmark'."""
    from .benchmark import benchmark_fps

    input_path = args.input
    if not os.path.exists(input_path):
        print(f"❌ File không tồn tại: {input_path}")
        sys.exit(1)

    benchmark_fps(
        input_path,
        duration=args.duration,
    )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Tạm biệt!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Lỗi: {e}")
        sys.exit(1)
