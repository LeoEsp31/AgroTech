from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import random

# Importamos todo lo necesario
from .database import engine, Base, get_db
from .models_db import SectorDB, SensorDB
from .models import (
    SectorCreate, SectorUpdate, SectorResponse,
    SensorCreate, SensorUpdate, SensorResponse
)
from .logic import calcular_promedio, evaluar_estado_sector

# Creamos las tablas
Base.metadata.create_all(bind=engine)

app = FastAPI(title="AgroTech San Juan - API Profesional")

# --- RUTAS DE SECTORES ---

@app.post("/sectores/", response_model=SectorResponse, status_code=status.HTTP_201_CREATED)
def crear_sector(sector: SectorCreate, db: Session = Depends(get_db)):
    nuevo_sector = SectorDB(**sector.model_dump())
    db.add(nuevo_sector)
    db.commit()
    db.refresh(nuevo_sector)
    return nuevo_sector

@app.get("/sectores/", response_model=List[SectorResponse])
def listar_sectores(db: Session = Depends(get_db)):
    return db.query(SectorDB).all()

@app.patch("/sectores/{sector_id}", response_model=SectorResponse)
def actualizar_parcial_sector(sector_id: int, datos: SectorUpdate, db: Session = Depends(get_db)):
    sector_db = db.query(SectorDB).filter(SectorDB.id == sector_id).first()
    if not sector_db:
        raise HTTPException(status_code=404, detail="Sector no encontrado")
    
    # El bucle inteligente con setattr
    datos_dict = datos.model_dump(exclude_unset=True)
    for key, value in datos_dict.items():
        setattr(sector_db, key, value)
    
    db.commit()
    db.refresh(sector_db)
    return sector_db

@app.delete("/sectores/{sector_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_sector(sector_id: int, db: Session = Depends(get_db)):
    sector = db.query(SectorDB).filter(SectorDB.id == sector_id).first()
    if not sector:
        raise HTTPException(status_code=404, detail="Sector no encontrado")
    db.delete(sector)
    db.commit()
    return None

# --- RUTAS DE MONITOREO ---

@app.get("/monitoreo/{sector_id}")
def monitorear_sector(sector_id: int, db: Session = Depends(get_db)):
    sector = db.query(SectorDB).filter(SectorDB.id == sector_id).first()
    if not sector or not sector.sensores:
        raise HTTPException(status_code=404, detail="Sector sin sensores o inexistente")
    
    lecturas = [random.randint(20, 80) for _ in sector.sensores]
    promedio = calcular_promedio(lecturas)
    analisis = evaluar_estado_sector(promedio, sector.humedad_minima)
    
    return {
        "sector": sector.nombre,
        "humedad_promedio": f"{promedio:.2f}%",
        "analisis": analisis,
        "sensores_activos": len(sector.sensores)
    }
    
@app.put("/sectores/{sector_id}", response_model=SectorResponse)
def reemplazar_sector_completo(sector_id: int, datos: SectorCreate, db: Session = Depends(get_db)):
    if datos.id != sector_id:
        raise HTTPException(status_code=400, detail="El ID del cuerpo no coincide con el de la URL")
    # 1. Buscamos el registro existente
    sector_db = db.query(SectorDB).filter(SectorDB.id == sector_id).first()
    
    if not sector_db:
        raise HTTPException(status_code=404, detail="El sector no existe, no se puede reemplazar.")

    # 2. Convertimos todo el modelo a diccionario
    # NO usamos exclude_unset=True porque en PUT queremos procesar todos los campos
    datos_dict = datos.model_dump()

    # 3. Aplicamos el bucle setattr
    for key, value in datos_dict.items():
        setattr(sector_db, key, value)

    # 4. Guardamos los cambios
    db.commit()
    db.refresh(sector_db)
    
    return sector_db

# --- RUTAS DE SENSORES ---

@app.post("/sensores/", response_model=SensorResponse, status_code=status.HTTP_201_CREATED)
def crear_sensor(sensor: SensorCreate, db: Session = Depends(get_db)):
    # Validación extra: ¿Existe el sector al que lo queremos asignar?
    sector_existe = db.query(SectorDB).filter(SectorDB.id == sensor.sector_id).first()
    if not sector_existe:
        raise HTTPException(status_code=404, detail="No podés crear un sensor para un sector que no existe.")
    
    nuevo_sensor = SensorDB(**sensor.model_dump())
    db.add(nuevo_sensor)
    db.commit()
    db.refresh(nuevo_sensor)
    return nuevo_sensor

@app.get("/sensores/", response_model=List[SensorResponse])
def listar_sensores(db: Session = Depends(get_db)):
    return db.query(SensorDB).all()

@app.get("/sensores/{sensor_id}", response_model=SensorResponse)
def obtener_sensor(sensor_id: int, db: Session = Depends(get_db)):
    sensor = db.query(SensorDB).filter(SensorDB.id == sensor_id).first()
    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor no encontrado")
    return sensor

@app.patch("/sensores/{sensor_id}", response_model=SensorResponse)
def actualizar_parcial_sensor(sensor_id: int, datos: SensorUpdate, db: Session = Depends(get_db)):
    sensor_db = db.query(SensorDB).filter(SensorDB.id == sensor_id).first()
    if not sensor_db:
        raise HTTPException(status_code=404, detail="Sensor no encontrado")

    # Si se intenta cambiar el sector_id, validamos que el nuevo sector exista
    if datos.sector_id is not None:
        sector_existe = db.query(SectorDB).filter(SectorDB.id == datos.sector_id).first()
        if not sector_existe:
            raise HTTPException(status_code=404, detail="El nuevo sector_id no existe")

    # El bucle inteligente que ya es tu marca registrada
    datos_dict = datos.model_dump(exclude_unset=True)
    for key, value in datos_dict.items():
        setattr(sensor_db, key, value)

    db.commit()
    db.refresh(sensor_db)
    return sensor_db

@app.delete("/sensores/{sensor_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_sensor(sensor_id: int, db: Session = Depends(get_db)):
    sensor = db.query(SensorDB).filter(SensorDB.id == sensor_id).first()
    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor no encontrado")
    db.delete(sensor)
    db.commit()
    return None