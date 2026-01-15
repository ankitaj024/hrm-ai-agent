from contextvars import ContextVar
from typing import Optional, Dict, Any

# Context variable to store current user information
current_user_context: ContextVar[Optional[Dict[str, Any]]] = ContextVar("current_user_context", default=None)
