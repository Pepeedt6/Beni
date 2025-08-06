from __future__ import annotations

import typer
from typing import Optional

from . import planner

app = typer.Typer(help="Agente de planificación de turnos laborales")


@app.command()
def add_employee(
    nombre: str,
    roles: str = typer.Option("operario", help="Roles separados por coma"),
    seniority: int = typer.Option(0, help="Antigüedad en años"),
    weekly_hours: int = typer.Option(40, help="Horas semanales"),
):
    """Registrar o actualizar un empleado."""
    roles_list = [r.strip() for r in roles.split(",") if r.strip()]
    planner.registrar_preferencia(
        nombre,
        {
            "roles": roles_list,
            "seniority": seniority,
            "weekly_hours": weekly_hours,
        },
    )


@app.command()
def generar(start: str, end: str):
    """Generar planning entre fechas (YYYY-MM-DD)."""
    planner.generar_planning(start, end)


@app.command()
def mostrar(nombre: Optional[str] = typer.Argument(None)):
    """Mostrar planning completo o de un empleado."""
    planner.mostrar_planning(nombre)


@app.command()
def ausencia(nombre: str, fecha: str, motivo: str = "Ausencia"):
    """Registrar ausencia."""
    planner.registrar_ausencia(nombre, fecha, motivo)


@app.command()
def intercambio(origen: str, destino: str, fecha: str):
    """Solicitar intercambio de turno el mismo día."""
    planner.solicitar_intercambio(origen, destino, fecha)


@app.command()
def reemplazo(fecha: str, turno: str, rol: str = "operario"):
    """Sugerir reemplazo."""
    planner.sugerir_reemplazo(fecha, turno, rol)


@app.command()
def estadisticas():
    """Ver estadísticas de carga y equidad."""
    planner.ver_estadisticas()


@app.command()
def modificar(nombre: str, fecha: str, nuevo_turno: str):
    """Modificar turno asignado."""
    planner.modificar_turno(nombre, fecha, nuevo_turno)


if __name__ == "__main__":
    app()