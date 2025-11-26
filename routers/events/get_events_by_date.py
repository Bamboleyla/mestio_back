from fastapi import APIRouter, Query, HTTPException
from datetime import date, datetime
from typing import List
import asyncpg
import json
from database import db
from .models import EventByDateResponse


router = APIRouter()


@router.get(
    "/by-date",
    response_model=List[EventByDateResponse],
    summary="Получить события по дате",
    description="""
    Этот эндпоинт возвращает список событий для указанной даты.

    **Особенности:**
    - Возвращает полную информацию о событиях
    - Включает дату, цену, название события, категорию, локацию и путь к изображению
    - Поле img_path может содержать строку с путем к изображению или null
    - Автоматически форматирует даты в ISO-формат
    """,
    response_description="Список событий с детальной информацией",
    tags=["События"],
)
async def get_events_by_date(
    search_date: date = Query(
        ...,
        description="Дата в формате YYYY-MM-DD, например: 2023-08-01",
    ),
):
    """
    Получить события по дате
    """
    try:
        # Вызываем хранимую процедуру
        result = await db.execute_procedure("get_events_by_date", search_date)

        # Результат уже в формате JSON, нужно его распарсить
        if result and len(result) > 0:
            # Получаем JSON-результат из первого столбца
            json_result = result[0][0] if result[0] and len(result[0]) > 0 else []
        else:
            json_result = []

        # Если результат - строка, то парсим как JSON
        if isinstance(json_result, str):
            import json as json_module

            json_result = json_module.loads(json_result)

        # Если результат - None, возвращаем пустой список
        if json_result is None:
            json_result = []

        # Конвертируем даты в ISO-формат, если нужно
        def convert_dates_to_iso(obj):
            """Рекурсивно преобразует объекты date и datetime в ISO строки"""
            if isinstance(obj, dict):
                return {key: convert_dates_to_iso(value) for key, value in obj.items()}
            elif isinstance(obj, list):
                return [convert_dates_to_iso(item) for item in obj]
            elif isinstance(obj, (date, datetime)):
                return obj.isoformat()
            else:
                return obj

        formatted_result = convert_dates_to_iso(json_result)

        return formatted_result

    except asyncpg.exceptions.PostgresError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
