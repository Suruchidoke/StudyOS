import sys
import os
from datetime import datetime, timedelta

# Ensure studyos root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.models import Subject, Task
from core.priority import calculate_task_priority, calculate_urgency
from core.risk import calculate_subject_risk
from core.planner import generate_daily_plan

def test_priority_engine():
    print("\n--- 1. Testing Priority Engine ---")
    today_str = datetime.now().date().strftime("%Y-%m-%d")
    subject = Subject(id=1, name="DBMS", mastery_percentage=10, importance="Critical", exam_date=today_str)
    task = Task(
        id=1, subject_id=1, title="Normalization", task_type="Revision", 
        deadline=today_str, total_duration_minutes=240, remaining_minutes=240, 
        importance="Critical", status="Pending"
    )
    p_res = calculate_task_priority(task, subject)
    print(f"Priority Score: {p_res['priority_score']}/100")
    assert p_res['priority_score'] > 75, f"Expected >75, got {p_res['priority_score']}"
    print("[PASS] Priority Engine passed.")

def test_urgency_continuity():
    print("\n--- 2. Testing Urgency Continuity & Inversion Fix ---")
    today = datetime.now().date()
    day_0 = today.strftime("%Y-%m-%d")
    day_1 = (today + timedelta(days=1)).strftime("%Y-%m-%d")
    day_7 = (today + timedelta(days=7)).strftime("%Y-%m-%d")
    day_8 = (today + timedelta(days=8)).strftime("%Y-%m-%d")
    day_30 = (today + timedelta(days=30)).strftime("%Y-%m-%d")

    u0 = calculate_urgency(day_0)
    u1 = calculate_urgency(day_1)
    u7 = calculate_urgency(day_7)
    u8 = calculate_urgency(day_8)
    u30 = calculate_urgency(day_30)

    print(f"Urgency Day 0: {u0}, Day 1: {u1:.1f}, Day 7: {u7:.1f}, Day 8: {u8:.1f}, Day 30: {u30:.1f}")
    assert u0 == 100.0, "Day 0 should be 100.0"
    assert u0 >= u1, "Day 0 must be >= Day 1"
    assert u1 > u7, "Day 1 must be > Day 7"
    assert u7 > u8, f"Day 7 ({u7}) MUST be greater than Day 8 ({u8}) to prevent inversion!"
    assert u8 > u30, "Day 8 must be > Day 30"
    print("[PASS] Urgency continuity verified with no inversions.")

def test_risk_engine():
    print("\n--- 3. Testing Risk Engine & Skipped Tasks ---")
    today_str = datetime.now().date().strftime("%Y-%m-%d")
    subject = Subject(id=1, name="DBMS", mastery_percentage=10, importance="Critical", exam_date=today_str)
    
    # Subject with pending task
    pending_task = Task(
        id=1, subject_id=1, title="Normalization", task_type="Revision", 
        deadline=today_str, total_duration_minutes=240, remaining_minutes=240, 
        importance="Critical", status="Pending"
    )
    r_pending = calculate_subject_risk(subject, [pending_task])
    print(f"Risk with Pending Task: {r_pending['risk_level']} ({r_pending['risk_score']})")
    assert r_pending['risk_level'] in ["High", "Critical"], "Risk engine failed to flag critical subject."

    # Subject with skipped task (should NOT decrease risk score compared to completed)
    skipped_task = Task(
        id=2, subject_id=1, title="Normalization", task_type="Revision", 
        deadline=today_str, total_duration_minutes=240, remaining_minutes=240, 
        importance="Critical", status="Skipped"
    )
    r_skipped = calculate_subject_risk(subject, [skipped_task])
    print(f"Risk with Skipped Task: {r_skipped['risk_level']} ({r_skipped['risk_score']})")
    assert r_skipped['risk_score'] == r_pending['risk_score'], "Skipping tasks should not lower academic risk!"
    assert any("skipped" in r.lower() for r in r_skipped['reasons']), "Reasons should mention skipped tasks."
    print("[PASS] Risk Engine and skipped task handling passed.")

