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
def obtener_alertas_globales( 
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(get_current_user)
):
    sectores = db.query(SectorDB).options(joinedload(SectorDB.sensores)).all()
    
    ids_sensores = []
    for sector in sectores:
        for sensor in sector.sensores:
            ids_sensores.append(sensor.id)
    
    if not ids_sensores:
        return {"total_alertas": 0, "detalles": []}

    limite_tiempo = datetime.now(timezone.utc) - timedelta(hours=24)
    lecturas_bulk = db.query(LecturaDB).filter(
        LecturaDB.sensor_id.in_(ids_sensores),
        LecturaDB.fecha >= limite_tiempo
    ).all()
    
    ultima_lectura_por_sensor = {}
    for lectura in lecturas_bulk:
        sensor_id = lectura.sensor_id
        if sensor_id not in ultima_lectura_por_sensor:
            ultima_lectura_por_sensor[sensor_id] = lectura
        else:
            if lectura.fecha > ultima_lectura_por_sensor[sensor_id].fecha:
                ultima_lectura_por_sensor[sensor_id] = lectura

    alertas = []
    for sector in sectores:
        for sensor in sector.sensores:
            lectura = ultima_lectura_por_sensor.get(sensor.id)
            
            if lectura:
                tipo_alerta = evaluar_sensor(
                    sensor.tipo, 
                    lectura.valor, 
                    sector.humedad_minima, 
                    sector.temp_maxima
                )
                
                if tipo_alerta:
                    unidad = "%" if "Humedad" in sensor.tipo else "°C"
                    alertas.append({
                        "ubicacion": f"{sector.nombre}",
                        "sensor": sensor.nombre,
                        "tipo_alerta": tipo_alerta, 
                        "valor_actual": f"{lectura.valor}{unidad}",
                        "mensaje": f"⚠️ {tipo_alerta}: {sensor.nombre} marca {lectura.valor}{unidad}."
                    })
    
    return {"total_alertas": len(alertas), "detalles": alertas}

@router.get("/{sector_id}")
def monitorear_sector(sector_id: int, db: Session = Depends(get_db)):
    sector = db.query(SectorDB).filter(SectorDB.id == sector_id).first()
    if not sector:
        raise HTTPException(status_code=404, detail="Sector no encontrado")
    
    ids_sensores = [s.id for s in sector.sensores]
    
    limite_tiempo = datetime.now(timezone.utc) - timedelta(hours=24)
    lecturas_bulk = db.query(LecturaDB).filter(
        LecturaDB.sensor_id.in_(ids_sensores),
        LecturaDB.fecha >= limite_tiempo
    ).all()
    
    lecturas_por_sensor = defaultdict(list)
    for lectura in lecturas_bulk:
        lecturas_por_sensor[lectura.sensor_id].append(lectura.valor)

    alertas_agrupadas = {}
    
    for sensor in sector.sensores:
        valores = lecturas_por_sensor[sensor.id]
        if not valores: 
            continue
            
        promedio = sum(valores) / len(valores)
        
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

    estado_final = generar_resumen_estado(alertas_agrupadas)
    
    return {
        "sector": sector.nombre,
        "estado": estado_final,    
        "sensores_activos": len(sector.sensores),
        "total_lecturas_24h": len(lecturas_bulk)
    }