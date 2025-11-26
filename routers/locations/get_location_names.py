from fastapi import APIRouter, HTTPException
from typing import List
import asyncpg
from database import db
from .models import LocationNameResponse


router = APIRouter()


@router.get(
    "/names",
    response_model=List[LocationNameResponse],
    summary="Получить названия локаций",
    description="""Этот эндпоинт возвращает список ID и названий всех локаций из таблицы locations.""",
    response_description="Список ID и названий локаций",
    tags=["Локации"],
)
async def get_location_names():
    """
    Получить ID и названия всех локаций
    """
    try:
        # Запрос для получения ID и названий локаций
        query = "SELECT id, name FROM locations ORDER BY name"
        result = await db.fetch(query)

        # Преобразуем результат в список словарей для совместимости с Pydantic
        locations = []
        for record in result:
            locations.append({"id": record["id"], "name": record["name"]})

        return locations

    except asyncpg.exceptions.PostgresError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
