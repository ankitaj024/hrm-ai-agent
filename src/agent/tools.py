from langchain_core.tools import tool
from src.core.database import db
from src.models.employee import EmployeeSchema, Gender, BankDetails, Department, Designation
from typing import Optional, List
import bcrypt
from datetime import date, datetime
from src.core.context import current_user_context

def check_permission(target_email: str = None, require_super_admin: bool = False) -> str | None:
    """
    Checks permissions based on current user context.
    Returns None if allowed, or an error message string if denied.
    """
    user = current_user_context.get()
    if not user:
        return "Error: Unauthorized. Please log in."
        
    role = user.get("role", "employee")
    current_email = user.get("email")
    
    if role == "super_admin":
        return None
        
    if require_super_admin:
        return "Error: Permission Denied. Requires Super Admin role."
        
    if target_email:
        # If target is provided, non-admins can only access their own data
        if target_email.lower() != current_email.lower():
            return f"Error: Permission Denied. You can only access your own data ({current_email}). You cannot access {target_email}."
            
    return None

def hash_password(password: str) -> str:
    # Generate a salt and hash the password
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def clean_input(value):
    """Clean string inputs that might be passed as 'None' literal."""
    if isinstance(value, str):
        if value.lower() == "none" or value.lower() == "null":
            return None
        return value.strip()
    return value

def clean_department(value: str) -> str:
    """Normalize department input to match Enum values."""
    if not value:
        return None
    val_lower = value.lower().strip()
    
    # Mapping common variations
    mapping = {
        "hr": Department.HUMAN_RESOURCE,
        "human resource": Department.HUMAN_RESOURCE,
        "engineering": Department.ENGINEERING,
        "engineer": Department.ENGINEERING,
        "softwre": Department.ENGINEERING, # handling typos
        "software": Department.ENGINEERING,
        "it": Department.ENGINEERING,
        "backend": Department.ENGINEERING,
        "frontend": Department.ENGINEERING,
        "business": Department.BUSINESS_DEVELOPMENT,
        "sales": Department.BUSINESS_DEVELOPMENT,
        "business development": Department.BUSINESS_DEVELOPMENT,
        "qa": Department.QUALITY_ASSURANCE,
        "quality": Department.QUALITY_ASSURANCE,
        "testing": Department.QUALITY_ASSURANCE,
        "quality assurance": Department.QUALITY_ASSURANCE,
        "design": Department.DESIGNING,
        "designing": Department.DESIGNING,
        "ui/ux": Department.DESIGNING,
        "product": Department.BUSINESS_DEVELOPMENT # or maybe its own, but mapping to valid enum
    }
    
    # If exact match found in values
    for dept in Department:
        if dept.value.lower() == val_lower:
            return dept
            
    # Check mapping
    if val_lower in mapping:
        return mapping[val_lower]
        
    # Return as title case if not found, let validation fail or accept if close
    return value.title()

    return value.title()

def clean_designation(value: str) -> str:
    """Normalize designation input to match Enum values."""
    if not value:
        return None
    val_lower = value.lower().strip()
    
    # Mapping common variations
    mapping = {
        # Eng
        "sde 1": Designation.SDE_1, "sde i": Designation.SDE_1, "software engineer": Designation.SDE_1, "junior engineer": Designation.SDE_1,
        "sde 2": Designation.SDE_2, "sde ii": Designation.SDE_2, "senior software engineer": Designation.SDE_2,
        "sde 3": Designation.SDE_3, "sde iii": Designation.SDE_3, "staff engineer": Designation.SDE_3,
        "lead": Designation.TEAM_LEAD, "team lead": Designation.TEAM_LEAD, "tech lead": Designation.TEAM_LEAD,
        "manager": Designation.ENGINEERING_MANAGER, "em": Designation.ENGINEERING_MANAGER, "engineering manager": Designation.ENGINEERING_MANAGER,
        # HR
        "hr": Designation.HR_EXECUTIVE, "hr executive": Designation.HR_EXECUTIVE, "recruiter": Designation.TALENT_ACQUISITION, "ta": Designation.TALENT_ACQUISITION,
        # QA
        "qa": Designation.QA_ENGINEER, "tester": Designation.QA_ENGINEER, "senior qa": Designation.SENIOR_QA,
        # Design
        "designer": Designation.UI_UX_DESIGNER, "ui/ux": Designation.UI_UX_DESIGNER, "product designer": Designation.UI_UX_DESIGNER,
        # Business
        "sales": Designation.SALES_EXECUTIVE, "ba": Designation.BUSINESS_ANALYST, "business analyst": Designation.BUSINESS_ANALYST
    }

    # If exact match
    for des in Designation:
        if des.value.lower() == val_lower:
            return des
            
    # Check mapping
    if val_lower in mapping:
        return mapping[val_lower]
        
    return value.title()

