# Agentic Calendar – Implementation Plan

## 1. Project Overview

Agentic Calendar is an intelligent planning assistant that goes beyond simple reminders. Instead of only telling users “you have a meeting tomorrow,” it:
- Understands the goal behind a user’s request (e.g., “prepare for a collaboration meeting,” “submit a conference paper,” “learn Python in 3 months”).
- Validates and enriches the request using LLM APIs (e.g., ChatGPT/Claude) and web information.
- Decomposes the goal into concrete, actionable sub‑tasks.
- Negotiates feasible time slots with the user based on their availability.
- Generates a structured schedule that can be exported to Apple Calendar / Google Calendar via `.ics` files.

The app is designed as a small, self‑contained Python application with a simple GUI and minimal dependencies (installable via `pip`) and with explicit attention to HCI principles.

## 2. Target Users, Platform, and Constraints

- **Target users:** General users who are familiar with basic apps and calendars but may not be technical. The interface must be simple, intuitive, and non‑intimidating.
- **Platforms:** Desktop or laptop users on Linux and Windows (and optionally macOS) running a Python app in a browser or local window.
- **Technology constraints:**
  - Only use Python and libraries installable via `pip`.
  - No extra language runtimes required (no Node.js, etc.).
  - Keep `requirements.txt` short and common.

## 3. Core User Tasks & Flows

### 3.1 Main Use Cases

1. **Goal‑driven planning**
   - User provides a high‑level goal (“Prepare for meeting with X next Wednesday” or “Finish draft of HCI project report by May 5th”).
   - System validates information, expands it, and proposes a concrete execution plan.
   - System schedules sub‑tasks into calendar blocks respecting user availability and deadline.
   - User exports the plan to Apple/Google Calendar.

2. **Interactive refinement of plan**
   - User clicks on individual task “bubbles” to modify them (change duration, deadline, description).
   - User adds comments or constraints (e.g., “Only evenings after 7pm,” “Need 2 hours of focused work per session”).
   - System regenerates or adjusts the schedule accordingly.

3. **Availability specification**
   - User provides their availability and busy slots for the upcoming days (e.g., through natural language, explicit form fields, or a screenshot/image of an existing calendar).
   - System interprets this information and uses it as constraints when scheduling tasks.

### 3.2 High‑Level Flow

1. **Input step:** User submits a goal via text, link, or image.
2. **Analysis step (LLM):** App calls LLM API to:
   - Interpret and validate the goal and context.
   - Gather necessary background information or task structure from the web (via LLM tools or search, if available).
   - Decompose the goal into subtasks and learning/working steps.
3. **Review step:** App presents:
   - A brief “goal briefing” summarizing the target, feasibility, and key considerations.
   - A list of task blocks (“bubbles”) that can be edited, rearranged, or deleted.
4. **Scheduling step:** App asks for/uses user availability and:
   - Proposes a schedule mapping tasks to time slots before the deadline.
5. **Export step:** App generates an `.ics` calendar file or equivalent export that can be imported into Apple Calendar / Google Calendar.
6. **Iteration:** At any stage, user can go back, cancel, or refine inputs.

## 4. Functional Requirements

### 4.1 Input Module

- Accept **three types of input**:
  - Text: free‑form natural language description of the goal.
  - Link: URL to reference material (e.g., project description, paper CFP, meeting agenda).
  - Image: screenshot of calendar or task description.
- Provide “input type” controls with clear labels and icons (text bubble, link icon, image icon).
- For images, forward them to an LLM vision API (or stub during development) to extract text and key information.
- Perform basic validation:
  - If input is empty or obviously invalid, show an error message with examples of valid inputs.

### 4.2 LLM & Information Retrieval Module

- Wrap LLM API calls into a single `llm_client` abstraction to allow:
  - Switching between OpenAI/Anthropic or a local stub without changing UI code.
  - Configuring API key via environment variable or config file.
