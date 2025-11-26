from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
import os

load_dotenv()

from database import db
from services.config import settings
from routers.events import router as events_router
from routers.images import router as images_router
from routers.locations import router as locations_router

app = FastAPI(title="Mestio API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Монтируем статику для отдачи изображений
app.mount(
    "/static/images",
    StaticFiles(directory=settings.IMAGE_UPLOAD_DIR),
    name="static_images",
)


# События запуска/остановки
@app.on_event("startup")
async def startup():
    await db.connect()


@app.on_event("shutdown")
async def shutdown():
    await db.disconnect()


# Регистрируем роутеры
app.include_router(events_router)
app.include_router(images_router)
app.include_router(locations_router)
