# Agentic Calendar - User Manual

## Overview

Agentic Calendar is an intelligent planning assistant that helps you break down complex goals into actionable tasks and schedule them into your calendar. Unlike simple reminder apps, it understands your objectives, creates detailed plans, and respects your availability.

## Installation

### Prerequisites

- **Python 3.10 or higher** (installed via Homebrew on macOS)
- An API key from OpenAI or Anthropic

### macOS Installation (via Homebrew)

1. **Install Python** (if not already installed):
   ```bash
   brew install python@3.11
   ```

2. **Clone or download the project**, then navigate to the folder:
   ```bash
   cd /path/to/agentic_new
   ```

3. **Create a virtual environment** (recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

4. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

5. **Set up your API key**:
   ```bash
   cp .env.example .env
   # Edit .env and add your API key
   ```

6. **Run the application**:
   ```bash
   streamlit run app.py
   ```

The app will open in your default web browser at `http://localhost:8501`.

## Getting Started

### Step 1: Enter Your Goal

When you first open Agentic Calendar, you'll see the input screen. You can describe your goal in three ways:

1. **Text**: Type a natural language description of what you want to achieve.
   - Example: "Prepare for my thesis defense next month"
   - Example: "Learn Python basics in 2 weeks"

2. **Link**: Provide a URL to relevant information (project page, conference CFP, etc.)

3. **Image**: Upload a screenshot of your calendar or task list.

**Tips for good goal descriptions:**
- Be specific about what you want to achieve
- Include context about your experience level
- Mention any constraints (e.g., "I can only work evenings")

### Step 2: Set Your Deadline

Choose when you need to complete this goal. The deadline helps the system:
- Calculate how much time you have
- Spread tasks appropriately
- Alert you if the goal may not be feasible

### Step 3: Review the Analysis

After clicking "Analyze Goal," the system will:
1. Interpret your objective
2. Assess feasibility
3. Break it down into concrete tasks

You'll see:
- **Goal Summary**: A refined description of your objective
- **Feasibility Rating**: High/Medium/Low based on time and complexity
- **Assumptions**: What the system is assuming
- **Missing Information**: Things that would help improve the plan

### Step 4: Edit Your Tasks

Each task block shows:
- **Title**: Short description of the task
- **Estimated Hours**: How long it should take
- **Priority**: Must do (red) or Nice to have (yellow)

You can:
- Click on any task to edit its details
- Delete tasks you don't need
- Add new tasks with the "Add Task" button
- Regenerate the entire plan if needed

### Step 5: Set Your Availability

Tell the system when you're available to work:

1. **Weekday hours**: Your typical working hours (e.g., 9 AM - 6 PM)
2. **Weekend hours**: If you want to work weekends
3. **Max hours per day**: How many hours you can dedicate daily
4. **Busy times**: Mark specific times you're not available

### Step 6: Generate and Export Schedule

Click "Generate Schedule" to see your tasks mapped to specific time slots. The preview shows:
- Tasks organized by day
- Start and end times for each session
- Priority indicators

**Export Options:**
- **.ics file**: Import into Apple Calendar, Google Calendar, or Outlook
- **Text file**: Plain text version for reference

## Importing Your Calendar

### Apple Calendar (macOS)

1. Download the .ics file
2. Double-click to open with Calendar
3. Select which calendar to add events to
4. Click "Add"

### Apple Calendar (iOS)

1. Download the .ics file
2. Tap to open
3. Select "Add All Events"
4. Choose your calendar

### Google Calendar

1. Go to [calendar.google.com](https://calendar.google.com)
2. Click the gear icon → Settings
3. Select "Import & Export"
4. Click "Select file from your computer"
5. Choose the .ics file
6. Select destination calendar
7. Click "Import"

### Microsoft Outlook

1. Open Outlook
2. File → Open & Export → Import/Export
3. Choose "Import an iCalendar (.ics) file"
4. Select the downloaded file
5. Choose Open as New or Import

## Tips for Best Results

### Writing Effective Goals

**Good examples:**
- "Complete the HCI project report by May 5th. I need to write the introduction, methodology, results, and conclusion sections."
- "Prepare for AWS certification exam in 3 weeks. I'm already familiar with EC2 and S3."

**Less effective:**
- "Study" (too vague)
- "Do everything for work" (not specific)

### Managing Your Schedule

1. **Be realistic about availability**: Don't overcommit. If you know you have a busy week, mark those times as busy.

2. **Buffer time**: The system schedules tasks with some flexibility, but consider adding buffer time for unexpected delays.

3. **Review and adjust**: The generated plan is a starting point. Feel free to modify tasks and reschedule as needed.

4. **Update as you progress**: Come back to mark tasks as completed or adjust remaining tasks.

## Troubleshooting

### "API key not configured"

Make sure you've:
1. Created a `.env` file in the project directory
2. Added your API key: `OPENAI_API_KEY=your-key-here` or `ANTHROPIC_API_KEY=your-key-here`
3. Restarted the application

### "Analysis failed"

This usually means:
- The LLM service is temporarily unavailable
- Your API key has expired or hit rate limits
- Network connectivity issues

Try:
1. Clicking "Try Again"
2. Checking your internet connection
3. Verifying your API key is valid

### Calendar import issues

If your calendar app doesn't recognize the .ics file:
1. Make sure you downloaded the complete file
2. Try a different import method (email the file to yourself)
3. Check that the file extension is .ics (not .txt)

### Tasks not fitting in schedule

If you see "Deadline not met":
1. Extend your deadline if possible
2. Reduce estimated hours for tasks
3. Increase your available hours
4. Remove lower-priority tasks

## Privacy & Data

- All data is stored locally on your computer
- Session files are saved in the `sessions/` folder
- Exported calendars are saved in the `exports/` folder
- Your goals and tasks are sent to the LLM API for analysis (OpenAI or Anthropic)

## Getting Help

If you encounter issues:
1. Check this manual for guidance
2. Review the in-app help section (sidebar)
3. Ensure your Python environment is correctly configured

## Keyboard Shortcuts

- **Enter**: Submit forms
- **Esc**: Close expanded sections
- Standard text editing shortcuts work in all input fields

---

*Agentic Calendar - Plan smarter, achieve more.*
