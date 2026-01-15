from enum import Enum
from datetime import datetime, date
from pydantic import BaseModel, Field, EmailStr, BeforeValidator
from typing import Optional, List
from typing_extensions import Annotated

# Helper to map MongoDB _id to id
PyObjectId = Annotated[str, BeforeValidator(str)]

class Gender(str, Enum):
    MALE = "Male"
    FEMALE = "Female"
    OTHER = "Other"

class Department(str, Enum):
    ENGINEERING = "Engineering"
    HUMAN_RESOURCE = "Human Resource"
    BUSINESS_DEVELOPMENT = "Business Development"
    QUALITY_ASSURANCE = "Quality Assurance"
    DESIGNING = "Designing"

class Designation(str, Enum):
    # Engineering
    INTERN = "Intern"
    SDE_1 = "SDE I"
    SDE_2 = "SDE II"
    SDE_3 = "SDE III"
    TEAM_LEAD = "Team Lead"
    ENGINEERING_MANAGER = "Engineering Manager"
    PRINCIPAL_ENGINEER = "Principal Engineer"
    
    # HR
    HR_INTERN = "HR Intern"
    HR_EXECUTIVE = "HR Executive"
    TALENT_ACQUISITION = "Talent Acquisition Specialist"
    HR_MANAGER = "HR Manager"
    
    # Business
    SALES_INTERN = "Sales Intern"
    SALES_EXECUTIVE = "Sales Executive"
    BUSINESS_ANALYST = "Business Analyst"
    BD_MANAGER = "Business Development Manager"
    
    # QA
    QA_INTERN = "QA Intern"
    QA_ENGINEER = "QA Engineer"
    SENIOR_QA = "Senior QA Engineer"
    QA_LEAD = "QA Lead"
    
    # Design
    DESIGN_INTERN = "Design Intern"
    UI_UX_DESIGNER = "UI/UX Designer"
    SENIOR_DESIGNER = "Senior Product Designer"
    DESIGN_LEAD = "Design Lead"

class BankDetails(BaseModel):
    account_number: str = Field(..., description="Bank Account Number")
    bank_name: str = Field(..., description="Name of the Bank")
    ifsc_code: Optional[str] = Field(None, description="IFSC Code or equivalent")

class EmployeeSchema(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    
    # Required Fields
    name: str = Field(..., description="Full name of the employee")
    email: EmailStr = Field(..., description="Work email address")
    password: str = Field(..., description="Hashed password")
    phone_number: str = Field(..., description="Phone Number")
    permanent_address: str = Field(..., description="Permanent Residential Address")
    dob: date = Field(..., description="Date of Birth (YYYY-MM-DD)")
    
    # Other Fields
    role: str = Field(..., description="Job Role")
    designation: Designation = Field(..., description="Official Designation")
    department: Department = Field(..., description="Department Name")
    
    city: Optional[str] = Field(None, description="City")
    temporary_address: Optional[str] = Field(None, description="Temporary Address")
    
    gender: Optional[Gender] = Field(None, description="Gender")
    
    date_of_joining: datetime = Field(default_factory=datetime.now, description="Date of Joining")
    
    bank_details: Optional[BankDetails] = Field(None, description="Bank Details")
    
    leave_count: int = Field(default=1, description="Default annual leave count")
    short_leave_count: int = Field(default=2, description="Default short leave count")
    
    # Leave Balances
    privilege_leave_balance: float = Field(default=1.0, description="Accumulated Privilege Leaves (Carries forward)")
    short_leaves_taken: int = Field(default=0, description="Short leaves taken this month (Resets monthly)")
    
    skills: List[str] = Field(default=[], description="List of technical or professional skills")

    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        populate_by_name = True
        json_encoders = {date: lambda v: v.isoformat()}
        json_schema_extra = {
            "example": {
                "name": "Jane Doe",
                "email": "jane@example.com",
                "password": "hashed_secret",
                "phone_number": "+1234567890",
                "role": "Developer",
                "department": "Engineering",
                "permanent_address": "123 Main St",
                "dob": "1990-01-01",
                "skills": ["Python", "FastAPI"]
            }
        }