@tool
async def create_employee_tool(
    name: str, 
    email: str, 
    password: str,
    phone_number: str,
    permanent_address: str,
    dob: str,
    role: str, 
    department: str,
    gender: str = None,
    city: str = None,
    temporary_address: str = None,
    designation: str = None,
    skills: list[str] = [],
    bank_account_number: str = None,
    bank_name: str = None,
    bank_ifsc: str = None
):
    """
    Creates a new employee record.
    REQUIRED: name, email, password, phone_number, permanent_address, dob (YYYY-MM-DD), role, department.
    Requires Super Admin privileges.
    """
    if error := check_permission(require_super_admin=True):
        return error

    # Clean inputs
    gender = clean_input(gender)
    city = clean_input(city)
    temporary_address = clean_input(temporary_address)
    designation = clean_input(designation)
    bank_account_number = clean_input(bank_account_number)
    bank_name = clean_input(bank_name)
    bank_name = clean_input(bank_name)
    bank_ifsc = clean_input(bank_ifsc)
    
    # Normalize Department and Designation
    department = clean_department(department)
    designation = clean_designation(designation)

    # Hash password
    try:
        hashed_password = hash_password(password)
    except Exception as e:
        return f"Error hashing password: {str(e)}"
    
    # Parse DOB
    try:
        dob_date = date.fromisoformat(dob)
    except ValueError:
        return "Error: Date of Birth must be in YYYY-MM-DD format."

    # Bank Details
    bank_details_obj = None
    if bank_account_number and bank_name:
        bank_details_obj = BankDetails(
            account_number=bank_account_number,
            bank_name=bank_name,
            ifsc_code=bank_ifsc
        )

    try:
        employee_data = EmployeeSchema(
            name=name,
            email=email,
            password=hashed_password,
            phone_number=phone_number,
            permanent_address=permanent_address,
            dob=dob_date,
            role=role,
            designation=designation,
            department=department,
            gender=Gender(gender) if gender else None,
            city=city,
            temporary_address=temporary_address,
            skills=skills or [],
            bank_details=bank_details_obj
        )
    except Exception as e:
        return f"Validation Error: {str(e)}"
    
    data = employee_data.model_dump(by_alias=True, exclude=["id"])
    
    # Convert date objects to datetime for MongoDB
    if "dob" in data and isinstance(data["dob"], date):
        data["dob"] = datetime.combine(data["dob"], datetime.min.time())
    
    collection = db.get_db()["employees"]
    existing = await collection.find_one({"email": email})
    if existing:
        return f"Error: Employee with email {email} already exists."
        
    result = await collection.insert_one(data)
    
    # Send Notification Email
    import asyncio
    from src.core.email import send_email
    from src.core.templates import get_employee_welcome_template
    
    email_body = get_employee_welcome_template(name, email, role, str(department), str(designation))
    
    # Run in thread to avoid blocking async loop
    asyncio.create_task(asyncio.to_thread(send_email, to_email="adminkmit@yopmail.com", subject="New Employee Created - Welcome!", body=email_body))
    
    return f"Successfully created employee {name} with ID: {str(result.inserted_id)}"

@tool
async def get_employee_tool(email: str):
    """
    Retrieves employee details by their email address.
    """
    if error := check_permission(target_email=email):
        return error
        
    collection = db.get_db()["employees"]
    employee = await collection.find_one({"email": email})
    
    if not employee:
        return f"No employee found with email: {email}"
        
    employee["_id"] = str(employee["_id"])
    # Redact password
    if "password" in employee:
        employee["password"] = "********"
        
    return str(employee)

