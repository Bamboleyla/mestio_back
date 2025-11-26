from fastapi import APIRouter, Query, HTTPException
from datetime import date
import asyncpg
import json
from database import db
from .models import EventDetailsFullResponse


router = APIRouter()


@router.get(
    "/{event_id}/details",
    response_model=EventDetailsFullResponse,
    summary="Получить детальную информацию о событии",
    description="""
    Этот эндпоинт возвращает детальную информацию о событии по его ID и дате, включая:
    - Основные данные события (название, описание, длительность, категория)
    - Информацию о локации (название, категория, адрес)
    - Время работы локации в указанный день недели
    - Список изображений события

    **Особенности:**
    - Возвращает полную информацию о событии и связанной локации
    - Использует хранимую процедуру `get_event_details` для получения данных
    - Время работы локации возвращается для дня недели, соответствующего переданной дате
    - Может возвращать null значения для необязательных полей
    """,
    response_description="Детальная информация о событии и локации в формате JSON",
    tags=["События"],
)
async def get_event_details(
    event_id: int,
    date: date = Query(
        ...,
        description="Дата для определения расписания работы локации в формате YYYY-MM-DD, например: 2025-11-25",
    ),
):
    """
    Получить детальную информацию о событии по его ID и дате
    """
    try:
        # Вызываем хранимую процедуру с ID события и датой
        result = await db.execute_procedure("get_event_details", event_id, date)

        # Проверяем, есть ли результат
        if result and len(result) > 0:
            # Результат процедуры - JSONB объект в первом столбце первой строки
            json_result = result[0][0] if result[0] and len(result[0]) > 0 else None

            if json_result:
                # Проверяем тип json_result и при необходимости десериализуем его
                if isinstance(json_result, str):
                    import json as json_module

                    json_result = json_module.loads(json_result)

                # Преобразуем JSONB результат в Pydantic модель для валидации и документирования
                return EventDetailsFullResponse(**json_result)
            else:
                # Если событие не найдено, возвращаем HTTP 404
                raise HTTPException(
                    status_code=404, detail=f"Событие с ID {event_id} не найдено"
                )
        else:
            # Если событие не найдено, возвращаем HTTP 404
            raise HTTPException(
                status_code=404, detail=f"Событие с ID {event_id} не найдено"
            )

    except asyncpg.exceptions.PostgresError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
