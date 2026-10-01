from typing import List, Dict, Any, Optional, TypedDict
from pydantic import BaseModel

class AgentState(TypedDict):
    user_query: str
    user_role: str
    conversation_id: str
    user_context: Optional[Dict[str, Any]]
    intent: Optional[str]
    actions_performed: List[str]
    tools_to_call: List[Dict[str, Any]]
    tool_results: List[Dict[str, Any]]
    rag_sources: List[Dict[str, Any]]
    structured_data: Optional[Dict[str, Any]]
    final_response: Optional[str]
    error: Optional[str]

