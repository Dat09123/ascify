"""
webcam.py - Webcam realtime ASCII Art (Ascify-CLI)
Sử dụng OpenCV để đọc webcam và hiển thị ASCII realtime
"""

import sys
import time
import threading
from dataclasses import dataclass, field
from queue import Queue

from config import VIDEO_CONFIG


try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False


@dataclass
class WebcamState:
    """Trạng thái webcam streaming."""
    running: bool = False
    fps: float = 0.0
    frame_count: int = 0
    current_ascii: str = ""
    error: str | None = None
    _queue: Queue = field(default_factory=Queue)


class WebcamASCII:
    """Stream webcam thành ASCII Art realtime."""

    def __init__(
        self,
        camera_id: int | None = None,
        width: int = 80,
        charset_name: str = "standard",
        invert: bool = False,
        enable_color: bool = True,
        braille_mode: bool = False,
        block_mode: bool = False,
    ):
        if not CV2_AVAILABLE:
            raise ImportError("OpenCV không khả dụng. Cài: pip install opencv-python")

        self.camera_id = camera_id if camera_id is not None else VIDEO_CONFIG.get("webcam_id", 0)
        self.width = width
        self.charset_name = charset_name
        self.invert = invert
        self.enable_color = enable_color
        self.braille_mode = braille_mode
        self.block_mode = block_mode
        self.state = WebcamState()
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()

    def start(self) -> bool:
        """Bắt đầu streaming webcam."""
        self.cap = cv2.VideoCapture(self.camera_id)
        if not self.cap.isOpened():
            self.state.error = f"Không thể mở webcam ID {self.camera_id}"
            return False

        self.state.running = True
        self._thread = threading.Thread(target=self._processing_loop, daemon=True)
        self._thread.start()
        return True

    def stop(self) -> None:
        """Dừng streaming."""
        self.state.running = False
        if self._thread:
            self._thread.join(timeout=2.0)
        if hasattr(self, 'cap') and self.cap:
            self.cap.release()
        print("\n⏹ Webcam đã dừng.")

    def _processing_loop(self) -> None:
        """Vòng lặp xử lý frame từ webcam."""
        from converter import image_to_ascii
        from PIL import Image

        prev_time = time.time()

        while self.state.running:
            ret, frame = self.cap.read()
            if not ret:
                self.state.error = "Mất kết nối webcam"
                break

            # Tính FPS
            current_time = time.time()
            self.state.fps = 1.0 / (current_time - prev_time + 0.0001)
            prev_time = current_time

            # Convert BGR → RGB → Pillow
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(frame_rgb)

            ascii_art = image_to_ascii(
                pil_image,
                width=self.width,
                charset_name=self.charset_name,
                invert=self.invert,
                enable_color=self.enable_color,
                braille_mode=self.braille_mode,
                block_mode=self.block_mode,
            )

            with self._lock:
                self.state.current_ascii = ascii_art
                self.state.frame_count += 1

    def get_frame(self) -> str | None:
        """Lấy frame ASCII hiện tại."""
        with self._lock:
            if self.state.current_ascii:
                return self.state.current_ascii
            return None


def run_webcam_interactive(
    camera_id: int | None = None,
    width: int = 80,
    charset_name: str = "standard",
    invert: bool = False,
    enable_color: bool = True,
    braille_mode: bool = False,
    block_mode: bool = False,
) -> None:
    """Chạy webcam ASCII interactive trên terminal.

    Hiển thị realtime với FPS counter.
    Nhấn Ctrl+C để thoát.
    """
    if not CV2_AVAILABLE:
        print("❌ OpenCV không khả dụng. Cài: pip install opencv-python")
        return

    import shutil

    term_width = shutil.get_terminal_size().columns
    if width > term_width:
        width = term_width - 2

    cam = WebcamASCII(
        camera_id=camera_id,
        width=width,
        charset_name=charset_name,
        invert=invert,
        enable_color=enable_color,
        braille_mode=braille_mode,
        block_mode=block_mode,
    )

    if not cam.start():
        print(f"❌ {cam.state.error}")
        return

    print(f"\n📷 Webcam ASCII - ID: {camera_id or VIDEO_CONFIG.get('webcam_id', 0)}")
    print("   Nhấn Ctrl+C để dừng.\n")

    try:
        while True:
            frame = cam.get_frame()
            if frame:
                sys.stdout.write("\033[H\033[J")  # Clear screen
                sys.stdout.write(frame)
                if enable_color:
                    sys.stdout.write(f"\n\033[0m📷 FPS: {cam.state.fps:.1f} | Frames: {cam.state.frame_count}")
                else:
                    sys.stdout.write(f"\n📷 FPS: {cam.state.fps:.1f} | Frames: {cam.state.frame_count}")
                sys.stdout.flush()
            time.sleep(0.03)  # ~30fps display
    except KeyboardInterrupt:
        pass
    finally:
        cam.stop()
