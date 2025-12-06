"""
Agentic Calendar - Main Streamlit Application

An intelligent planning assistant that helps users break down goals into
actionable tasks and schedule them into their calendar.
"""

import streamlit as st
from datetime import datetime, timedelta
from typing import Optional
import tempfile
import os

from models import (
    Session, UserInput, GoalUnderstanding, TaskBlock, Resource,
    Availability, PreferredHours, BusyInterval,
)
from storage import create_session, save_session, load_session, list_sessions
from llm_client import get_llm_client, LLMClient
from planner import schedule_tasks, calculate_schedule_stats
from calendar_export import generate_ics_content, preview_schedule_text


# Page configuration
st.set_page_config(
    page_title="Agentic Calendar",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for better styling
st.markdown("""
<style>
    .step-indicator {
        display: flex;
        justify-content: space-between;
        margin-bottom: 2rem;
    }
    .step {
        text-align: center;
        flex: 1;
        padding: 10px;
        border-radius: 5px;
        margin: 0 5px;
    }
    .step-active {
        background-color: #4CAF50;
        color: white;
    }
    .step-completed {
        background-color: #8BC34A;
        color: white;
    }
    .step-pending {
        background-color: #E0E0E0;
        color: #666;
    }
    .task-card {
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #ddd;
        margin-bottom: 1rem;
        background-color: #f9f9f9;
    }
    .task-must {
        border-left: 4px solid #f44336;
    }
    .task-nice {
        border-left: 4px solid #FFC107;
    }
    .stButton > button {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)


# Step definitions
STEPS = [
    ("1. Input", "Enter your goal"),
    ("2. Analysis", "Understanding your goal"),
    ("3. Plan Review", "Review and edit tasks"),
    ("4. Scheduling", "Schedule your tasks"),
    ("5. Export", "Export to calendar"),
]


def init_session_state():
    """Initialize session state variables."""
    if 'session' not in st.session_state:
        st.session_state.session = create_session()
    if 'llm_provider' not in st.session_state:
        st.session_state.llm_provider = 'openai'
    if 'processing' not in st.session_state:
        st.session_state.processing = False
    if 'error_message' not in st.session_state:
        st.session_state.error_message = None


def get_llm() -> Optional[LLMClient]:
    """Get LLM client with error handling."""
    try:
        return get_llm_client(st.session_state.llm_provider)
    except Exception as e:
        st.session_state.error_message = str(e)
        return None


def render_step_indicator(current_step: int):
    """Render the step progress indicator."""
    cols = st.columns(len(STEPS))

    for i, (title, desc) in enumerate(STEPS):
        with cols[i]:
            if i < current_step:
                st.success(f"✓ {title}")
            elif i == current_step:
                st.info(f"● {title}")
            else:
                st.text(f"○ {title}")


def render_sidebar():
    """Render the sidebar with settings and help."""
    with st.sidebar:
        st.title("⚙️ Settings")

        # LLM Provider selection
        provider = st.selectbox(
            "LLM Provider",
            options=["openai", "anthropic"],
            index=0 if st.session_state.llm_provider == "openai" else 1,
            help="Select which AI provider to use",
        )
        if provider != st.session_state.llm_provider:
            st.session_state.llm_provider = provider

        # API Key status
        st.markdown("---")
        st.subheader("API Key Status")

        openai_key = os.getenv("OPENAI_API_KEY")
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")

        if openai_key:
            st.success("OpenAI: Configured ✓")
        else:
            st.warning("OpenAI: Not configured")

        if anthropic_key:
            st.success("Anthropic: Configured ✓")
        else:
            st.warning("Anthropic: Not configured")

        # Help section
        st.markdown("---")
        st.subheader("📚 Help")

        with st.expander("How to use"):
            st.markdown("""
            1. **Enter your goal** - Describe what you want to achieve
            2. **Set a deadline** - When does this need to be done?
            3. **Review the plan** - Edit tasks as needed
            4. **Set availability** - Tell us when you're free
            5. **Export** - Download your schedule as .ics
            """)

        with st.expander("Example goals"):
            st.markdown("""
            - "Prepare for my thesis defense next month"
            - "Learn Python basics in 2 weeks"
            - "Write a research paper by December 15"
            - "Prepare for job interview at Google"
            """)

        # Session management
        st.markdown("---")
        st.subheader("📁 Sessions")

        if st.button("🆕 New Session"):
            st.session_state.session = create_session()
            st.rerun()

        sessions = list_sessions()
        if sessions:
            with st.expander(f"Load Previous ({len(sessions)})"):
                for sess in sessions[:5]:
                    if st.button(
                        f"{sess['session_id'][:8]}... ({sess['task_count']} tasks)",
                        key=f"load_{sess['session_id']}",
                    ):
                        loaded = load_session(sess['session_id'])
                        if loaded:
                            st.session_state.session = loaded
                            st.rerun()


def render_input_step():
    """Render the goal input step."""
    st.header("📝 What's your goal?")

    # Input type tabs
    input_type = st.radio(
        "Input type",
        options=["Text", "Link", "Image"],
        horizontal=True,
        help="Choose how you want to describe your goal",
    )

    session = st.session_state.session

    # Text input
    if input_type == "Text":
        goal_text = st.text_area(
            "Describe your goal",
            placeholder="Example: Prepare for my thesis proposal defense next month. I need to create slides, practice the presentation, and prepare for Q&A.",
            height=150,
            value=session.user_input.content if session.user_input else "",
        )

    # Link input
    elif input_type == "Link":
        goal_text = st.text_input(
            "Enter a URL",
            placeholder="https://example.com/project-requirements",
            help="We'll extract relevant information from this page",
        )

    # Image input
    else:
        uploaded_file = st.file_uploader(
            "Upload a calendar screenshot or task image",
            type=["png", "jpg", "jpeg"],
            help="We'll analyze the image to extract schedule information",
        )
        goal_text = ""

        if uploaded_file:
            st.image(uploaded_file, caption="Uploaded image", use_container_width=True)
            # Save temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                tmp.write(uploaded_file.getvalue())
                goal_text = f"IMAGE:{tmp.name}"

    # Deadline input
    col1, col2 = st.columns(2)

    with col1:
        deadline_date = st.date_input(
            "Deadline date",
            value=(datetime.now() + timedelta(days=14)).date(),
            min_value=datetime.now().date(),
            help="When does this need to be completed?",
        )

    with col2:
        deadline_time = st.time_input(
            "Deadline time (optional)",
            value=None,
            help="Specific time if applicable",
        )

    # Combine deadline
    if deadline_time:
        deadline = datetime.combine(deadline_date, deadline_time)
    else:
        deadline = datetime.combine(deadline_date, datetime.max.time().replace(microsecond=0))

    # Additional context
    with st.expander("Additional context (optional)"):
        additional_context = st.text_area(
            "Any other information that might help?",
            placeholder="E.g., 'I can only work on this in the evenings' or 'I'm a beginner at this topic'",
            height=100,
        )

    # Submit button
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        if st.button("🚀 Analyze Goal", type="primary", use_container_width=True):
            if not goal_text and input_type != "Image":
                st.error("Please enter a goal description.")
                return

            # Save input
            input_type_map = {"Text": "text", "Link": "link", "Image": "image"}
            session.user_input = UserInput(
                type=input_type_map[input_type],
                content=goal_text,
                deadline=deadline,
            )

            # Move to analysis step
            session.current_step = 1
            save_session(session)
            st.rerun()


def render_analysis_step():
    """Render the goal analysis step."""
    st.header("🔍 Analyzing your goal...")

    session = st.session_state.session

    # Show spinner during analysis
    if session.goal_understanding is None:
        with st.spinner("Understanding your goal and creating a plan..."):
            llm = get_llm()

            if llm is None:
                st.error(f"Failed to initialize LLM: {st.session_state.error_message}")
                st.info("Please configure your API key in the environment variables.")

                if st.button("⬅️ Go Back"):
                    session.current_step = 0
                    save_session(session)
                    st.rerun()
                return

            try:
                # Handle different input types
                content = session.user_input.content
                context = None

                if session.user_input.type == "link":
                    with st.status("Fetching URL content..."):
                        context = llm.fetch_url_content(content)
                        content = f"Goal from URL: {content}"

                elif session.user_input.type == "image" and content.startswith("IMAGE:"):
                    image_path = content.replace("IMAGE:", "")
                    with st.status("Analyzing image..."):
                        context = llm.analyze_image(image_path)
                        content = "Goal from calendar image"

                # Understand goal
                st.text("Understanding your goal...")
                understanding = llm.understand_goal(
                    content,
                    deadline=session.user_input.deadline,
                    context=context,
                )

                session.goal_understanding = GoalUnderstanding(**understanding)

                # Decompose into tasks
                st.text("Breaking down into tasks...")
                st.text("Searching for learning resources on YouTube and the web...")
                tasks_data = llm.decompose_goal(
                    session.goal_understanding.summary,
                    deadline=session.user_input.deadline,
                    search_resources=True,
                )

                # Create task blocks with resources
                session.task_blocks = []
                for i, t in enumerate(tasks_data):
                    # Parse resources if provided
                    resources = []
                    for r in t.get("resources", []):
                        try:
                            resources.append(Resource(
                                title=r.get("title", "Resource"),
                                url=r.get("url", ""),
                                type=r.get("type", "other"),
                                description=r.get("description"),
                            ))
                        except Exception:
                            pass  # Skip invalid resources

                    session.task_blocks.append(TaskBlock(
                        title=t.get("title", "Task"),
                        description=t.get("description", ""),
                        estimated_hours=float(t.get("estimated_hours", 1.0)),
                        priority=t.get("priority", "must"),
                        order=t.get("order", i),
                        resources=resources,
                    ))

                session.current_step = 2
                save_session(session)
                st.rerun()

            except Exception as e:
                st.error(f"Analysis failed: {str(e)}")

                if st.button("🔄 Try Again"):
                    st.rerun()

                if st.button("⬅️ Go Back"):
                    session.current_step = 0
                    session.goal_understanding = None
                    save_session(session)
                    st.rerun()


def render_plan_review_step():
    """Render the plan review step."""
    st.header("📋 Review Your Plan")

    session = st.session_state.session

    # Goal briefing
    if session.goal_understanding:
        with st.expander("📌 Goal Briefing", expanded=True):
            st.markdown(f"**Summary:** {session.goal_understanding.summary}")

            col1, col2 = st.columns(2)
            with col1:
                feasibility_colors = {
                    "high": "🟢",
                    "medium": "🟡",
                    "low": "🔴",
                }
                st.markdown(
                    f"**Feasibility:** {feasibility_colors.get(session.goal_understanding.feasibility, '⚪')} "
                    f"{session.goal_understanding.feasibility.capitalize()}"
                )

            with col2:
                if session.user_input and session.user_input.deadline:
                    st.markdown(f"**Deadline:** {session.user_input.deadline.strftime('%B %d, %Y')}")

            if session.goal_understanding.assumptions:
                st.markdown("**Assumptions:**")
                for assumption in session.goal_understanding.assumptions:
                    st.markdown(f"- {assumption}")

            if session.goal_understanding.missing_information:
                st.warning("**Missing Information:**")
                for info in session.goal_understanding.missing_information:
                    st.markdown(f"- {info}")

    # Task blocks
    st.subheader("📦 Task Blocks")
    st.caption("Click on a task to edit it. Drag to reorder (coming soon).")

    # Add new task button
    if st.button("➕ Add Task"):
        new_task = TaskBlock(
            title="New Task",
            description="Description here",
            estimated_hours=1.0,
            order=len(session.task_blocks),
        )
        session.task_blocks.append(new_task)
        save_session(session)
        st.rerun()

    # Display tasks
    for i, task in enumerate(session.task_blocks):
        if task.status == "deleted":
            continue

        priority_class = "task-must" if task.priority == "must" else "task-nice"

        with st.container():
            col1, col2, col3 = st.columns([0.7, 0.2, 0.1])

            with col1:
                with st.expander(f"{'🔴' if task.priority == 'must' else '🟡'} {task.title} ({task.estimated_hours}h)"):
                    # Edit form
                    new_title = st.text_input(
                        "Title",
                        value=task.title,
                        key=f"title_{task.id}",
                    )
                    new_desc = st.text_area(
                        "Description",
                        value=task.description,
                        key=f"desc_{task.id}",
                    )
                    new_hours = st.number_input(
                        "Estimated hours",
                        value=task.estimated_hours,
                        min_value=0.5,
                        max_value=8.0,
                        step=0.5,
                        key=f"hours_{task.id}",
                    )
                    new_priority = st.selectbox(
                        "Priority",
                        options=["must", "nice"],
                        index=0 if task.priority == "must" else 1,
                        key=f"priority_{task.id}",
                    )

                    # Display resources
                    if task.resources:
                        st.markdown("**📚 Learning Resources:**")
                        for res in task.resources:
                            resource_icon = {
                                "video": "🎬",
                                "article": "📄",
                                "tutorial": "📖",
                                "documentation": "📋",
                                "course": "🎓",
                                "other": "🔗",
                            }.get(res.type, "🔗")
                            st.markdown(f"{resource_icon} [{res.title}]({res.url})")
                            if res.description:
                                st.caption(f"   {res.description}")

                    if st.button("💾 Save Changes", key=f"save_{task.id}"):
                        task.title = new_title
                        task.description = new_desc
                        task.estimated_hours = new_hours
                        task.priority = new_priority
                        task.status = "edited"
                        save_session(session)
                        st.success("Saved!")
                        st.rerun()

            with col3:
                if st.button("🗑️", key=f"delete_{task.id}", help="Delete task"):
                    task.status = "deleted"
                    save_session(session)
                    st.rerun()

    # Total hours
    total_hours = sum(t.estimated_hours for t in session.task_blocks if t.status != "deleted")
    st.info(f"📊 **Total estimated time:** {total_hours} hours")

    # Navigation
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        if st.button("⬅️ Back to Input"):
            session.current_step = 0
            save_session(session)
            st.rerun()

    with col2:
        if st.button("🔄 Regenerate Plan"):
            session.goal_understanding = None
            session.task_blocks = []
            session.current_step = 1
            save_session(session)
            st.rerun()

    with col3:
        if st.button("➡️ Schedule Tasks", type="primary"):
            session.current_step = 3
            save_session(session)
            st.rerun()


def render_scheduling_step():
    """Render the scheduling step."""
    st.header("📆 Schedule Your Tasks")

    session = st.session_state.session

    # Availability settings
    st.subheader("⏰ Your Availability")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Weekday hours**")
        weekday_start = st.time_input("Start", value=datetime.strptime("09:00", "%H:%M").time(), key="wd_start")
        weekday_end = st.time_input("End", value=datetime.strptime("18:00", "%H:%M").time(), key="wd_end")

    with col2:
        st.markdown("**Weekend hours**")
        weekend_start = st.time_input("Start", value=datetime.strptime("10:00", "%H:%M").time(), key="we_start")
        weekend_end = st.time_input("End", value=datetime.strptime("16:00", "%H:%M").time(), key="we_end")

    # Max hours per day
    max_hours = st.slider(
        "Maximum hours per day",
        min_value=1.0,
        max_value=10.0,
        value=6.0,
        step=0.5,
        help="Maximum number of hours to schedule per day",
    )

    # Busy times
    with st.expander("🚫 Add busy times"):
        st.caption("Mark times when you're not available")

        busy_date = st.date_input("Date", key="busy_date")
        busy_col1, busy_col2 = st.columns(2)
        with busy_col1:
            busy_start = st.time_input("From", key="busy_start")
        with busy_col2:
            busy_end = st.time_input("To", key="busy_end")
        busy_reason = st.text_input("Reason (optional)", key="busy_reason")

        if st.button("Add Busy Time"):
            busy_interval = BusyInterval(
                start=datetime.combine(busy_date, busy_start),
                end=datetime.combine(busy_date, busy_end),
                reason=busy_reason or None,
            )
            if session.user_input.availability is None:
                session.user_input.availability = Availability()
            session.user_input.availability.busy_intervals.append(busy_interval)
            save_session(session)
            st.success("Added busy time!")

        # Show existing busy times
        if session.user_input and session.user_input.availability:
            for i, busy in enumerate(session.user_input.availability.busy_intervals):
                st.text(f"• {busy.start.strftime('%m/%d %H:%M')} - {busy.end.strftime('%H:%M')}: {busy.reason or 'Busy'}")

    # Generate schedule button
    st.markdown("---")

    if st.button("📅 Generate Schedule", type="primary", use_container_width=True):
        # Update availability
        if session.user_input.availability is None:
            session.user_input.availability = Availability()

        session.user_input.availability.preferred_hours = PreferredHours(
            weekday=[f"{weekday_start.strftime('%H:%M')}-{weekday_end.strftime('%H:%M')}"],
            weekend=[f"{weekend_start.strftime('%H:%M')}-{weekend_end.strftime('%H:%M')}"],
        )

        # Schedule tasks
        with st.spinner("Scheduling tasks..."):
            active_tasks = [t for t in session.task_blocks if t.status != "deleted"]
            session.schedule = schedule_tasks(
                active_tasks,
                session.user_input.availability,
                deadline=session.user_input.deadline,
                max_hours_per_day=max_hours,
            )
            save_session(session)

        st.success("Schedule generated!")
        st.rerun()

    # Show schedule preview
    if session.schedule:
        st.subheader("📋 Schedule Preview")

        preview = preview_schedule_text(session)
        st.text(preview)

        # Stats
        active_tasks = [t for t in session.task_blocks if t.status != "deleted"]
        stats = calculate_schedule_stats(active_tasks, session.schedule, session.user_input.deadline)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Hours", f"{stats['total_hours']:.1f}")
        with col2:
            st.metric("Days Needed", stats['days_used'])
        with col3:
            st.metric("Deadline Met", "✅ Yes" if stats['deadline_met'] else "❌ No")

    # Navigation
    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        if st.button("⬅️ Back to Plan"):
            session.current_step = 2
            save_session(session)
            st.rerun()

    with col2:
        if st.button("➡️ Export to Calendar", type="primary", disabled=not session.schedule):
            session.current_step = 4
            save_session(session)
            st.rerun()


def render_export_step():
    """Render the export step."""
    st.header("📤 Export Your Plan")

    session = st.session_state.session

    # Success message
    st.success("Your plan is ready to export!")

    # Preview
    st.subheader("📋 Final Schedule")
    preview = preview_schedule_text(session)
    st.text(preview)

    # Export options
    st.subheader("📥 Download Options")

    col1, col2 = st.columns(2)

    with col1:
        # Generate ICS content
        ics_content = generate_ics_content(session)

        st.download_button(
            label="📅 Download .ics file",
            data=ics_content,
            file_name=f"agentic_plan_{session.session_id[:8]}.ics",
            mime="text/calendar",
            type="primary",
            use_container_width=True,
        )
        st.caption("Import this file into Apple Calendar, Google Calendar, or Outlook")

    with col2:
        # Copy as text with resources
        plan_text = f"# Plan: {session.goal_understanding.summary}\n\n"
        plan_text += f"Created: {session.created_at.strftime('%Y-%m-%d')}\n"
        plan_text += f"Deadline: {session.user_input.deadline.strftime('%Y-%m-%d')}\n\n"
        plan_text += "## Tasks:\n"
        for task in session.task_blocks:
            if task.status != "deleted":
                plan_text += f"- [ ] {task.title} ({task.estimated_hours}h)\n"
                plan_text += f"      {task.description}\n"
                if task.resources:
                    plan_text += "      📚 Resources:\n"
                    for res in task.resources:
                        plan_text += f"        - [{res.type.upper()}] {res.title}\n"
                        plan_text += f"          {res.url}\n"
                plan_text += "\n"
        plan_text += f"\n## Schedule:\n{preview}"

        st.download_button(
            label="📝 Download as text",
            data=plan_text,
            file_name=f"agentic_plan_{session.session_id[:8]}.txt",
            mime="text/plain",
            use_container_width=True,
        )
        st.caption("Plain text version of your plan")

    # Instructions
    st.markdown("---")
    st.subheader("📖 How to import")

    with st.expander("Apple Calendar (macOS/iOS)"):
        st.markdown("""
        1. Download the .ics file
        2. Double-click the file to open it with Calendar
        3. Choose which calendar to add events to
        4. Click "Add" or "Import"
        """)

    with st.expander("Google Calendar"):
        st.markdown("""
        1. Download the .ics file
        2. Go to [Google Calendar](https://calendar.google.com)
        3. Click the gear icon → Settings
        4. Click "Import & Export" in the left sidebar
        5. Click "Select file from your computer" and choose the .ics file
        6. Select the calendar to add events to
        7. Click "Import"
        """)

    with st.expander("Outlook"):
        st.markdown("""
        1. Download the .ics file
        2. Open Outlook
        3. Go to File → Open & Export → Import/Export
        4. Choose "Import an iCalendar (.ics) file"
        5. Select the downloaded file
        6. Choose to open as new or import
        """)

    # Navigation
    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        if st.button("⬅️ Back to Schedule"):
            session.current_step = 3
            save_session(session)
            st.rerun()

    with col2:
        if st.button("🆕 Start New Plan"):
            st.session_state.session = create_session()
            st.rerun()


def main():
    """Main application entry point."""
    init_session_state()

    # Title
    st.title("📅 Agentic Calendar")
    st.caption("Your intelligent planning assistant")

    # Render sidebar
    render_sidebar()

    # Get current session
    session = st.session_state.session

    # Render step indicator
    render_step_indicator(session.current_step)

    # Render current step
    if session.current_step == 0:
        render_input_step()
    elif session.current_step == 1:
        render_analysis_step()
    elif session.current_step == 2:
        render_plan_review_step()
    elif session.current_step == 3:
        render_scheduling_step()
    elif session.current_step == 4:
        render_export_step()


if __name__ == "__main__":
    main()
