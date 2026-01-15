import asyncio
from src.core.database import db
from src.core.security import get_password_hash
from src.models.employee import Gender, Department, Designation
from datetime import datetime

async def create_admin():
    db.connect()
    collection = db.get_db()["employees"]
    
    email = "super.admin@company.com"
    password = "superadmin@12"
    
    hashed = get_password_hash(password)
    
    admin_data = {
        "name": "Super Admin",
        "email": email,
        "password": hashed,
        "role": "super_admin",
        "department": Department.HUMAN_RESOURCE.value,
        "designation": Designation.HR_EXECUTIVE.value,
        "phone_number": "1234567890",
        "permanent_address": "Admin HQ",
        "dob": datetime(1990, 1, 1),
        "gender": Gender.MALE.value,
        "city": "Remote",
        "joining_date": datetime.now(),
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }
    
    # Upsert
    await collection.update_one({"email": email}, {"$set": admin_data}, upsert=True)
    print(f"Created/Updated Admin: {email} / {password}")
    db.close()

if __name__ == "__main__":
    asyncio.run(create_admin())