- Key prompts (implemented as templates in code):
  1. **Goal understanding & validation prompt** – outputs:
     - Refined task description.
     - Feasibility assessment and any missing information.
     - List of assumptions made.
  2. **Task decomposition prompt** – outputs:
     - Ordered list of task blocks.
     - For each block: description, estimated effort, dependencies, “must finish by” date relative to the overall deadline.
  3. **Scheduling assistance prompt** – optionally helps refine the mapping from task blocks + availability → time slots, but the app will enforce final scheduling constraints locally.
- Where possible, instruct the LLM to output **strict JSON** following a predefined schema so the Python backend can parse it safely.

### 4.3 Planning & Scheduling Module

- Implement a planner that:
  - Receives structured tasks from LLM (or fallback heuristic).
  - Receives user availability constraints:
    - Fixed busy intervals.
    - Preferred working hours and days.
  - Allocates time blocks sequentially before the overall deadline, respecting:
    - Task order and dependencies.
    - Daily/weekly caps for workload to avoid unrealistic schedules.
- Provide basic algorithms:
  - Greedy scheduling over time slots.
  - Simple conflict resolution (e.g., push conflicting tasks to the next available slot).
- Support re‑scheduling when:
  - User edits tasks (duration, order, deadlines).
  - User modifies availability or cancels certain blocks.

### 4.4 Output & Calendar Export Module

- Output is split into three clearly separated sections in the UI:
  1. **Briefing about the target**
     - Summary of the goal, constraints, and feasibility.
     - List of assumptions and key risks or dependencies.
  2. **Task block overview**
     - Display each task block as a clickable “bubble” card.
     - Show title, short description, estimated duration, and deadline.
     - Support operations:
       - Edit text.
       - Adjust duration.
       - Mark as “optional” or “must do.”
       - Delete or duplicate.
  3. **Calendar view / export preview**
     - Show scheduled blocks in a simple timeline or list grouped by day.
     - Provide a button with a calendar icon to **export as `.ics` file**.
     - Generated `.ics` file includes:
       - Event titles = task block titles.
       - Start/end times.
       - Description field = block description + link back to the JSON plan (if available).

### 4.5 Data Storage Module

- Store user sessions as **JSON documents** on disk:
  - One file per planning session (e.g., `sessions/session_<timestamp>.json`).
  - Fields include:
    - Raw user input (text, link, image reference).
    - Parsed and validated goal representation.
    - LLM outputs (goal understanding, task decomposition).
    - User‑edited task blocks and schedule.
    - Export status and generated `.ics` filename.
- Provide utility functions for:
  - Creating new session files.
  - Loading and updating existing sessions.
  - Versioning changes to support undo/redo in the future (optional).

## 5. UI Design & HCI Principles

The app will use a simple web‑based UI (e.g., Streamlit or a minimal Flask + HTML/JS front‑end) with a chat‑like layout and clearly separated steps. Each Nielsen heuristic is explicitly supported:

1. **H2‑1: Visibility of system status**
   - Show a **stepper** or progress bar indicating which step the user is in: Input → Analysis → Plan Review → Scheduling → Export.
   - During LLM inference and scheduling, display:
     - A spinner / progress indicator.
     - Status text such as “Understanding your goal…”, “Decomposing into tasks…”, “Scheduling tasks into your calendar…”.
   - Optionally display estimated remaining time (“Usually < 10 seconds”).

2. **H2‑2: Match between system and real world**
   - Use plain, everyday language in labels and explanations.
   - Icons:
     - Trash bin icon for deleting a task.
     - Calendar icon for exporting to calendar.
     - Pencil/edit icon for editing a block.
     - “Chat bubble” icon for comments.
   - Describe the process using planning metaphors (e.g., “We’ll break down your goal into steps and place them on your calendar.”).

