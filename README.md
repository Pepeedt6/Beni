# 🤖 Sistema de Planificación de Turnos Laborales

Sistema inteligente y autónomo para la gestión de turnos laborales, asignación de personal y manejo de ausencias con interfaz web moderna.

## 🌟 Características Principales

- **Generación Automática de Planning**: Crea plannings semanales considerando múltiples factores
- **Gestión de Ausencias**: Registro y búsqueda automática de sustitutos
- **Intercambio de Turnos**: Sistema de intercambios validado entre empleados
- **Estadísticas en Tiempo Real**: Métricas de cobertura, equidad y distribución
- **Interfaz Web Moderna**: Dashboard intuitivo con Bootstrap 5
- **Exportación de Datos**: Genera archivos CSV y guarda/carga estados

## 🚀 Instalación Rápida

1. **Clonar el repositorio**
```bash
git clone <repository-url>
cd planning-system
```

2. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

3. **Ejecutar la aplicación**
```bash
python app.py
```

4. **Abrir en el navegador**
```
http://localhost:5000
```

## 📋 Requisitos del Sistema

- Python 3.8 o superior
- Flask 2.3.3
- flask-cors 4.0.0
- Navegador web moderno

## 🏗️ Estructura del Proyecto

```
planning-system/
│
├── planning_agent.py      # Core del agente de planificación
├── app.py                 # Aplicación Flask y API REST
├── templates/
│   └── index.html        # Interfaz web
├── requirements.txt      # Dependencias
├── ejemplo_uso.py        # Script de demostración
└── README.md            # Este archivo
```

## 💻 Uso del Sistema

### 1. Interfaz Web

La interfaz web proporciona acceso completo a todas las funcionalidades:

- **Planning**: Genera y visualiza plannings semanales
- **Empleados**: Gestiona la plantilla y preferencias
- **Ausencias**: Registra ausencias y encuentra sustitutos
- **Intercambios**: Procesa intercambios de turnos
- **Estadísticas**: Visualiza métricas y alertas

### 2. API REST

El sistema expone los siguientes endpoints:

```
POST   /api/generar_planning      - Genera planning semanal
GET    /api/mostrar_planning      - Muestra planning actual
POST   /api/registrar_ausencia    - Registra una ausencia
POST   /api/solicitar_intercambio - Procesa intercambio de turnos
POST   /api/sugerir_reemplazo     - Busca reemplazos disponibles
GET    /api/ver_estadisticas      - Obtiene estadísticas
POST   /api/registrar_preferencia - Actualiza preferencias de empleado
GET    /api/empleados             - Lista todos los empleados
POST   /api/agregar_empleado      - Agrega nuevo empleado
POST   /api/exportar_csv          - Exporta planning a CSV
POST   /api/guardar_estado        - Guarda estado actual
POST   /api/cargar_estado         - Carga estado guardado
```

### 3. Uso Programático

```python
from planning_agent import PlanningAgent

# Crear instancia del agente
agent = PlanningAgent()

# Generar planning
planning = agent.generar_planning("2024-08-12", "2024-08-18")

# Registrar ausencia
resultado = agent.registrar_ausencia("Juan García", "2024-08-14", "Enfermedad")

# Ver estadísticas
stats = agent.ver_estadisticas()
```

## 📊 Reglas de Negocio

El sistema implementa las siguientes reglas:

### Límites Laborales
- Máximo 40 horas semanales por empleado
- Mínimo 20 horas semanales por empleado
- Descanso mínimo de 12 horas entre turnos
- 2 días libres por semana

### Cobertura Mínima por Turno
- Operarios: 3 personas
- Supervisor: 1 persona
- Técnicos: 2 personas
- Seguridad: 2 personas
- Limpieza: 1 persona

### Criterios de Asignación
1. Antigüedad (mayor prioridad)
2. Preferencias del empleado
3. Equidad en distribución de horas
4. Rotación de turnos

## 🔧 Configuración Avanzada

### Agregar Nuevos Roles

En `planning_agent.py`:
```python
class Rol(Enum):
    NUEVO_ROL = "Nuevo Rol"
```

### Modificar Turnos

```python
class TipoTurno(Enum):
    PERSONALIZADO = "Personalizado"  # 10:00 - 18:00
```

### Ajustar Reglas

Modifica el diccionario `config` en la clase `PlanningAgent`:
```python
self.config = {
    "horas_max_dia": 10,
    "horas_max_semana": 40,
    "horas_min_descanso": 12,
    "dias_libres_semana": 2,
    "turnos_min_por_dia": {...}
}
```

## 📈 Métricas y KPIs

El sistema calcula automáticamente:

- **Porcentaje de Cobertura**: Turnos cubiertos vs. requeridos
- **Índice de Equidad**: Distribución de horas entre empleados
- **Satisfacción de Preferencias**: Turnos asignados según preferencias
- **Alertas Automáticas**: Problemas de cobertura o equidad

## 🔍 Ejemplos de Uso

### Ejemplo 1: Planning Básico
```bash
python ejemplo_uso.py
```

### Ejemplo 2: Gestión de Ausencias
```python
# Registrar ausencia con búsqueda de sustitutos
resultado = agent.registrar_ausencia("María López", "2024-08-15", "Vacaciones")

# Los sustitutos se sugieren automáticamente
for sustituto in resultado['sustitutos_sugeridos']:
    print(f"Candidato: {sustituto['nombre']} - Score: {sustituto['puntuacion']}")
```

### Ejemplo 3: Intercambio de Turnos
```python
# Solicitar intercambio entre empleados del mismo rol
resultado = agent.solicitar_intercambio("Carlos Ruiz", "Pedro Sánchez", "2024-08-16")
```

## 🛡️ Validaciones Automáticas

El sistema valida automáticamente:

- ✅ Cumplimiento de normativas laborales
- ✅ Disponibilidad de empleados
- ✅ Compatibilidad de roles en intercambios
- ✅ Límites de horas semanales
- ✅ Descansos mínimos entre turnos

## 📝 Formatos de Exportación

### CSV
```
Fecha,Día,Turno,Empleado,Rol,Horas
2024-08-12,Lunes,Mañana,Juan García,Operario,8
```

### JSON (Estado Completo)
```json
{
  "fecha_guardado": "2024-08-12T10:30:00",
  "empleados": {...},
  "planning": {...},
  "ausencias": [...],
  "intercambios": [...]
}
```

## 🤝 Contribuciones

Para contribuir al proyecto:

1. Fork el repositorio
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo licencia MIT. Ver archivo `LICENSE` para más detalles.

## 🆘 Soporte

Para reportar problemas o solicitar nuevas funcionalidades, por favor abre un issue en el repositorio.

---

**Desarrollado con ❤️ para optimizar la gestión de turnos laborales**