from fastapi import APIRouter, Query, HTTPException
from datetime import date, datetime
from typing import List
from database import db
from models import (
    EventCategoryRequest,
    EventCategoryResponse,
    EventRequest,
    EventByDateResponse,
    EventDetailsFullResponse,
)
from typing import List
import asyncpg
import logging
import json

# Создаем роутер для событий
router = APIRouter(prefix="/api/v1/events")


# Эндпоинт для получения событий по дате
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


# Эндпоинт для создания новой категории события
@router.post(
    "/categories",
    response_model=int,
    status_code=201,
    summary="Создать новую категорию события",
    description="""
    Этот эндпоинт создает новую категорию события с помощью хранимой процедуры.
    
    **Особенности:**
    - Возвращает ID созданной категории
    - Автоматически валидирует уникальность названия
    - Проверяет максимальную длину названия (50 символов)
    - В случае дублирования возвращает ошибку 409
    """,
    response_description="ID созданной категории события",
    tags=["Категории"],
)
async def create_event_category(category: EventCategoryRequest):
    """
    Создать новую категорию события
    """
    try:
        # Вызываем функцию для добавления категории
        category_id = await db.execute_function(
            "add_event_category_func", category.category_name
        )
        return category_id

    except asyncpg.exceptions.UniqueViolationError:
        raise HTTPException(
            status_code=409,
            detail=f"Категория с именем '{category.category_name}' уже существует",
        )
    except asyncpg.exceptions.PostgresError as e:
        logging.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        logging.error(f"Internal server error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# Эндпоинт для создания нового события
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


# Эндпоинт для получения всех категорий событий
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


# Эндпоинт для получения детальной информации о событии
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
        ..., description="Дата для определения расписания работы локации"
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