@tool
async def list_employees_tool():
    """
    Lists employees.
    Super Admins: lists ALL employees.
    Employees: lists ONLY themselves.
    """
    user = current_user_context.get()
    is_super_admin = user and user.get("role") == "super_admin"
    current_email = user.get("email") if user else None
    
    collection = db.get_db()["employees"]
    
    if is_super_admin:
        cursor = collection.find({})
    else:
        # Strict Restriction: Non-admins can only see themselves
        if not current_email:
            return "Error: Unauthorized. Please log in."
        cursor = collection.find({"email": current_email})

    employees = []
    async for employee in cursor:
        employee["_id"] = str(employee["_id"])
        
        # Standard Redaction (Password only)
        # Since non-admins only see themselves, they are allowed to see their own details.
        
        if "password" in employee:
            employee["password"] = "********"
        employees.append(employee)
        
    if not employees:
        return "No employees found."
        
    return str(employees)

@tool
async def update_employee_tool(
    email: str,
    name: str = None, 
    password: str = None,
    phone_number: str = None,
    permanent_address: str = None,
    dob: str = None,
    role: str = None, 
    department: str = None,
    gender: str = None,
    city: str = None,
    temporary_address: str = None,
    designation: str = None,
    skills: list[str] = None,
    bank_account_number: str = None,
    bank_name: str = None,
    bank_ifsc: str = None
):
    """
    Updates an existing employee's details. Refers to the employee by email.
    Only provide the fields that need to be updated.
    """
    if error := check_permission(target_email=email):
        return error

    # Clean inputs
    name = clean_input(name)
    phone_number = clean_input(phone_number)
    permanent_address = clean_input(permanent_address)
    role = clean_input(role)
    department = clean_input(department)
    gender = clean_input(gender)
    city = clean_input(city)
    temporary_address = clean_input(temporary_address)
    designation = clean_input(designation)
    bank_account_number = clean_input(bank_account_number)
    bank_name = clean_input(bank_name)
    bank_ifsc = clean_input(bank_ifsc)
    
    collection = db.get_db()["employees"]
    employee = await collection.find_one({"email": email})
    
    if not employee:
        return f"No employee found with email: {email}"
    
    update_data = {}
    
    if name: update_data["name"] = name
    if phone_number: update_data["phone_number"] = phone_number
    if permanent_address: update_data["permanent_address"] = permanent_address
    if role: update_data["role"] = role
    if department: update_data["department"] = department
    if city: update_data["city"] = city
    if temporary_address: update_data["temporary_address"] = temporary_address
    if designation: update_data["designation"] = designation
    if skills is not None: update_data["skills"] = skills
    if gender: update_data["gender"] = gender

    if password:
        update_data["password"] = hash_password(password)
        
    if dob:
        try:
            # Store as datetime for MongoDB
            dob_date = date.fromisoformat(dob)
            update_data["dob"] = datetime.combine(dob_date, datetime.min.time())
        except ValueError:
            return "Error: Date of Birth must be in YYYY-MM-DD format."
            
    # Handle Bank Details update carefully
    if bank_account_number or bank_name or bank_ifsc:
        current_bank = employee.get("bank_details", {}) or {}
        if bank_account_number: current_bank["account_number"] = bank_account_number
        if bank_name: current_bank["bank_name"] = bank_name
        if bank_ifsc: current_bank["ifsc_code"] = bank_ifsc
        update_data["bank_details"] = current_bank

    update_data["updated_at"] = datetime.now()

    if not update_data:
        return "No fields provided for update."

    await collection.update_one({"email": email}, {"$set": update_data})
    return f"Successfully updated employee: {email}"

@tool
async def delete_employee_tool(email: str):
    """
    Deletes an employee record from the system using their email.
    """
    if error := check_permission(require_super_admin=True):
        return error
        
    collection = db.get_db()["employees"]
    result = await collection.delete_one({"email": email})
    
    if result.deleted_count == 0:
        return f"No employee found with email {email} to delete."
        
    return f"Successfully deleted employee with email: {email}"

