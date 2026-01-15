from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, BaseMessage
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver

from src.core.config import settings
from src.agent.tools import (
    create_employee_tool, get_employee_tool, delete_employee_tool, update_employee_tool, list_employees_tool,
    apply_leave_tool, get_leave_status_tool, approve_leave_tool, reject_leave_tool, list_leaves_tool,
    update_leave_status_tool
)

class State(TypedDict):
    messages: Annotated[list, add_messages]

# Initialize LLM with tools
llm = ChatOpenAI(
    model="xiaomi/mimo-v2-flash:free",  # Using Gemini Flash 2.0
    api_key=settings.OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1",
    temperature=0,
)

safe_tools = [
    create_employee_tool, get_employee_tool, list_employees_tool, update_employee_tool,
    get_leave_status_tool, reject_leave_tool, list_leaves_tool, update_leave_status_tool
]

# Sensitive tools require human approval
sensitive_tools = [delete_employee_tool, approve_leave_tool, apply_leave_tool]

# Bind ALL tools to the LLM so it knows it can perform these actions
llm_with_tools = llm.bind_tools(safe_tools + sensitive_tools)

async def reasoner(state: State):
    from datetime import datetime
    today = datetime.now().strftime("%Y-%m-%d")
    
    system_prompt = (
        f"You are a helpful HR Assistant. Today's date is {today}.\n"
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
