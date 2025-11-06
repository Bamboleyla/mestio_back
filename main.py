from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
import os

load_dotenv()

from database import db
from services.config import settings
from routers import events
from routers import images

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
app.include_router(events.router)
app.include_router(images.router)
