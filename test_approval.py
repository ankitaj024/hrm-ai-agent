
import asyncio
from src.core.database import db
from src.agent.tools import _approve_leave_logic, list_leaves_tool

async def main():
    print("Connecting to DB...")
    db.connect()
    
    print("Listing leaves...")
    # list_leaves_tool is a StructuredTool. We need to run it.
    # Since it's async, we use ainvoke.
    leaves = await list_leaves_tool.ainvoke({})
    print(f"Leaves:\n{leaves}")
    
    # Extract an ID if possible, or use a hardcoded one if you found it in logs
    # Let's try to parse the first ID
    import re
    match = re.search(r"ID: ([a-f0-9]+)", leaves)
    if match:
        req_id = match.group(1)
        print(f"Found Request ID: {req_id}")
        
        print("Approving leave...")
        result = await _approve_leave_logic(req_id)
        print(f"Result: {result}")
    else:
        print("No leaves found to test approval.")

if __name__ == "__main__":
    asyncio.run(main())
