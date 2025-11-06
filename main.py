from fastapi import FastAPI, HTTPException, Query, UploadFile, File, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi import APIRouter
import asyncpg
from datetime import date, datetime
from dotenv import load_dotenv
from typing import List
from pathlib import Path
import os

load_dotenv()

from database import db
from models import EventResponse
from config import settings
from image_service import ImageService

app = FastAPI(title="Mestio API", version="1.0.0")

# Создаем роутер для событий
router = APIRouter(prefix="/api/v1/events")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Монтируем статику для отдачи изображений
app.mount(
    "/static/images",
    StaticFiles(directory=settings.IMAGE_UPLOAD_DIR),
    name="static_images",
)


# Зависимости
def get_image_service():
    return ImageService(settings.IMAGE_UPLOAD_DIR)


# События запуска/остановки
@app.on_event("startup")
async def startup():
    await db.connect()


@app.on_event("shutdown")
async def shutdown():
    await db.disconnect()


# Эндпоинт для получения событий по датам
@app.get(
    "/events/by-dates",
    response_model=List[EventResponse],
    summary="Получить события по датам",
    description="""
    Этот эндпоинт возвращает список событий для указанных дат.
    
    **Особенности:**
    - Поддерживает множественные даты
    - Возвращает полную информацию о событиях
    - Автоматически форматирует даты в ISO-формат
    """,
    response_description="Список событий с детальной информацией",
    tags=["События"],
)
async def get_events_by_dates(
    dates: List[date] = Query(
        ...,
        description="Список дат в формате YYYY-MM-DD, например: ['2023-08-01', '2023-08-02']",
    ),
):
    """
    Получить события по списку дат
    """
    try:
        # Вызываем хранимую процедуру
        result = await db.execute_procedure("get_events_by_dates", dates)

        # Преобразуем даты в строки
        formatted_result = []
        for record in result:
            record_dict = dict(record)
            # Преобразуем datetime в строку
            if isinstance(record_dict.get("event_start_date"), datetime):
                record_dict["event_start_date"] = record_dict[
                    "event_start_date"
                ].isoformat()
            # Преобразуем date в строку
            if isinstance(record_dict.get("event_date"), date):
                record_dict["event_date"] = record_dict["event_date"].isoformat()
            formatted_result.append(record_dict)

        return formatted_result

    except asyncpg.exceptions.PostgresError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# Эндпоинты для работы с изображениями событий с использованием хранимых процедур
@router.post(
    "/{event_id}/images",
    summary="Загрузить изображение для события",
    description="Загружает изображение для указанного события",
    tags=["Изображения событий"],
)
async def upload_event_image(
    event_id: int,
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
    file_extension = Path(file.filename).suffix.lower()
    file_path = image_service.generate_file_path(event_id, file_extension)

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
            False,  # is_primary
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


# Регистрируем роутер
app.include_router(router)
