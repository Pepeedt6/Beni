#!/usr/bin/env python3
"""
Ejemplo de uso del Agente de Planificación de Turnos
Demuestra las principales funcionalidades del sistema
"""

from planning_agent import PlanningAgent
from datetime import datetime, timedelta


def ejemplo_completo():
    """Ejemplo completo de uso del agente"""
    print("🤖 DEMOSTRACIÓN DEL AGENTE DE PLANIFICACIÓN DE TURNOS")
    print("=" * 70)
    
    # Crear instancia del agente
    agent = PlanningAgent()
    
    # 1. GENERAR PLANNING SEMANAL
    print("\n1️⃣ GENERANDO PLANNING SEMANAL")
    print("-" * 40)
    
    # Obtener fechas de la próxima semana
    hoy = datetime.now().date()
    lunes = hoy - timedelta(days=hoy.weekday())  # Lunes de esta semana
    domingo = lunes + timedelta(days=6)
    
    fecha_inicio = lunes.strftime("%Y-%m-%d")
    fecha_fin = domingo.strftime("%Y-%m-%d")
    
    print(f"📅 Período: {fecha_inicio} al {fecha_fin}")
    
    # Generar planning
    planning = agent.generar_planning(fecha_inicio, fecha_fin)
    
    print(f"\n✅ Planning generado exitosamente:")
    print(f"   - Total turnos: {planning['resumen']['total_turnos']}")
    print(f"   - Turnos cubiertos: {planning['resumen']['turnos_cubiertos']}")
    print(f"   - Cobertura: {planning['resumen']['porcentaje_cobertura']}%")
    
    # 2. MOSTRAR PLANNING DE UN EMPLEADO
    print("\n\n2️⃣ PLANNING INDIVIDUAL")
    print("-" * 40)
    print(agent.mostrar_planning("Juan García"))
    
    # 3. REGISTRAR AUSENCIA
    print("\n\n3️⃣ REGISTRO DE AUSENCIA")
    print("-" * 40)
    
    fecha_ausencia = (lunes + timedelta(days=2)).strftime("%Y-%m-%d")  # Miércoles
    print(f"📋 Registrando ausencia de María López el {fecha_ausencia}")
    
    resultado_ausencia = agent.registrar_ausencia("María López", fecha_ausencia, "Enfermedad")
    print(f"✅ {resultado_ausencia['mensaje']}")
    
    if resultado_ausencia['sustitutos_sugeridos']:
        print("\n👥 Sustitutos sugeridos:")
        for sug in resultado_ausencia['sustitutos_sugeridos']:
            print(f"\n   Turno {sug['turno']}:")
            for i, cand in enumerate(sug['candidatos'][:3], 1):
                print(f"   {i}. {cand['nombre']} - Puntuación: {cand['puntuacion']}")
    
    # 4. SOLICITAR INTERCAMBIO
    print("\n\n4️⃣ INTERCAMBIO DE TURNOS")
    print("-" * 40)
    
    fecha_intercambio = (lunes + timedelta(days=4)).strftime("%Y-%m-%d")  # Viernes
    print(f"🔄 Solicitando intercambio entre Carlos Ruiz y Pedro Sánchez para el {fecha_intercambio}")
    
    resultado_intercambio = agent.solicitar_intercambio("Carlos Ruiz", "Pedro Sánchez", fecha_intercambio)
    print(f"✅ {resultado_intercambio['mensaje']}")
    
    # 5. VER ESTADÍSTICAS
    print("\n\n5️⃣ ESTADÍSTICAS DEL PLANNING")
    print("-" * 40)
    
    stats = agent.ver_estadisticas()
    
    print(f"📊 Resumen General:")
    print(f"   - Cobertura total: {stats['resumen_general']['porcentaje_cobertura']}%")
    print(f"   - Turnos sin cubrir: {stats['resumen_general']['turnos_sin_cubrir']}")
    
    print(f"\n📈 Distribución de Turnos:")
    for tipo, cantidad in stats['distribucion_turnos'].items():
        print(f"   - {tipo}: {cantidad} turnos")
    
    print(f"\n⚖️ Equidad:")
    if stats['equidad']:
        print(f"   - Horas promedio: {stats['equidad']['horas_promedio']}h")
        print(f"   - Rango: {stats['equidad']['horas_minimas']}h - {stats['equidad']['horas_maximas']}h")
        print(f"   - Coeficiente de variación: {stats['equidad']['coeficiente_variacion']}%")
    
    if stats['alertas']:
        print(f"\n⚠️ Alertas detectadas:")
        for alerta in stats['alertas']:
            print(f"   - {alerta}")
    
    # 6. REGISTRAR PREFERENCIAS
    print("\n\n6️⃣ ACTUALIZACIÓN DE PREFERENCIAS")
    print("-" * 40)
    
    print("⚙️ Actualizando preferencias de Ana Martín")
    preferencias = {
        "turnos_preferidos": ["Mañana"],
        "dias_no_disponibles": ["domingo"],
        "horas_semanales_max": 35
    }
    
    resultado_pref = agent.registrar_preferencia("Ana Martín", preferencias)
    print(f"✅ {resultado_pref['mensaje']}")
    for cambio in resultado_pref['cambios']:
        print(f"   - {cambio}")
    
    # 7. BUSCAR REEMPLAZOS
    print("\n\n7️⃣ BÚSQUEDA DE REEMPLAZOS")
    print("-" * 40)
    
    fecha_reemplazo = (lunes + timedelta(days=1)).strftime("%Y-%m-%d")  # Martes
    print(f"🔍 Buscando reemplazos para turno de Tarde de Operario el {fecha_reemplazo}")
    
    reemplazos = agent.sugerir_reemplazo(fecha_reemplazo, "Tarde", "Operario")
    print(f"✅ Encontrados {reemplazos['total_disponibles']} candidatos disponibles:")
    
    for i, cand in enumerate(reemplazos['candidatos'][:5], 1):
        print(f"\n   {i}. {cand['nombre']}")
        print(f"      - Puntuación: {cand['puntuacion']}")
        print(f"      - Horas actuales: {cand['horas_semana_actual']}h")
        print(f"      - Antigüedad: {cand['antiguedad_meses']} meses")
    
    # 8. EXPORTAR Y GUARDAR
    print("\n\n8️⃣ EXPORTACIÓN Y GUARDADO")
    print("-" * 40)
    
    # Exportar a CSV
    archivo_csv = agent.exportar_planning_csv(fecha_inicio, fecha_fin, "planning_ejemplo.csv")
    print(f"📄 {archivo_csv}")
    
    # Guardar estado
    archivo_json = agent.guardar_estado("estado_ejemplo.json")
    print(f"💾 {archivo_json}")
    
    print("\n" + "=" * 70)
    print("✅ DEMOSTRACIÓN COMPLETADA")
    print("\nEl sistema está listo para gestionar los turnos de forma autónoma.")
    print("Puede acceder a la interfaz web ejecutando: python app.py")


