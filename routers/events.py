from fastapi import APIRouter, Query, HTTPException
from datetime import date, datetime
from typing import List
from database import db
from models import EventResponse
import asyncpg

# Создаем роутер для событий
router = APIRouter(prefix="/api/v1/events")


# Эндпоинт для получения событий по датам
@router.get(
    "/by-dates",
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
