from pydantic import BaseModel, Field
from enum import Enum

class PlanStatus(str, Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"

class PlanItem(BaseModel):
    content : str = Field(min_length=1)
    status : PlanStatus = PlanStatus.pending
    active_form : str = ""    
    
class PlanningState(BaseModel):
    items: list[PlanItem] = Field(default_factory=list)
    rounds_since_update: int = 0
    
