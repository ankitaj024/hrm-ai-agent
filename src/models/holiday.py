from datetime import date as DateType, datetime
from typing import Optional
from typing_extensions import Annotated
from pydantic import BaseModel, Field, BeforeValidator

# Helper to map MongoDB _id to id
PyObjectId = Annotated[str, BeforeValidator(str)]

class HolidaySchema(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    name: str = Field(..., description="Name of the holiday")
    date: DateType = Field(..., description="Date of the holiday (YYYY-MM-DD)")
    day: Optional[str] = Field(None, description="Day of the week (e.g., Monday)")
    description: Optional[str] = Field(None, description="Description of the holiday")
    
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        populate_by_name = True
        json_encoders = {DateType: lambda v: v.isoformat()}
        json_schema_extra = {
            "example": {
                "name": "New Year's Day",
                "date": "2026-01-01",
                "day": "Thursday",
                "description": "Public Holiday"
            }
        }
