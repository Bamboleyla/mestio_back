from fastapi import APIRouter, HTTPException
from datetime import datetime
from typing import List
import asyncpg
import logging
import json
from database import db
from .models import EventRequest


router = APIRouter()


@router.post(
    "/",
    response_model=int,
    status_code=201,
    summary="Создать новое событие",
    description="""
    Этот эндпоинт создает новое событие с помощью хранимой процедуры `add_event`.

    **Особенности:**
    - Возвращает ID созданного события
    - Автоматически валидирует все параметры
    - Проверяет существование локации и категории
    - Валидирует корректность расписания событий (даты и цены)
    - Проверяет уникальность названия события
    """,
    response_description="ID созданного события",
    tags=["События"],
)
async def create_event(event: EventRequest):
    """
    Создать новое событие
    """
    try:
        # Преобразуем расписание в JSONB
        def convert_schedule_dates_to_iso(schedule_list):
            """Преобразует даты в расписании в ISO строки для JSON сериализации"""
            result = []
            for schedule in schedule_list:
                schedule_dict = schedule.dict()
                if "date" in schedule_dict and isinstance(
                    schedule_dict["date"], datetime
                ):
                    schedule_dict["date"] = schedule_dict["date"].isoformat()
                result.append(schedule_dict)
            return result

        schedule_dates = json.dumps(convert_schedule_dates_to_iso(event.schedules))

        # Вызываем функцию для добавления события
        event_id = await db.execute_function(
            "add_event",
            event.title,
            event.location_id,
            event.category_id,
            event.description,
            event.duration,
            schedule_dates,
        )
        return event_id

    except HTTPException:
        # Перебрасываем HTTPException из базы данных (уже с правильным кодом)
        raise
    except Exception as e:
        logging.error(f"Internal server error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
