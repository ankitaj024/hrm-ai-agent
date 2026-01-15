from src.core.database import db
import asyncio

async def check_and_fix():
    db.connect()
    collection = db.get_db()["employees"]
    email = "ankitj@keymouseit.com"
    
    # 1. Update All: Set default 1.0 (or verify against leave_count field?)
    # For now, let's set privilege_leave_balance to 1.0 if missing.
    result = await collection.update_many(
        {"privilege_leave_balance": {"$exists": False}}, 
        {"$set": {"privilege_leave_balance": 1.0, "short_leaves_taken": 0}}
    )
    print(f"Updated {result.modified_count} employees with missing defaults.")

    # 2. Reset Ankit (or everyone with 0.0) to 1.0
    result_reset = await collection.update_many(
        {"privilege_leave_balance": 0.0},
        {"$set": {"privilege_leave_balance": 1.0}}
    )
    print(f"Reset {result_reset.modified_count} employees from 0.0 to 1.0")

    # 3. Verify
    emp = await collection.find_one({"email": email})
    if emp:
        print(f"New Balance for {email}: {emp.get('privilege_leave_balance')}")
    
    db.close()

if __name__ == "__main__":
    asyncio.run(check_and_fix())
