"""
Planning and Scheduling module for Agentic Calendar.
Handles task scheduling based on availability constraints.
"""

from datetime import datetime, timedelta
from typing import Optional
from dateutil import parser as date_parser

from models import (
    TaskBlock,
    ScheduledTask,
    Availability,
    PreferredHours,
    BusyInterval,
)


def parse_time_range(time_range: str) -> tuple[int, int]:
    """Parse a time range string like '09:00-12:00' into (start_hour, end_hour)."""
    try:
        start, end = time_range.split("-")
        start_hour = int(start.split(":")[0])
        end_hour = int(end.split(":")[0])
        return start_hour, end_hour
    except (ValueError, IndexError):
        return 9, 17  # Default working hours


def get_available_slots(
    date: datetime,
    availability: Availability,
    existing_schedule: list[ScheduledTask],
    min_slot_hours: float = 1.0,
) -> list[tuple[datetime, datetime]]:
    """
    Get available time slots for a given date based on availability constraints.

    Returns a list of (start, end) datetime tuples representing available slots.
    """
    # Determine if it's a weekday or weekend
    is_weekend = date.weekday() >= 5

    # Get preferred hours for this day type
    if is_weekend:
        time_ranges = availability.preferred_hours.weekend
    else:
        time_ranges = availability.preferred_hours.weekday

    # Create initial available slots from preferred hours
    available = []
    for time_range in time_ranges:
        start_hour, end_hour = parse_time_range(time_range)
        slot_start = date.replace(hour=start_hour, minute=0, second=0, microsecond=0)
        slot_end = date.replace(hour=end_hour, minute=0, second=0, microsecond=0)
        available.append((slot_start, slot_end))

    # Remove busy intervals
    for busy in availability.busy_intervals:
        if busy.start.date() == date.date():
            available = subtract_interval(available, busy.start, busy.end)

    # Remove already scheduled tasks
    for scheduled in existing_schedule:
        if scheduled.start.date() == date.date():
            available = subtract_interval(available, scheduled.start, scheduled.end)

    # Filter out slots that are too short
    min_duration = timedelta(hours=min_slot_hours)
    available = [(s, e) for s, e in available if e - s >= min_duration]

    return available


def subtract_interval(
    slots: list[tuple[datetime, datetime]],
    busy_start: datetime,
    busy_end: datetime,
) -> list[tuple[datetime, datetime]]:
    """Remove a busy interval from available slots."""
    result = []

    for slot_start, slot_end in slots:
        # No overlap
        if busy_end <= slot_start or busy_start >= slot_end:
            result.append((slot_start, slot_end))
        # Busy interval completely contains slot
        elif busy_start <= slot_start and busy_end >= slot_end:
            continue  # Skip this slot entirely
        # Busy interval is in the middle of slot
        elif busy_start > slot_start and busy_end < slot_end:
            result.append((slot_start, busy_start))
            result.append((busy_end, slot_end))
        # Busy interval overlaps start of slot
        elif busy_start <= slot_start and busy_end > slot_start:
            if busy_end < slot_end:
                result.append((busy_end, slot_end))
        # Busy interval overlaps end of slot
        elif busy_start < slot_end and busy_end >= slot_end:
            if busy_start > slot_start:
                result.append((slot_start, busy_start))

    return result


