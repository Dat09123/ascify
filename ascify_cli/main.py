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

    # List charsets — không cần file ảnh, check TRƯỚC khi validate input
    if args.list_charsets:
        print("\n📖 Các bộ ký tự có sẵn:\n")
        for name, charset in list_charsets().items():
            print(f"  {name:<12} {charset}")
        print()
        return

    # Kiểm tra file
    input_path = args.input
    if not input_path:
        print("❌ Thiếu file ảnh đầu vào")
        sys.exit(1)
    if not os.path.exists(input_path):
        print(f"❌ File không tồn tại: {input_path}")
        sys.exit(1)

    # Load ảnh
    try:
        image = Image.open(input_path)
        print(f"📷 Ảnh: {input_path} ({image.size[0]}x{image.size[1]})")
    except Exception as e:
        print(f"❌ Lỗi đọc ảnh: {e}")
        sys.exit(1)

    # Xác định màu
    enable_color = resolve_color(args)

    # Xác định invert: -i ưu tiên, kế đến --no-invert, còn lại None (auto)
    if args.invert:
        invert = True
    elif args.no_invert:
        invert = False
    else:
        invert = None

    # Auto chọn chế độ theo độ phân giải:
    #   Ảnh nhỏ (icon/logo) → ASCII
    #   Ảnh lớn (ảnh chụp, art cao phân giải) → Unicode/Braille
    width = args.width
    height = args.height
    braille_mode = args.braille
    block_mode = args.block
    # --charset chỉ có ý nghĩa với ASCII, nên nó ngầm ép dùng ASCII
    if not braille_mode and not block_mode and not args.ascii and not args.charset:
        w, h = image.size
        if max(w, h) >= IMAGE_CONFIG.get("auto_unicode_min_size", 400):
            braille_mode = True
            # Ảnh lớn chi tiết: tự fit CẢ chiều rộng lẫn chiều cao vào terminal
            # (trước chỉ fit chiều rộng → ảnh dọc tràn màn hình "quá to khó nhìn")
            if width is None and height is None:
                import shutil
                term = shutil.get_terminal_size()
                # os.terminal_size có thuộc tính .columns và .lines (không phải .rows)
                max_cols = max(10, term.columns - 2)
                max_rows = max(10, term.lines - 4)
                # Braille: grid rows ≈ orig_h * width / (2 * orig_w)
                # (1 ký tự braille = block 2x4 px)
                width_fit_rows = int(max_rows * 2 * w / h) if h else max_cols
                width = min(max_cols, width_fit_rows, IMAGE_CONFIG["max_width"])
                width = max(10, width)

    # Ảnh màu (photo) → hiện true color thay vì auto-invert đen trắng:
    # chuẩn chafa/viu, ảnh chụp nhìn rõ ngay. Chỉ khi user không ép
    # (-i/--no-invert/--no-color). Áp dụng cho cả -b/--block rõ ràng.
    from .converter import _is_colorful
    if invert is None and enable_color and _is_colorful(image):
        invert = False

    # Convert — clamp ngưỡng dot braille về 0-255
    threshold = args.threshold
    if threshold is not None:
        threshold = max(0, min(255, threshold))

    ascii_art = image_to_ascii(
        image,
        width=width,
        height=height,
        charset_name=args.charset,
        invert=invert,
        enable_color=enable_color,
        braille_mode=braille_mode,
        block_mode=block_mode,
        force_color=bool(args.color),
        dither=None if not args.no_dither else False,
        threshold=threshold,
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
