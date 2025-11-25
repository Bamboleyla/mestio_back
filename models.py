from pydantic import BaseModel, Field
from datetime import datetime, date
from typing import Optional, List


class EventCategoryRequest(BaseModel):
    category_name: str = Field(
        ...,
        max_length=50,
        description="Название категории события, максимум 50 символов",
    )

    class Config:
        description = "Запрос на создание новой категории события"


class EventCategoryResponse(BaseModel):
    id: int = Field(..., description="ID категории события")
    name: str = Field(..., max_length=50, description="Название категории события")

    class Config:
        description = "Ответ с информацией о категории события"
        from_attributes = True


class EventScheduleRequest(BaseModel):
    date: datetime = Field(..., description="Дата и время проведения события")
    price: Optional[int] = Field(
        None, ge=0, description="Цена билета, должна быть положительной"
    )

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


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

    class Config:
        description = "Запрос на создание нового события"
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class UserResponse(BaseModel):
    id: int
    email: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class LocationNameResponse(BaseModel):
    id: int = Field(..., description="ID локации")
    name: str = Field(..., description="Название локации")

    class Config:
        description = "Ответ с ID и названием локации"
        from_attributes = True


class EventByDateResponse(BaseModel):
    event_id: int
    date: datetime
    price: Optional[int] = None
    title: str
    category_name: str
    location_name: str

    class Config:
        from_attributes = True
        json_encoders = {
            date: lambda v: v.isoformat(),
            datetime: lambda v: v.isoformat(),
        }
