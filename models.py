from pydantic import BaseModel, EmailStr, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal


class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    password: str
    interests: Optional[List[int]] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(UserBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class LocationBase(BaseModel):
    name: str
    address: Optional[str] = None
    lat: float
    lng: float
    category_id: Optional[int] = None


class EventBase(BaseModel):
    title: str
    description: Optional[str] = None
    event_type: str
    start_date: datetime
    end_date: Optional[datetime] = None
    location_id: int
    category_id: Optional[int] = None
    price_min: Optional[Decimal] = None
    price_max: Optional[Decimal] = None
    price_description: Optional[str] = None


class EventResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    short_description: Optional[str] = None
    start_date: datetime
    price_description: Optional[str] = None
    location_name: str
    address: Optional[str] = None
    distance_km: Optional[float] = None
    relevance_score: Optional[float] = None
    images: Optional[List[str]] = None
    model_config = ConfigDict(from_attributes=True)


class SearchFilters(BaseModel):
    query: Optional[str] = None
    categories: Optional[List[int]] = None
    event_types: Optional[List[str]] = None
    price_min: Optional[Decimal] = None
    price_max: Optional[Decimal] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    radius_km: int = 10


class UserAction(BaseModel):
    event_id: int
    action_type: str
    session_id: Optional[str] = None
    dwell_time: Optional[int] = None


class RecommendationRequest(BaseModel):
    lat: Optional[float] = None
    lng: Optional[float] = None
    radius_km: int = 10
    limit: int = 50


class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: int
