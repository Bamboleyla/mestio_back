from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from database import db
from services.image_service import ImageService
from services.config import settings
import asyncpg

# Создаем роутер для изображений
router = APIRouter(prefix="/api/v1/events")


# Зависимости
def get_image_service():
    return ImageService(settings.IMAGE_UPLOAD_DIR)


# Эндпоинты для работы с изображениями событий с использованием хранимых процедур
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


@router.get(
    "/{event_id}/images",
    summary="Получить изображения события",
    description="Возвращает список всех изображений для указанного события",
    tags=["Изображения событий"],
)
async def get_event_images(event_id: int):
    try:
        # Вызываем хранимую процедуру для получения изображений
        images = await db.execute_procedure("get_event_images", event_id)

        return [
            {
                "id": img["id"],
                "url": f"/static/images/{img['file_path']}",
                "file_name": img["file_name"],
                "file_size": img["file_size"],
                "width": img["width"],
                "height": img["height"],
                "image_quality": img["image_quality"],
                "sort_order": img["sort_order"],
                "is_primary": img["is_primary"],
                "created_at": (
                    img["created_at"].isoformat() if img["created_at"] else None
                ),
            }
            for img in images
        ]

    except asyncpg.exceptions.PostgresError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.delete(
    "/{event_id}/images/{image_id}",
    summary="Удалить изображение события",
    description="Удаляет указанное изображение события",
    tags=["Изображения событий"],
)
async def delete_event_image(
    event_id: int,
    image_id: int,
    image_service: ImageService = Depends(get_image_service),
):
    try:
        # Вызываем хранимую процедуру для удаления
        file_path = await db.execute_function("delete_event_image", image_id, event_id)

        if file_path:
            # Удаляем физический файл
            image_service.delete_image(file_path)
            return {"message": "Image deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Image not found")

    except asyncpg.exceptions.PostgresError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
