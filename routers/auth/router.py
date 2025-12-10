from fastapi import APIRouter, Query, HTTPException, status, Request
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address
from database import db


class CheckEmailResponse(BaseModel):
    available: bool


class ErrorResponse(BaseModel):
    error: str
    message: str


router = APIRouter(prefix="/auth", tags=["Аутентификация"])

# Инициализация лимитера
limiter = Limiter(key_func=get_remote_address)


# Эндпоинт проверки email
@router.get(
    "/check-email",
    summary="Проверка доступности email",
    description="Проверяет, занят ли указанный email в системе",
    response_model=CheckEmailResponse,
    responses={
        200: {
            "description": "Email проверен успешно",
            "model": CheckEmailResponse,
            "content": {
                "application/json": {
                    "examples": {
                        "email_available": {
                            "summary": "Email доступен",
                            "value": {"available": True},
                        },
                        "email_not_available": {
                            "summary": "Email недоступен",
                            "value": {"available": False},
                        },
                    }
                }
            },
        },
        400: {"description": "Ошибка валидации", "model": ErrorResponse},
        422: {
            "description": "Некорректный формат email",
            "model": ErrorResponse,
        },
        500: {"description": "Внутренняя ошибка сервера", "model": ErrorResponse},
    },
)
@limiter.limit("20/hour")
async def check_email(
    request: Request,  # Добавляем параметр request для rate limiting
    email: str = Query(
        ..., description="Email для проверки (макс. 100 символов)", max_length=100
    ),
) -> CheckEmailResponse:
    """
    Проверяет уникальность email перед регистрацией
    """
    # Валидация email
    if not email or email.strip() == "":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "validation_error",
                "message": "Email не может быть пустым",
            },
        )

    # Приведение email к нижнему регистру
    email = email.lower().strip()

    # Проверка формата email с использованием email-validator
    from email_validator import validate_email, EmailNotValidError

    try:
        validated_email = validate_email(email)
        email = validated_email.email
    except EmailNotValidError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "error": "validation_error",
                "message": "Некорректный формат email",
            },
        )

    # Вызов хранимой процедуры для проверки доступности email
    try:
        is_available = await db.execute_function("check_email_availability", email)
        return {"available": is_available}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "internal_error", "message": "Внутренняя ошибка сервера"},
        )


# Импортируем роутер регистрации
from .register import router as register_router

# Включаем роутер регистрации в основной роутер аутентификации
router.include_router(register_router)
