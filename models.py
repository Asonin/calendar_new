"""
Data models for Agentic Calendar.
Defines the structure for tasks, schedules, and sessions.
"""

from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field
from uuid import uuid4


class BusyInterval(BaseModel):
    """Represents a time interval when the user is busy."""
    start: datetime
    end: datetime
    reason: Optional[str] = None


class PreferredHours(BaseModel):
    """User's preferred working hours."""
    weekday: list[str] = Field(default_factory=lambda: ["09:00-12:00", "14:00-18:00"])
    weekend: list[str] = Field(default_factory=lambda: ["10:00-16:00"])


class Availability(BaseModel):
    """User availability constraints."""
    busy_intervals: list[BusyInterval] = Field(default_factory=list)
    preferred_hours: PreferredHours = Field(default_factory=PreferredHours)


class UserInput(BaseModel):
    """User's input for planning."""
    type: Literal["text", "link", "image"] = "text"
    content: str
    deadline: Optional[datetime] = None
    availability: Availability = Field(default_factory=Availability)


class GoalUnderstanding(BaseModel):
    """LLM's understanding of the user's goal."""
    summary: str
    feasibility: Literal["high", "medium", "low"] = "medium"
    assumptions: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)


class Resource(BaseModel):
    """A learning resource or material for a task."""
    title: str
    url: str
    type: Literal["video", "article", "tutorial", "documentation", "course", "other"] = "other"
    description: Optional[str] = None


class TaskBlock(BaseModel):
    """A single task block in the plan."""
    id: str = Field(default_factory=lambda: str(uuid4())[:8])
    title: str
    description: str
    estimated_hours: float = 1.0
    deadline: Optional[datetime] = None
    status: Literal["planned", "edited", "deleted", "completed"] = "planned"
    priority: Literal["must", "nice"] = "must"
    order: int = 0
    resources: list[Resource] = Field(default_factory=list)


class ScheduledTask(BaseModel):
    """A task that has been scheduled to a specific time slot."""
    task_id: str
    start: datetime
    end: datetime


class ExportInfo(BaseModel):
    """Information about calendar export."""
    ics_file: Optional[str] = None
    exported_at: Optional[datetime] = None


class Session(BaseModel):
    """A complete planning session."""
    session_id: str = Field(default_factory=lambda: str(uuid4()))
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    user_input: Optional[UserInput] = None
    goal_understanding: Optional[GoalUnderstanding] = None
    task_blocks: list[TaskBlock] = Field(default_factory=list)
    schedule: list[ScheduledTask] = Field(default_factory=list)
    export: ExportInfo = Field(default_factory=ExportInfo)
    current_step: int = 0  # 0=Input, 1=Analysis, 2=Plan Review, 3=Scheduling, 4=Export

    def update_timestamp(self):
        """Update the updated_at timestamp."""
        self.updated_at = datetime.now()
