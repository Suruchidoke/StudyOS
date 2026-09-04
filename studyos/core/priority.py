from datetime import datetime
from typing import Dict, Any
from core.models import Task, Subject

IMPORTANCE_MAP = {
    "Low": 25,
    "Medium": 50,
    "High": 75,
    "Critical": 100
}

def calculate_urgency(deadline_str: str) -> float:
    if not deadline_str:
        return 0.0
    
    try:
        deadline = datetime.strptime(str(deadline_str).strip(), "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return 0.0

    today = datetime.now().date()
    days_left = (deadline - today).days

    if days_left <= 0:
        return 100.0
    elif 0 < days_left <= 7:
        # Scale smoothly from 100 down to 50 over 7 days
        return max(50.0, 100.0 - ((50.0 / 7.0) * days_left))
    elif 7 < days_left <= 30:
        # Scale smoothly from 50 down to 0 over days 8-30
        return max(0.0, 50.0 - ((50.0 / 23.0) * (days_left - 7)))
    else:
        return 0.0

def calculate_task_priority(task: Task, subject: Subject) -> Dict[str, Any]:
    """Calculates priority and returns an explainable breakdown."""
    
    # 1. Urgency (40%)
    u_score = calculate_urgency(task.deadline)
    
    # 2. Weakness (30%)
    w_score = max(0.0, min(100.0, 100.0 - float(subject.mastery_percentage)))
    
    # 3. Workload (20%) - Scales against a 4-hour (240 min) benchmark
    rem_mins = max(0, task.remaining_minutes)
    l_score = min(100.0, (rem_mins / 240.0) * 100.0)
    
    # 4. Importance (10%)
    i_score = IMPORTANCE_MAP.get(task.importance, 50.0)

    # Weighted Total
    final_score = max(0.0, min(100.0, (0.40 * u_score) + (0.30 * w_score) + (0.20 * l_score) + (0.10 * i_score)))

    return {
        "task_id": task.id,
        "priority_score": round(final_score, 2),
        "breakdown": {
            "urgency": round(u_score, 2),
            "weakness": round(w_score, 2),
            "workload": round(l_score, 2),
            "importance": round(i_score, 2)
        },
        "explanation": [
            f"Urgency is {round(u_score)}/100 based on the deadline ({task.deadline}).",
            f"Subject weakness is {round(w_score)}/100 (Mastery: {subject.mastery_percentage}%).",
            f"Workload adds {round(l_score)}/100 due to {rem_mins} mins remaining.",
            f"Task importance is rated {task.importance} ({round(i_score)}/100)."
        ]
    }