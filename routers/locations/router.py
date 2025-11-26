from fastapi import APIRouter
from .get_location_names import router as get_location_names_router


router = APIRouter(prefix="/api/v1/locations")

# Подключаем роутер для локаций
router.include_router(get_location_names_router)
