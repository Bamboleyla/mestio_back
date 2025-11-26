from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class ImageResponse(BaseModel):
    id: int
    url: str
    file_name: str
    file_size: int
    width: int
    height: int
    event_id: int
    image_quality: Optional[str] = None
    sort_order: Optional[int] = 0
    is_primary: Optional[bool] = False
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
