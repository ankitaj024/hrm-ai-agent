from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from src.agent.graph import graph
from src.dependencies import get_current_user_deps
from src.core.context import current_user_context
from langchain_core.messages import HumanMessage, AIMessage

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    thread_id: str = "default_thread"

from fastapi.responses import StreamingResponse
import json

@router.post("/chat")
async def chat(request: ChatRequest, user: dict = Depends(get_current_user_deps)):
    print(f"Received message: {request.message} for thread: {request.thread_id} from {user['email']}")
    
    # Set context for this request (propagates to tools running in same context)
    current_user_context.set(user)
    
    async def event_generator():
        try:
            config = {"configurable": {"thread_id": request.thread_id}}
            
            # Check current state for pending approval (interruption handling remains similar)
            snapshot = await graph.aget_state(config)
            input_data = {"messages": [HumanMessage(content=request.message)]}
            
            if snapshot.next and "sensitive_tools" in snapshot.next:
                 user_msg_lower = request.message.lower()
                 if any(keyword in user_msg_lower for keyword in ["approve", "yes", "confirm"]):
                     print("Resuming graph execution via approval...")
                     input_data = None
                 elif any(keyword in user_msg_lower for keyword in ["deny", "no", "cancel"]):
                    print("Cancelling action and resuming graph...")
                    msgs = snapshot.values.get("messages", [])
                    if msgs:
                        last_msg = msgs[-1]
                        if hasattr(last_msg, "tool_calls"):
                             from langchain_core.messages import ToolMessage
                             tool_msgs = []
                             for tc in last_msg.tool_calls:
                                 tool_msgs.append(ToolMessage(
                                     tool_call_id=tc["id"],
                                     content="Tool execution denied by user."
                                 ))
                             await graph.aupdate_state(config, {"messages": tool_msgs}, as_node="sensitive_tools")
                             input_data = None
                    
                    if not input_data:
                         yield f"data: {json.dumps({'type': 'response', 'content': 'Action cancelled by user.'})}\n\n"
                 else:
                      yield f"data: {json.dumps({'type': 'response', 'content': '⚠️ **APPROVAL REQUIRED**: A sensitive action is pending. Type \"approve\" to confirm.'})}\n\n"
                      return

            print("Starting graph execution with astream_events...")
            # Use astream_events for granular tokens and tool events
            # We filter for relevant events to reduce noise
            async for event in graph.astream_events(input_data, config=config, version="v2"):
                kind = event["event"]
                
                # Stream Tokens
                if kind == "on_chat_model_stream":
                    # print(f"DEBUG: Token event data: {event['data']}")
                    content = event["data"]["chunk"].content
                    if content:
                        payload = {"type": "token", "content": content}
                        yield f"data: {json.dumps(payload)}\n\n"
                
                # Tool Start
                elif kind == "on_tool_start":
                    payload = {
                        "type": "tool_start", 
                        "name": event["name"], 
                        "run_id": event["run_id"],
                        "input": event["data"].get("input")
                    }
                    print(f"DEBUG: Tool Start: {event['name']}")
                    yield f"data: {json.dumps(payload)}\n\n"
                    
                # Tool End
                elif kind == "on_tool_end":
                    output = event["data"].get("output")
                    # Handle LangChain Message objects (like ToolMessage)
                    if hasattr(output, "content"):
                        output = output.content
                    elif not isinstance(output, (str, int, float, bool, list, dict, type(None))):
                        output = str(output)
                        
                    payload = {
                        "type": "tool_end", 
                        "name": event["name"], 
                        "run_id": event["run_id"],
                        "output": output
                    }
                    yield f"data: {json.dumps(payload)}\n\n"

            print("DEBUG: Finished streaming events.")

            # Check next state for interrupt
            snapshot = await graph.aget_state(config)
            print(f"DEBUG: Snapshot next: {snapshot.next}")
            
            if snapshot.next and "sensitive_tools" in snapshot.next:
                 print("DEBUG: Sensitive tool detected. Sending approval request.")
                 yield f"data: {json.dumps({'type': 'response', 'content': '\n\n⚠️ **APPROVAL REQUIRED**: A sensitive action is pending. Type \"approve\" to confirm.'})}\n\n"
            
        except Exception as e:
            print(f"Error streaming events: {e}")
            error_msg = {"type": "error", "content": str(e)}
            yield f"data: {json.dumps(error_msg)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@router.get("/history/{thread_id}")
async def get_history(thread_id: str):
    """
    Fetches the message history for a specific thread.
    """
    config = {"configurable": {"thread_id": thread_id}}
    try:
        snapshot = await graph.aget_state(config)
        if not snapshot.values:
            return {"messages": []}
            
        messages = snapshot.values.get("messages", [])
        formatted_msgs = []
        
        for msg in messages:
            # We only return Human and AI messages for the UI
            if isinstance(msg, HumanMessage):
                formatted_msgs.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage) and msg.content:
                formatted_msgs.append({"role": "assistant", "content": msg.content})
                
        return {"messages": formatted_msgs}
    except Exception as e:
        print(f"Error fetching history: {e}")
        return {"messages": []}
