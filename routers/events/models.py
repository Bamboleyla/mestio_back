from pydantic import BaseModel, Field
from datetime import datetime, date
from typing import Optional, List


class EventCategoryRequest(BaseModel):
    category_name: str = Field(
        ...,
        max_length=50,
        description="Название категории события, максимум 50 символов",
    )

    model_config = {"from_attributes": True}


class EventCategoryResponse(BaseModel):
    id: int = Field(..., description="ID категории события")
    name: str = Field(..., max_length=50, description="Название категории события")

    model_config = {"from_attributes": True}


class EventScheduleRequest(BaseModel):
    date: datetime = Field(..., description="Дата и время проведения события")
    price: Optional[int] = Field(
        None, ge=0, description="Цена билета, должна быть положительной"
    )

    model_config = {"from_attributes": True}


class EventRequest(BaseModel):
    title: str = Field(
        ..., max_length=100, description="Название события, максимум 100 символов"
    )
    location_id: int = Field(..., description="ID локации проведения события")
    category_id: int = Field(..., description="ID категории события")
    schedules: List[EventScheduleRequest] = Field(
        ..., description="Список расписаний события с датами и ценами"
    )
    description: Optional[str] = Field(
        None, max_length=1000, description="Описание события, максимум 1000 символов"
    )
    duration: Optional[int] = Field(
        None, ge=0, description="Длительность события в минутах"
    )

    model_config = {"from_attributes": True}


class EventByDateResponse(BaseModel):
    event_id: int
    date: datetime
    price: Optional[int] = None
    title: str
    category_name: str
    location_name: str
    img_path: Optional[str] = None

    model_config = {"from_attributes": True}


class EventLocationResponse(BaseModel):
    name: str
    category: str
    city: Optional[str] = None
    street: Optional[str] = None
    house_number: Optional[str] = None
    building_number: Optional[str] = None
    apartment_number: Optional[str] = None

    model_config = {"from_attributes": True}


class EventOpeningHoursResponse(BaseModel):
    open_time: Optional[str] = None
    close_time: Optional[str] = None
    break_start: Optional[str] = None
    break_end: Optional[str] = None

    model_config = {"from_attributes": True}


class EventDetailsFullResponse(BaseModel):
    title: str
    description: Optional[str] = None
    duration: Optional[int] = None
    event_category: str
    location: EventLocationResponse
    opening_hours: EventOpeningHoursResponse
    images: List[str]

    model_config = {"from_attributes": True}
