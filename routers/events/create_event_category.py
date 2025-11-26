from fastapi import APIRouter, HTTPException
import asyncpg
import logging
from database import db
from .models import EventCategoryRequest


router = APIRouter()


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