# --- Leave Management Tools ---
from src.models.leave import LeaveRequestSchema, LeaveType, LeaveSlot, LeaveStatus

@tool
async def apply_leave_tool(
    email: str,
    date_str: str,
    reason: str,
    leave_type: str,
    slot: str = "Full Day"
):
    """
    Applies for a leave.
    
    Args:
        email: Employee email
        date_str: Date in YYYY-MM-DD format
        reason: Reason for leave
        leave_type: 'Short Leave', 'Full Day', or 'Half Day'
        slot: 'Morning', 'Evening', or 'Full Day' (for full day leaves)
    """
    if error := check_permission(target_email=email):
        return error
        
    collection_emp = db.get_db()["employees"]
    collection_leaves = db.get_db()["leaves"]
    
    employee = await collection_emp.find_one({"email": email})
    if not employee:
        return f"Error: Employee with email {email} not found."
    
    try:
        leave_date = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return "Error: Date must be YYYY-MM-DD format."
        
    # Validate Enum inputs
    try:
        l_type = LeaveType(leave_type)
        l_slot = LeaveSlot(slot)
    except ValueError:
        return f"Error: Invalid leave type or slot. Valid types: {[t.value for t in LeaveType]}. Valid slots: {[s.value for s in LeaveSlot]}"

    # Logic for Paid/Unpaid
    is_paid = True
    balance_msg = ""
    
    # --- Logic for Paid/Unpaid with Future Projection ---
    
    today = datetime.now()
    # Calculate months difference for PL accrual
    # Assuming 1 PL accrues on the 1st of every month.
    # If leave is in future month, add (leave_month - current_month) * 1.0
    months_diff = (leave_date.year - today.year) * 12 + (leave_date.month - today.month)
    projected_accrual = max(0, months_diff) * 1.0
    
    current_pl = employee.get("privilege_leave_balance", 0.0)
    projected_pl = current_pl + projected_accrual
    
    # Dynamic Quotas from DB
    short_leave_quota = employee.get("short_leave_count", 2)
    
    balance_msg = ""
    is_paid = True

    if l_type == LeaveType.SHORT:
        if l_slot == LeaveSlot.FULL_DAY:
            return "Error: Short leaves cannot be Full Day. Choose Morning or Evening."
            
        # Check Short Leaves count for the TARGET month
        # We cannot rely on 'short_leaves_taken' field as that is likely for the current month/cached.
        # We must count leaves in DB for that specific month.
        start_date = datetime(leave_date.year, leave_date.month, 1)
        if leave_date.month == 12:
            end_date = datetime(leave_date.year + 1, 1, 1)
        else:
            end_date = datetime(leave_date.year, leave_date.month + 1, 1)
            
        existing_short_count = await collection_leaves.count_documents({
            "employee_email": email,
            "leave_type": "Short Leave",
            "status": {"$in": ["Pending", "Approved"]},
            "date": {"$gte": start_date, "$lt": end_date}
        })
        
        if existing_short_count >= short_leave_quota:
            return f"Error: Quota Exceeded. You have already taken {existing_short_count}/{short_leave_quota} short leaves for {leave_date.strftime('%B')}. Cannot apply for more."
        else:
            balance_msg = f"(Within Quota for {leave_date.strftime('%B')}: Will be {existing_short_count + 1}/{short_leave_quota})"
            
    elif l_type == LeaveType.FULL_DAY:
        if projected_pl < 1.0:
            if projected_pl > 0:
                is_paid = True # Mark as paid to trigger deduction logic, which will cap at available balance
                balance_msg = f"(Partial Balance: {projected_pl} available. Will consume {projected_pl} and rest is Unpaid.)"
            else:
                is_paid = False
                balance_msg = f"(Insufficient Balance: {projected_pl}. This will be fully UNPAID)"
        else:
            balance_msg = f"(Sufficient Projected Balance: {projected_pl})"
            
    elif l_type == LeaveType.HALF_DAY:
        if projected_pl < 0.5:
            if projected_pl > 0:
                is_paid = True
                balance_msg = f"(Partial Balance: {projected_pl} available. Will consume {projected_pl} and rest is Unpaid.)"
            else:
                is_paid = False
                balance_msg = f"(Insufficient Balance: {projected_pl}. This will be fully UNPAID)"
        else:
            balance_msg = f"(Sufficient Projected Balance: {projected_pl})"

    leave_request = LeaveRequestSchema(
        employee_email=email,
        leave_type=l_type,
        date=leave_date,
        slot=l_slot,
        reason=reason,
        status=LeaveStatus.PENDING,
        is_paid=is_paid
    )
    
    data = leave_request.model_dump(by_alias=True, exclude=["id"])
    result = await collection_leaves.insert_one(data)
    
    # Send Notification Email
    import asyncio
    from src.core.email import send_email
    from src.core.templates import get_leave_request_template
    
    email_body = get_leave_request_template(email, leave_date.strftime('%Y-%m-%d'), l_type.value, reason)

    # Run in thread to avoid blocking async loop
    asyncio.create_task(asyncio.to_thread(send_email, to_email="adminkmit@yopmail.com", subject="New Leave Request", body=email_body))
    
    return f"Leave Request Created (ID: {str(result.inserted_id)}). Status: PENDING. Type: {l_type.value}. {balance_msg}. APPROVAL REQUIRED to finalize."

