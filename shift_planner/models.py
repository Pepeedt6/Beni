from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class Employee:
    """Represents an employee in the organisation."""

    name: str
    roles: List[str]
    seniority: int  # Years in the company
    weekly_hours: int
    preferences: Dict[str, any] = field(default_factory=dict)
    restrictions: List[str] = field(default_factory=list)  # e.g. ["night", "tuesday"]
    assigned_hours: int = 0  # updated each planning cycle

    def can_work_shift(self, shift_type: str, date: dt.date) -> bool:
        """Return True if employee is allowed to work the given shift on date."""
        weekday = date.strftime("%A").lower()
        if weekday in self.restrictions:
            return False
        if shift_type in self.restrictions:
            return False
        return True


@dataclass
class Absence:
    employee: str
    date: dt.date
    reason: str


@dataclass
class ShiftDefinition:
    """Definition of a shift type."""

    name: str  # e.g. "M" for morning
    start: dt.time
    end: dt.time
    hours: int


@dataclass
class ShiftAssignment:
    date: dt.date
    shift_type: str  # e.g. "M", "T", "N"
    role: str
    employee: Optional[str] = None  # Assigned employee name

    def key(self):
        return f"{self.date.isoformat()}|{self.shift_type}|{self.role}"