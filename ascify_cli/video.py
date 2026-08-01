"""
video.py - Chuyển đổi video → ASCII Art (Ascify-CLI)
Sử dụng OpenCV để đọc file video và xuất ASCII frames
"""

import sys
import time
from pathlib import Path

from .config import VIDEO_CONFIG, EXPORT_CONFIG


try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False


def video_to_ascii(
    video_path: str,
    width: int = 80,
    charset_name: str = "standard",
    invert: bool | None = None,
    enable_color: bool = True,
    max_frames: int | None = None,
    frame_skip: int | None = None,
    export_format: str | None = None,
    output_dir: str | None = None,
    show_progress: bool = True,
) -> list[str]:
    """Chuyển video thành list ASCII frames.

    Args:
        video_path: Đường dẫn file video
        width: Chiều rộng ASCII
        charset_name: Tên bộ ký tự
        invert: Đảo ngược màu
        enable_color: Bật màu
        max_frames: Số frame tối đa
        frame_skip: Bỏ qua frame (1 = xử lý tất cả)
        export_format: Định dạng xuất (txt, html...)
        output_dir: Thư mục xuất
        show_progress: Hiển thị tiến trình

    Returns:
        List các frame ASCII dạng string
    """
    if not CV2_AVAILABLE:
        print("❌ OpenCV không khả dụng. Cài: pip install opencv-python")
        return []

    if max_frames is None:
        max_frames = VIDEO_CONFIG.get("max_frames", 1000)
    if frame_skip is None:
        frame_skip = VIDEO_CONFIG.get("frame_skip", 1)

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"❌ Không thể mở video: {video_path}")
        return []

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)

    print(f"🎬 Video: {Path(video_path).name}")
    print(f"   Frames: {total_frames}, FPS: {fps:.1f}")

    from .converter import image_to_ascii
    from PIL import Image

    frames = []
    frame_count = 0
    processed = 0

    while frame_count < max_frames:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_count % frame_skip == 0:
            # Convert BGR → RGB → Pillow
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(frame_rgb)

            ascii_art = image_to_ascii(
                pil_image,
                width=width,
                charset_name=charset_name,
                invert=invert,
                enable_color=enable_color,
            )
            frames.append(ascii_art)
            processed += 1

            if show_progress and processed % 10 == 0:
                pct = min(100, int(processed / max(1, max_frames // frame_skip) * 100))
                print(f"   ⏳ Đã xử lý: {processed} frames ({pct}%)")

        frame_count += 1

    cap.release()
    print(f"✅ Hoàn thành: {processed} frames")

    # Export nếu có yêu cầu
    if export_format and output_dir:
        _export_video_frames(frames, output_dir, export_format, fps)

    return frames


def _export_video_frames(
    frames: list[str],
    output_dir: str,
    fmt: str,
    fps: float,
) -> None:
    """Xuất các frame ASCII ra file."""
    from .exporter import export_ascii

    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    if fmt == "txt":
        output_file = out_path / "video_ascii.txt"
        with open(output_file, "w", encoding="utf-8") as f:
            for i, frame in enumerate(frames):
                f.write(f"=== Frame {i} ===\n")
                f.write(frame + "\n\n")
        print(f"📄 Đã xuất: {output_file}")
    elif fmt == "html":
        # HTML với animation bằng JS
        html = _generate_animation_html(frames, fps, width=80)
        output_file = out_path / "video_ascii.html"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"🌐 Đã xuất HTML animation: {output_file}")
    else:
        for i, frame in enumerate(frames):
            export_ascii(frame, str(out_path / f"frame_{i:04d}"), fmt)


def _generate_animation_html(frames: list[str], fps: float, width: int) -> str:
    """Tạo HTML với JavaScript animation cho video ASCII."""
    import json
    from .color import strip_ansi

    escaped_frames = []
    for f in frames:
        # Strip ANSI codes vì dùng textContent
        plain = strip_ansi(f)
        escaped = plain.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        escaped_frames.append(escaped)

    frames_json = json.dumps(escaped_frames)
    frame_delay = int(1000 / fps)

    return f"""<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<title>ASCII Video Animation</title>
<style>
  body {{ background: #000; color: #0f0; font-family: monospace; font-size: 10px; line-height: 1; }}
  pre {{ margin: 0; padding: 10px; white-space: pre; }}
</style>
</head>
<body>
<pre id="ascii-frame"></pre>
<script>
const frames = {frames_json};
let idx = 0;
const el = document.getElementById('ascii-frame');
function showFrame() {{
  el.textContent = frames[idx] || '';
  idx = (idx + 1) % frames.length;
}}
setInterval(showFrame, {frame_delay});
showFrame();
</script>
</body>
</html>"""


def play_video_ascii(
    video_path: str,
    width: int = 80,
    charset_name: str = "standard",
    invert: bool | None = None,
    enable_color: bool = True,
    fps_limit: int | None = None,
) -> None:
    """Phát video ASCII realtime trên terminal.

    Args:
        video_path: Đường dẫn file video
        width: Chiều rộng ASCII
        charset_name: Tên bộ ký tự
        invert: Đảo ngược màu
        enable_color: Bật màu
        fps_limit: Giới hạn FPS (None = dùng FPS gốc)
    """
    import shutil

    if not CV2_AVAILABLE:
        print("❌ OpenCV không khả dụng.")
        return

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"❌ Không thể mở video: {video_path}")
        return

    fps = cap.get(cv2.CAP_PROP_FPS) if fps_limit is None else fps_limit
    frame_time = 1.0 / fps
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    from .converter import image_to_ascii
    from PIL import Image

    term_width = shutil.get_terminal_size().columns
    if width > term_width:
        width = term_width - 2

    frame_count = 0
    print(f"\n🎬 Phát: {Path(video_path).name} ({total_frames} frames @ {fps:.1f}fps)")
    print("   Nhấn Ctrl+C để dừng.\n")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # Loop
                continue

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(frame_rgb)

            start = time.time()
            ascii_art = image_to_ascii(
                pil_image,
                width=width,
                charset_name=charset_name,
                invert=invert,
                enable_color=enable_color,
            )
            elapsed = time.time() - start

            # Clear screen và in frame
            sys.stdout.write("\033[H\033[J")  # Clear screen
            sys.stdout.write(ascii_art)
            sys.stdout.write(f"\n\033[0mFrame: {frame_count} | FPS: {1/elapsed:.1f}" if enable_color else f"\nFrame: {frame_count} | FPS: {1/elapsed:.1f}")
            sys.stdout.flush()

            sleep_time = max(0, frame_time - elapsed)
            time.sleep(sleep_time)
            frame_count += 1

    except KeyboardInterrupt:
        print("\n\n⏹ Đã dừng.")
    finally:
        cap.release()