@tool
async def get_leave_status_tool(email: str):
    """
    Checks leave balance and pending requests for an employee.
    """
    if error := check_permission(target_email=email):
        return error
        
    collection_emp = db.get_db()["employees"]
    collection_leaves = db.get_db()["leaves"]
    
    employee = await collection_emp.find_one({"email": email})
    if not employee:
        return f"Error: Employee not found."
        
    pl_balance = employee.get("privilege_leave_balance", 0.0)
    short_taken = employee.get("short_leaves_taken", 0)
    
    # Get recent leaves
    cursor = collection_leaves.find({"employee_email": email}).sort("date", -1).limit(5)
    recent_leaves = []
    async for doc in cursor:
        recent_leaves.append(f"- {doc['date'].strftime('%Y-%m-%d')} ({doc['leave_type']}): {doc['status']}")
        
    return f"""
    Employee: {employee['name']}
    ---------------------------
    Privilege Leave Balance: {pl_balance} (Carries forward)
    Short Leaves Taken (This Month): {short_taken}/2
    
    Recent Requests:
    {chr(10).join(recent_leaves) if recent_leaves else "None"}
    """


async def _approve_leave_logic(request_id: str, reason: str = "Approved by Admin"):
    if error := check_permission(require_super_admin=True):
        return error
        
    from bson import ObjectId
    collection_leaves = db.get_db()["leaves"]
    collection_emp = db.get_db()["employees"]
    
    try:
        req = await collection_leaves.find_one({"_id": ObjectId(request_id)})
    except:
        return "Error: Invalid Request ID"
        
    if not req:
        return "Error: Request not found."
        
    if req["status"] != "Pending":
        return f"Request is already {req['status']}."
        
    email = req["employee_email"]
    l_type = req["leave_type"]
    
    # Deduct Logic
    employee = await collection_emp.find_one({"email": email})
    if not employee: return "Employee not found."
    
    if req["is_paid"]:
        if l_type == "Short Leave":
            await collection_emp.update_one({"email": email}, {"$inc": {"short_leaves_taken": 1}})
        elif l_type == "Full Day":
            await collection_emp.update_one({"email": email}, {"$inc": {"privilege_leave_balance": -1.0}})
        elif l_type == "Half Day":
            await collection_emp.update_one({"email": email}, {"$inc": {"privilege_leave_balance": -0.5}})
            
    await collection_leaves.update_one(
        {"_id": ObjectId(request_id)}, 
        {"$set": {"status": "Approved", "decision_reason": reason}}
    )

    # Send Email
    import asyncio
    from src.core.email import send_email
    from src.core.templates import get_leave_status_update_template
    
    date_str = req["date"].strftime('%Y-%m-%d')
    # Pass is_paid status to template logic
    is_paid_status = req.get("is_paid", True)
    email_body = get_leave_status_update_template(email, date_str, "Approved", reason, is_paid=is_paid_status)
    asyncio.create_task(asyncio.to_thread(send_email, to_email="testagent@yopmail.com", subject="Leave Request Approved", body=email_body))
    
    return f"Leave Approved for {email}. Balance updated."

