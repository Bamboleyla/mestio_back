from fastapi import APIRouter, Depends, HTTPException, status, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from pydantic import BaseModel, Field
import re
from datetime import datetime, timedelta
from jose import jwt
from jose.jwt import JWTError
import os
import secrets
import asyncio
from database import db
from models import UserResponse
from auth import get_password_hash

router = APIRouter(tags=["Аутентификация"])

# Инициализация лимитера
limiter = Limiter(key_func=get_remote_address)


# Модель для тела запроса регистрации
class RegisterRequest(BaseModel):
    email: str = Field(..., max_length=100, description="Email пользователя")
    password: str = Field(
        ..., min_length=8, max_length=40, description="Пароль пользователя"
    )


# Модель для ответа регистрации
class RegisterResponse(BaseModel):
    success: bool
    message: str
    user_id: int
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int


def validate_password(password: str) -> bool:
    """
    Валидация пароля по требованиям ТЗ:
    - Минимум 8 символов
    - Максимум 40 символов
    - Минимум 1 заглавная буква
    - Минимум 1 прописная буква
    - Минимум 1 цифра
    - Минимум 1 специальный символ
    """
    if len(password) < 8 or len(password) > 40:
        return False

    # Проверка наличия заглавной буквы
    if not re.search(r"[A-Z]", password):
        return False

    # Проверка наличия прописной буквы
    if not re.search(r"[a-z]", password):
        return False

    # Проверка наличия цифры
    if not re.search(r"\d", password):
        return False

    # Проверка наличия специального символа
    if not re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]', password):
        return False

    return True


@router.post(
    "/register",
    status_code=201,
    summary="Регистрация нового пользователя",
    description="""
    Регистрирует нового пользователя в системе.
    
    После успешной регистрации:
    - Создается учетная запись с ролью "user" (role_id = 1)
    - Отправляется welcome email с ссылкой для подтверждения
    - Пользователь автоматически входит в систему (возвращаются токены)
    - Аккаунт временно неактивен (is_active = false) до подтверждения email
    
    Ограничения:
    - Email должен быть уникальным
    - Пароль: 8-40 символов, минимум 1 заглавная, 1 строчная, 1 цифра, 1 спецсимвол
    """,
    response_description="Данные зарегистрированного пользователя и токены доступа",
    response_model=RegisterResponse,
)
@limiter.limit("20/hour")
async def register(request: Request, data: RegisterRequest):
    """
    Регистрация нового пользователя
    """
    # Валидация email
    if not data.email or data.email.strip() == "":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "validation_error",
                "message": "Email не может быть пустым",
            },
        )

    # Приведение email к нижнему регистру
    email = data.email.lower().strip()

    # Проверка формата email с использованием email-validator
    from email_validator import validate_email, EmailNotValidError

    try:
        validated_email = validate_email(email)
        email = validated_email.email
    except EmailNotValidError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "validation_error",
                "message": "Некорректный формат email",
            },
        )

    # Валидация пароля
    if not validate_password(data.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "password_validation_error",
                "message": "Пароль должен содержать минимум 8 символов, включая заглавные и строчные буквы, цифры и специальные символы",
            },
        )

    # Хеширование пароля
    password_hash = get_password_hash(data.password)

    # Получение информации об устройстве из заголовка User-Agent
    device_info = request.headers.get("User-Agent", "")

    try:
        # Вызов хранимой процедуры register_user
        user_id = await db.execute_function(
            "register_user",
            email,
            password_hash,
            None,  # name
            None,  # country
            None,  # city
            1,  # role_id (обычный пользователь)
            device_info,
        )

        # Настройки JWT
        SECRET_KEY = os.getenv("SECRET_KEY")
        if not SECRET_KEY:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"error": "internal_error", "message": "Не настроен SECRET_KEY"},
            )

        ALGORITHM = "HS256"
        ACCESS_TOKEN_EXPIRE_MINUTES = 15
        REFRESH_TOKEN_EXPIRE_DAYS = 30

        # Создание access токена
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token_payload = {
            "user_id": user_id,
            "role": "user",
            "exp": datetime.utcnow() + access_token_expires,
        }
        access_token = jwt.encode(access_token_payload, SECRET_KEY, algorithm=ALGORITHM)

        # Создание refresh токена (случайная строка 64 символа)
        refresh_token = secrets.token_urlsafe(64)

        # Сохранение refresh токена в БД
        new_token_id = await db.execute_function(
            "save_refresh_token",
            user_id,
            refresh_token,
            device_info,
            REFRESH_TOKEN_EXPIRE_DAYS,
        )

        # Отправка welcome email асинхронно
        from routers.auth.email_service import EmailService

        # Запускаем отправку email в фоновом режиме
        asyncio.create_task(EmailService.send_activation_email(user_id, email))

        # Возврат успешного ответа
        return {
            "success": True,
            "message": "Регистрация прошла успешно",
            "user_id": user_id,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # в секундах
        }

    except Exception as e:
        # Обработка специфичных ошибок
        error_msg = str(e)
        if "USER_ALREADY_EXISTS" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": "email_already_exists",
                    "message": "Пользователь с таким email уже существует",
                },
            )
        elif "ROLE_NOT_FOUND" in error_msg or "EMPTY_PASSWORD_HASH" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "validation_error",
                    "message": "Некорректные данные пользователя",
                },
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": "registration_failed",
                    "message": "Ошибка при регистрации пользователя",
                },
            )
