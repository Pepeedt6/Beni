# Sistema de Planificación de Turnos


## Instalación

```bash
pip install -r requirements.txt
```

## Uso rápido

```bash
python -m shift_planner.cli add-employee Juan --roles operario --seniority 5 --weekly-hours 40

# Generar planning del 12 al 18 de agosto
python -m shift_planner.cli generar 2025-08-12 2025-08-18

# Mostrar planning
python -m shift_planner.cli mostrar
```