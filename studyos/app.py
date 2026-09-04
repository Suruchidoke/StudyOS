import streamlit as st
import pandas as pd
from datetime import datetime

from core.database import init_db
from core.models import Subject, Task
from core.crud import (
    get_all_subjects, get_all_tasks, add_subject, add_task,
    update_task, delete_subject, delete_task
)
from core.priority import calculate_task_priority
from core.risk import calculate_subject_risk
from core.planner import generate_daily_plan

# Initialize DB on first run
init_db()

st.set_page_config(page_title="StudyOS", layout="wide", page_icon="🎓")

# --- Helper to load data into Pydantic models ---
def load_data():
    subjects = get_all_subjects()
    subjects_dict = {s.id: s for s in subjects if s.id is not None}
    tasks_list = get_all_tasks()
    return subjects_dict, tasks_list

# --- UI Routing ---
st.sidebar.title("🎓 StudyOS")
page = st.sidebar.radio("Navigation", ["Dashboard", "My Subjects", "Manage Tasks", "AI Assistant"])
st.sidebar.markdown("---")
available_minutes = st.sidebar.number_input("Today's Available Time (mins)", min_value=30, max_value=600, value=120, step=30)

subjects_dict, tasks_list = load_data()

# ==========================================
# PAGE 1: DASHBOARD (The Core MVP)
# ==========================================
if page == "Dashboard":
    st.title("StudyOS Dashboard")
    
    if not subjects_dict:
        st.warning("Welcome to StudyOS! Please add your first Subject and Task using the sidebar to generate a plan.")
        st.stop()
        
    # Run the Engines
    plan_result = generate_daily_plan(available_minutes, tasks_list, subjects_dict)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("🎯 Next Best Action")
        if plan_result["schedule"]:
            nba = plan_result["schedule"][0]
            st.success(f"**Study {nba['subject_name']}: {nba['task_title']}** for **{nba['chunk_minutes']} minutes**.")
            with st.expander("Why is this my top priority?"):
                for reason in nba['reasons']:
                    st.write(f"- {reason}")
        else:
            st.info("No pending tasks! Enjoy your day.")

        st.subheader("📅 Today's Adaptive Plan")
        if plan_result["schedule"]:
            # Format schedule for display
            display_plan = []
            for item in plan_result["schedule"]:
                display_plan.append({
                    "Subject": item["subject_name"],
                    "Task": item["task_title"],
                    "Type": item["task_type"],
                    "Time Allocation": f"{item['chunk_minutes']} mins",
                    "Priority Score": item["priority_score"]
                })
            st.dataframe(pd.DataFrame(display_plan), use_container_width=True)
            st.caption(f"Total time scheduled: {plan_result['total_scheduled_minutes']} mins. Unused time: {plan_result['unscheduled_minutes']} mins.")
        else:
            st.caption("No scheduled study sessions for today.")
        
    with col2:
        st.subheader("⚠️ Academic Risk")
        for sub_id, subject in subjects_dict.items():
            sub_tasks = [t for t in tasks_list if t.subject_id == sub_id]
            risk_data = calculate_subject_risk(subject, sub_tasks)
            
            # Choose color based on risk
            color = "green"
            if risk_data["risk_level"] == "Medium":
                color = "orange"
            elif risk_data["risk_level"] in ["High", "Critical"]:
                color = "red"
            
            st.markdown(f"**{subject.name}**: :{color}[{risk_data['risk_level']}] (Score: {risk_data['risk_score']})")
            with st.expander(f"View {subject.name} Risk Factors (ID: {sub_id})"):
                for reason in risk_data["reasons"]:
                    st.write(f"- {reason}")

