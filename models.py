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
    img_path: Optional[str] = None

    model_config = {"from_attributes": True}


class EventDetailsResponse(BaseModel):
    # Основные данные события
    event_title: str = Field(..., max_length=100, description="Название события")
    event_description: Optional[str] = Field(
        None, max_length=1000, description="Описание события"
    )
    event_duration: Optional[int] = Field(
        None, ge=0, description="Длительность события в минутах"
    )
    event_category_name: str = Field(
        ..., max_length=50, description="Название категории события"
    )

    # Данные локации
    location_name: str = Field(..., max_length=255, description="Название локации")
    location_category_name: str = Field(
        ..., max_length=50, description="Название категории локации"
    )
    location_city: Optional[str] = Field(
        None, max_length=100, description="Город локации"
    )
    location_street: Optional[str] = Field(
        None, max_length=255, description="Улица локации"
    )
    location_house_number: Optional[str] = Field(
        None, max_length=20, description="Номер дома"
    )
    location_building_number: Optional[str] = Field(
        None, max_length=20, description="Номер корпуса"
    )
    location_apartment_number: Optional[str] = Field(
        None, max_length=20, description="Номер квартиры/офиса"
    )

    # Время работы локации
    day_of_week: Optional[int] = Field(
        None, ge=1, le=7, description="День недели (1-7)"
    )
    open_time: Optional[str] = Field(None, description="Время открытия")
    close_time: Optional[str] = Field(None, description="Время закрытия")
    break_start: Optional[str] = Field(None, description="Время начала перерыва")
    break_end: Optional[str] = Field(None, description="Время окончания перерыва")

    # Изображения события
    file_path: Optional[str] = Field(
        None, max_length=500, description="Путь к файлу изображения"
    )

    class Config:
        description = "Подробная информация о событии и связанной локации"
        from_attributes = True


class EventLocationResponse(BaseModel):
    name: str
    category: str
    city: Optional[str] = None
    street: Optional[str] = None
    house_number: Optional[str] = None
    building_number: Optional[str] = None
    apartment_number: Optional[str] = None

    class Config:
        description = "Информация о локации события"
        from_attributes = True


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
