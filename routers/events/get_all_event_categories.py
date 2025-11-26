from fastapi import APIRouter, HTTPException
from typing import List
import asyncpg
from database import db
from .models import EventCategoryResponse


router = APIRouter()


@router.get(
    "/categories",
    response_model=List[EventCategoryResponse],
    summary="Получить все категории событий",
    description="""
    Этот эндпоинт возвращает список всех категорий событий.

    **Особенности:**
    - Возвращает все записи из таблицы event_categories
    - Включает ID и название каждой категории
    """,
    response_description="Список всех категорий событий",
    tags=["Категории"],
)
async def get_all_event_categories():
    """
    Получить все категории событий
    """
    try:
        # Запрос для получения всех категорий
        query = "SELECT id, name FROM event_categories ORDER BY name"
        result = await db.fetch(query)

        # Преобразуем результат в список словарей для совместимости с Pydantic
        categories = []
        for record in result:
            categories.append({"id": record["id"], "name": record["name"]})

        return categories

    except asyncpg.exceptions.PostgresError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