# ==========================================
# PAGE 2: MY SUBJECTS
# ==========================================
elif page == "My Subjects":
    st.title("My Subjects")
    
    with st.form("add_subject_form"):
        st.subheader("Add New Subject")
        s_name = st.text_input("Subject Name (e.g., DBMS)")
        s_mastery = st.slider("Current Mastery (%)", 0, 100, 50)
        s_importance = st.selectbox("Importance", ["Low", "Medium", "High", "Critical"])
        s_exam = st.date_input("Exam Date (Optional)", value=None)
        
        if st.form_submit_button("Add Subject"):
            if s_name.strip():
                new_sub = Subject(
                    name=s_name.strip(),
                    mastery_percentage=int(s_mastery),
                    importance=s_importance,
                    exam_date=str(s_exam) if s_exam else None
                )
                add_subject(new_sub)
                st.success(f"Added {s_name}!")
                st.rerun()
            else:
                st.error("Please enter a subject name.")

    if subjects_dict:
        st.subheader("Current Subjects")
        subjects_data = [
            {
                "ID": s.id,
                "Name": s.name,
                "Mastery %": s.mastery_percentage,
                "Importance": s.importance,
                "Exam Date": s.exam_date if s.exam_date else "None"
            }
            for s in subjects_dict.values()
        ]
        st.dataframe(pd.DataFrame(subjects_data), use_container_width=True)

        col_edit, col_del = st.columns([1, 1])
        with col_edit:
            with st.expander("✏️ Edit Subject Details"):
                edit_sub_id = st.selectbox(
                    "Subject to Edit",
                    options=list(subjects_dict.keys()),
                    format_func=lambda x: f"{subjects_dict[x].name} (ID: {x})",
                    key="edit_sub_select"
                )
                curr_sub = subjects_dict[edit_sub_id]
                new_m = st.slider("Update Mastery (%)", 0, 100, curr_sub.mastery_percentage, key="edit_mastery_slider")
                new_imp = st.selectbox("Update Importance", ["Low", "Medium", "High", "Critical"], index=["Low", "Medium", "High", "Critical"].index(curr_sub.importance), key="edit_imp_select")
                new_dt = st.date_input("Update Exam Date", value=datetime.strptime(curr_sub.exam_date, "%Y-%m-%d").date() if curr_sub.exam_date else None, key="edit_date_input")
                
                from core.crud import update_subject
                if st.button("Save Subject Changes", key="save_sub_btn"):
                    update_subject(edit_sub_id, mastery_percentage=new_m, importance=new_imp, exam_date=str(new_dt) if new_dt else "")
                    st.success("Subject updated!")
                    st.rerun()

        with col_del:
            with st.expander("🗑️ Delete a Subject"):
                del_sub_id = st.selectbox(
                    "Select Subject to Delete",
                    options=list(subjects_dict.keys()),
                    format_func=lambda x: f"{subjects_dict[x].name} (ID: {x})",
                    key="del_sub_select"
                )
                if st.button("Delete Subject & Its Tasks", type="primary", key="del_sub_btn"):
                    delete_subject(del_sub_id)
                    st.success("Subject and associated tasks deleted!")
                    st.rerun()

# ==========================================
# PAGE 3: MANAGE TASKS
# ==========================================
elif page == "Manage Tasks":
    st.title("Manage Tasks")
    
    if not subjects_dict:
        st.warning("Please add a subject first.")
        st.stop()
        
    with st.form("add_task_form"):
        st.subheader("Add New Task (Manual)")
        t_sub = st.selectbox("Subject", options=list(subjects_dict.keys()), format_func=lambda x: f"{subjects_dict[x].name} (ID: {x})")
        t_title = st.text_input("Task Title (e.g., Normalization Revision)")
        t_type = st.selectbox("Task Type", ["Revision", "Assignment", "Project", "Exam Prep"])
        t_deadline = st.date_input("Deadline")
        t_dur = st.number_input("Estimated Duration (mins)", min_value=15, value=60, step=15)
        t_imp = st.selectbox("Importance", ["Medium", "High", "Critical", "Low"])
        
        if st.form_submit_button("Add Task"):
            if t_title.strip():
                new_task = Task(
                    subject_id=t_sub,
                    title=t_title.strip(),
                    task_type=t_type,
                    deadline=str(t_deadline),
                    total_duration_minutes=int(t_dur),
                    remaining_minutes=int(t_dur),
                    importance=t_imp,
                    status="Pending"
                )
                add_task(new_task)
                st.success(f"Added {t_title}!")
                st.rerun()
            else:
                st.error("Please enter a task title.")

    tasks = get_all_tasks()
    if tasks:
        st.subheader("⚡ Quick Manual Actions")
        st.caption("One-click buttons to complete, skip, or delete any task directly.")

        for t in tasks:
            col_t_info, col_t_actions = st.columns([3, 2])
            with col_t_info:
                sub_name = subjects_dict.get(t.subject_id, Subject(name="Unknown", mastery_percentage=0, importance="Low")).name
                status_color = "gray"
                if t.status == "Completed":
                    status_color = "green"
                elif t.status == "In Progress":
                    status_color = "blue"
                elif t.status == "Skipped":
                    status_color = "red"
                elif t.status == "Pending":
                    status_color = "orange"
                    
                st.markdown(f"**{t.title}** ({sub_name}) — :{status_color}[{t.status}] | **{t.remaining_minutes}m left** | Due: {t.deadline}")
                
            with col_t_actions:
                c1, c2, c3 = st.columns(3)
                with c1:
                    if t.status != "Completed":
                        if st.button("✅ Done", key=f"done_{t.id}", help="Mark as Completed"):
                            update_task(t.id, "Completed", 0)
                            st.rerun()
                with c2:
                    if t.status != "Skipped":
                        if st.button("⏭️ Skip", key=f"skip_{t.id}", help="Mark as Skipped"):
                            update_task(t.id, "Skipped", t.remaining_minutes)
                            st.rerun()
                with c3:
                    if st.button("🗑️ Delete", key=f"del_{t.id}", help="Permanently delete"):
                        delete_task(t.id)
                        st.rerun()

        st.markdown("---")
        st.subheader("📊 Bulk Task Editor")
        st.info("💡 Edit 'status' or 'remaining_minutes' in bulk below and click Save.")
        
        table_rows = [
            {
                "id": t.id,
                "subject": subjects_dict.get(t.subject_id, Subject(name="Unknown", mastery_percentage=0, importance="Low")).name,
                "title": t.title,
                "status": t.status,
                "remaining_minutes": t.remaining_minutes,
                "deadline": t.deadline
            }
            for t in tasks
        ]
        df = pd.DataFrame(table_rows)
        
        edited_df = st.data_editor(
            df,
            key="task_editor",
            disabled=["id", "subject", "title", "deadline"],
            column_config={
                "status": st.column_config.SelectboxColumn(
                    "Status",
                    options=["Pending", "In Progress", "Completed", "Skipped"],
                    required=True
                ),
                "remaining_minutes": st.column_config.NumberColumn(
                    "Remaining (mins)",
                    min_value=0,
                    step=15,
                    required=True
                )
            },
            use_container_width=True
        )
        
        if st.button("💾 Save Bulk Changes & Replan"):
            for _, row in edited_df.iterrows():
                update_task(int(row["id"]), str(row["status"]), int(row["remaining_minutes"]))
            st.success("Database updated! The schedule has adapted.")
            st.rerun()

