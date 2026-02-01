# backend/routers/monitoreo.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from datetime import datetime, timedelta, timezone
from collections import defaultdict

from ..database import get_db
from ..models_db import SectorDB, LecturaDB, UserDB
from ..logic import evaluar_sensor, generar_resumen_estado
from ..dependencies import get_current_user

router = APIRouter(
    prefix="/monitoreo",
    tags=["Monitoreo"]
)

@router.get("/alertas")
def obtener_alertas_riego(
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(get_current_user)
):
    # 1. Traemos Sectores y precargamos sus Sensores en una sola query (Eager Loading)
    # Esto evita queries extra cuando hacemos 'for sensor in sector.sensores'
    sectores = db.query(SectorDB).options(joinedload(SectorDB.sensores)).all()
    
    # 2. Recolectamos IDs solo de los sensores de Humedad
    ids_sensores_humedad = []
    for sector in sectores:
        for sensor in sector.sensores:
            if sensor.tipo.lower() == "humedad":
                ids_sensores_humedad.append(sensor.id)
    
    if not ids_sensores_humedad:
        return {"total_alertas": 0, "detalles": []}

    # 3. Traer lecturas "recientes" de golpe (Bulk Fetching)
    # Definimos un límite razonable (ej. últimas 24hs) para no traer toda la historia
    limite_tiempo = datetime.now(timezone.utc) - timedelta(hours=24)
    
    lecturas_bulk = db.query(LecturaDB).filter(
        LecturaDB.sensor_id.in_(ids_sensores_humedad),
        LecturaDB.fecha >= limite_tiempo
    ).all()
    
    # 4. Encontrar la ÚLTIMA lectura de cada sensor en memoria
    # Creamos un diccionario: { sensor_id: ObjetoLecturaMasReciente }
    ultima_lectura_por_sensor = {}
    
    for lectura in lecturas_bulk:
        sensor_id = lectura.sensor_id
        
        # Si es la primera vez que vemos este sensor, lo guardamos
        if sensor_id not in ultima_lectura_por_sensor:
            ultima_lectura_por_sensor[sensor_id] = lectura
        else:
            # Si ya tenemos una, comparamos fechas y nos quedamos con la más nueva
            if lectura.fecha > ultima_lectura_por_sensor[sensor_id].fecha:
                ultima_lectura_por_sensor[sensor_id] = lectura

    # 5. Construimos las alertas cruzando los datos que ya tenemos en RAM
    alertas = []

    for sector in sectores:
        for sensor in sector.sensores:
            # Solo procesamos humedad
            if sensor.tipo.lower() == "humedad":
                # Buscamos su última lectura en nuestro diccionario (O(1) lookup)
                lectura = ultima_lectura_por_sensor.get(sensor.id)
                
                # Si hay lectura y el valor es menor al mínimo del sector...
                if lectura and lectura.valor < sector.humedad_minima:
                    alertas.append({
                        "ubicacion": f"{sector.nombre} - {sector.descripcion}",
                        "sensor": sensor.nombre,
                        "valor_actual": lectura.valor,
                        "minimo_requerido": sector.humedad_minima,
                        "mensaje": f"¡Alerta! En {sector.nombre}, sensor {sensor.nombre} marca {lectura.valor}%. Mínimo: {sector.humedad_minima}%."
                    })
    
    return {"total_alertas": len(alertas), "detalles": alertas}

@router.get("/{sector_id}")
def monitorear_sector(sector_id: int, db: Session = Depends(get_db)):
    # 1. Buscar el sector
    sector = db.query(SectorDB).filter(SectorDB.id == sector_id).first()
    if not sector:
        raise HTTPException(status_code=404, detail="Sector no encontrado")
    
    # 2. Traer lecturas reales (Bulk query optimizada)
    ids_sensores = [s.id for s in sector.sensores]
    
    limite_tiempo = datetime.now(timezone.utc) - timedelta(hours=24)
    lecturas_bulk = db.query(LecturaDB).filter(
        LecturaDB.sensor_id.in_(ids_sensores),
        LecturaDB.fecha >= limite_tiempo
    ).all()
    
    # 3. Agrupar lecturas en memoria
    lecturas_por_sensor = defaultdict(list)
    for lectura in lecturas_bulk:
        lecturas_por_sensor[lectura.sensor_id].append(lectura.valor)

    # 4. Aplicar la lógica de negocio (logic.py)
    alertas_agrupadas = {}
    
    for sensor in sector.sensores:
        valores = lecturas_por_sensor[sensor.id]
        if not valores: 
            continue
            
        promedio = sum(valores) / len(valores)
        
        # Usamos tu función nueva
        tipo_alerta = evaluar_sensor(
            sensor.tipo, 
            promedio, 
            sector.humedad_minima, 
            sector.temp_maxima
        )
        
        if tipo_alerta:
            if tipo_alerta not in alertas_agrupadas:
                alertas_agrupadas[tipo_alerta] = []
            alertas_agrupadas[tipo_alerta].append(promedio)

    # 5. Generar el texto final
    estado_final = generar_resumen_estado(alertas_agrupadas)
    
    return {
        "sector": sector.nombre,
        "estado": estado_final,     # Antes era "analisis"
        "sensores_activos": len(sector.sensores),
        "total_lecturas_24h": len(lecturas_bulk)
    }