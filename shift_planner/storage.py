from __future__ import annotations

import json
import datetime as dt
from pathlib import Path
from typing import Dict, Any, List

from .models import Employee, Absence, ShiftAssignment


STATE_PATH = Path("planner_state.json")


def _default_state() -> Dict[str, Any]:
    return {
        "employees": {},  # name -> employee dict
        "absences": [],  # list of {employee, date, reason}
        "planning": {},  # assignment_key -> employee name
    }


def load_state() -> Dict[str, Any]:
    if not STATE_PATH.exists():
        return _default_state()
    with STATE_PATH.open("r", encoding="utf-8") as f:
        raw = json.load(f)
    # convert date strings back to date objects
    for absence in raw.get("absences", []):
        absence["date"] = dt.date.fromisoformat(absence["date"])
    return raw


def save_state(state: Dict[str, Any]):
    # convert dates to strings for JSON serialization
    serializable = json.loads(json.dumps(state, default=str))
    with STATE_PATH.open("w", encoding="utf-8") as f:
        json.dump(serializable, f, indent=2, ensure_ascii=False)


# Helper conversions ----------------------------------------------------------------

def employee_from_dict(data: Dict[str, Any]) -> Employee:
    return Employee(
        name=data["name"],
        roles=data["roles"],
        seniority=data["seniority"],
        weekly_hours=data["weekly_hours"],
        preferences=data.get("preferences", {}),
        restrictions=data.get("restrictions", []),
        assigned_hours=data.get("assigned_hours", 0),
    )


def employee_to_dict(emp: Employee) -> Dict[str, Any]:
    return emp.__dict__


def absence_from_dict(data: Dict[str, Any]) -> Absence:
    return Absence(
        employee=data["employee"],
        date=data["date"],
        reason=data["reason"],
    )


def absence_to_dict(absence: Absence) -> Dict[str, Any]:
    return {
        "employee": absence.employee,
        "date": absence.date,
        "reason": absence.reason,
    }