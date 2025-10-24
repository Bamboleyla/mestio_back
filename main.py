from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from datetime import datetime
import asyncpg
from dotenv import load_dotenv

load_dotenv()

from database import db
from models import (
    UserCreate,
    UserResponse,
    UserLogin,
    Token,
    EventResponse,
    SearchFilters,
    UserAction,
    RecommendationRequest,
)
from auth import (
    authenticate_user,
    create_access_token,
    get_current_user,
    get_password_hash,
)

app = FastAPI(title="Mestio API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# События запуска/остановки
@app.on_event("startup")
async def startup():
    await db.connect()


@app.on_event("shutdown")
async def shutdown():
    await db.disconnect()


# Эндпоинты аутентификации
@app.post("/auth/register", response_model=dict)
async def register(user_data: UserCreate):
    try:
        # Хэшируем пароль
        hashed_password = get_password_hash(user_data.password)

        # Вызываем хранимую процедуру регистрации
        result = await db.execute_procedure(
            "register_user", user_data.email, hashed_password, user_data.interests
        )

        if result and result[0]["success"]:
            user_id = result[0]["user_id"]

            # Создаем токен
            access_token = create_access_token({"user_id": user_id})

            return {
                "access_token": access_token,
                "token_type": "bearer",
                "user_id": user_id,
            }
        else:
            raise HTTPException(
                status_code=400, detail="User with this email already exists"
            )

    except asyncpg.exceptions.UniqueViolationError:
        raise HTTPException(
            status_code=400, detail="User with this email already exists"
        )


@app.post("/auth/login", response_model=Token)
async def login(user_data: UserLogin):
    user = await authenticate_user(user_data.email, user_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    access_token = create_access_token({"user_id": user["id"]})

    # Обновляем last_login
    await db.execute_procedure("log_user_action", user["id"], None, "login")

    return {"access_token": access_token, "token_type": "bearer", "user_id": user["id"]}


# Эндпоинты событий
@app.get("/events/recommended", response_model=List[EventResponse])
async def get_recommended_events(
    request: RecommendationRequest,
    current_user: UserResponse = Depends(get_current_user),
):
    """Получить рекомендованные события для пользователя"""
    result = await db.execute_procedure(
        "get_recommended_events",
        current_user.id,
        request.lat,
        request.lng,
        request.radius_km,
        request.limit,
    )

    events = []
    for row in result:
        events.append(
            EventResponse(
                id=row["event_id"],
                title=row["title"],
                description=row["description"],
                short_description=(
                    row["description"][:100] + "..." if row["description"] else None
                ),
                start_date=row["start_date"],
                price_description=row["price_description"],
                location_name=row["location_name"],
                distance_km=row["distance_km"],
                relevance_score=row["relevance_score"],
                images=row["images"] or [],
            )
        )

    return events


@app.post("/events/search", response_model=List[EventResponse])
async def search_events(
    filters: SearchFilters,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """Поиск событий с фильтрами"""
    result = await db.execute_procedure(
        "search_events",
        filters.query,
        filters.categories,
        filters.event_types,
        filters.price_min,
        filters.price_max,
        filters.start_date,
        filters.end_date,
        filters.lat,
        filters.lng,
        filters.radius_km,
        limit,
        offset,
    )

    events = []
    for row in result:
        events.append(
            EventResponse(
                id=row["event_id"],
                title=row["title"],
                short_description=row["short_description"],
                start_date=row["start_date"],
                price_description=row["price_description"],
                location_name=row["location_name"],
                address=row["address"],
                distance_km=row["distance_km"],
                images=row["images"] or [],
                relevance_score=row["match_score"],
            )
        )

    return events


@app.get("/events/{event_id}", response_model=EventResponse)
async def get_event_details(event_id: int):
    """Получить детальную информацию о событии"""
    event = await db.fetch_one(
        """
        SELECT 
            e.id, e.title, e.description, e.short_description,
            e.start_date, e.price_description, e.images,
            l.name as location_name, l.address
        FROM events e
        JOIN locations l ON e.location_id = l.id
        WHERE e.id = $1 AND e.is_active = true
    """,
        event_id,
    )

    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    return EventResponse(**event)


# Эндпоинты пользовательских действий
@app.post("/user/actions")
async def log_action(
    action: UserAction, current_user: UserResponse = Depends(get_current_user)
):
    """Логирование действия пользователя"""
    await db.execute_procedure(
        "log_user_action",
        current_user.id,
        action.event_id,
        action.action_type,
        action.session_id,
        action.dwell_time,
    )

    return {"status": "success", "message": "Action logged"}


@app.put("/user/interests")
async def update_interests(
    tag_ids: List[int], current_user: UserResponse = Depends(get_current_user)
):
    """Обновление интересов пользователя"""
    await db.execute_procedure("update_user_interests", current_user.id, tag_ids)

    return {"status": "success", "message": "Interests updated"}


@app.get("/user/favorites", response_model=List[EventResponse])
async def get_favorites(current_user: UserResponse = Depends(get_current_user)):
    """Получить избранные события пользователя"""
    result = await db.fetch_all(
        """
        SELECT 
            e.id, e.title, e.description, e.short_description,
            e.start_date, e.price_description, e.images,
            l.name as location_name, l.address
        FROM user_favorites uf
        JOIN events e ON uf.event_id = e.id
        JOIN locations l ON e.location_id = l.id
        WHERE uf.user_id = $1 AND e.is_active = true
        ORDER BY uf.saved_at DESC
    """,
        current_user.id,
    )

    events = [EventResponse(**row) for row in result]
    return events


@app.post("/user/favorites/{event_id}")
async def add_to_favorites(
    event_id: int, current_user: UserResponse = Depends(get_current_user)
):
    """Добавить событие в избранное"""
    try:
        await db.fetch_one(
            """
            INSERT INTO user_favorites (user_id, event_id)
            VALUES ($1, $2)
            ON CONFLICT (user_id, event_id) DO NOTHING
            RETURNING user_id
        """,
            current_user.id,
            event_id,
        )

        # Логируем действие
        await db.execute_procedure("log_user_action", current_user.id, event_id, "save")

        return {"status": "success", "message": "Event added to favorites"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/user/favorites/{event_id}")
async def remove_from_favorites(
    event_id: int, current_user: UserResponse = Depends(get_current_user)
):
    """Удалить событие из избранного"""
    result = await db.fetch_one(
        """
        DELETE FROM user_favorites 
        WHERE user_id = $1 AND event_id = $2
        RETURNING user_id
    """,
        current_user.id,
        event_id,
    )

    if not result:
        raise HTTPException(status_code=404, detail="Favorite not found")

    return {"status": "success", "message": "Event removed from favorites"}


# Эндпоинты для работы с категориями и тегами
@app.get("/categories")
async def get_categories():
    """Получить все категории событий"""
    categories = await db.fetch_all("SELECT * FROM event_categories ORDER BY name")
    return categories


@app.get("/tags")
async def get_tags(tag_type: Optional[str] = None):
    """Получить теги с фильтрацией по типу"""
    if tag_type:
        tags = await db.fetch_all(
            "SELECT * FROM tags WHERE tag_type = $1 ORDER BY name", tag_type
        )
    else:
        tags = await db.fetch_all("SELECT * FROM tags ORDER BY name")

    return tags


@app.get("/location-categories")
async def get_location_categories():
    """Получить категории локаций"""
    categories = await db.fetch_all("SELECT * FROM location_categories ORDER BY name")
    return categories


# Эндпоинт для обновления местоположения пользователя
@app.put("/user/location")
async def update_user_location(
    lat: float, lng: float, current_user: UserResponse = Depends(get_current_user)
):
    """Обновить местоположение пользователя"""
    await db.fetch_one(
        """
        UPDATE users 
        SET current_location = ST_SetSRID(ST_MakePoint($1, $2), 4326)::geography
        WHERE id = $3
    """,
        lng,
        lat,
        current_user.id,
    )

    return {"status": "success", "message": "Location updated"}


# Health check
@app.get("/health")
async def health_check():
    """Проверка работоспособности API и базы данных"""
    try:
        # Проверяем соединение с базой
        result = await db.fetch_one("SELECT 1 as status")
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="Service unhealthy")