async def _reject_leave_logic(request_id: str, reason: str = "Rejected by Admin"):
    if error := check_permission(require_super_admin=True):
        return error

    from bson import ObjectId
    collection_leaves = db.get_db()["leaves"]
    try:
        req = await collection_leaves.find_one({"_id": ObjectId(request_id)})
        if not req: return "Error: Request not found"
        
        await collection_leaves.update_one(
            {"_id": ObjectId(request_id)}, 
            {"$set": {"status": "Rejected", "decision_reason": reason}}
        )
        
        # Send Email
        import asyncio
        from src.core.email import send_email
        from src.core.templates import get_leave_status_update_template
        
        date_str = req["date"].strftime('%Y-%m-%d')
        email_body = get_leave_status_update_template(req["employee_email"], date_str, "Rejected", reason)
        asyncio.create_task(asyncio.to_thread(send_email, to_email="testagent@yopmail.com", subject="Leave Request Rejected", body=email_body))
        
        return "Leave Request Rejected."
    except Exception as e:
        return f"Error processing rejection: {str(e)}"

@tool
async def approve_leave_tool(request_id: str, reason: str = "Approved by Admin"):
    """
    Approves a pending leave request and deducts balance.
    """
    return await _approve_leave_logic(request_id, reason)

@tool
async def reject_leave_tool(request_id: str, reason: str = "Rejected by Admin"):
    """
    Rejects a leave request.
    """
    return await _reject_leave_logic(request_id, reason)

@tool
async def list_leaves_tool(email: str = None, status: str = None):
    """
    Lists leave requests. 
    Can filter by employee email or status (Pending/Approved/Rejected).
    If no filters provided, lists all recent leaves.
    """
    # If not provided, and not admin, default to self?
    # Or strict check? User logic says "get only their only leave".
    # So if email is None and user is not admin, force email=current_user.
    
    user = current_user_context.get()
    
    # Permission Logic:
    # 1. Super Admin: Can view any email (or all if None).
    # 2. Employee: Can ONLY view their own email.
    
    if user:
        role = user.get("role", "employee")
        current_email = user.get("email")
        
        if role != "super_admin":
            # If requesting specific email that is NOT self -> ERROR
            if email and email.lower() != current_email.lower():
                return f"Error: Permission Denied. You can only view your own leaves ({current_email})."
            
            # If no email provided (requesting ALL), DENY.
            if not email:
                return "Error: Permission Denied. Only Super Admins can view ALL leave requests. Please provide your email to view your own."
        
    collection_leaves = db.get_db()["leaves"]
    query = {}
    if email:
        query["employee_email"] = email
    if status:
        query["status"] = status
        
    cursor = collection_leaves.find(query).sort("date", -1).limit(20)
    leaves = []
    async for doc in cursor:
        leaves.append(f"ID: {str(doc['_id'])} | {doc['employee_email']} | {doc['date'].strftime('%Y-%m-%d')} | {doc['leave_type']} | {doc['status']}")
        
    if not leaves:
        return "No leave requests found matching criteria."
        
    return "\n".join(leaves)

@tool
async def update_leave_status_tool(request_id: str, status: str, reason: str = "Updated by Admin"):
    """
    Updates the status of a leave request.
    Use this to 'Approve' or 'Reject' a leave.
    
    Args:
        request_id: The ID of the leave request
        status: 'Approved' or 'Rejected'
    """
    s_lower = status.lower()
    if "approve" in s_lower:
        return await _approve_leave_logic(request_id, reason)
    elif "reject" in s_lower:
        return await _reject_leave_logic(request_id, reason)
    else:
        return "Error: Invalid status. Use 'Approved' or 'Rejected'."
