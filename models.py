from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class UserResponse(BaseModel):
    id: int
    email: str
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
