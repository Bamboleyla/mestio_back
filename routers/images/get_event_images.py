from fastapi import APIRouter, HTTPException
from typing import List
import asyncpg
from database import db
from .models import ImageResponse


router = APIRouter()


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