def schedule_tasks(
    tasks: list[TaskBlock],
    availability: Availability,
    deadline: Optional[datetime] = None,
    start_date: Optional[datetime] = None,
    max_hours_per_day: float = 6.0,
) -> list[ScheduledTask]:
    """
    Schedule tasks into available time slots using a greedy algorithm.

    Args:
        tasks: List of tasks to schedule
        availability: User's availability constraints
        deadline: Overall deadline for all tasks
        start_date: When to start scheduling (defaults to tomorrow)
        max_hours_per_day: Maximum hours to schedule per day

    Returns:
        List of scheduled tasks with assigned time slots
    """
    if start_date is None:
        start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)

    if deadline is None:
        # Default to 2 weeks from now
        deadline = start_date + timedelta(days=14)

    # Sort tasks by order and priority
    sorted_tasks = sorted(
        [t for t in tasks if t.status != "deleted"],
        key=lambda t: (t.order, 0 if t.priority == "must" else 1),
    )

    scheduled = []
    current_date = start_date
    hours_scheduled_today = 0.0

    for task in sorted_tasks:
        remaining_hours = task.estimated_hours
        task_deadline = task.deadline or deadline

        while remaining_hours > 0 and current_date <= task_deadline:
            # Check if we've hit daily limit
            if hours_scheduled_today >= max_hours_per_day:
                current_date += timedelta(days=1)
                hours_scheduled_today = 0.0
                continue

            # Get available slots for this date
            slots = get_available_slots(current_date, availability, scheduled)

            if not slots:
                current_date += timedelta(days=1)
                hours_scheduled_today = 0.0
                continue

            # Find a slot that fits (or partially fits)
            for slot_start, slot_end in slots:
                slot_duration = (slot_end - slot_start).total_seconds() / 3600

                # Calculate how much we can schedule in this slot
                available_today = max_hours_per_day - hours_scheduled_today
                can_schedule = min(remaining_hours, slot_duration, available_today)

                if can_schedule >= 0.5:  # Minimum 30 minutes
                    task_end = slot_start + timedelta(hours=can_schedule)

                    scheduled.append(ScheduledTask(
                        task_id=task.id,
                        start=slot_start,
                        end=task_end,
                    ))

                    remaining_hours -= can_schedule
                    hours_scheduled_today += can_schedule

                    if remaining_hours <= 0:
                        break

            # Move to next day if no slots worked
            if remaining_hours > 0:
                current_date += timedelta(days=1)
                hours_scheduled_today = 0.0

    return scheduled


def reschedule_single_task(
    task: TaskBlock,
    new_start: datetime,
    availability: Availability,
    existing_schedule: list[ScheduledTask],
) -> Optional[ScheduledTask]:
    """
    Reschedule a single task to a new start time if the slot is available.

    Returns the new scheduled task or None if the slot is not available.
    """
    new_end = new_start + timedelta(hours=task.estimated_hours)

    # Check if the new slot is within preferred hours
    is_weekend = new_start.weekday() >= 5
    time_ranges = (
        availability.preferred_hours.weekend
        if is_weekend
        else availability.preferred_hours.weekday
    )

    slot_valid = False
    for time_range in time_ranges:
        start_hour, end_hour = parse_time_range(time_range)
        if new_start.hour >= start_hour and new_end.hour <= end_hour:
            slot_valid = True
            break

    if not slot_valid:
        return None

    # Check for conflicts with busy intervals
    for busy in availability.busy_intervals:
        if (new_start < busy.end and new_end > busy.start):
            return None

    # Check for conflicts with other scheduled tasks
    for scheduled in existing_schedule:
        if scheduled.task_id == task.id:
            continue  # Skip the task being rescheduled
        if (new_start < scheduled.end and new_end > scheduled.start):
            return None

    return ScheduledTask(
        task_id=task.id,
        start=new_start,
        end=new_end,
    )


def calculate_schedule_stats(
    tasks: list[TaskBlock],
    schedule: list[ScheduledTask],
    deadline: Optional[datetime] = None,
) -> dict:
    """Calculate statistics about the schedule."""
    total_hours = sum(t.estimated_hours for t in tasks if t.status != "deleted")
    scheduled_hours = sum(
        (s.end - s.start).total_seconds() / 3600
        for s in schedule
    )

    # Group by day
    days_used = set()
    for s in schedule:
        days_used.add(s.start.date())

    # Check if deadline is met
    deadline_met = True
    if deadline and schedule:
        last_end = max(s.end for s in schedule)
        deadline_met = last_end <= deadline

    return {
        "total_hours": total_hours,
        "scheduled_hours": scheduled_hours,
        "coverage": scheduled_hours / total_hours if total_hours > 0 else 0,
        "days_used": len(days_used),
        "deadline_met": deadline_met,
    }
