from datetime import datetime
from typing import Optional
from core.crud import (
    get_all_subjects, get_all_tasks, get_subject_by_id, get_subject_by_name,
    add_subject, update_subject, delete_subject,
    get_task_by_id, add_task, update_task, delete_task
)
from core.models import Subject, Task
from core.planner import generate_daily_plan
from core.risk import calculate_subject_risk

def get_academic_status() -> dict:
    """Use this to understand the student's complete academic state: all subjects, their tasks, mastery levels, and risk bottlenecks."""
    subjects = get_all_subjects()
    if not subjects:
        return {"status": "No subjects found in database."}

    tasks = get_all_tasks()
    status_report = []
    for subject in subjects:
        sub_tasks = [t for t in tasks if t.subject_id == subject.id]
        risk = calculate_subject_risk(subject, sub_tasks)
        status_report.append({
            "subject_id": subject.id,
            "subject": subject.name,
            "mastery": f"{subject.mastery_percentage}%",
            "importance": subject.importance,
            "exam_date": subject.exam_date if subject.exam_date else "None specified",
            "risk_level": risk["risk_level"],
            "risk_score": risk["risk_score"],
            "reasons": risk["reasons"],
            "tasks": [
                {
                    "task_id": t.id,
                    "title": t.title,
                    "type": t.task_type,
                    "status": t.status,
                    "remaining_minutes": t.remaining_minutes,
                    "deadline": t.deadline
                }
                for t in sub_tasks
            ]
        })
    return {"academic_status": status_report}

def get_study_plan(available_minutes: int) -> dict:
    """Use this to generate the prioritized study schedule for today based on available minutes."""
    try:
        available_minutes = max(0, int(available_minutes))
    except (ValueError, TypeError):
        available_minutes = 60

    subjects = get_all_subjects()
    if not subjects:
        return {"schedule": [], "message": "No subjects found. Please add subjects first."}

    tasks = get_all_tasks()
    subjects_dict = {s.id: s for s in subjects if s.id is not None}
    plan = generate_daily_plan(available_minutes, tasks, subjects_dict)
    return plan

def create_subject(name: str, mastery_percentage: int, importance: str, exam_date: str = "") -> str:
    """Use this when a student wants to add a new academic subject.
    - name: Name of the subject (e.g., 'DBMS', 'Operating Systems').
    - mastery_percentage: Current estimated mastery between 0 and 100.
    - importance: One of 'Low', 'Medium', 'High', 'Critical'.
    - exam_date: Optional exam date in 'YYYY-MM-DD' format, or empty string if not known.
    """
    clean_name = name.strip()
    if not clean_name:
        return "Error: Subject name cannot be empty."

    valid_importances = {"Low", "Medium", "High", "Critical"}
    clean_importance = importance.strip().title() if importance else "Medium"
    if clean_importance not in valid_importances:
        clean_importance = "Medium"

    mastery = max(0, min(100, int(mastery_percentage)))
    clean_exam_date = exam_date.strip() if exam_date and exam_date.strip() else None

    new_sub = Subject(
        name=clean_name,
        mastery_percentage=mastery,
        importance=clean_importance,
        exam_date=clean_exam_date
    )
    sub_id = add_subject(new_sub)
    return f"Subject '{clean_name}' created successfully with ID {sub_id} (Mastery: {mastery}%, Importance: {clean_importance}, Exam: {clean_exam_date or 'None'})."

def update_subject_details(subject_id: int, mastery_percentage: int = -1, importance: str = "", exam_date: str = "") -> str:
    """Use this when a student wants to update an existing subject's mastery, importance, or exam date.
    - subject_id: The ID of the subject to update.
    - mastery_percentage: New mastery 0-100 (or -1 to leave unchanged).
    - importance: New importance 'Low', 'Medium', 'High', 'Critical' (or empty to leave unchanged).
    - exam_date: New exam date 'YYYY-MM-DD' (or empty to leave unchanged).
    """
    sub = get_subject_by_id(subject_id)
    if not sub:
        return f"Error: Subject with ID {subject_id} not found."

    m = mastery_percentage if 0 <= mastery_percentage <= 100 else None
    imp = importance.strip().title() if importance.strip().title() in ["Low", "Medium", "High", "Critical"] else None
    dt = exam_date.strip() if exam_date.strip() else None

    success = update_subject(subject_id, mastery_percentage=m, importance=imp, exam_date=dt)
    if success:
        return f"Subject ID {subject_id} ('{sub.name}') updated successfully."
    return f"Failed to update subject ID {subject_id}."

