#!/usr/bin/env python3
"""
Agente de Planificación de Turnos Laborales
Gestión autónoma de planning semanal con asignación inteligente de personal
"""

from datetime import datetime, timedelta, date
from typing import List, Dict, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import json
import csv
from collections import defaultdict
import copy


class TipoTurno(Enum):
    """Tipos de turno disponibles"""
    MANANA = "Mañana"  # 06:00 - 14:00
    TARDE = "Tarde"    # 14:00 - 22:00
    NOCHE = "Noche"    # 22:00 - 06:00
    PARTIDO = "Partido" # 09:00 - 13:00 y 16:00 - 20:00
    COMPLETO = "Completo" # 08:00 - 17:00


class Rol(Enum):
    """Roles disponibles en la empresa"""
    OPERARIO = "Operario"
    SUPERVISOR = "Supervisor"
    TECNICO = "Técnico"
    ADMINISTRATIVO = "Administrativo"
    LIMPIEZA = "Limpieza"
    SEGURIDAD = "Seguridad"


class MotivoAusencia(Enum):
    """Motivos de ausencia"""
    VACACIONES = "Vacaciones"
    ENFERMEDAD = "Enfermedad"
    PERMISO = "Permiso"
    FORMACION = "Formación"
    ASUNTOS_PROPIOS = "Asuntos propios"


@dataclass
class Empleado:
    """Modelo de empleado"""
    id: int
    nombre: str
    rol: Rol
    antiguedad_meses: int
    horas_semanales_max: int = 40
    horas_semanales_min: int = 20
    turnos_preferidos: List[TipoTurno] = field(default_factory=list)
    turnos_no_disponibles: List[TipoTurno] = field(default_factory=list)
    dias_no_disponibles: List[int] = field(default_factory=list)  # 0=Lunes, 6=Domingo
    restricciones_medicas: List[str] = field(default_factory=list)
    
    def __hash__(self):
        return hash(self.id)


@dataclass
class Turno:
    """Modelo de turno asignado"""
    fecha: date
    tipo: TipoTurno
    empleado: Optional[Empleado] = None
    rol_requerido: Optional[Rol] = None
    horas: int = 8
    
    def __str__(self):
        emp = self.empleado.nombre if self.empleado else "Sin asignar"
        return f"{self.fecha} - {self.tipo.value} - {emp}"


@dataclass
class Ausencia:
    """Modelo de ausencia"""
    empleado: Empleado
    fecha_inicio: date
    fecha_fin: date
    motivo: MotivoAusencia
    aprobada: bool = False
    sustituto: Optional[Empleado] = None


@dataclass
class IntercambioTurno:
    """Modelo de solicitud de intercambio"""
    solicitante: Empleado
    receptor: Empleado
    fecha_turno_solicitante: date
    fecha_turno_receptor: date
    estado: str = "pendiente"  # pendiente, aprobado, rechazado
    fecha_solicitud: datetime = field(default_factory=datetime.now)


