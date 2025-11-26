from fastapi import APIRouter
from .get_events_by_date import router as get_events_by_date_router
from .create_event_category import router as create_event_category_router
from .create_event import router as create_event_router
from .get_all_event_categories import router as get_all_event_categories_router
from .get_event_details import router as get_event_details_router


router = APIRouter(prefix="/api/v1/events")

# Подключаем все роутеры для событий
router.include_router(get_events_by_date_router)
router.include_router(create_event_category_router)
router.include_router(create_event_router)
router.include_router(get_all_event_categories_router)
router.include_router(get_event_details_router)