def delete_subject_by_id(subject_id: int) -> str:
    """Use this when a student wants to delete a subject and all its related tasks.
    - subject_id: The ID of the subject to delete.
    """
    sub = get_subject_by_id(subject_id)
    if not sub:
        return f"Error: Subject with ID {subject_id} not found."

    success = delete_subject(subject_id)
    if success:
        return f"Subject '{sub.name}' (ID {subject_id}) and all its associated tasks have been deleted."
    return f"Failed to delete subject ID {subject_id}."

def create_task(
    subject_id_or_name: str,
    title: str,
    task_type: str,
    deadline: str,
    total_duration_minutes: int,
    importance: str
) -> str:
    """Use this when a student wants to add a new study task, assignment, revision, or project.
    - subject_id_or_name: Either the numeric subject ID (e.g. '1') or the exact subject name (e.g. 'DBMS').
    - title: Title of the task (e.g., 'Chapter 3 Normalization', 'SQL Lab Assignment').
    - task_type: One of 'Revision', 'Assignment', 'Project', 'Exam Prep'.
    - deadline: Due date in 'YYYY-MM-DD' format. If student says 'tomorrow', calculate YYYY-MM-DD.
    - total_duration_minutes: Estimated time in minutes (e.g., 60, 90, 120).
    - importance: One of 'Low', 'Medium', 'High', 'Critical'.
    """
    # 1. Resolve subject
    subject = None
    if str(subject_id_or_name).strip().isdigit():
        subject = get_subject_by_id(int(subject_id_or_name.strip()))
    if not subject:
        subject = get_subject_by_name(str(subject_id_or_name).strip())

    if not subject:
        all_subs = get_all_subjects()
        names = [f"{s.name} (ID: {s.id})" for s in all_subs]
        return f"Error: Could not identify subject '{subject_id_or_name}'. Available subjects: {', '.join(names) if names else 'None'}. Please create the subject first."

    # 2. Sanitize task details
    clean_title = title.strip()
    if not clean_title:
        return "Error: Task title cannot be empty."

    valid_types = {"Revision", "Assignment", "Project", "Exam Prep"}
    clean_type = task_type.strip().title() if task_type else "Revision"
    if clean_type not in valid_types:
        clean_type = "Revision"

    valid_importances = {"Low", "Medium", "High", "Critical"}
    clean_imp = importance.strip().title() if importance else "Medium"
    if clean_imp not in valid_importances:
        clean_imp = "Medium"

    duration = max(15, int(total_duration_minutes)) if total_duration_minutes else 60

    new_task = Task(
        subject_id=subject.id,
        title=clean_title,
        task_type=clean_type,
        deadline=str(deadline).strip(),
        total_duration_minutes=duration,
        remaining_minutes=duration,
        importance=clean_imp,
        status="Pending"
    )
    task_id = add_task(new_task)
    return f"Task '{clean_title}' added for subject '{subject.name}' (ID: {task_id}, Type: {clean_type}, Duration: {duration} mins, Deadline: {deadline}). Schedule has adapted."

def update_task_status(task_id: int, status: str, remaining_minutes: int) -> str:
    """Use this when a student completes, skips, starts, or updates remaining time on a task.
    - task_id: The ID of the task to update.
    - status: 'Pending', 'In Progress', 'Completed', or 'Skipped'.
    - remaining_minutes: Minutes remaining (0 if completed).
    """
    valid_statuses = {"Pending", "In Progress", "Completed", "Skipped"}
    normalized_status = status.strip().title() if status else "Pending"
    if normalized_status not in valid_statuses:
        if normalized_status in ("Done", "Finished", "Complete"):
            normalized_status = "Completed"
        elif normalized_status in ("Skip", "Missed"):
            normalized_status = "Skipped"
        else:
            normalized_status = "Pending"

    if normalized_status == "Completed":
        remaining_minutes = 0
    else:
        try:
            remaining_minutes = max(0, int(remaining_minutes))
        except (ValueError, TypeError):
            remaining_minutes = 0

    success = update_task(task_id, normalized_status, remaining_minutes)
    if success:
        return f"Task {task_id} successfully updated to '{normalized_status}' with {remaining_minutes} mins remaining. Priorities and schedule have adapted."
    else:
        return f"Task with ID {task_id} was not found in the database."

def delete_task_by_id(task_id: int) -> str:
    """Use this when a student wants to delete or remove a task.
    - task_id: The ID of the task to delete.
    """
    task = get_task_by_id(task_id)
    if not task:
        return f"Error: Task with ID {task_id} not found."

    success = delete_task(task_id)
    if success:
        return f"Task '{task.title}' (ID {task_id}) has been permanently deleted from your schedule."
    return f"Failed to delete task ID {task_id}."