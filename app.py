from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime, timedelta, date
from dateutil import parser
import pandas as pd
import json
import os
from werkzeug.security import generate_password_hash, check_password_hash
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
import io

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///shifts.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Modelos de datos
class Employee(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    seniority = db.Column(db.Integer, default=0)  # Años de antigüedad
    max_hours_week = db.Column(db.Integer, default=40)
    preferences = db.Column(db.Text, default='{}')  # JSON string
    is_active = db.Column(db.Boolean, default=True)
    
    def get_preferences(self):
        return json.loads(self.preferences)
    
    def set_preferences(self, prefs):
        self.preferences = json.dumps(prefs)

class Shift(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.String(5), nullable=False)  # HH:MM
    end_time = db.Column(db.String(5), nullable=False)    # HH:MM
    role = db.Column(db.String(50), nullable=False)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'))
    status = db.Column(db.String(20), default='assigned')  # assigned, available, absent
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Absence(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'))
    date = db.Column(db.Date, nullable=False)
    reason = db.Column(db.String(200))
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected

class ShiftExchange(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    requester_id = db.Column(db.Integer, db.ForeignKey('employee.id'))
    target_id = db.Column(db.Integer, db.ForeignKey('employee.id'))
    shift_id = db.Column(db.Integer, db.ForeignKey('shift.id'))
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return Employee.query.get(int(user_id))

# Clase principal para gestión de turnos
class ShiftManager:
    def __init__(self):
        self.week_start = None
        self.week_end = None
        self.shifts = []
        self.employees = []
        self.absences = []
        
    def generar_planning(self, fecha_inicio, fecha_fin):
        """Genera el planning semanal desde cero"""
        self.week_start = fecha_inicio
        self.week_end = fecha_fin
        
        # Obtener empleados activos
        self.employees = Employee.query.filter_by(is_active=True).all()
        
        # Obtener ausencias confirmadas
        self.absences = Absence.query.filter(
            Absence.date >= fecha_inicio,
            Absence.date <= fecha_fin,
            Absence.status == 'approved'
        ).all()
        
        # Definir turnos estándar
        shifts_config = [
            {'start': '08:00', 'end': '16:00', 'role': 'Operario'},
            {'start': '16:00', 'end': '00:00', 'role': 'Operario'},
            {'start': '00:00', 'end': '08:00', 'role': 'Operario'},
        ]
        
        # Generar turnos para cada día
        current_date = fecha_inicio
        while current_date <= fecha_fin:
            for shift_config in shifts_config:
                # Verificar si ya existe un turno para esta fecha/hora
                existing_shift = Shift.query.filter_by(
                    date=current_date,
                    start_time=shift_config['start'],
                    role=shift_config['role']
                ).first()
                
                if not existing_shift:
                    shift = Shift(
                        date=current_date,
                        start_time=shift_config['start'],
                        end_time=shift_config['end'],
                        role=shift_config['role'],
                        status='available'
                    )
                    db.session.add(shift)
            
            current_date += timedelta(days=1)
        
        db.session.commit()
        return self.asignar_empleados()
    
    def asignar_empleados(self):
        """Asigna empleados a turnos disponibles considerando reglas"""
        # Obtener turnos sin asignar
        available_shifts = Shift.query.filter_by(status='available').all()
        
        for shift in available_shifts:
            # Buscar empleado disponible
            available_employees = self.get_available_employees(shift)
            
            if available_employees:
                # Seleccionar empleado con mayor antigüedad
                selected_employee = max(available_employees, key=lambda e: e.seniority)
                shift.employee_id = selected_employee.id
                shift.status = 'assigned'
        
        db.session.commit()
        return True
    
    def get_available_employees(self, shift):
        """Obtiene empleados disponibles para un turno específico"""
        available = []
        
        for employee in self.employees:
            if self.is_employee_available(employee, shift):
                available.append(employee)
        
        return available
    
    def is_employee_available(self, employee, shift):
        """Verifica si un empleado está disponible para un turno"""
        # Verificar ausencias
        absence = Absence.query.filter_by(
            employee_id=employee.id,
            date=shift.date,
            status='approved'
        ).first()
        
        if absence:
            return False
        
        # Verificar horas máximas semanales
        week_shifts = Shift.query.filter(
            Shift.employee_id == employee.id,
            Shift.date >= shift.date - timedelta(days=shift.date.weekday()),
            Shift.date < shift.date - timedelta(days=shift.date.weekday()) + timedelta(days=7),
            Shift.status == 'assigned'
        ).all()
        
        total_hours = sum(self.calculate_shift_hours(s) for s in week_shifts)
        shift_hours = self.calculate_shift_hours(shift)
        
        if total_hours + shift_hours > employee.max_hours_week:
            return False
        
        # Verificar descanso mínimo entre turnos
        if not self.check_rest_period(employee, shift):
            return False
        
        return True
    
    def calculate_shift_hours(self, shift):
        """Calcula las horas de un turno"""
        start = datetime.strptime(shift.start_time, '%H:%M')
        end = datetime.strptime(shift.end_time, '%H:%M')
        
        if end < start:  # Turno nocturno
            end += timedelta(days=1)
        
        return (end - start).total_seconds() / 3600
    
    def check_rest_period(self, employee, shift):
        """Verifica el período de descanso mínimo"""
        # Buscar turnos del empleado en días anteriores y posteriores
        previous_shifts = Shift.query.filter(
            Shift.employee_id == employee.id,
            Shift.date < shift.date,
            Shift.date >= shift.date - timedelta(days=1),
            Shift.status == 'assigned'
        ).all()
        
        next_shifts = Shift.query.filter(
            Shift.employee_id == employee.id,
            Shift.date > shift.date,
            Shift.date <= shift.date + timedelta(days=1),
            Shift.status == 'assigned'
        ).all()
        
        # Verificar descanso mínimo de 11 horas entre turnos
        for prev_shift in previous_shifts:
            prev_end = datetime.strptime(prev_shift.end_time, '%H:%M')
            if prev_shift.end_time < prev_shift.start_time:  # Turno nocturno
                prev_end += timedelta(days=1)
            
            shift_start = datetime.strptime(shift.start_time, '%H:%M')
            if shift_start < prev_end:
                shift_start += timedelta(days=1)
            
            rest_hours = (shift_start - prev_end).total_seconds() / 3600
            if rest_hours < 11:
                return False
        
        return True
    
    def mostrar_planning(self, nombre=None):
        """Muestra el planning completo o de una persona específica"""
        if nombre:
            employee = Employee.query.filter_by(name=nombre).first()
            if not employee:
                return None
            
            shifts = Shift.query.filter_by(employee_id=employee.id).order_by(Shift.date, Shift.start_time).all()
        else:
            shifts = Shift.query.order_by(Shift.date, Shift.start_time).all()
        
        return shifts
    
    def registrar_ausencia(self, nombre, fecha, motivo):
        """Registra una ausencia y busca sustituto"""
        employee = Employee.query.filter_by(name=nombre).first()
        if not employee:
            return False, "Empleado no encontrado"
        
        # Verificar si ya existe una ausencia para esa fecha
        existing_absence = Absence.query.filter_by(
            employee_id=employee.id,
            date=fecha
        ).first()
        
        if existing_absence:
            return False, "Ya existe una ausencia registrada para esa fecha"
        
        # Crear ausencia
        absence = Absence(
            employee_id=employee.id,
            date=fecha,
            reason=motivo,
            status='approved'
        )
        db.session.add(absence)
        
        # Buscar turnos afectados
        affected_shifts = Shift.query.filter_by(
            employee_id=employee.id,
            date=fecha
        ).all()
        
        # Liberar turnos y buscar reemplazos
        for shift in affected_shifts:
            shift.employee_id = None
            shift.status = 'available'
            
            # Buscar reemplazo automático
            replacement = self.sugerir_reemplazo(fecha, shift.start_time, shift.role)
            if replacement:
                shift.employee_id = replacement.id
                shift.status = 'assigned'
        
        db.session.commit()
        return True, "Ausencia registrada y reemplazos asignados"
    
    def sugerir_reemplazo(self, fecha, turno, rol):
        """Busca reemplazos viables para un turno"""
        available_employees = Employee.query.filter_by(is_active=True).all()
        
        for employee in sorted(available_employees, key=lambda e: e.seniority, reverse=True):
            # Crear turno temporal para verificar disponibilidad
            temp_shift = Shift(
                date=fecha,
                start_time=turno,
                end_time=self.get_end_time(turno),
                role=rol
            )
            
            if self.is_employee_available(employee, temp_shift):
                return employee
        
        return None
    
    def get_end_time(self, start_time):
        """Obtiene la hora de fin basada en la hora de inicio"""
        start = datetime.strptime(start_time, '%H:%M')
        
        if start_time == '08:00':
            return '16:00'
        elif start_time == '16:00':
            return '00:00'
        elif start_time == '00:00':
            return '08:00'
        else:
            return '16:00'  # Default
    
    def solicitar_intercambio(self, origen, destino, fecha):
        """Evalúa y procesa intercambio de turnos"""
        origin_employee = Employee.query.filter_by(name=origen).first()
        target_employee = Employee.query.filter_by(name=destino).first()
        
        if not origin_employee or not target_employee:
            return False, "Uno o ambos empleados no encontrados"
        
        # Buscar turnos de ambos empleados en la fecha
        origin_shift = Shift.query.filter_by(
            employee_id=origin_employee.id,
            date=fecha
        ).first()
        
        target_shift = Shift.query.filter_by(
            employee_id=target_employee.id,
            date=fecha
        ).first()
        
        if not origin_shift or not target_shift:
            return False, "Uno o ambos empleados no tienen turno en esa fecha"
        
        # Verificar que ambos empleados puedan hacer el intercambio
        if (self.is_employee_available(origin_employee, target_shift) and 
            self.is_employee_available(target_employee, origin_shift)):
            
            # Realizar intercambio
            origin_shift.employee_id, target_shift.employee_id = target_shift.employee_id, origin_shift.employee_id
            
            db.session.commit()
            return True, "Intercambio realizado exitosamente"
        else:
            return False, "No se puede realizar el intercambio - conflictos de disponibilidad"
    
    def ver_estadisticas(self):
        """Muestra métricas de carga, cobertura y equidad"""
        employees = Employee.query.filter_by(is_active=True).all()
        stats = {
            'total_employees': len(employees),
            'total_shifts': Shift.query.count(),
            'assigned_shifts': Shift.query.filter_by(status='assigned').count(),
            'available_shifts': Shift.query.filter_by(status='available').count(),
            'employee_stats': []
        }
        
        for employee in employees:
            employee_shifts = Shift.query.filter_by(employee_id=employee.id).all()
            total_hours = sum(self.calculate_shift_hours(s) for s in employee_shifts)
            
            stats['employee_stats'].append({
                'name': employee.name,
                'shifts_count': len(employee_shifts),
                'total_hours': total_hours,
                'seniority': employee.seniority
            })
        
        return stats
    
    def registrar_preferencia(self, nombre, datos):
        """Guarda o actualiza preferencias de un empleado"""
        employee = Employee.query.filter_by(name=nombre).first()
        if not employee:
            return False, "Empleado no encontrado"
        
        current_prefs = employee.get_preferences()
        current_prefs.update(datos)
        employee.set_preferences(current_prefs)
        
        db.session.commit()
        return True, "Preferencias actualizadas"
    
    def modificar_turno(self, nombre, fecha, nuevo_turno):
        """Cambia turno asignado si es válido"""
        employee = Employee.query.filter_by(name=nombre).first()
        if not employee:
            return False, "Empleado no encontrado"
        
        shift = Shift.query.filter_by(
            employee_id=employee.id,
            date=fecha
        ).first()
        
        if not shift:
            return False, "No se encontró turno para esa fecha"
        
        # Verificar si el nuevo turno está disponible
        available_shift = Shift.query.filter_by(
            date=fecha,
            start_time=nuevo_turno,
            status='available'
        ).first()
        
        if not available_shift:
            return False, "El turno solicitado no está disponible"
        
        # Verificar disponibilidad del empleado
        if not self.is_employee_available(employee, available_shift):
            return False, "El empleado no está disponible para ese turno"
        
        # Realizar cambio
        shift.employee_id = None
        shift.status = 'available'
        available_shift.employee_id = employee.id
        available_shift.status = 'assigned'
        
        db.session.commit()
        return True, "Turno modificado exitosamente"

# Instancia global del gestor de turnos
shift_manager = ShiftManager()

# Rutas de la aplicación
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        employee = Employee.query.filter_by(email=email).first()
        if employee and check_password_hash(employee.password_hash, password):
            login_user(employee)
            return redirect(url_for('dashboard'))
        
        flash('Credenciales inválidas')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/generar_planning', methods=['POST'])
@login_required
def api_generar_planning():
    data = request.get_json()
    fecha_inicio = parser.parse(data['fecha_inicio']).date()
    fecha_fin = parser.parse(data['fecha_fin']).date()
    
    success = shift_manager.generar_planning(fecha_inicio, fecha_fin)
    
    if success:
        return jsonify({'success': True, 'message': 'Planning generado exitosamente'})
    else:
        return jsonify({'success': False, 'message': 'Error al generar planning'})

@app.route('/api/mostrar_planning')
@login_required
def api_mostrar_planning():
    nombre = request.args.get('nombre')
    shifts = shift_manager.mostrar_planning(nombre)
    
    if shifts is None:
        return jsonify({'success': False, 'message': 'Empleado no encontrado'})
    
    shifts_data = []
    for shift in shifts:
        employee = Employee.query.get(shift.employee_id) if shift.employee_id else None
        shifts_data.append({
            'id': shift.id,
            'date': shift.date.strftime('%Y-%m-%d'),
            'start_time': shift.start_time,
            'end_time': shift.end_time,
            'role': shift.role,
            'employee': employee.name if employee else 'Sin asignar',
            'status': shift.status
        })
    
    return jsonify({'success': True, 'shifts': shifts_data})

@app.route('/api/registrar_ausencia', methods=['POST'])
@login_required
def api_registrar_ausencia():
    data = request.get_json()
    success, message = shift_manager.registrar_ausencia(
        data['nombre'],
        parser.parse(data['fecha']).date(),
        data['motivo']
    )
    
    return jsonify({'success': success, 'message': message})

@app.route('/api/solicitar_intercambio', methods=['POST'])
@login_required
def api_solicitar_intercambio():
    data = request.get_json()
    success, message = shift_manager.solicitar_intercambio(
        data['origen'],
        data['destino'],
        parser.parse(data['fecha']).date()
    )
    
    return jsonify({'success': success, 'message': message})

@app.route('/api/ver_estadisticas')
@login_required
def api_ver_estadisticas():
    stats = shift_manager.ver_estadisticas()
    return jsonify({'success': True, 'stats': stats})

@app.route('/api/registrar_preferencia', methods=['POST'])
@login_required
def api_registrar_preferencia():
    data = request.get_json()
    success, message = shift_manager.registrar_preferencia(
        data['nombre'],
        data['datos']
    )
    
    return jsonify({'success': success, 'message': message})

@app.route('/api/modificar_turno', methods=['POST'])
@login_required
def api_modificar_turno():
    data = request.get_json()
    success, message = shift_manager.modificar_turno(
        data['nombre'],
        parser.parse(data['fecha']).date(),
        data['nuevo_turno']
    )
    
    return jsonify({'success': success, 'message': message})

@app.route('/api/exportar_csv')
@login_required
def exportar_csv():
    shifts = Shift.query.order_by(Shift.date, Shift.start_time).all()
    
    data = []
    for shift in shifts:
        employee = Employee.query.get(shift.employee_id) if shift.employee_id else None
        data.append({
            'Fecha': shift.date.strftime('%Y-%m-%d'),
            'Hora Inicio': shift.start_time,
            'Hora Fin': shift.end_time,
            'Rol': shift.role,
            'Empleado': employee.name if employee else 'Sin asignar',
            'Estado': shift.status
        })
    
    df = pd.DataFrame(data)
    
    # Crear archivo CSV en memoria
    output = io.StringIO()
    df.to_csv(output, index=False, encoding='utf-8')
    output.seek(0)
    
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name='planning_semanal.csv'
    )

@app.route('/api/exportar_pdf')
@login_required
def exportar_pdf():
    shifts = Shift.query.order_by(Shift.date, Shift.start_time).all()
    
    # Crear PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    
    # Datos para la tabla
    data = [['Fecha', 'Hora Inicio', 'Hora Fin', 'Rol', 'Empleado', 'Estado']]
    
    for shift in shifts:
        employee = Employee.query.get(shift.employee_id) if shift.employee_id else None
        data.append([
            shift.date.strftime('%Y-%m-%d'),
            shift.start_time,
            shift.end_time,
            shift.role,
            employee.name if employee else 'Sin asignar',
            shift.status
        ])
    
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(table)
    doc.build(elements)
    
    buffer.seek(0)
    
    return send_file(
        buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name='planning_semanal.pdf'
    )

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        # Crear empleados de ejemplo si no existen
        if Employee.query.count() == 0:
            employees_data = [
                {'name': 'Juan Pérez', 'email': 'juan@empresa.com', 'role': 'Operario', 'seniority': 5},
                {'name': 'María García', 'email': 'maria@empresa.com', 'role': 'Operario', 'seniority': 3},
                {'name': 'Carlos López', 'email': 'carlos@empresa.com', 'role': 'Operario', 'seniority': 2},
                {'name': 'Ana Martínez', 'email': 'ana@empresa.com', 'role': 'Operario', 'seniority': 1},
                {'name': 'Luis Rodríguez', 'email': 'luis@empresa.com', 'role': 'Operario', 'seniority': 4},
            ]
            
            for emp_data in employees_data:
                employee = Employee(
                    name=emp_data['name'],
                    email=emp_data['email'],
                    password_hash=generate_password_hash('password123'),
                    role=emp_data['role'],
                    seniority=emp_data['seniority']
                )
                db.session.add(employee)
            
            db.session.commit()
    
    app.run(debug=True, host='0.0.0.0', port=5000)