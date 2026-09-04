from typing import List, Dict, Any
from core.models import Task, Subject
from core.priority import calculate_task_priority

# Tasks longer than this will be split into multiple study sessions
MAX_CHUNK_MINUTES = 60 

def generate_daily_plan(available_minutes: int, tasks: List[Task], subjects_dict: Dict[int, Subject]) -> Dict[str, Any]:
    """Generates an adaptive, balanced chunked schedule based on priority and available daily time."""
    if available_minutes <= 0:
        return {
            "total_scheduled_minutes": 0,
            "schedule": [],
            "unscheduled_minutes": 0
        }

    # 1. Filter out completed/skipped tasks or those with no time remaining
    active_tasks = [t for t in tasks if t.status in ["Pending", "In Progress"] and t.remaining_minutes > 0]
    
    # 2. Calculate priorities dynamically based on current state
    prioritized_tasks = []
    for task in active_tasks:
        subject = subjects_dict.get(task.subject_id)
        if not subject:
            continue
            
        priority_data = calculate_task_priority(task, subject)
        prioritized_tasks.append({
            "task": task,
            "subject": subject,
            "priority_score": priority_data["priority_score"],
            "explanation": priority_data["explanation"],
            "remaining": max(0, task.remaining_minutes)
        })
        
    # 3. Sort by priority score (highest first)
    prioritized_tasks.sort(key=lambda x: x["priority_score"], reverse=True)
    
    # 4. Allocate time chunks using priority round-robin to prevent starvation of other subjects
    schedule = []
    minutes_left_today = available_minutes
    
    while minutes_left_today > 0:
        chunks_added_this_pass = 0
        for p_task in prioritized_tasks:
            if minutes_left_today <= 0:
                break
            if p_task["remaining"] <= 0:
                continue

            task = p_task["task"]
            subject = p_task["subject"]
            chunk_size = min(MAX_CHUNK_MINUTES, p_task["remaining"], minutes_left_today)
            
            schedule.append({
                "task_id": task.id,
                "task_title": task.title,
                "subject_name": subject.name,
                "task_type": task.task_type,
                "chunk_minutes": chunk_size,
                "priority_score": p_task["priority_score"],
                "reasons": p_task["explanation"]
            })
            
            p_task["remaining"] -= chunk_size
            minutes_left_today -= chunk_size
            chunks_added_this_pass += 1
            
        if chunks_added_this_pass == 0:
            break
            
    return {
        "total_scheduled_minutes": available_minutes - minutes_left_today,
        "schedule": schedule,
        "unscheduled_minutes": minutes_left_today
    }