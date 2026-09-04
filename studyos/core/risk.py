from datetime import datetime
from typing import Dict, Any, List
from core.models import Subject, Task
from core.priority import calculate_urgency

def calculate_subject_risk(subject: Subject, subject_tasks: List[Task]) -> Dict[str, Any]:
    """Calculates overall risk level for a subject."""
    
    # 1. Exam Urgency (45%)
    e_score = calculate_urgency(subject.exam_date) if subject.exam_date else 0.0
    
    # 2. Weakness (35%)
    w_score = max(0.0, min(100.0, 100.0 - float(subject.mastery_percentage)))
    
    # 3. Unfinished Workload Ratio (20%) 
    # Benchmark against an arbitrary 10 hours (600 mins) total expected study per subject.
    # Note: Skipped tasks still count toward unfinished academic debt.
    unfinished_tasks = [t for t in subject_tasks if t.status in ["Pending", "In Progress", "Skipped"]]
    total_remaining = sum(max(0, t.remaining_minutes) for t in unfinished_tasks)
    skipped_count = sum(1 for t in subject_tasks if t.status == "Skipped")
    
    u_score = min(100.0, (total_remaining / 600.0) * 100.0)
    
    risk_score = max(0.0, min(100.0, (0.45 * e_score) + (0.35 * w_score) + (0.20 * u_score)))
    risk_score = round(risk_score, 2)

    # Categorize Risk
    if risk_score < 40:
        level = "Low"
    elif risk_score < 65:
        level = "Medium"
    elif risk_score < 85:
        level = "High"
    else:
        level = "Critical"

    reasons = [
        f"Exam urgency is {round(e_score)}/100." if subject.exam_date else "No upcoming exam date set.",
        f"Mastery is {subject.mastery_percentage}%.",
        f"There are {total_remaining} minutes of unfinished tasks."
    ]
    if skipped_count > 0:
        reasons.append(f"{skipped_count} task(s) currently skipped.")

    return {
        "subject_id": subject.id,
        "risk_level": level,
        "risk_score": risk_score,
        "breakdown": {
            "exam_urgency": round(e_score, 2),
            "weakness": round(w_score, 2),
            "unfinished_workload": round(u_score, 2)
        },
        "reasons": reasons
    }