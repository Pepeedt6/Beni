# Sistema de Gestión de Turnos Laborales

Un sistema completo y automatizado para la planificación semanal de turnos laborales, considerando disponibilidad, antigüedad, preferencias y normativas legales.

## 🚀 Características Principales

### ✅ Funcionalidades Core
- **Planificación Automática**: Generación automática de turnos considerando antigüedad y disponibilidad
- **Gestión de Ausencias**: Registro de ausencias con búsqueda automática de reemplazos
- **Intercambios de Turnos**: Sistema de intercambios con validación de disponibilidad
- **Estadísticas Detalladas**: Métricas de carga laboral, cobertura y equidad
- **Exportación de Reportes**: CSV y PDF para análisis y archivo

### 🎯 Cumplimiento Legal
- ✅ Horas máximas semanales (40h por defecto)
- ✅ Descanso mínimo entre turnos (11 horas)
- ✅ Rotación equitativa de turnos
- ✅ Consideración de antigüedad como criterio de prioridad

### 🎨 Interfaz Moderna
- 📱 Diseño responsive y mobile-friendly
- 🎨 UI moderna con Bootstrap 5 y Font Awesome
- ⚡ Interacciones fluidas y animaciones
- 🔔 Sistema de notificaciones en tiempo real

## 📋 Requisitos del Sistema

- Python 3.8+
- Flask 2.3+
- SQLite (incluido)
- Navegador web moderno

## 🛠️ Instalación

### 1. Clonar el repositorio
```bash
git clone <repository-url>
cd shift-management-system
```

### 2. Crear entorno virtual
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Ejecutar la aplicación
```bash
python app.py
```

### 5. Acceder al sistema
Abrir navegador en: `http://localhost:5000`

## 👥 Credenciales de Demo

El sistema incluye empleados de ejemplo con las siguientes credenciales:

| Empleado | Email | Contraseña | Antigüedad |
|----------|-------|------------|------------|
| Juan Pérez | juan@empresa.com | password123 | 5 años |
| María García | maria@empresa.com | password123 | 3 años |
| Carlos López | carlos@empresa.com | password123 | 2 años |
| Ana Martínez | ana@empresa.com | password123 | 1 año |
| Luis Rodríguez | luis@empresa.com | password123 | 4 años |

## 📖 Guía de Uso

### 🗓️ Generar Planning Semanal

1. **Iniciar sesión** con cualquier credencial de demo
2. **Ir al Dashboard** y hacer clic en "Generar Planning"
3. **Seleccionar fechas** (lunes a domingo)
4. **Confirmar generación** - El sistema asignará automáticamente empleados

### 👤 Ver Turnos Asignados

1. **Hacer clic en "Ver Planning"** en el dashboard
2. **Usar filtros** por empleado o estado
3. **Exportar** a CSV o PDF según necesidad

### 🚫 Registrar Ausencia

1. **Hacer clic en "Registrar Ausencia"**
2. **Seleccionar empleado** y fecha
3. **Especificar motivo** (enfermedad, vacaciones, etc.)
4. **Confirmar** - El sistema buscará reemplazo automáticamente

### 🔄 Solicitar Intercambio

1. **Hacer clic en "Intercambiar Turno"**
2. **Seleccionar empleados** origen y destino
3. **Especificar fecha** del intercambio
4. **Verificar disponibilidad** de ambos empleados
5. **Confirmar intercambio**

### 📊 Ver Estadísticas

1. **Hacer clic en "Ver Estadísticas Detalladas"**
2. **Revisar métricas** de carga y equidad
3. **Analizar distribución** de turnos por empleado

## 🔧 Configuración Avanzada

### Variables de Entorno

Crear archivo `.env` en la raíz del proyecto:

```env
SECRET_KEY=tu-clave-secreta-aqui
FLASK_ENV=development
DATABASE_URL=sqlite:///shifts.db
```

### Personalizar Turnos

Editar en `app.py` la sección `shifts_config`:

```python
shifts_config = [
    {'start': '08:00', 'end': '16:00', 'role': 'Operario'},
    {'start': '16:00', 'end': '00:00', 'role': 'Operario'},
    {'start': '00:00', 'end': '08:00', 'role': 'Operario'},
]
```

