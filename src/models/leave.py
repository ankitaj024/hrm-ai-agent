from enum import Enum
from datetime import datetime, date
from pydantic import BaseModel, Field, BeforeValidator
from typing import Optional
from typing_extensions import Annotated

PyObjectId = Annotated[str, BeforeValidator(str)]

class LeaveType(str, Enum):
    SHORT = "Short Leave"
    FULL_DAY = "Full Day"
    HALF_DAY = "Half Day"

class LeaveSlot(str, Enum):
    MORNING = "Morning"
    EVENING = "Evening"
    FULL_DAY = "Full Day" # Valid only for full day leaves

class LeaveStatus(str, Enum):
    PENDING = "Pending"
    APPROVED = "Approved"
    REJECTED = "Rejected"

class LeaveRequestSchema(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    
    employee_email: str = Field(..., description="Email of the employee applying")
    leave_type: LeaveType = Field(..., description="Type of leave")
    date: datetime = Field(..., description="Date of leave")
    slot: LeaveSlot = Field(..., description="Morning/Evening/Full")
    reason: str = Field(..., description="Reason for leave")
    
    status: LeaveStatus = Field(default=LeaveStatus.PENDING, description="Approval status")
    is_paid: bool = Field(default=True, description="Whether this leave is paid (calculated based on balance)")
    
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    decision_reason: Optional[str] = Field(default=None, description="Reason for approval/rejection")

    class Config:
        populate_by_name = True
        json_encoders = {date: lambda v: v.isoformat(), datetime: lambda v: v.isoformat()}