def ejemplo_casos_especiales():
    """Ejemplos de casos especiales y manejo de errores"""
    print("\n\n🔧 CASOS ESPECIALES Y VALIDACIONES")
    print("=" * 70)
    
    agent = PlanningAgent()
    
    # Generar un planning base
    hoy = datetime.now().date()
    lunes = hoy - timedelta(days=hoy.weekday())
    domingo = lunes + timedelta(days=6)
    
    agent.generar_planning(lunes.strftime("%Y-%m-%d"), domingo.strftime("%Y-%m-%d"))
    
    # Caso 1: Intentar intercambio entre roles diferentes
    print("\n❌ Caso 1: Intercambio entre roles diferentes")
    resultado = agent.solicitar_intercambio("Juan García", "María López", lunes.strftime("%Y-%m-%d"))
    print(f"   Resultado: {resultado['mensaje']}")
    
    # Caso 2: Empleado no encontrado
    print("\n❌ Caso 2: Empleado inexistente")
    resultado = agent.registrar_ausencia("Empleado Fantasma", lunes.strftime("%Y-%m-%d"), "Vacaciones")
    print(f"   Resultado: {resultado['mensaje']}")
    
    # Caso 3: Modificar turno
    print("\n✅ Caso 3: Modificar turno asignado")
    fecha_modificar = (lunes + timedelta(days=3)).strftime("%Y-%m-%d")
    resultado = agent.modificar_turno("Carlos Ruiz", fecha_modificar, "Tarde")
    print(f"   Resultado: {resultado['mensaje']}")
    
    # Caso 4: Múltiples ausencias
    print("\n✅ Caso 4: Gestión de múltiples ausencias")
    for i in range(3):
        fecha = (lunes + timedelta(days=i)).strftime("%Y-%m-%d")
        empleado = list(agent.empleados.values())[i].nombre
        resultado = agent.registrar_ausencia(empleado, fecha, "Vacaciones")
        print(f"   - {empleado} ausente el {fecha}")
    
    # Ver estadísticas después de los cambios
    stats = agent.ver_estadisticas()
    print(f"\n📊 Impacto en cobertura: {stats['resumen_general']['porcentaje_cobertura']}%")
    print(f"   Turnos sin cubrir: {stats['resumen_general']['turnos_sin_cubrir']}")


if __name__ == "__main__":
    # Ejecutar ejemplo completo
    ejemplo_completo()
    
    # Ejecutar casos especiales
    ejemplo_casos_especiales()
    
    print("\n\n💡 Para usar la interfaz web, ejecute:")
    print("   python app.py")
    print("\n   Luego abra http://localhost:5000 en su navegador")