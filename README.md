# Agentic Calendar

An intelligent planning assistant that helps you break down goals into actionable tasks and schedule them into your calendar.

## Quick Start (macOS with Homebrew)

```bash
# Run the setup script
./setup.sh

# Activate the virtual environment
source venv/bin/activate

# Add your API key to .env file
# (edit .env and add OPENAI_API_KEY or ANTHROPIC_API_KEY)

# Run the app
streamlit run app.py
```

## Manual Installation

1. **Install Python 3.10+** via Homebrew:
   ```bash
   brew install python@3.11
   ```

2. **Create and activate virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure API key**:
   ```bash
   cp .env.example .env
   # Edit .env and add your OpenAI or Anthropic API key
   ```

5. **Run the application**:
   ```bash
   streamlit run app.py
   ```

## Features

- **Goal-driven planning**: Describe what you want to achieve in natural language
- **Smart task decomposition**: AI breaks down your goal into concrete tasks
- **Flexible scheduling**: Respects your availability and preferences
- **Calendar export**: Generate .ics files for Apple Calendar, Google Calendar, or Outlook
- **Session management**: Save and load planning sessions

## Project Structure

```
agentic_new/
├── app.py              # Main Streamlit application
├── llm_client.py       # LLM API abstraction (OpenAI/Anthropic)
├── planner.py          # Task scheduling logic
├── calendar_export.py  # .ics file generation
├── storage.py          # JSON session persistence
├── models.py           # Data models (Pydantic)
├── requirements.txt    # Python dependencies
├── setup.sh           # macOS setup script
├── .env.example       # Environment variable template
├── docs/
│   └── User_Manual.md # Detailed user documentation
├── sessions/          # Saved planning sessions
└── exports/           # Generated calendar files
```

## Requirements

- Python 3.10+
- OpenAI API key OR Anthropic API key

## Documentation

See [docs/User_Manual.md](docs/User_Manual.md) for detailed usage instructions.

## License

MIT