### Ajustar Reglas Laborales

Modificar en la clase `ShiftManager`:

```python
# Horas máximas semanales
max_hours_week = 40

# Descanso mínimo entre turnos (horas)
min_rest_hours = 11
```

## 📁 Estructura del Proyecto

```
shift-management-system/
├── app.py                 # Aplicación principal Flask
├── requirements.txt       # Dependencias Python
├── README.md             # Este archivo
├── templates/            # Plantillas HTML
│   ├── base.html        # Plantilla base
│   ├── index.html       # Página de inicio
│   ├── login.html       # Página de login
│   ├── dashboard.html   # Dashboard principal
│   └── modals/          # Modales de funcionalidades
├── static/              # Archivos estáticos
│   ├── css/
│   │   └── style.css    # Estilos personalizados
│   └── js/
│       └── app.js       # JavaScript principal
└── shifts.db            # Base de datos SQLite (se crea automáticamente)
```

## 🔌 API Endpoints

### Planning
- `POST /api/generar_planning` - Generar planning semanal
- `GET /api/mostrar_planning` - Obtener planning actual
- `POST /api/modificar_turno` - Modificar turno asignado

### Ausencias
- `POST /api/registrar_ausencia` - Registrar ausencia
- `POST /api/solicitar_intercambio` - Solicitar intercambio

### Estadísticas
- `GET /api/ver_estadisticas` - Obtener estadísticas
- `POST /api/registrar_preferencia` - Guardar preferencias

### Exportación
- `GET /api/exportar_csv` - Exportar a CSV
- `GET /api/exportar_pdf` - Exportar a PDF

## 🧪 Testing

### Ejecutar tests básicos
```bash
python -m pytest tests/
```

### Verificar funcionalidades
1. **Login** con credenciales de demo
2. **Generar planning** para la próxima semana
3. **Registrar ausencia** y verificar reemplazo automático
4. **Solicitar intercambio** entre empleados
5. **Exportar reportes** en diferentes formatos

## 🚀 Despliegue en Producción

### Usando Gunicorn
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Usando Docker
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

### Variables de entorno para producción
```env
SECRET_KEY=clave-super-secreta-y-compleja
FLASK_ENV=production
DATABASE_URL=postgresql://user:pass@localhost/shifts
```

## 🔒 Seguridad

- ✅ Autenticación de usuarios
- ✅ Validación de formularios
- ✅ Protección CSRF
- ✅ Sanitización de datos
- ✅ Logs de auditoría

## 📈 Monitoreo

### Logs de aplicación
```bash
tail -f logs/app.log
```

### Métricas de rendimiento
- Tiempo de respuesta de API
- Uso de memoria y CPU
- Errores y excepciones

## 🤝 Contribución

1. **Fork** el repositorio
2. **Crear** rama para feature (`git checkout -b feature/nueva-funcionalidad`)
3. **Commit** cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. **Push** a la rama (`git push origin feature/nueva-funcionalidad`)
5. **Crear** Pull Request

## 📝 Licencia

Este proyecto está bajo la Licencia MIT. Ver `LICENSE` para más detalles.

## 🆘 Soporte

### Problemas Comunes

**Error: "No module named 'flask'"**
```bash
pip install -r requirements.txt
```

**Error: "Database is locked"**
```bash
rm shifts.db
python app.py  # Se recreará automáticamente
```

**Error: "Port 5000 already in use"**
```bash
python app.py --port 5001
```

### Contacto
- 📧 Email: soporte@empresa.com
- 📱 Teléfono: +34 123 456 789
- 💬 Chat: Disponible en la aplicación

## 🎯 Roadmap

### Versión 2.0 (Próximamente)
- 🔔 Notificaciones push en tiempo real
- 📱 App móvil nativa
- 🤖 IA para optimización de turnos
- 🔗 Integración con sistemas de nómina
- 📊 Dashboard ejecutivo avanzado

### Versión 2.1
- 🌍 Soporte multiidioma
- 🎨 Temas personalizables
- 📈 Reportes avanzados
- 🔐 Autenticación 2FA

---

**Desarrollado con ❤️ para optimizar la gestión de turnos laborales**