3. **H2‑3: User control and freedom**
   - Provide **Cancel** buttons during long operations (e.g., while waiting for LLM).
   - Allow users to:
     - Go back to previous steps without losing all data.
     - Delete or modify any suggested task block.
     - Regenerate the plan from scratch.
   - Confirm before destructive actions (e.g., “Are you sure you want to discard this plan?”).

4. **H2‑4: Consistency and standards**
   - Use a consistent layout and color palette across steps.
   - Keep navigation elements (e.g., step indicator, action buttons) in fixed positions.
   - Use standard interaction patterns:
     - Clickable cards/bubbles for tasks.
     - Standard file upload widget for images.
     - Text area for chat‑style input.

5. **H2‑5: Error prevention**
   - Validate input before sending to the LLM:
     - Check for empty text input.
     - Validate URLs.
   - Ask for missing critical info (e.g., deadline) with clear prompts.
   - Provide presets or examples of useful prompts for users.

6. **H2‑6: Recognition rather than recall**
   - Provide placeholder examples in the input box (e.g., “Example: ‘Prepare for my thesis proposal defense next month’.”).
   - Use pre‑formatted templates for availability (e.g., checkboxes for days, sliders for time ranges).
   - Auto‑fill fields based on LLM understanding and let users edit rather than type from scratch.

7. **H2‑7: Flexibility and efficiency of use**
   - Allow quick‑start with a single sentence, but also advanced options:
     - Advanced panel for specifying exact deadline and priorities.
   - Keyboard shortcuts for common actions (e.g., press `Enter` to submit).
   - Option to copy/paste the generated plan textually as well as exporting to `.ics`.

8. **H2‑8: Aesthetic and minimalist design**
   - Use a clean, uncluttered layout:
     - Most of the screen is dedicated to the current step’s content.
     - Side panel for status and help only.
   - Avoid overly dense text; rely on short headings, bullets, and icons.

9. **H2‑9: Help users recognize, diagnose, and recover from errors**
   - Provide clear error messages for:
     - API failures (e.g., “We couldn’t reach the planning service. Please check your internet connection or API key.”).
     - Invalid input formats.
   - Offer “Try again” and “Edit input” shortcuts in error states.

10. **H2‑10: Help and documentation**
    - Add a dedicated **Help** section accessible from the main UI:
      - Short description of the app.
      - Examples of good input prompts.
      - Explanation of how to export and import calendar files.
    - Provide a separate written **User Manual** (Markdown or PDF) that explains:
      - Installation and setup (Python, dependencies, API keys).
      - Step‑by‑step usage walkthrough.
      - Troubleshooting common issues.

## 6. System Architecture & Components

### 6.1 High‑Level Architecture

- **Frontend/UI layer (Python web app):**
  - Built using `streamlit` (or similar) to keep setup simple and purely Python.
  - Manages user interactions, file uploads, and displaying steps.
- **Backend logic:**
  - `llm_client.py` – handles LLM API calls and prompt templates.
  - `planner.py` – handles task decomposition parsing, scheduling logic, and calendar block generation.
  - `storage.py` – handles session JSON persistence.
  - `calendar_export.py` – builds `.ics` files from task schedules using a library like `ics` or `icalendar`.
- **Data store:**
  - Local JSON files on disk under `sessions/`.

### 6.2 Suggested File Structure

- `app.py` – main entry point for the UI.
- `llm_client.py` – LLM API abstraction and prompt templates.
- `planner.py` – planning and scheduling logic.
- `calendar_export.py` – `.ics` export utilities.
- `storage.py` – JSON session I/O.
- `models.py` – data classes or typed dictionaries for tasks, schedules, and sessions.
- `requirements.txt` – Python dependencies.
- `docs/User_Manual.md` – help and documentation.

### 6.3 Data Model (JSON Schema Sketch)

