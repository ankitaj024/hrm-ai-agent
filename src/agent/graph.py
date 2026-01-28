from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, BaseMessage
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver

from src.core.config import settings
from src.core.context import current_user_context
from src.agent.tools import (
    create_employee_tool, get_employee_tool, delete_employee_tool, update_employee_tool, list_employees_tool,
    apply_leave_tool, get_leave_status_tool, approve_leave_tool, reject_leave_tool, list_leaves_tool,
    update_leave_status_tool,
    create_holiday_tool, list_holidays_tool, update_holiday_tool, delete_holiday_tool,
    create_policy_tool, update_policy_tool, delete_policy_tool, get_policy_tool, list_policies_tool,
    generate_document_tool
)

class State(TypedDict):
    messages: Annotated[list, add_messages]

# Initialize LLM with tools
llm = ChatOpenAI(
    model="z-ai/glm-4.5-air:free",  # Using Gemini Flash 2.0
    # model="allenai/molmo-2-8b:free",  # Using Gemini Flash 2.0
    api_key=settings.OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1",
    temperature=0,
)

safe_tools = [
    create_employee_tool, get_employee_tool, list_employees_tool, update_employee_tool,
    get_leave_status_tool, reject_leave_tool, list_leaves_tool, update_leave_status_tool,
    list_holidays_tool, create_holiday_tool, update_holiday_tool,
    create_policy_tool, update_policy_tool, get_policy_tool, list_policies_tool,
    generate_document_tool
]

# Sensitive tools require human approval
sensitive_tools = [delete_employee_tool, approve_leave_tool, apply_leave_tool, delete_holiday_tool, delete_policy_tool]

# Bind ALL tools to the LLM so it knows it can perform these actions
llm_with_tools = llm.bind_tools(safe_tools + sensitive_tools)

async def reasoner(state: State):
    from datetime import datetime
    today = datetime.now().strftime("%Y-%m-%d")
    
    user = current_user_context.get()
    email = user.get("email", "unknown") if user else "unknown"
    role = user.get("role", "employee") if user else "employee"
    
    system_prompt = (
        f"You are a helpful HR Assistant. Today's date is {today}.\n"
        f"Current User Context:\n"
        f"- Email: {email}\n"
        f"- Role: {role}\n\n"
        "Permission Rules:\n"
        "- Super Admins can do everything (Create/Update/Delete Employees, Holidays, Policies).\n"
        "- Regular Employees can ONLY:\n"
        "  - View their own profile (`get_employee_tool` with their own email).\n"
        "  - View policies and holidays.\n"
        "  - Apply for leave.\n"
        "  - View their own leave status.\n"
        "- If a regular employee asks to do an admin task (like updating policies, deleting users, etc.), politely decline their request immediately without trying to call the tool. Explain that they require Super Admin privileges.\n\n"
        "When a user asks to perform an action that requires approval (like Apply Leave, Approve Leave, Delete Employee):\n"
        "1. Identify the tool call.\n"
        "2. If the tool is sensitive (approve_leave_tool, delete_employee_tool, apply_leave_tool), the system will pause.\n"
        "3. You should specificy EXACTLY what action is pending. Do NOT say 'delete employee' unless the user is actually deleting an employee.\n"
        "4. If applies for leave, state 'Creating Leave Request'. If approving, state 'Approving Leave'.\n"
        "5. Always be precise with dates. 'Tomorrow' is relative to today's date."
    )
    
    messages = [SystemMessage(content=system_prompt)] + state["messages"]
    return {"messages": [await llm_with_tools.ainvoke(messages)]}

def route_tools(state: State):
    """
    Route to the appropriate tool node based on the tool calls.
    """
    last_message = state["messages"][-1]
    if not hasattr(last_message, "tool_calls") or not last_message.tool_calls:
        return END
    
    # Check if any tool call is sensitive
    for tool_call in last_message.tool_calls:
        if tool_call["name"] in [t.name for t in sensitive_tools]:
            return "sensitive_tools"
            
    return "safe_tools"

# Build Graph
builder = StateGraph(State)

# Add Nodes
builder.add_node("reasoner", reasoner)
builder.add_node("safe_tools", ToolNode(safe_tools))
builder.add_node("sensitive_tools", ToolNode(sensitive_tools))

# Add Edges
builder.add_edge(START, "reasoner")

# Conditional Routing
builder.add_conditional_edges(
    "reasoner",
    route_tools,
    {
        "safe_tools": "safe_tools",
        "sensitive_tools": "sensitive_tools",
        END: END
    }
)

builder.add_edge("safe_tools", "reasoner")
builder.add_edge("sensitive_tools", "reasoner")

# Compile Graph with Interrupt
memory = MemorySaver()
graph = builder.compile(
    checkpointer=memory,
    interrupt_before=["sensitive_tools"]
)
