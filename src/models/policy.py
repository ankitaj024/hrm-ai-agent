from datetime import datetime
from typing import Optional
from typing_extensions import Annotated
from pydantic import BaseModel, Field, BeforeValidator

# Helper to map MongoDB _id to id
PyObjectId = Annotated[str, BeforeValidator(str)]

class PolicySchema(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    name: str = Field(..., description="Name of the policy")
    content: str = Field(..., description="HTML content of the policy")
    
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "name": "Remote Work Policy",
                "content": "<p>Employees can work remotely...</p>"
            }
        }