```json
{
  "session_id": "string",
  "created_at": "ISO8601 timestamp",
  "user_input": {
    "type": "text | link | image",
    "content": "raw input string or path",
    "deadline": "ISO8601 date or datetime",
    "availability": {
      "busy_intervals": [
        {"start": "ISO8601", "end": "ISO8601", "reason": "string"}
      ],
      "preferred_hours": {
        "weekday": ["09:00-12:00", "14:00-18:00"],
        "weekend": ["10:00-16:00"]
      }
    }
  },
  "goal_understanding": {
    "summary": "string",
    "feasibility": "high | medium | low",
    "assumptions": ["string"],
    "missing_information": ["string"]
  },
  "task_blocks": [
    {
      "id": "string",
      "title": "string",
      "description": "string",
      "estimated_hours": 2,
      "deadline": "ISO8601",
      "status": "planned | edited | deleted | completed",
      "priority": "must | nice"
    }
  ],
  "schedule": [
    {
      "task_id": "string",
      "start": "ISO8601 datetime",
      "end": "ISO8601 datetime"
    }
  ],
  "export": {
    "ics_file": "path or filename",
    "exported_at": "ISO8601 timestamp"
  }
}
```

## 7. Implementation Steps & Milestones

### Milestone 1 – Minimal MVP (Text Input Only)

1. Set up Python environment and `requirements.txt` with:
   - `streamlit` (UI)
   - `requests` or relevant LLM SDK
   - `python-dotenv` (for API keys)
   - `ics` or `icalendar` (for calendar export)
2. Implement `app.py` with:
   - Single text input.
   - Stepper UI (Input → Analysis → Plan → Export).
   - Stubbed responses (hardcoded), before integrating real LLM.
3. Implement basic `storage.py` to create a JSON session for each run.

### Milestone 2 – LLM Integration and Task Decomposition

1. Implement `llm_client.py` with environment‑based API key loading.
2. Define prompt templates for goal understanding and task decomposition.
3. Parse LLM JSON output into internal data models (`models.py`).
4. Display goal briefing and list of task blocks (as clickable cards/bubbles).

### Milestone 3 – Availability and Scheduling

1. Build UI for specifying availability:
   - Simple form (date range, preferred hours, busy slots).
   - Later add natural language description parsing via LLM.
2. Implement `planner.py` with:
   - Greedy scheduling algorithm.
   - Simple conflict resolution.
3. Render the resulting schedule in the UI as a daily/weekly list.

### Milestone 4 – Editing, Iteration, and Export

1. Enable editing of task blocks:
   - Click to open an edit dialog.
   - Persist edits to JSON session.
2. Add “Regenerate with feedback”:
   - User comments on a block or overall plan.
   - Send feedback + existing plan back to LLM for refinement.
3. Implement `.ics` export via `calendar_export.py` and add:
   - Calendar icon button.
   - Success/failure notifications.

### Milestone 5 – Image & Link Inputs + HCI Polish

1. Add file upload for image inputs and integrate with LLM vision API or placeholder.
2. Add URL input field and pass target page summary to LLM.
3. Refine UI for:
   - Clear status messages and spinners during LLM calls.
   - Consistent icons and color palette.
   - Help panel and link to `docs/User_Manual.md`.
4. Conduct heuristic evaluation and adjust the interface according to H2‑1 ~ H2‑10.

## 8. Evaluation Plan (HCI Perspective)

- **Heuristic evaluation:** Systematically check the interface against the 10 Nielsen heuristics and document how each is (or is not yet) satisfied.
- **Think‑aloud user testing (small scale):**
  - Recruit several participants.
  - Ask them to complete a concrete planning task (e.g., “Plan your exam preparation over the next 2 weeks.”).
  - Collect observations related to:
    - Understanding of system status.
    - Ease of entering goals and availability.
    - Clarity of generated plan and schedule.
- **Metrics:**
  - Time to create a first acceptable plan.
  - Number of errors or confusion events.
  - Subjective satisfaction (short Likert‑scale questionnaire).

This implementation plan should guide the development of a small but functional Agentic Calendar prototype that demonstrates both technical feasibility and strong alignment with core HCI principles.
