from __future__ import annotations

import datetime as dt
from collections import defaultdict
from typing import List, Dict, Optional, Tuple

from rich.console import Console
from rich.table import Table

from .models import Employee, ShiftDefinition, ShiftAssignment, Absence
from .storage import (
    load_state,
    save_state,
    employee_from_dict,
    employee_to_dict,
    absence_to_dict,
)

console = Console()

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SHIFT_DEFS: Dict[str, ShiftDefinition] = {
    "M": ShiftDefinition("M", dt.time(8, 0), dt.time(16, 0), 8),
    "T": ShiftDefinition("T", dt.time(16, 0), dt.time(0, 0), 8),
    "N": ShiftDefinition("N", dt.time(0, 0), dt.time(8, 0), 8),
}

REQUIRED_ROLES = {"operario": 1}
# ---------------------------------------------------------------------------


def _load_employees(state) -> List[Employee]:
    return [employee_from_dict(e) for e in state["employees"].values()]


def _get_absent_on(date: dt.date, state) -> List[str]:
    return [a["employee"] for a in state["absences"] if a["date"] == date]


def generar_planning(fecha_inicio: str, fecha_fin: str):  # noqa: C901
    """Crea planning semanal desde cero y lo guarda en estado global."""

    start_date = dt.date.fromisoformat(fecha_inicio)
    end_date = dt.date.fromisoformat(fecha_fin)

    state = load_state()
    employees = _load_employees(state)

    if not employees:
        console.print("[red]⚠️  No hay empleados registrados. Usa registrar_preferencia para añadirlos.")
        return

    # Reset assigned hours for fairness tracking
    for emp in employees:
        emp.assigned_hours = 0

    planning: Dict[str, str] = {}

    current_date = start_date
    while current_date <= end_date:
        absent_today = _get_absent_on(current_date, state)

        # Track employees assigned today to avoid double-assigning
        assigned_today = set()

        # Sort employees by fairness then seniority (lower assigned hours, higher seniority first)
        employees.sort(key=lambda e: (e.assigned_hours, -e.seniority))

        for shift_type, shift_def in SHIFT_DEFS.items():
            for role, qty in REQUIRED_ROLES.items():
                for _ in range(qty):
                    # Find first available employee
                    selected: Optional[Employee] = None
                    for emp in employees:
                        if emp.name in assigned_today:
                            continue
                        if emp.name in absent_today:
                            continue
                        if role not in emp.roles:
                            continue
                        if not emp.can_work_shift(shift_type, current_date):
                            continue
                        if emp.assigned_hours + shift_def.hours > emp.weekly_hours:
                            continue
                        selected = emp
                        break

                    assignment = ShiftAssignment(
                        date=current_date,
                        shift_type=shift_type,
                        role=role,
                        employee=selected.name if selected else None,
                    )
                    planning[assignment.key()] = assignment.employee
                    if selected:
                        selected.assigned_hours += shift_def.hours
                        assigned_today.add(selected.name)
        current_date += dt.timedelta(days=1)

    # Persist planning and updated employee hours
    state["planning"] = planning
    state["employees"] = {e.name: employee_to_dict(e) for e in employees}
    save_state(state)

    console.print(f"✅ Planning generado del {fecha_inicio} al {fecha_fin}")


def mostrar_planning(nombre: Optional[str] = None):
    """Muestra todo el planning o el de una persona en tabla."""
    state = load_state()
    planning: Dict[str, str] = state.get("planning", {})

    if not planning:
        console.print("[yellow]No hay planning generado todavía.")
        return

    table = Table(title="Planning Semanal")
    table.add_column("Fecha")
    table.add_column("Turno")
    table.add_column("Rol")
    table.add_column("Empleado")

    for key, employee in sorted(planning.items()):
        date_str, shift, role = key.split("|")
        if nombre and employee != nombre:
            continue
        table.add_row(date_str, shift, role, employee or "--")

    console.print(table)


def registrar_ausencia(nombre: str, fecha: str, motivo: str):
    state = load_state()
    absence_obj = Absence(employee=nombre, date=dt.date.fromisoformat(fecha), reason=motivo)
    state.setdefault("absences", []).append(absence_to_dict(absence_obj))
    save_state(state)
    console.print(f"📌 Ausencia registrada para {nombre} el {fecha} ({motivo}).")