def test_adaptive_planner():
    print("\n--- 4. Testing Adaptive Planner & Starvation Prevention ---")
    today_str = datetime.now().date().strftime("%Y-%m-%d")
    sub1 = Subject(id=1, name="DBMS", mastery_percentage=20, importance="Critical", exam_date=today_str)
    sub2 = Subject(id=2, name="OS", mastery_percentage=30, importance="High", exam_date=today_str)
    subjects_dict = {1: sub1, 2: sub2}

    task1 = Task(id=1, subject_id=1, title="DBMS Heavy", task_type="Revision", deadline=today_str, total_duration_minutes=240, remaining_minutes=240, importance="Critical", status="Pending")
    task2 = Task(id=2, subject_id=2, title="OS Core", task_type="Revision", deadline=today_str, total_duration_minutes=60, remaining_minutes=60, importance="High", status="Pending")

    plan = generate_daily_plan(available_minutes=120, tasks=[task1, task2], subjects_dict=subjects_dict)
    scheduled_tasks = [s["task_id"] for s in plan["schedule"]]
    print(f"Total Chunks Scheduled: {len(plan['schedule'])}, Task IDs: {scheduled_tasks}")

    assert plan['schedule'][0]['chunk_minutes'] <= 60, "Planner chunk exceeded MAX_CHUNK_MINUTES."
    assert 1 in scheduled_tasks and 2 in scheduled_tasks, "Both high-priority tasks should be scheduled (no starvation)."
    assert plan['total_scheduled_minutes'] == 120, f"Expected 120 scheduled minutes, got {plan['total_scheduled_minutes']}"
    print("[PASS] Adaptive Planner passed.")

def test_model_nan_sanitization():
    print("\n--- 5. Testing Model NaN and Null Sanitization ---")
    import numpy as np
    sub_nan = Subject(name="Math", mastery_percentage=50, importance="High", exam_date=np.nan)
    assert sub_nan.exam_date is None, "NaN exam_date must be sanitized to None"

    sub_empty = Subject(name="Physics", mastery_percentage=40, importance="Medium", exam_date="   ")
    assert sub_empty.exam_date is None, "Whitespace exam_date must be sanitized to None"

    task_neg = Task(subject_id=1, title="Test", task_type="Revision", deadline="2026-09-10", total_duration_minutes=60, remaining_minutes=-10, importance="Low", status="Pending")
    assert task_neg.remaining_minutes == 0, "Negative remaining minutes must clamp to 0"
    print("[PASS] Model sanitization passed.")

def test_ai_tools_crud():
    print("\n--- 6. Testing AI Tools (Create, Update, Delete for Tasks & Subjects) ---")
    from ai.tools import (
        create_subject, create_task, update_task_status,
        update_subject_details, delete_task_by_id, delete_subject_by_id
    )
    from core.crud import get_subject_by_name, get_task_by_title

    # 1. Create subject via AI tool
    res_sub = create_subject(name="Discrete Math", mastery_percentage=45, importance="High", exam_date="2026-10-15")
    print(res_sub)
    assert "created successfully" in res_sub

    # 2. Lookup subject
    sub = get_subject_by_name("Discrete Math")
    assert sub is not None, "Subject should exist in DB"
    sub_id = sub.id

    # 3. Create task via AI tool using subject name
    res_task = create_task(
        subject_id_or_name="Discrete Math",
        title="Graph Theory HW",
        task_type="Assignment",
        deadline="2026-09-12",
        total_duration_minutes=90,
        importance="High"
    )
    print(res_task)
    assert "added for subject" in res_task

    # 4. Lookup task
    task = get_task_by_title("Graph Theory HW")
    assert task is not None, "Task should exist in DB"
    task_id = task.id

    # 5. Update task status via AI tool
    res_up_task = update_task_status(task_id=task_id, status="Completed", remaining_minutes=0)
    print(res_up_task)
    assert "updated to 'Completed'" in res_up_task

    # 6. Delete task via AI tool
    res_del_task = delete_task_by_id(task_id=task_id)
    print(res_del_task)
    assert "permanently deleted" in res_del_task

    # 7. Delete subject via AI tool
    res_del_sub = delete_subject_by_id(subject_id=sub_id)
    print(res_del_sub)
    assert "have been deleted" in res_del_sub
    print("[PASS] AI Chatbot Tools CRUD verified.")

def run_tests():
    test_priority_engine()
    test_urgency_continuity()
    test_risk_engine()
    test_adaptive_planner()
    test_model_nan_sanitization()
    test_ai_tools_crud()
    print("\n==========================================")
    print("[ALL TESTS PASSED SUCCESSFULLY]")
    print("==========================================")

if __name__ == "__main__":
    run_tests()