# ==========================================
# PAGE 4: AI ASSISTANT (Chat-Driven Operations)
# ==========================================
elif page == "AI Assistant":
    st.title("🤖 StudyOS AI Assistant")
    st.caption("Ask questions, or manage tasks and subjects entirely through natural conversation!")

    from ai.assistant import get_chat_session
    
    # Initialize chat session in Streamlit state
    if "chat_session" not in st.session_state:
        session = get_chat_session()
        if session:
            st.session_state.chat_session = session
            st.session_state.messages = []
        else:
            st.error("Missing GEMINI_API_KEY in .env file.")
            st.stop()
            
    # Starter chip buttons for natural interaction
    st.markdown("**💡 Quick AI Commands (Click to use):**")
    chip_col1, chip_col2, chip_col3 = st.columns(3)
    suggested_prompt = None
    with chip_col1:
        if st.button("📋 What should I study today?"):
            suggested_prompt = "What should I study today and what are my highest priority tasks?"
    with chip_col2:
        if st.button("📊 Show my academic status & risks"):
            suggested_prompt = "Give me a full overview of my subjects, mastery levels, and risk bottlenecks."
    with chip_col3:
        if st.button("➕ Add a 60-min Revision task"):
            suggested_prompt = "Please add a 60-minute Revision task for DBMS called 'SQL Indexing' due tomorrow."

    # Display chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
    # Chat input
    user_input = st.chat_input("E.g. 'Add task...', 'Mark task 2 complete', 'Delete DBMS', 'What to study?'")
    active_prompt = suggested_prompt or user_input
    
    if active_prompt:
        st.session_state.messages.append({"role": "user", "content": active_prompt})
        with st.chat_message("user"):
            st.markdown(active_prompt)
            
        with st.chat_message("assistant"):
            with st.spinner("Executing request and analyzing academic state..."):
                try:
                    response = st.session_state.chat_session.send_message(
                        f"Today's date is {datetime.now().date().strftime('%Y-%m-%d')}. My available time today is {available_minutes} minutes. User prompt: {active_prompt}"
                    )
                    reply_text = response.text if (response and hasattr(response, "text")) else "No response generated."
                    st.markdown(reply_text)
                    st.session_state.messages.append({"role": "assistant", "content": reply_text})
                except Exception as e:
                    err_msg = f"⚠️ Assistant Error: {str(e)}"
                    st.error(err_msg)
                    st.session_state.messages.append({"role": "assistant", "content": err_msg})