def solicitar_intercambio(origen: str, destino: str, fecha: str):
    state = load_state()
    planning = state.get("planning", {})
    shift_keys = [k for k in planning.keys() if k.startswith(f"{fecha}|")]

    orig_key = next((k for k in shift_keys if planning[k] == origen), None)
    dest_key = next((k for k in shift_keys if planning[k] == destino), None)

    if not orig_key:
        console.print(f"[red]No se encontró turno para {origen} el {fecha}.")
        return
    if not dest_key:
        console.print(f"[red]No se encontró turno para {destino} el {fecha}.")
        return

    # Swap assignments
    planning[orig_key], planning[dest_key] = planning[dest_key], planning[orig_key]
    save_state(state)
    console.print(f"🔄 Intercambio realizado entre {origen} y {destino} para el {fecha}.")


def sugerir_reemplazo(fecha: str, turno: str, rol: str):
    date_obj = dt.date.fromisoformat(fecha)
    state = load_state()
    employees = _load_employees(state)
    absent = _get_absent_on(date_obj, state)

    shift_def = SHIFT_DEFS.get(turno)
    if not shift_def:
        console.print(f"[red]Turno {turno} no existe.")
        return

    candidates = []
    for emp in employees:
        if emp.name in absent:
            continue
        if rol not in emp.roles:
            continue
        if not emp.can_work_shift(turno, date_obj):
            continue
        if emp.assigned_hours + shift_def.hours > emp.weekly_hours:
            continue
        candidates.append(emp.name)

    console.print("👥 Posibles reemplazos:", ", ".join(candidates) if candidates else "Ninguno")


def ver_estadisticas():
    state = load_state()
    employees = _load_employees(state)
    planning = state.get("planning", {})

    total_hours = sum(e.assigned_hours for e in employees)
    avg_hours = total_hours / len(employees) if employees else 0

    table = Table(title="Estadísticas de Equidad")
    table.add_column("Empleado")
    table.add_column("Horas Asignadas")
    table.add_column("% Desviación")

    for e in sorted(employees, key=lambda x: x.assigned_hours, reverse=True):
        deviation = (e.assigned_hours - avg_hours) / avg_hours * 100 if avg_hours else 0
        table.add_row(e.name, str(e.assigned_hours), f"{deviation:.1f}%")

    console.print(table)


def registrar_preferencia(nombre: str, datos: Dict):
    state = load_state()
    employees = state.setdefault("employees", {})
    if nombre not in employees:
        # Create new employee with minimal info plus defaults
        emp = Employee(
            name=nombre,
            roles=datos.get("roles", ["operario"]),
            seniority=datos.get("seniority", 0),
            weekly_hours=datos.get("weekly_hours", 40),
            preferences=datos.get("preferences", {}),
            restrictions=datos.get("restrictions", []),
        )
    else:
        emp = employee_from_dict(employees[nombre])
        for k, v in datos.items():
            setattr(emp, k, v)
    employees[nombre] = employee_to_dict(emp)
    save_state(state)
    console.print(f"✅ Preferencias/empleado actualizado: {nombre}")


def modificar_turno(nombre: str, fecha: str, nuevo_turno: str):
    state = load_state()
    planning = state.get("planning", {})

    # Find the assignment of employee on date
    key_to_modify = None
    for key, emp in planning.items():
        if emp == nombre and key.startswith(f"{fecha}|"):
            key_to_modify = key
            break
    if not key_to_modify:
        console.print(f"[red]No se encontró turno para {nombre} el {fecha}.")
        return

    # Ensure the new shift is valid
    date_part, _old_turno, rol = key_to_modify.split("|")
    if nuevo_turno not in SHIFT_DEFS:
        console.print("[red]Turno no válido.")
        return

    new_key = f"{date_part}|{nuevo_turno}|{rol}"
    # Check if new_key is already occupied
    if planning.get(new_key):
        console.print("[red]El turno solicitado ya está ocupado.")
        return

    # Move assignment
    planning[new_key] = nombre
    del planning[key_to_modify]
    save_state(state)
    console.print(f"✏️ Turno actualizado para {nombre} el {fecha}: {nuevo_turno}")