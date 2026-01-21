from fastapi import APIRouter, Depends, HTTPException
from src.core.database import db

router = APIRouter(tags=["Analytics"])

@router.get("/analytics/dashboard-stats")
async def get_dashboard_stats():
    """
    Get aggregated statistics for the dashboard.
    """
    try:
        database = db.get_db()

        # 1. Total Employees
        total_employees = await database.employees.count_documents({})

        # 2. Employees by Department
        dept_pipeline = [
            {"$group": {"_id": "$department", "count": {"$sum": 1}}},
            {"$project": {"name": "$_id", "value": "$count", "_id": 0}}
        ]
        employees_by_dept = await database.employees.aggregate(dept_pipeline).to_list(None)

        # 3. Leave Stats
        # Pending Requests
        pending_leaves = await database.leaves.count_documents({"status": "Pending"})
        
        # Approved Today (Example Metric) - For now just total approved
        approved_leaves = await database.leaves.count_documents({"status": "Approved"})

        # Leaves by Status
        leave_pipeline = [
            {"$group": {"_id": "$status", "count": {"$sum": 1}}},
            {"$project": {"name": "$_id", "value": "$count", "_id": 0}}
        ]
        leaves_by_status = await database.leaves.aggregate(leave_pipeline).to_list(None)

        return {
            "total_employees": total_employees,
            "department_distribution": employees_by_dept,
            "leave_stats": {
                "pending": pending_leaves,
                "approved": approved_leaves,
                "distribution": leaves_by_status
            }
        }

    except Exception as e:
        print(f"Error fetching stats: {str(e)}") # Add logging
        raise HTTPException(status_code=500, detail=str(e))
