import math
from pydantic import BaseModel, field_validator
from typing import Optional, Any

class Subject(BaseModel):
    id: Optional[int] = None
    name: str
    mastery_percentage: int  # 0 to 100
    importance: str          # Low, Medium, High, Critical
    exam_date: Optional[str] = None # YYYY-MM-DD

    @field_validator('exam_date', mode='before')
    @classmethod
    def sanitize_exam_date(cls, v: Any) -> Optional[str]:
        if v is None:
            return None
        if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
            return None
        s = str(v).strip()
        if not s or s.lower() in ("none", "nan", "nat"):
            return None
        return s

class Task(BaseModel):
    id: Optional[int] = None
    subject_id: int
    title: str
    task_type: str           
    deadline: str            # YYYY-MM-DD
    total_duration_minutes: int
    remaining_minutes: int
    importance: str          
    status: str              # Pending, In Progress, Completed, Skipped

    @field_validator('remaining_minutes', mode='before')
    @classmethod
    def sanitize_remaining_minutes(cls, v: Any) -> int:
        try:
            val = int(v)
            return max(0, val)
        except (ValueError, TypeError):
            return 0