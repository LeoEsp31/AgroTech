from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import Dict, List
from collections import defaultdict
from datetime import datetime, timedelta, timezone

# Importamos desde los módulos padres (..)
from ..database import get_db
from ..models_db import SectorDB, LecturaDB, UserDB
from ..models import SectorCreate, SectorUpdate, SectorResponse, SectorListResponse
from ..logic import evaluar_sensor, generar_resumen_estado
from ..dependencies import get_current_user

# Creamos el Router
router = APIRouter(
    prefix="/sectores",    
    tags=["Sectores"]     
)
# --- RUTAS DE SECTORES ---

@router.post("/", response_model=SectorResponse, status_code=status.HTTP_201_CREATED)
def crear_sector(sector: SectorCreate, db: Session = Depends(get_db), current_user: UserDB = Depends(get_current_user)):
    nuevo_sector = SectorDB(**sector.model_dump())
    db.add(nuevo_sector)
    db.commit()
    db.refresh(nuevo_sector)
    return nuevo_sector

@router.get("/", response_model=List[SectorListResponse])
def listar_sectores(db: Session = Depends(get_db), current_user: UserDB = Depends(get_current_user)):
    sectores = db.query(SectorDB).options(joinedload(SectorDB.sensores)).all()
    
    ids_sensores = [s.id for sector in sectores for s in sector.sensores]
    
    if not ids_sensores:
        return sectores

    limite_tiempo = datetime.now(timezone.utc) - timedelta(hours=24)
    lecturas_bulk = db.query(LecturaDB).filter(
        LecturaDB.sensor_id.in_(ids_sensores),
        LecturaDB.fecha >= limite_tiempo
    ).all()
    
    lecturas_por_sensor = defaultdict(list)
    for lectura in lecturas_bulk:
        lecturas_por_sensor[lectura.sensor_id].append(lectura.valor)
    
    for sector in sectores:
        alertas_agrupadas: Dict[str, List[float]] = {}
        
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

        
        sector.estado = generar_resumen_estado(alertas_agrupadas)
                
    return sectores


@router.patch("/{sector_id}", response_model=SectorResponse)
def actualizar_parcial_sector(sector_id: int, datos: SectorUpdate, db: Session = Depends(get_db), current_user: UserDB = Depends(get_current_user)):
    sector_db = db.query(SectorDB).filter(SectorDB.id == sector_id).first()
    if not sector_db:
        raise HTTPException(status_code=404, detail="Sector no encontrado")
    
    datos_dict = datos.model_dump(exclude_unset=True)
    for key, value in datos_dict.items():
        setattr(sector_db, key, value)
    
    db.commit()
    db.refresh(sector_db)
    return sector_db

@router.delete("/{sector_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_sector(sector_id: int, db: Session = Depends(get_db), current_user: UserDB = Depends(get_current_user)):
    sector = db.query(SectorDB).filter(SectorDB.id == sector_id).first()
    if not sector:
        raise HTTPException(status_code=404, detail="Sector no encontrado")
    db.delete(sector)
    db.commit()
    return None

@router.put("/{sector_id}", response_model=SectorResponse)
def reemplazar_sector_completo(sector_id: int, datos: SectorCreate, db: Session = Depends(get_db), current_user: UserDB = Depends(get_current_user)):
    if datos.id != sector_id:
        raise HTTPException(status_code=400, detail="El ID del cuerpo no coincide con el de la URL")

    sector_db = db.query(SectorDB).filter(SectorDB.id == sector_id).first()
    
    if not sector_db:
        raise HTTPException(status_code=404, detail="El sector no existe, no se puede reemplazar.")

    datos_dict = datos.model_dump()

    for key, value in datos_dict.items():
        setattr(sector_db, key, value)

    db.commit()
    db.refresh(sector_db)
    
    return sector_db
