from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

class ToolCallDetail(BaseModel):
    tool_name: str
    tool_input: Dict[str, Any]
    tool_output: Any
    success: bool = True
    execution_time_ms: float = 0.0

class AgentSource(BaseModel):
    title: str
    document_code: str
    category: str
    snippet: str

class AgentChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000, description="User operational query message")
    conversation_id: Optional[str] = Field(None, max_length=255)
    user_role: Optional[str] = Field("Logistics Manager", max_length=100)

class AgentChatResponse(BaseModel):
    conversation_id: str
    user_query: str
    response: str
    actions_performed: List[str] = [] # Concise chain e.g. ["Checked shipment database", "Filtered delayed shipments", "Calculated delay duration"]
    tools_used: List[str] = []
    tool_calls: List[ToolCallDetail] = []
    structured_data: Optional[Dict[str, Any]] = None # Table/cards/route data for direct UI widget rendering
    sources: List[AgentSource] = [] # RAG references if used
    latency_ms: float = 0.0
    timestamp: datetime = datetime.utcnow()

class SuggestedPrompt(BaseModel):
    label: str
    query: str
    category: str

class AgentCapabilitiesResponse(BaseModel):
    role: str
    user_name: str
    user_email: str
    permissions: List[str]
    allowed_tools: List[str]
    allowed_document_categories: List[str]
    operational_scope: Dict[str, Any] # e.g. driver_id, vehicle_id, driver_code
    suggested_prompts: List[SuggestedPrompt]
