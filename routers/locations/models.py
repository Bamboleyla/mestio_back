from pydantic import BaseModel, Field
from typing import Optional


class LocationNameResponse(BaseModel):
    id: int = Field(..., description="ID локации")
    name: str = Field(..., description="Название локации")

    model_config = {"from_attributes": True}
