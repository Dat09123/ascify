# config.py
"""
Cấu hình trung tâm cho Ascify-CLI
Tất cả tham số có thể tùy chỉnh đều được đặt tại đây
"""

IMAGE_CONFIG = {
    "default_width": 120,
    "default_height": 40,
    "min_width": 10,
    "min_height": 10,
    "max_width": 500,
    "max_height": 200,
    "keep_aspect_ratio": True,
    "background_color": (0, 0, 0),
    # Ảnh có cạnh nhỏ hơn ngưỡng này (icon, logo, meme nhỏ) → dùng ASCII.
    # Ảnh lớn hơn (ảnh chụp, art cao phân giải) → tự chuyển sang Unicode/Braille.
    "auto_unicode_min_size": 400,
    # Phân loại ảnh "nhiều màu" (photo) để tự bật màu true-color:
    #   auto_color_min_saturation:  bão hoà HSV trung bình tối thiểu (0-255)
    #   auto_color_min_hue_buckets: số hue buckets riêng biệt tối thiểu
    #     (photo thật có NHIỀU hue; anime/manga palette giới hạn → ít hue,
    #      dù saturation cao vẫn giữ negative style)
    "auto_color_min_saturation": 40,
    "auto_color_min_hue_buckets": 12,
}

CHARSET_CONFIG = {
    "charset": {
        "standard": " .:-=+*#%@",
        "detailed": " .'`^\",:;Il!i><~+_-?][}{1)(|\\/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$",
        "block": " ░▒▓█",
        "braille": " ⡀⡄⡆⡇⣇⣧⣷⣿",
        "numbers": " 123456789#",
        "letters": "  abcdefghijklmnopqrstuvwxyz#",
    },
    "default": "standard",
    "invert": False,
}

COLOR_CONFIG = {
    "enable": True,
    "background": False,
}

VIDEO_CONFIG = {
    "fps": 30,
    "webcam_id": 0,
    "max_frames": 1000,
    "frame_skip": 1,
    "real_time": True,
    "snapshot_dir": "output/",
}

EXPORT_CONFIG = {
    "format": ["txt", "html", "png", "ansi"],
    "default_format": "txt",
    "html": {
        "font_family": "monospace",
        "font_size": "12px",
        "background": "#000000",
        "color": "#00ff00",
    },
    "png": {
        "font_size": 14,
        "font_path": None,
        "background_color": (0, 0, 0),
        "color": (255, 255, 255),
    },
    "txt": {
        "encoding": "utf-8",
        "newline": "\n",
    },
}

PERFORMANCE_CONFIG = {
    "benchmark_iterations": 100,
}

UNICODE_CONFIG = {
    "enable": True,
    "braille_mode": False,
    "block_mode": False,
    "braille_dither": True,    # Dithering Floyd-Steinberg cho braille (giữ chi tiết)
    "braille_threshold": 128,  # Ngưỡng bật/tắt dot braille (0-255)
}
