from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import asyncpg
from datetime import date, datetime
from dotenv import load_dotenv
from typing import List

load_dotenv()

from database import db
from models import EventResponse

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


# Эндпоинт для получения событий по датам
@app.get("/events/by-dates", response_model=List[EventResponse])
async def get_events_by_dates(
    dates: List[date] = Query(..., description="Список дат в формате YYYY-MM-DD"),
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