class PlanningAgent:
    """Agente principal de gestión de planning"""
    
    def __init__(self):
        self.empleados: Dict[int, Empleado] = {}
        self.planning: Dict[date, List[Turno]] = defaultdict(list)
        self.ausencias: List[Ausencia] = []
        self.intercambios: List[IntercambioTurno] = []
        self.historico_turnos: Dict[int, List[Turno]] = defaultdict(list)
        
        # Configuración de reglas laborales
        self.config = {
            "horas_max_dia": 10,
            "horas_max_semana": 40,
            "horas_min_descanso": 12,
            "dias_libres_semana": 2,
            "turnos_min_por_dia": {
                Rol.OPERARIO: 3,
                Rol.SUPERVISOR: 1,
                Rol.TECNICO: 2,
                Rol.SEGURIDAD: 2,
                Rol.LIMPIEZA: 1
            }
        }
        
        # Inicializar con datos de ejemplo
        self._inicializar_empleados_ejemplo()
    
    def _inicializar_empleados_ejemplo(self):
        """Crea empleados de ejemplo para demostración"""
        empleados_data = [
            {"id": 1, "nombre": "Juan García", "rol": Rol.OPERARIO, "antiguedad": 36},
            {"id": 2, "nombre": "María López", "rol": Rol.SUPERVISOR, "antiguedad": 60},
            {"id": 3, "nombre": "Carlos Ruiz", "rol": Rol.OPERARIO, "antiguedad": 24},
            {"id": 4, "nombre": "Ana Martín", "rol": Rol.TECNICO, "antiguedad": 18},
            {"id": 5, "nombre": "Pedro Sánchez", "rol": Rol.OPERARIO, "antiguedad": 12},
            {"id": 6, "nombre": "Laura Gómez", "rol": Rol.TECNICO, "antiguedad": 30},
            {"id": 7, "nombre": "Miguel Torres", "rol": Rol.SEGURIDAD, "antiguedad": 48},
            {"id": 8, "nombre": "Isabel Díaz", "rol": Rol.LIMPIEZA, "antiguedad": 6},
            {"id": 9, "nombre": "Roberto Vega", "rol": Rol.SEGURIDAD, "antiguedad": 15},
            {"id": 10, "nombre": "Carmen Silva", "rol": Rol.ADMINISTRATIVO, "antiguedad": 42}
        ]
        
        for emp_data in empleados_data:
            empleado = Empleado(
                id=emp_data["id"],
                nombre=emp_data["nombre"],
                rol=emp_data["rol"],
                antiguedad_meses=emp_data["antiguedad"]
            )
            self.empleados[empleado.id] = empleado
    
    def generar_planning(self, fecha_inicio: str, fecha_fin: str) -> Dict[str, List[Dict]]:
        """
        Genera el planning semanal completo
        
        Args:
            fecha_inicio: Fecha de inicio en formato YYYY-MM-DD
            fecha_fin: Fecha de fin en formato YYYY-MM-DD
            
        Returns:
            Dict con el planning generado
        """
        inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d").date()
        fin = datetime.strptime(fecha_fin, "%Y-%m-%d").date()
        
        # Limpiar planning existente para el período
        dias_planificar = []
        fecha_actual = inicio
        while fecha_actual <= fin:
            self.planning[fecha_actual] = []
            dias_planificar.append(fecha_actual)
            fecha_actual += timedelta(days=1)
        
        # Generar turnos necesarios por día
        for dia in dias_planificar:
            self._generar_turnos_dia(dia)
        
        # Asignar empleados a turnos
        self._asignar_empleados_a_turnos(inicio, fin)
        
        # Validar y ajustar planning
        self._validar_planning(inicio, fin)
        
        return self._planning_to_dict(inicio, fin)
    
    def _generar_turnos_dia(self, fecha: date):
        """Genera los turnos necesarios para un día específico"""
        dia_semana = fecha.weekday()
        
        # Determinar tipos de turno según el día
        if dia_semana < 5:  # Lunes a Viernes
            tipos_turno = [TipoTurno.MANANA, TipoTurno.TARDE, TipoTurno.NOCHE]
        else:  # Fin de semana
            tipos_turno = [TipoTurno.MANANA, TipoTurno.TARDE]
        
        # Crear turnos según requisitos mínimos
        for tipo_turno in tipos_turno:
            for rol, cantidad in self.config["turnos_min_por_dia"].items():
                # Ajustar cantidad para fines de semana
                if dia_semana >= 5 and rol == Rol.ADMINISTRATIVO:
                    continue
                if dia_semana >= 5:
                    cantidad = max(1, cantidad // 2)
                
                for _ in range(cantidad):
                    turno = Turno(
                        fecha=fecha,
                        tipo=tipo_turno,
                        rol_requerido=rol
                    )
                    self.planning[fecha].append(turno)
    
    def _asignar_empleados_a_turnos(self, fecha_inicio: date, fecha_fin: date):
        """Asigna empleados a los turnos generados"""
        # Contar horas asignadas por empleado
        horas_asignadas = defaultdict(int)
        turnos_asignados = defaultdict(list)
        
        # Ordenar empleados por antigüedad (mayor a menor)
        empleados_ordenados = sorted(
            self.empleados.values(),
            key=lambda e: e.antiguedad_meses,
            reverse=True
        )
        
        # Asignar turnos día por día
        fecha_actual = fecha_inicio
        while fecha_actual <= fecha_fin:
            turnos_dia = self.planning[fecha_actual]
            
            # Agrupar turnos por rol
            turnos_por_rol = defaultdict(list)
            for turno in turnos_dia:
                if turno.rol_requerido and not turno.empleado:
                    turnos_por_rol[turno.rol_requerido].append(turno)
            
            # Asignar por rol
            for rol, turnos_rol in turnos_por_rol.items():
                empleados_rol = [e for e in empleados_ordenados if e.rol == rol]
                
                for turno in turnos_rol:
                    mejor_empleado = self._encontrar_mejor_empleado(
                        turno, empleados_rol, horas_asignadas, 
                        turnos_asignados, fecha_inicio, fecha_fin
                    )
                    
                    if mejor_empleado:
                        turno.empleado = mejor_empleado
                        horas_asignadas[mejor_empleado.id] += turno.horas
                        turnos_asignados[mejor_empleado.id].append(turno)
            
            fecha_actual += timedelta(days=1)
    
    def _encontrar_mejor_empleado(self, turno: Turno, empleados_disponibles: List[Empleado],
                                  horas_asignadas: Dict, turnos_asignados: Dict,
                                  fecha_inicio: date, fecha_fin: date) -> Optional[Empleado]:
        """Encuentra el mejor empleado para un turno específico"""
        candidatos_validos = []
        
        for empleado in empleados_disponibles:
            # Verificar disponibilidad
            if not self._empleado_disponible(empleado, turno, horas_asignadas, turnos_asignados):
                continue
            
            # Calcular puntuación
            puntuacion = self._calcular_puntuacion_asignacion(
                empleado, turno, horas_asignadas, turnos_asignados
            )
            
            candidatos_validos.append((empleado, puntuacion))
        
        if candidatos_validos:
            # Ordenar por puntuación (mayor es mejor)
            candidatos_validos.sort(key=lambda x: x[1], reverse=True)
            return candidatos_validos[0][0]
        
        return None
    
    def _empleado_disponible(self, empleado: Empleado, turno: Turno,
                            horas_asignadas: Dict, turnos_asignados: Dict) -> bool:
        """Verifica si un empleado está disponible para un turno"""
        # Verificar ausencias
        for ausencia in self.ausencias:
            if (ausencia.empleado.id == empleado.id and 
                ausencia.fecha_inicio <= turno.fecha <= ausencia.fecha_fin and
                ausencia.aprobada):
                return False
        
        # Verificar día no disponible
        if turno.fecha.weekday() in empleado.dias_no_disponibles:
            return False
        
        # Verificar turno no disponible
        if turno.tipo in empleado.turnos_no_disponibles:
            return False
        
        # Verificar horas máximas semanales
        if horas_asignadas[empleado.id] + turno.horas > empleado.horas_semanales_max:
            return False
        
        # Verificar descanso entre turnos
        turnos_empleado = turnos_asignados[empleado.id]
        for turno_previo in turnos_empleado:
            if turno_previo.fecha == turno.fecha:
                return False  # Ya tiene turno ese día
            
            # Verificar horas de descanso
            if abs((turno.fecha - turno_previo.fecha).days) == 1:
                # Simplificación: asumimos que necesita 12h entre turnos
                if turno_previo.tipo == TipoTurno.NOCHE and turno.tipo == TipoTurno.MANANA:
                    return False
        
        return True
    
    def _calcular_puntuacion_asignacion(self, empleado: Empleado, turno: Turno,
                                       horas_asignadas: Dict, turnos_asignados: Dict) -> float:
        """Calcula puntuación para asignar un empleado a un turno"""
        puntuacion = 100.0
        
        # Bonus por antigüedad
        puntuacion += empleado.antiguedad_meses * 0.5
        
        # Bonus por turno preferido
        if turno.tipo in empleado.turnos_preferidos:
            puntuacion += 20
        
        # Penalización por exceso de horas
        horas_actuales = horas_asignadas[empleado.id]
        if horas_actuales > 30:
            puntuacion -= (horas_actuales - 30) * 2
        
        # Bonus por pocas horas (equidad)
        if horas_actuales < 20:
            puntuacion += (20 - horas_actuales) * 3
        
        # Penalización por muchos turnos del mismo tipo
        turnos_mismo_tipo = sum(1 for t in turnos_asignados[empleado.id] if t.tipo == turno.tipo)
        if turnos_mismo_tipo > 2:
            puntuacion -= turnos_mismo_tipo * 5
        
        return puntuacion
    
    def _validar_planning(self, fecha_inicio: date, fecha_fin: date) -> List[str]:
        """Valida el planning generado y retorna lista de problemas"""
        problemas = []
        
        # Validar cobertura mínima
        fecha_actual = fecha_inicio
        while fecha_actual <= fecha_fin:
            turnos_dia = self.planning[fecha_actual]
            
            # Contar turnos cubiertos por rol
            cobertura = defaultdict(int)
            for turno in turnos_dia:
                if turno.empleado and turno.rol_requerido:
                    cobertura[turno.rol_requerido] += 1
            
            # Verificar mínimos
            for rol, minimo in self.config["turnos_min_por_dia"].items():
                if fecha_actual.weekday() >= 5 and rol == Rol.ADMINISTRATIVO:
                    continue
                if fecha_actual.weekday() >= 5:
                    minimo = max(1, minimo // 2)
                
                if cobertura[rol] < minimo:
                    problemas.append(
                        f"Falta cobertura {rol.value} el {fecha_actual}: "
                        f"{cobertura[rol]}/{minimo}"
                    )
            
            fecha_actual += timedelta(days=1)
        
        # Validar horas por empleado
        horas_por_empleado = defaultdict(int)
        for turnos_dia in self.planning.values():
            for turno in turnos_dia:
                if turno.empleado:
                    horas_por_empleado[turno.empleado.id] += turno.horas
        
        for emp_id, horas in horas_por_empleado.items():
            empleado = self.empleados[emp_id]
            if horas > empleado.horas_semanales_max:
                problemas.append(
                    f"{empleado.nombre} excede horas máximas: {horas}/{empleado.horas_semanales_max}"
                )
            elif horas < empleado.horas_semanales_min:
                problemas.append(
                    f"{empleado.nombre} no alcanza horas mínimas: {horas}/{empleado.horas_semanales_min}"
                )
        
        return problemas
    
    def _planning_to_dict(self, fecha_inicio: date, fecha_fin: date) -> Dict:
        """Convierte el planning a diccionario para visualización"""
        resultado = {
            "periodo": {
                "inicio": fecha_inicio.isoformat(),
                "fin": fecha_fin.isoformat()
            },
            "planning": {},
            "resumen": {
                "total_turnos": 0,
                "turnos_cubiertos": 0,
                "horas_por_empleado": {}
            }
        }
        
        fecha_actual = fecha_inicio
        while fecha_actual <= fecha_fin:
            turnos_dia = []
            for turno in self.planning[fecha_actual]:
                turno_dict = {
                    "tipo": turno.tipo.value,
                    "rol": turno.rol_requerido.value if turno.rol_requerido else None,
                    "empleado": turno.empleado.nombre if turno.empleado else "Sin asignar",
                    "horas": turno.horas
                }
                turnos_dia.append(turno_dict)
                
                resultado["resumen"]["total_turnos"] += 1
                if turno.empleado:
                    resultado["resumen"]["turnos_cubiertos"] += 1
                    emp_nombre = turno.empleado.nombre
                    if emp_nombre not in resultado["resumen"]["horas_por_empleado"]:
                        resultado["resumen"]["horas_por_empleado"][emp_nombre] = 0
                    resultado["resumen"]["horas_por_empleado"][emp_nombre] += turno.horas
            
            resultado["planning"][fecha_actual.isoformat()] = turnos_dia
            fecha_actual += timedelta(days=1)
        
        # Calcular porcentaje de cobertura
        if resultado["resumen"]["total_turnos"] > 0:
            resultado["resumen"]["porcentaje_cobertura"] = round(
                (resultado["resumen"]["turnos_cubiertos"] / resultado["resumen"]["total_turnos"]) * 100, 2
            )
        else:
            resultado["resumen"]["porcentaje_cobertura"] = 0
        
        return resultado
    
    def mostrar_planning(self, nombre: Optional[str] = None) -> str:
        """
        Muestra el planning completo o de un empleado específico
        
        Args:
            nombre: Nombre del empleado (opcional)
            
        Returns:
            String con el planning formateado
        """
        if not self.planning:
            return "No hay planning generado actualmente."
        
        # Encontrar rango de fechas
        fechas = sorted(self.planning.keys())
        if not fechas:
            return "No hay turnos asignados."
        
        fecha_inicio = fechas[0]
        fecha_fin = fechas[-1]
        
        if nombre:
            # Buscar empleado
            empleado = None
            for emp in self.empleados.values():
                if emp.nombre.lower() == nombre.lower():
                    empleado = emp
                    break
            
            if not empleado:
                return f"Empleado '{nombre}' no encontrado."
            
            # Mostrar turnos del empleado
            resultado = f"\n📅 PLANNING DE {empleado.nombre.upper()}\n"
            resultado += f"Período: {fecha_inicio} al {fecha_fin}\n"
            resultado += "=" * 60 + "\n"
            
            total_horas = 0
            fecha_actual = fecha_inicio
            while fecha_actual <= fecha_fin:
                turnos_empleado = [t for t in self.planning[fecha_actual] 
                                 if t.empleado and t.empleado.id == empleado.id]
                
                if turnos_empleado:
                    dia_semana = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"][fecha_actual.weekday()]
                    resultado += f"\n{dia_semana} {fecha_actual}:\n"
                    for turno in turnos_empleado:
                        resultado += f"  - {turno.tipo.value} ({turno.horas}h)\n"
                        total_horas += turno.horas
                
                fecha_actual += timedelta(days=1)
            
            resultado += f"\n{'=' * 60}\n"
            resultado += f"TOTAL HORAS SEMANA: {total_horas}h\n"
            
        else:
            # Mostrar planning completo
            resultado = f"\n📊 PLANNING COMPLETO\n"
            resultado += f"Período: {fecha_inicio} al {fecha_fin}\n"
            resultado += "=" * 80 + "\n"
            
            fecha_actual = fecha_inicio
            while fecha_actual <= fecha_fin:
                dia_semana = ["Lunes", "Martes", "Miércoles", "Jueves", 
                             "Viernes", "Sábado", "Domingo"][fecha_actual.weekday()]
                resultado += f"\n{dia_semana} {fecha_actual}:\n"
                resultado += "-" * 80 + "\n"
                
                # Agrupar por turno
                for tipo_turno in TipoTurno:
                    turnos_tipo = [t for t in self.planning[fecha_actual] if t.tipo == tipo_turno]
                    if turnos_tipo:
                        resultado += f"\n  {tipo_turno.value}:\n"
                        for turno in turnos_tipo:
                            empleado_nombre = turno.empleado.nombre if turno.empleado else "⚠️ SIN ASIGNAR"
                            rol = turno.rol_requerido.value if turno.rol_requerido else ""
                            resultado += f"    - {empleado_nombre} ({rol})\n"
                
                fecha_actual += timedelta(days=1)
        
        return resultado
    
    def registrar_ausencia(self, nombre: str, fecha: str, motivo: str) -> Dict[str, any]:
        """
        Registra una ausencia y busca sustituto
        
        Args:
            nombre: Nombre del empleado
            fecha: Fecha de ausencia (YYYY-MM-DD)
            motivo: Motivo de la ausencia
            
        Returns:
            Dict con resultado de la operación
        """
        # Buscar empleado
        empleado = None
        for emp in self.empleados.values():
            if emp.nombre.lower() == nombre.lower():
                empleado = emp
                break
        
        if not empleado:
            return {
                "exito": False,
                "mensaje": f"Empleado '{nombre}' no encontrado."
            }
        
        # Parsear fecha
        fecha_ausencia = datetime.strptime(fecha, "%Y-%m-%d").date()
        
        # Buscar motivo
        motivo_enum = None
        for m in MotivoAusencia:
            if m.value.lower() == motivo.lower():
                motivo_enum = m
                break
        
        if not motivo_enum:
            motivo_enum = MotivoAusencia.ASUNTOS_PROPIOS
        
        # Crear ausencia
        ausencia = Ausencia(
            empleado=empleado,
            fecha_inicio=fecha_ausencia,
            fecha_fin=fecha_ausencia,
            motivo=motivo_enum,
            aprobada=True
        )
        self.ausencias.append(ausencia)
        
        # Buscar turnos afectados
        turnos_afectados = []
        if fecha_ausencia in self.planning:
            for turno in self.planning[fecha_ausencia]:
                if turno.empleado and turno.empleado.id == empleado.id:
                    turnos_afectados.append(turno)
                    turno.empleado = None  # Liberar turno
        
        # Buscar sustitutos
        sustitutos_sugeridos = []
        for turno in turnos_afectados:
            sugerencias = self.sugerir_reemplazo(
                fecha_ausencia.isoformat(),
                turno.tipo.value,
                turno.rol_requerido.value if turno.rol_requerido else None
            )
            if sugerencias["candidatos"]:
                sustitutos_sugeridos.append({
                    "turno": turno.tipo.value,
                    "candidatos": sugerencias["candidatos"][:3]
                })
        
        return {
            "exito": True,
            "mensaje": f"Ausencia registrada para {empleado.nombre} el {fecha}",
            "turnos_afectados": len(turnos_afectados),
            "sustitutos_sugeridos": sustitutos_sugeridos
        }
    
    def solicitar_intercambio(self, origen: str, destino: str, fecha: str) -> Dict[str, any]:
        """
        Procesa solicitud de intercambio de turnos
        
        Args:
            origen: Nombre del empleado que solicita
            destino: Nombre del empleado con quien intercambiar
            fecha: Fecha del turno a intercambiar
            
        Returns:
            Dict con resultado de la operación
        """
        # Buscar empleados
        emp_origen = None
        emp_destino = None
        
        for emp in self.empleados.values():
            if emp.nombre.lower() == origen.lower():
                emp_origen = emp
            elif emp.nombre.lower() == destino.lower():
                emp_destino = emp
        
        if not emp_origen:
            return {"exito": False, "mensaje": f"Empleado '{origen}' no encontrado."}
        if not emp_destino:
            return {"exito": False, "mensaje": f"Empleado '{destino}' no encontrado."}
        
        # Verificar que son del mismo rol
        if emp_origen.rol != emp_destino.rol:
            return {
                "exito": False,
                "mensaje": f"No se puede intercambiar entre roles diferentes: "
                          f"{emp_origen.rol.value} y {emp_destino.rol.value}"
            }
        
        # Parsear fecha
        fecha_intercambio = datetime.strptime(fecha, "%Y-%m-%d").date()
        
        # Buscar turnos
        turno_origen = None
        turno_destino = None
        
        if fecha_intercambio in self.planning:
            for turno in self.planning[fecha_intercambio]:
                if turno.empleado:
                    if turno.empleado.id == emp_origen.id:
                        turno_origen = turno
                    elif turno.empleado.id == emp_destino.id:
                        turno_destino = turno
        
        if not turno_origen:
            return {
                "exito": False,
                "mensaje": f"{emp_origen.nombre} no tiene turno asignado el {fecha}"
            }
        
        # Si destino no tiene turno ese día, es intercambio simple
        if not turno_destino:
            # Verificar disponibilidad del destino
            if self._empleado_disponible(emp_destino, turno_origen, {}, {}):
                turno_origen.empleado = emp_destino
                return {
                    "exito": True,
                    "mensaje": f"Turno del {fecha} transferido de {emp_origen.nombre} a {emp_destino.nombre}",
                    "detalles": {
                        "turno": turno_origen.tipo.value,
                        "nuevo_asignado": emp_destino.nombre
                    }
                }
            else:
                return {
                    "exito": False,
                    "mensaje": f"{emp_destino.nombre} no está disponible para ese turno"
                }
        
        # Intercambio real de turnos
        turno_origen.empleado = emp_destino
        turno_destino.empleado = emp_origen
        
        # Registrar intercambio
        intercambio = IntercambioTurno(
            solicitante=emp_origen,
            receptor=emp_destino,
            fecha_turno_solicitante=fecha_intercambio,
            fecha_turno_receptor=fecha_intercambio,
            estado="aprobado"
        )
        self.intercambios.append(intercambio)
        
        return {
            "exito": True,
            "mensaje": f"Intercambio realizado entre {emp_origen.nombre} y {emp_destino.nombre}",
            "detalles": {
                f"{emp_origen.nombre}": f"ahora trabaja en {turno_destino.tipo.value}",
                f"{emp_destino.nombre}": f"ahora trabaja en {turno_origen.tipo.value}"
            }
        }
    
    def sugerir_reemplazo(self, fecha: str, turno: str, rol: Optional[str] = None) -> Dict[str, List]:
        """
        Sugiere empleados disponibles para cubrir un turno
        
        Args:
            fecha: Fecha del turno
            turno: Tipo de turno
            rol: Rol requerido (opcional)
            
        Returns:
            Dict con lista de candidatos
        """
        fecha_turno = datetime.strptime(fecha, "%Y-%m-%d").date()
        
        # Buscar tipo de turno
        tipo_turno = None
        for t in TipoTurno:
            if t.value.lower() == turno.lower():
                tipo_turno = t
                break
        
        if not tipo_turno:
            return {"candidatos": [], "mensaje": f"Tipo de turno '{turno}' no válido"}
        
        # Buscar rol si se especifica
        rol_requerido = None
        if rol:
            for r in Rol:
                if r.value.lower() == rol.lower():
                    rol_requerido = r
                    break
        
        # Crear turno temporal para evaluar
        turno_temp = Turno(
            fecha=fecha_turno,
            tipo=tipo_turno,
            rol_requerido=rol_requerido
        )
        
        # Buscar candidatos
        candidatos = []
        horas_actuales = self._calcular_horas_semana_actual(fecha_turno)
        
        for empleado in self.empleados.values():
            # Filtrar por rol si se especifica
            if rol_requerido and empleado.rol != rol_requerido:
                continue
            
            # Verificar disponibilidad
            if self._empleado_disponible(empleado, turno_temp, horas_actuales, {}):
                # Calcular puntuación
                puntuacion = self._calcular_puntuacion_asignacion(
                    empleado, turno_temp, horas_actuales, {}
                )
                
                candidatos.append({
                    "nombre": empleado.nombre,
                    "rol": empleado.rol.value,
                    "antiguedad_meses": empleado.antiguedad_meses,
                    "horas_semana_actual": horas_actuales.get(empleado.id, 0),
                    "puntuacion": round(puntuacion, 2),
                    "preferencia_turno": turno in [t.value for t in empleado.turnos_preferidos]
                })
        
        # Ordenar por puntuación
        candidatos.sort(key=lambda x: x["puntuacion"], reverse=True)
        
        return {
            "candidatos": candidatos,
            "total_disponibles": len(candidatos)
        }
    
    def _calcular_horas_semana_actual(self, fecha: date) -> Dict[int, int]:
        """Calcula las horas asignadas en la semana de la fecha dada"""
        # Encontrar inicio de semana (lunes)
        inicio_semana = fecha - timedelta(days=fecha.weekday())
        fin_semana = inicio_semana + timedelta(days=6)
        
        horas_por_empleado = defaultdict(int)
        
        fecha_actual = inicio_semana
        while fecha_actual <= fin_semana:
            if fecha_actual in self.planning:
                for turno in self.planning[fecha_actual]:
                    if turno.empleado:
                        horas_por_empleado[turno.empleado.id] += turno.horas
            fecha_actual += timedelta(days=1)
        
        return dict(horas_por_empleado)
    
    def ver_estadisticas(self) -> Dict[str, any]:
        """
        Muestra estadísticas del planning actual
        
        Returns:
            Dict con métricas de carga, cobertura y equidad
        """
        if not self.planning:
            return {"mensaje": "No hay planning generado para mostrar estadísticas"}
        
        # Calcular métricas
        total_turnos = 0
        turnos_cubiertos = 0
        horas_por_empleado = defaultdict(int)
        turnos_por_empleado = defaultdict(int)
        turnos_por_tipo = defaultdict(int)
        cobertura_por_rol = defaultdict(lambda: {"requeridos": 0, "cubiertos": 0})
        
        for fecha, turnos in self.planning.items():
            for turno in turnos:
                total_turnos += 1
                turnos_por_tipo[turno.tipo.value] += 1
                
                if turno.rol_requerido:
                    cobertura_por_rol[turno.rol_requerido.value]["requeridos"] += 1
                
                if turno.empleado:
                    turnos_cubiertos += 1
                    horas_por_empleado[turno.empleado.nombre] += turno.horas
                    turnos_por_empleado[turno.empleado.nombre] += 1
                    
                    if turno.rol_requerido:
                        cobertura_por_rol[turno.rol_requerido.value]["cubiertos"] += 1
        
        # Calcular estadísticas
        estadisticas = {
            "resumen_general": {
                "total_turnos": total_turnos,
                "turnos_cubiertos": turnos_cubiertos,
                "turnos_sin_cubrir": total_turnos - turnos_cubiertos,
                "porcentaje_cobertura": round((turnos_cubiertos / total_turnos * 100) if total_turnos > 0 else 0, 2)
            },
            "distribucion_turnos": dict(turnos_por_tipo),
            "carga_por_empleado": {},
            "cobertura_por_rol": {},
            "equidad": {}
        }
        
        # Detalle por empleado
        for nombre, horas in horas_por_empleado.items():
            estadisticas["carga_por_empleado"][nombre] = {
                "horas_totales": horas,
                "turnos_totales": turnos_por_empleado[nombre],
                "promedio_horas_turno": round(horas / turnos_por_empleado[nombre], 1)
            }
        
        # Cobertura por rol
        for rol, datos in cobertura_por_rol.items():
            porcentaje = round((datos["cubiertos"] / datos["requeridos"] * 100) 
                             if datos["requeridos"] > 0 else 0, 2)
            estadisticas["cobertura_por_rol"][rol] = {
                "requeridos": datos["requeridos"],
                "cubiertos": datos["cubiertos"],
                "sin_cubrir": datos["requeridos"] - datos["cubiertos"],
                "porcentaje_cobertura": porcentaje
            }
        
        # Métricas de equidad
        if horas_por_empleado:
            horas_lista = list(horas_por_empleado.values())
            estadisticas["equidad"] = {
                "horas_maximas": max(horas_lista),
                "horas_minimas": min(horas_lista),
                "horas_promedio": round(sum(horas_lista) / len(horas_lista), 1),
                "desviacion": round(max(horas_lista) - min(horas_lista), 1),
                "coeficiente_variacion": round(
                    (max(horas_lista) - min(horas_lista)) / (sum(horas_lista) / len(horas_lista)) * 100
                    if sum(horas_lista) > 0 else 0, 2
                )
            }
        
        # Identificar problemas
        problemas = []
        if estadisticas["resumen_general"]["porcentaje_cobertura"] < 90:
            problemas.append("⚠️ Cobertura por debajo del 90%")
        
        if estadisticas["equidad"]["coeficiente_variacion"] > 30:
            problemas.append("⚠️ Alta desigualdad en distribución de horas")
        
        for rol, datos in estadisticas["cobertura_por_rol"].items():
            if datos["porcentaje_cobertura"] < 80:
                problemas.append(f"⚠️ Baja cobertura en {rol}: {datos['porcentaje_cobertura']}%")
        
        estadisticas["alertas"] = problemas
        
        return estadisticas
    
    def registrar_preferencia(self, nombre: str, datos: Dict[str, any]) -> Dict[str, any]:
        """
        Registra o actualiza preferencias de un empleado
        
        Args:
            nombre: Nombre del empleado
            datos: Dict con las preferencias (turnos_preferidos, dias_no_disponibles, etc.)
            
        Returns:
            Dict con resultado de la operación
        """
        # Buscar empleado
        empleado = None
        for emp in self.empleados.values():
            if emp.nombre.lower() == nombre.lower():
                empleado = emp
                break
        
        if not empleado:
            return {"exito": False, "mensaje": f"Empleado '{nombre}' no encontrado"}
        
        cambios_realizados = []
        
        # Actualizar turnos preferidos
        if "turnos_preferidos" in datos:
            nuevos_turnos = []
            for turno_str in datos["turnos_preferidos"]:
                for t in TipoTurno:
                    if t.value.lower() == turno_str.lower():
                        nuevos_turnos.append(t)
                        break
            empleado.turnos_preferidos = nuevos_turnos
            cambios_realizados.append(f"Turnos preferidos: {[t.value for t in nuevos_turnos]}")
        
        # Actualizar turnos no disponibles
        if "turnos_no_disponibles" in datos:
            nuevos_turnos = []
            for turno_str in datos["turnos_no_disponibles"]:
                for t in TipoTurno:
                    if t.value.lower() == turno_str.lower():
                        nuevos_turnos.append(t)
                        break
            empleado.turnos_no_disponibles = nuevos_turnos
            cambios_realizados.append(f"Turnos no disponibles: {[t.value for t in nuevos_turnos]}")
        
        # Actualizar días no disponibles
        if "dias_no_disponibles" in datos:
            dias_map = {
                "lunes": 0, "martes": 1, "miercoles": 2, "miércoles": 2,
                "jueves": 3, "viernes": 4, "sabado": 5, "sábado": 5, "domingo": 6
            }
            nuevos_dias = []
            for dia_str in datos["dias_no_disponibles"]:
                dia_num = dias_map.get(dia_str.lower())
                if dia_num is not None:
                    nuevos_dias.append(dia_num)
            empleado.dias_no_disponibles = nuevos_dias
            cambios_realizados.append(f"Días no disponibles: {datos['dias_no_disponibles']}")
        
        # Actualizar horas semanales
        if "horas_semanales_max" in datos:
            empleado.horas_semanales_max = datos["horas_semanales_max"]
            cambios_realizados.append(f"Horas máximas semanales: {datos['horas_semanales_max']}")
        
        if "horas_semanales_min" in datos:
            empleado.horas_semanales_min = datos["horas_semanales_min"]
            cambios_realizados.append(f"Horas mínimas semanales: {datos['horas_semanales_min']}")
        
        return {
            "exito": True,
            "mensaje": f"Preferencias actualizadas para {empleado.nombre}",
            "cambios": cambios_realizados
        }
    
    def modificar_turno(self, nombre: str, fecha: str, nuevo_turno: str) -> Dict[str, any]:
        """
        Modifica el turno asignado a un empleado
        
        Args:
            nombre: Nombre del empleado
            fecha: Fecha del turno a modificar
            nuevo_turno: Nuevo tipo de turno
            
        Returns:
            Dict con resultado de la operación
        """
        # Buscar empleado
        empleado = None
        for emp in self.empleados.values():
            if emp.nombre.lower() == nombre.lower():
                empleado = emp
                break
        
        if not empleado:
            return {"exito": False, "mensaje": f"Empleado '{nombre}' no encontrado"}
        
        # Parsear fecha
        fecha_turno = datetime.strptime(fecha, "%Y-%m-%d").date()
        
        # Buscar nuevo tipo de turno
        tipo_nuevo = None
        for t in TipoTurno:
            if t.value.lower() == nuevo_turno.lower():
                tipo_nuevo = t
                break
        
        if not tipo_nuevo:
            return {"exito": False, "mensaje": f"Tipo de turno '{nuevo_turno}' no válido"}
        
        # Buscar turno actual del empleado
        turno_actual = None
        if fecha_turno in self.planning:
            for turno in self.planning[fecha_turno]:
                if turno.empleado and turno.empleado.id == empleado.id:
                    turno_actual = turno
                    break
        
        if not turno_actual:
            return {
                "exito": False,
                "mensaje": f"{empleado.nombre} no tiene turno asignado el {fecha}"
            }
        
        # Verificar si hay un turno del nuevo tipo sin asignar
        turno_destino = None
        for turno in self.planning[fecha_turno]:
            if turno.tipo == tipo_nuevo and not turno.empleado and turno.rol_requerido == empleado.rol:
                turno_destino = turno
                break
        
        if turno_destino:
            # Intercambiar
            turno_actual.empleado = None
            turno_destino.empleado = empleado
            return {
                "exito": True,
                "mensaje": f"Turno de {empleado.nombre} cambiado de {turno_actual.tipo.value} a {tipo_nuevo.value}",
                "detalles": {
                    "turno_anterior": turno_actual.tipo.value,
                    "turno_nuevo": tipo_nuevo.value,
                    "fecha": fecha
                }
            }
        else:
            # Cambiar tipo de turno directamente
            tipo_anterior = turno_actual.tipo
            turno_actual.tipo = tipo_nuevo
            return {
                "exito": True,
                "mensaje": f"Turno de {empleado.nombre} modificado",
                "detalles": {
                    "turno_anterior": tipo_anterior.value,
                    "turno_nuevo": tipo_nuevo.value,
                    "fecha": fecha
                },
                "advertencia": "No había turno vacío del nuevo tipo, se modificó el existente"
            }
    
    def exportar_planning_csv(self, fecha_inicio: str, fecha_fin: str, archivo: str = "planning.csv"):
        """Exporta el planning a formato CSV"""
        inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d").date()
        fin = datetime.strptime(fecha_fin, "%Y-%m-%d").date()
        
        with open(archivo, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Encabezados
            writer.writerow(['Fecha', 'Día', 'Turno', 'Empleado', 'Rol', 'Horas'])
            
            # Datos
            fecha_actual = inicio
            while fecha_actual <= fin:
                dia_semana = ["Lunes", "Martes", "Miércoles", "Jueves", 
                             "Viernes", "Sábado", "Domingo"][fecha_actual.weekday()]
                
                if fecha_actual in self.planning:
                    for turno in self.planning[fecha_actual]:
                        writer.writerow([
                            fecha_actual.isoformat(),
                            dia_semana,
                            turno.tipo.value,
                            turno.empleado.nombre if turno.empleado else "Sin asignar",
                            turno.rol_requerido.value if turno.rol_requerido else "",
                            turno.horas
                        ])
                
                fecha_actual += timedelta(days=1)
        
        return f"Planning exportado a {archivo}"
    
    def guardar_estado(self, archivo: str = "planning_estado.json"):
        """Guarda el estado completo del planning"""
        estado = {
            "fecha_guardado": datetime.now().isoformat(),
            "empleados": {},
            "planning": {},
            "ausencias": [],
            "intercambios": []
        }
        
        # Serializar empleados
        for emp_id, emp in self.empleados.items():
            estado["empleados"][str(emp_id)] = {
                "id": emp.id,
                "nombre": emp.nombre,
                "rol": emp.rol.value,
                "antiguedad_meses": emp.antiguedad_meses,
                "horas_semanales_max": emp.horas_semanales_max,
                "horas_semanales_min": emp.horas_semanales_min,
                "turnos_preferidos": [t.value for t in emp.turnos_preferidos],
                "turnos_no_disponibles": [t.value for t in emp.turnos_no_disponibles],
                "dias_no_disponibles": emp.dias_no_disponibles
            }
        
        # Serializar planning
        for fecha, turnos in self.planning.items():
            estado["planning"][fecha.isoformat()] = []
            for turno in turnos:
                estado["planning"][fecha.isoformat()].append({
                    "tipo": turno.tipo.value,
                    "empleado_id": turno.empleado.id if turno.empleado else None,
                    "rol_requerido": turno.rol_requerido.value if turno.rol_requerido else None,
                    "horas": turno.horas
                })
        
        # Serializar ausencias
        for ausencia in self.ausencias:
            estado["ausencias"].append({
                "empleado_id": ausencia.empleado.id,
                "fecha_inicio": ausencia.fecha_inicio.isoformat(),
                "fecha_fin": ausencia.fecha_fin.isoformat(),
                "motivo": ausencia.motivo.value,
                "aprobada": ausencia.aprobada
            })
        
        with open(archivo, 'w', encoding='utf-8') as f:
            json.dump(estado, f, indent=2, ensure_ascii=False)
        
        return f"Estado guardado en {archivo}"


# Funciones de interfaz para el agente
def main():
    """Función principal para demostración"""
    agent = PlanningAgent()
    
    print("🤖 AGENTE DE PLANIFICACIÓN DE TURNOS INICIADO")
    print("=" * 60)
    
    # Ejemplo de uso
    print("\n📅 Generando planning para la semana del 12 al 18 de agosto de 2024...")
    planning = agent.generar_planning("2024-08-12", "2024-08-18")
    
    print(f"\n✅ Planning generado:")
    print(f"- Total turnos: {planning['resumen']['total_turnos']}")
    print(f"- Turnos cubiertos: {planning['resumen']['turnos_cubiertos']}")
    print(f"- Cobertura: {planning['resumen']['porcentaje_cobertura']}%")
    
    print("\n📊 Horas por empleado:")
    for empleado, horas in planning['resumen']['horas_por_empleado'].items():
        print(f"  - {empleado}: {horas}h")
    
    # Mostrar planning completo
    print(agent.mostrar_planning())
    
    # Ejemplo de ausencia
    print("\n🏥 Registrando ausencia...")
    resultado = agent.registrar_ausencia("Juan García", "2024-08-14", "Enfermedad")
    print(f"Resultado: {resultado['mensaje']}")
    if resultado['sustitutos_sugeridos']:
        print("Sustitutos sugeridos:")
        for sug in resultado['sustitutos_sugeridos']:
            print(f"  Turno {sug['turno']}:")
            for cand in sug['candidatos']:
                print(f"    - {cand['nombre']} (puntuación: {cand['puntuacion']})")
    
    # Ver estadísticas
    print("\n📈 Estadísticas del planning:")
    stats = agent.ver_estadisticas()
    print(f"Cobertura general: {stats['resumen_general']['porcentaje_cobertura']}%")
    print(f"Equidad (coef. variación): {stats['equidad']['coeficiente_variacion']}%")
    
    if stats['alertas']:
        print("\nAlertas detectadas:")
        for alerta in stats['alertas']:
            print(f"  {alerta}")
    
    # Guardar estado
    print(f"\n💾 {agent.guardar_estado()}")
    print(f"📄 {agent.exportar_planning_csv('2024-08-12', '2024-08-18')}")


if __name__ == "__main__":
    main()