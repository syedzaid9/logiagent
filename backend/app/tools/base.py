from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

def normalize_role(role: Optional[str]) -> str:
    if not role:
        return ""
    return role.strip().upper().replace(" ", "_")

class BaseAgentTool(ABC):
    name: str = ""
    description: str = ""
    required_permissions: List[str] = []
    allowed_roles: List[str] = ["Admin", "Logistics Manager", "Dispatcher", "Driver", "Operations Team"]
    data_scope: str = "operational"
    user_context: Optional[Dict[str, Any]] = None

    def is_authorized_for_role(self, role: Optional[str]) -> bool:
        if not role:
            return False
        norm = normalize_role(role)
        if norm == "ADMIN":
            return True
        allowed_norms = [normalize_role(r) for r in self.allowed_roles]
        return norm in allowed_norms or role in self.allowed_roles

    def check_authorization(self, user_context: Optional[Dict[str, Any]]) -> tuple[bool, Optional[str]]:
        ctx = user_context or getattr(self, "user_context", None)
        if not ctx:
            # Standalone execution / automated testing default
            return True, None
        
        role = ctx.get("role")
        if not role:
            return True, None
            
        if not self.is_authorized_for_role(role):
            return False, f"Access denied. Role '{role}' lacks authorization to execute '{self.name}'."
        
        return True, None

    @abstractmethod
    def execute(self, user_context: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        """Execute the tool logic and return structured result dictionary."""
        pass

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "required_permissions": self.required_permissions,
            "allowed_roles": self.allowed_roles,
            "data_scope": self.data_scope
        }
