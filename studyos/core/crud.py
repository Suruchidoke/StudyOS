from typing import List, Optional
from core.database import get_connection
from core.models import Subject, Task

def add_subject(subject: Subject) -> int:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO subjects (name, mastery_percentage, importance, exam_date) VALUES (?, ?, ?, ?)",
            (subject.name, subject.mastery_percentage, subject.importance, subject.exam_date)
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()

def get_all_subjects() -> List[Subject]:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, mastery_percentage, importance, exam_date FROM subjects")
        rows = cursor.fetchall()
        return [Subject(id=r[0], name=r[1], mastery_percentage=r[2], importance=r[3], exam_date=r[4]) for r in rows]
    finally:
        conn.close()

def get_subject_by_id(subject_id: int) -> Optional[Subject]:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, mastery_percentage, importance, exam_date FROM subjects WHERE id = ?", (subject_id,))
        r = cursor.fetchone()
        if r:
            return Subject(id=r[0], name=r[1], mastery_percentage=r[2], importance=r[3], exam_date=r[4])
        return None
    finally:
        conn.close()

def get_subject_by_name(name: str) -> Optional[Subject]:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, mastery_percentage, importance, exam_date FROM subjects WHERE LOWER(name) = LOWER(?) LIMIT 1", (name.strip(),))
        r = cursor.fetchone()
        if r:
            return Subject(id=r[0], name=r[1], mastery_percentage=r[2], importance=r[3], exam_date=r[4])
        return None
    finally:
        conn.close()

def update_subject(
    subject_id: int,
    name: Optional[str] = None,
    mastery_percentage: Optional[int] = None,
    importance: Optional[str] = None,
    exam_date: Optional[str] = None
) -> bool:
    current = get_subject_by_id(subject_id)
    if not current:
        return False
        
    new_name = name.strip() if name and name.strip() else current.name
    new_mastery = max(0, min(100, mastery_percentage)) if mastery_percentage is not None and mastery_percentage >= 0 else current.mastery_percentage
    new_importance = importance if importance in ["Low", "Medium", "High", "Critical"] else current.importance
    new_exam_date = exam_date if exam_date is not None else current.exam_date
    if new_exam_date == "":
        new_exam_date = None

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE subjects SET name = ?, mastery_percentage = ?, importance = ?, exam_date = ? WHERE id = ?",
            (new_name, new_mastery, new_importance, new_exam_date, subject_id)
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()

def delete_subject(subject_id: int) -> bool:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tasks WHERE subject_id = ?", (subject_id,))
        cursor.execute("DELETE FROM subjects WHERE id = ?", (subject_id,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()

def add_task(task: Task) -> int:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO tasks 
            (subject_id, title, task_type, deadline, total_duration_minutes, remaining_minutes, importance, status) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (task.subject_id, task.title, task.task_type, task.deadline, task.total_duration_minutes, 
             task.remaining_minutes, task.importance, task.status)
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()

def get_task_by_id(task_id: int) -> Optional[Task]:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, subject_id, title, task_type, deadline, total_duration_minutes, remaining_minutes, importance, status FROM tasks WHERE id = ?",
            (task_id,)
        )
        r = cursor.fetchone()
        if r:
            return Task(
                id=r[0], subject_id=r[1], title=r[2], task_type=r[3], deadline=r[4],
                total_duration_minutes=r[5], remaining_minutes=r[6], importance=r[7], status=r[8]
            )
        return None
    finally:
        conn.close()

def get_task_by_title(title: str) -> Optional[Task]:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, subject_id, title, task_type, deadline, total_duration_minutes, remaining_minutes, importance, status FROM tasks WHERE LOWER(title) LIKE LOWER(?) LIMIT 1",
            (f"%{title.strip()}%",)
        )
        r = cursor.fetchone()
        if r:
            return Task(
                id=r[0], subject_id=r[1], title=r[2], task_type=r[3], deadline=r[4],
                total_duration_minutes=r[5], remaining_minutes=r[6], importance=r[7], status=r[8]
            )
        return None
    finally:
        conn.close()

def get_all_tasks() -> List[Task]:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, subject_id, title, task_type, deadline, total_duration_minutes, remaining_minutes, importance, status FROM tasks"
        )
        rows = cursor.fetchall()
        return [
            Task(
                id=r[0], subject_id=r[1], title=r[2], task_type=r[3], deadline=r[4],
                total_duration_minutes=r[5], remaining_minutes=r[6], importance=r[7], status=r[8]
            )
            for r in rows
        ]
    finally:
        conn.close()

def get_pending_tasks() -> List[Task]:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, subject_id, title, task_type, deadline, total_duration_minutes, remaining_minutes, importance, status FROM tasks WHERE status IN ('Pending', 'In Progress')"
        )
        rows = cursor.fetchall()
        return [
            Task(
                id=r[0], subject_id=r[1], title=r[2], task_type=r[3], deadline=r[4],
                total_duration_minutes=r[5], remaining_minutes=r[6], importance=r[7], status=r[8]
            )
            for r in rows
        ]
    finally:
        conn.close()

def update_task(task_id: int, status: str, remaining_minutes: int) -> bool:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE tasks SET status = ?, remaining_minutes = ? WHERE id = ?",
            (status, max(0, remaining_minutes), task_id)
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()

def delete_task(task_id: int) -> bool:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()