from fastapi import APIRouter, HTTPException, Depends
from database import db
from services.image_service import ImageService
from services.config import settings
import asyncpg


def get_image_service():
    return ImageService(settings.IMAGE_UPLOAD_DIR)


router = APIRouter()


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
