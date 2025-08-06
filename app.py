#!/usr/bin/env python3
"""
Aplicación web para el Agente de Planificación de Turnos
"""

from flask import Flask, render_template, jsonify, request, send_file
from flask_cors import CORS
from planning_agent import PlanningAgent, Empleado, Rol, TipoTurno
from datetime import datetime, timedelta
import json
import os

app = Flask(__name__)
CORS(app)

# Instancia global del agente
agent = PlanningAgent()

@app.route('/')
def index():
    """Página principal"""
    return render_template('index.html')

@app.route('/api/generar_planning', methods=['POST'])
def generar_planning():
    """Endpoint para generar planning"""
    try:
        data = request.json
        fecha_inicio = data.get('fecha_inicio')
        fecha_fin = data.get('fecha_fin')
        
        if not fecha_inicio or not fecha_fin:
            return jsonify({"error": "Fechas de inicio y fin requeridas"}), 400
        
        resultado = agent.generar_planning(fecha_inicio, fecha_fin)
        return jsonify(resultado)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/mostrar_planning', methods=['GET'])
def mostrar_planning():
    """Endpoint para mostrar planning"""
    try:
        nombre = request.args.get('nombre')
        planning_texto = agent.mostrar_planning(nombre)
        
        # También obtener el planning estructurado si existe
        planning_data = None
        if agent.planning:
            fechas = sorted(agent.planning.keys())
            if fechas:
                planning_data = agent._planning_to_dict(fechas[0], fechas[-1])
        
        return jsonify({
            "texto": planning_texto,
            "datos": planning_data
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/registrar_ausencia', methods=['POST'])
def registrar_ausencia():
    """Endpoint para registrar ausencia"""
    try:
        data = request.json
        nombre = data.get('nombre')
        fecha = data.get('fecha')
        motivo = data.get('motivo', 'Asuntos propios')
        
        if not nombre or not fecha:
            return jsonify({"error": "Nombre y fecha requeridos"}), 400
        
        resultado = agent.registrar_ausencia(nombre, fecha, motivo)
        return jsonify(resultado)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/solicitar_intercambio', methods=['POST'])
def solicitar_intercambio():
    """Endpoint para solicitar intercambio"""
    try:
        data = request.json
        origen = data.get('origen')
        destino = data.get('destino')
        fecha = data.get('fecha')
        
        if not origen or not destino or not fecha:
            return jsonify({"error": "Todos los campos son requeridos"}), 400
        
        resultado = agent.solicitar_intercambio(origen, destino, fecha)
        return jsonify(resultado)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/sugerir_reemplazo', methods=['POST'])
def sugerir_reemplazo():
    """Endpoint para sugerir reemplazos"""
    try:
        data = request.json
        fecha = data.get('fecha')
        turno = data.get('turno')
        rol = data.get('rol')
        
        if not fecha or not turno:
            return jsonify({"error": "Fecha y turno requeridos"}), 400
        
        resultado = agent.sugerir_reemplazo(fecha, turno, rol)
        return jsonify(resultado)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/ver_estadisticas', methods=['GET'])
def ver_estadisticas():
    """Endpoint para ver estadísticas"""
    try:
        estadisticas = agent.ver_estadisticas()
        return jsonify(estadisticas)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/registrar_preferencia', methods=['POST'])
def registrar_preferencia():
    """Endpoint para registrar preferencias"""
    try:
        data = request.json
        nombre = data.get('nombre')
        preferencias = data.get('preferencias', {})
        
        if not nombre:
            return jsonify({"error": "Nombre requerido"}), 400
        
        resultado = agent.registrar_preferencia(nombre, preferencias)
        return jsonify(resultado)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/modificar_turno', methods=['POST'])
def modificar_turno():
    """Endpoint para modificar turno"""
    try:
        data = request.json
        nombre = data.get('nombre')
        fecha = data.get('fecha')
        nuevo_turno = data.get('nuevo_turno')
        
        if not nombre or not fecha or not nuevo_turno:
            return jsonify({"error": "Todos los campos son requeridos"}), 400
        
        resultado = agent.modificar_turno(nombre, fecha, nuevo_turno)
        return jsonify(resultado)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/empleados', methods=['GET'])
def listar_empleados():
    """Endpoint para listar empleados"""
    try:
        empleados = []
        for emp in agent.empleados.values():
            empleados.append({
                "id": emp.id,
                "nombre": emp.nombre,
                "rol": emp.rol.value,
                "antiguedad_meses": emp.antiguedad_meses,
                "horas_max": emp.horas_semanales_max,
                "horas_min": emp.horas_semanales_min
            })
        
        return jsonify(empleados)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/agregar_empleado', methods=['POST'])
def agregar_empleado():
    """Endpoint para agregar empleado"""
    try:
        data = request.json
        
        # Validar datos requeridos
        nombre = data.get('nombre')
        rol_str = data.get('rol')
        antiguedad = data.get('antiguedad_meses', 0)
        
        if not nombre or not rol_str:
            return jsonify({"error": "Nombre y rol son requeridos"}), 400
        
        # Buscar rol
        rol = None
        for r in Rol:
            if r.value.lower() == rol_str.lower():
                rol = r
                break
        
        if not rol:
            return jsonify({"error": f"Rol '{rol_str}' no válido"}), 400
        
        # Generar nuevo ID
        nuevo_id = max(agent.empleados.keys()) + 1 if agent.empleados else 1
        
        # Crear empleado
        nuevo_empleado = Empleado(
            id=nuevo_id,
            nombre=nombre,
            rol=rol,
            antiguedad_meses=antiguedad,
            horas_semanales_max=data.get('horas_max', 40),
            horas_semanales_min=data.get('horas_min', 20)
        )
        
        agent.empleados[nuevo_id] = nuevo_empleado
        
        return jsonify({
            "exito": True,
            "mensaje": f"Empleado {nombre} agregado correctamente",
            "empleado": {
                "id": nuevo_id,
                "nombre": nombre,
                "rol": rol.value
            }
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/exportar_csv', methods=['POST'])
def exportar_csv():
    """Endpoint para exportar planning a CSV"""
    try:
        data = request.json
        fecha_inicio = data.get('fecha_inicio')
        fecha_fin = data.get('fecha_fin')
        
        if not fecha_inicio or not fecha_fin:
            return jsonify({"error": "Fechas requeridas"}), 400
        
        archivo = f"planning_{fecha_inicio}_{fecha_fin}.csv"
        mensaje = agent.exportar_planning_csv(fecha_inicio, fecha_fin, archivo)
        
        return send_file(archivo, as_attachment=True, mimetype='text/csv')
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/guardar_estado', methods=['POST'])
def guardar_estado():
    """Endpoint para guardar estado"""
    try:
        archivo = "planning_estado.json"
        mensaje = agent.guardar_estado(archivo)
        return jsonify({"exito": True, "mensaje": mensaje})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/cargar_estado', methods=['POST'])
def cargar_estado():
    """Endpoint para cargar estado guardado"""
    try:
        archivo = "planning_estado.json"
        
        if not os.path.exists(archivo):
            return jsonify({"error": "No hay estado guardado"}), 404
        
        with open(archivo, 'r', encoding='utf-8') as f:
            estado = json.load(f)
        
        # Restaurar empleados
        agent.empleados.clear()
        for emp_id, emp_data in estado['empleados'].items():
            # Buscar rol
            rol = None
            for r in Rol:
                if r.value == emp_data['rol']:
                    rol = r
                    break
            
            empleado = Empleado(
                id=emp_data['id'],
                nombre=emp_data['nombre'],
                rol=rol,
                antiguedad_meses=emp_data['antiguedad_meses'],
                horas_semanales_max=emp_data['horas_semanales_max'],
                horas_semanales_min=emp_data['horas_semanales_min']
            )
            
            # Restaurar preferencias
            for turno_str in emp_data.get('turnos_preferidos', []):
                for t in TipoTurno:
                    if t.value == turno_str:
                        empleado.turnos_preferidos.append(t)
                        break
            
            agent.empleados[int(emp_id)] = empleado
        
        # Restaurar planning
        agent.planning.clear()
        for fecha_str, turnos_data in estado['planning'].items():
            fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
            agent.planning[fecha] = []
            
            for turno_data in turnos_data:
                from planning_agent import Turno
                
                # Buscar tipo de turno
                tipo_turno = None
                for t in TipoTurno:
                    if t.value == turno_data['tipo']:
                        tipo_turno = t
                        break
                
                # Buscar rol
                rol = None
                if turno_data['rol_requerido']:
                    for r in Rol:
                        if r.value == turno_data['rol_requerido']:
                            rol = r
                            break
                
                turno = Turno(
                    fecha=fecha,
                    tipo=tipo_turno,
                    rol_requerido=rol,
                    horas=turno_data['horas']
                )
                
                # Asignar empleado si existe
                if turno_data['empleado_id']:
                    turno.empleado = agent.empleados.get(turno_data['empleado_id'])
                
                agent.planning[fecha].append(turno)
        
        return jsonify({
            "exito": True,
            "mensaje": "Estado cargado correctamente",
            "fecha_guardado": estado.get('fecha_guardado')
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/tipos_turno', methods=['GET'])
def tipos_turno():
    """Endpoint para obtener tipos de turno disponibles"""
    tipos = [{"valor": t.value, "nombre": t.value} for t in TipoTurno]
    return jsonify(tipos)

@app.route('/api/roles', methods=['GET'])
def roles():
    """Endpoint para obtener roles disponibles"""
    roles = [{"valor": r.value, "nombre": r.value} for r in Rol]
    return jsonify(roles)

@app.route('/api/motivos_ausencia', methods=['GET'])
def motivos_ausencia():
    """Endpoint para obtener motivos de ausencia"""
    from planning_agent import MotivoAusencia
    motivos = [{"valor": m.value, "nombre": m.value} for m in MotivoAusencia]
    return jsonify(motivos)

if __name__ == '__main__':
    # Crear carpeta de templates si no existe
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    
    app.run(debug=True, host='0.0.0.0', port=5000)