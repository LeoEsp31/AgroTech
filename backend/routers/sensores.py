# backend/routers/sensores.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..models_db import SensorDB, LecturaDB, SectorDB, UserDB
from ..models import SensorCreate, SensorUpdate, SensorResponse, LecturaCreate, LecturaResponse
from ..dependencies import get_current_user
router = APIRouter(
    tags=["Sensores"]
)

# --- RUTAS DE SENSORES ---

@router.post("/sensores/", response_model=SensorResponse)
def crear_sensor(sensor: SensorCreate, db: Session = Depends(get_db), current_user: UserDB = Depends(get_current_user)):
    nuevo_sensor = SensorDB(**sensor.model_dump()) 
    db.add(nuevo_sensor)
    db.commit()
    db.refresh(nuevo_sensor)
    return nuevo_sensor

@router.get("/sensores/", response_model=List[SensorResponse])
def listar_sensores(db: Session = Depends(get_db), current_user: UserDB = Depends(get_current_user)):
    return db.query(SensorDB).all()

@router.get("/sensores/{sensor_id}", response_model=SensorResponse)
def obtener_sensor(sensor_id: int, db: Session = Depends(get_db)):
    sensor = db.query(SensorDB).filter(SensorDB.id == sensor_id).first()
    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor no encontrado")
    return sensor

@router.patch("/sensores/{sensor_id}", response_model=SensorResponse)
def actualizar_parcial_sensor(sensor_id: int, datos: SensorUpdate, db: Session = Depends(get_db), current_user: UserDB = Depends(get_current_user)):
    sensor_db = db.query(SensorDB).filter(SensorDB.id == sensor_id).first()
    if not sensor_db:
        raise HTTPException(status_code=404, detail="Sensor no encontrado")

    if datos.sector_id is not None:
        sector_existe = db.query(SectorDB).filter(SectorDB.id == datos.sector_id).first()
        if not sector_existe:
            raise HTTPException(status_code=404, detail="El nuevo sector_id no existe")

    datos_dict = datos.model_dump(exclude_unset=True)
    for key, value in datos_dict.items():
        setattr(sensor_db, key, value)

    db.commit()
    db.refresh(sensor_db)
    return sensor_db

@router.delete("/sensores/{sensor_id}")
def eliminar_sensor(sensor_id: int, db: Session = Depends(get_db), current_user: UserDB = Depends(get_current_user)):
    sensor = db.query(SensorDB).filter(SensorDB.id == sensor_id).first()
    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor no encontrado")
    db.delete(sensor)
    db.commit()
    return {"detail": f"Sensor {sensor_id} eliminado"}

@router.get("/sensores/{sensor_id}/lecturas", response_model=List[LecturaResponse])
def obtener_historial_sensor(sensor_id: int, db: Session = Depends(get_db), current_user: UserDB = Depends(get_current_user)):
    lecturas = db.query(LecturaDB).filter(LecturaDB.sensor_id == sensor_id).all()
    return lecturas

# --- RUTAS DE LECTURAS ---
# Las ponemos acá porque están muy relacionadas

@router.post("/lecturas/", response_model=LecturaResponse)
def crear_lectura(lectura: LecturaCreate, db: Session = Depends(get_db), current_user: UserDB = Depends(get_current_user)):
    sensor = db.query(SensorDB).filter(SensorDB.id == lectura.sensor_id).first()
    if not sensor:
        raise HTTPException(status_code=404, detail="El sensor no existe")

    nueva_lectura = LecturaDB(**lectura.model_dump())
    db.add(nueva_lectura)
    db.commit()
    db.refresh(nueva_lectura)
    return nueva_lectura

@router.get("/sensores/{sensor_id}/lecturas", response_model=List[LecturaResponse])
def obtener_historial_sensor(
    sensor_id: int, 
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(get_current_user)
):
    lecturas = db.query(LecturaDB).filter(LecturaDB.sensor_id == sensor_id).all()
    return lecturas