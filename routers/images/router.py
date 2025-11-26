from fastapi import APIRouter
from .upload_event_image import router as upload_event_image_router
from .get_event_images import router as get_event_images_router
from .delete_event_image import router as delete_event_image_router


router = APIRouter(prefix="/api/v1/events")

# Подключаем все роутеры для изображений
router.include_router(upload_event_image_router)
router.include_router(get_event_images_router)
router.include_router(delete_event_image_router)
