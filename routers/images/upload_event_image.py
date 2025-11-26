from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from database import db
from services.image_service import ImageService
from services.config import settings
import asyncpg
from .models import ImageResponse


# Зависимости
def get_image_service():
    return ImageService(settings.IMAGE_UPLOAD_DIR)


router = APIRouter()


@router.post(
    "/{event_id}/images/{is_primary}",
    summary="Загрузить изображение для события",
    description="Загружает изображение для указанного события",
    tags=["Изображения событий"],
)
async def upload_event_image(
    event_id: int,
    is_primary: bool,
    file: UploadFile = File(...),
    image_service: ImageService = Depends(get_image_service),
):
    # Валидация
    if file.content_type not in settings.ALLOWED_MIME_TYPES:
        raise HTTPException(400, "Invalid image type")

    # Чтение файла
    image_data = await file.read()
    if len(image_data) > settings.MAX_IMAGE_SIZE:
        raise HTTPException(400, "File too large")

    # Генерация пути
    file_extension = (
        file.filename.split(".")[-1].lower() if "." in file.filename else ".jpg"
    )
    file_path = image_service.generate_file_path(event_id, f".{file_extension}")

    # Создание сжатой версии
    compressed_data = image_service.compress_image(
        image_data, "compressed", settings.IMAGE_QUALITIES["compressed"]
    )

    # Получаем размеры изображения
    from PIL import Image
    import io

    image = Image.open(io.BytesIO(compressed_data))
    width, height = image.size

    try:
        # Сохранение в БД через хранимую процедуру
        image_id = await db.execute_function(
            "insert_event_image",
            event_id,
            file_path,
            "image/jpeg",  # Все конвертируем в JPEG
            file.filename,
            len(compressed_data),
            width,
            height,
            "compressed",
            0,  # sort_order
            is_primary,
        )

        # Сохраняем файл на диск только после успешного сохранения в БД
        image_service.save_image(file_path, compressed_data)

        return {
            "id": image_id,
            "url": f"/static/images/{file_path}",
            "file_name": file.filename,
            "file_size": len(compressed_data),
            "width": width,
            "height": height,
            "event_id": event_id,
        }

    except asyncpg.exceptions.PostgresError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
