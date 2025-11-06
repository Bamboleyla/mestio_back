import os
from pathlib import Path


class Settings:
    IMAGE_UPLOAD_DIR = Path(os.getenv("IMAGE_UPLOAD_DIR", "uploads/images"))
    MAX_IMAGE_SIZE = 2 * 1024 * 1024  # 2MB
    ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}
    IMAGE_QUALITIES = {
        "original": (1200, 1200),
        "compressed": (800, 800),
        "thumbnail": (300, 300),
    }


settings = Settings()
