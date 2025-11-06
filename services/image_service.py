import uuid
from pathlib import Path
from PIL import Image
import io


class ImageService:
    def __init__(self, upload_dir: Path):
        self.upload_dir = upload_dir
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def generate_file_path(self, event_id: int, extension: str) -> str:
        """Генерирует уникальный путь к файлу"""
        unique_name = f"{uuid.uuid4()}{extension}"
        return f"events/{event_id}/{unique_name}"

    def compress_image(self, image_data: bytes, quality: str, max_size: tuple) -> bytes:
        """Сжимает изображение до нужного размера"""
        image = Image.open(io.BytesIO(image_data))

        # Конвертируем в RGB если нужно
        if image.mode in ("RGBA", "P"):
            image = image.convert("RGB")

        # Ресайз с сохранением пропорций
        image.thumbnail(max_size, Image.Resampling.LANCZOS)

        # Сохраняем в буфер
        output = io.BytesIO()
        image.save(output, format="JPEG", quality=85, optimize=True)
        return output.getvalue()

    def save_image(self, file_path: str, image_data: bytes):
        """Сохраняет изображение на диск"""
        full_path = self.upload_dir / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)

        with open(full_path, "wb") as f:
            f.write(image_data)

    def delete_image(self, file_path: str):
        """Удаляет изображение"""
        full_path = self.upload_dir / file_path
        if full_path.exists():
            full_path.unlink()
