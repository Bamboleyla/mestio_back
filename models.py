from pydantic import BaseModel
from datetime import datetime, date
from typing import Optional


class EventResponse(BaseModel):
    event_title: str
    event_start_date: datetime  # Изменено с str на datetime
    location_name: str
    category_name: str
    event_price: Optional[int] = (
        None  # Добавлен Optional, так как price может быть NULL
    )
    event_date: date  # Изменено с str на date

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat(),
        }
