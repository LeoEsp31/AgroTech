from fastapi import FastAPI, HTTPException
from .models import Sensor, Sector
from .logic import evaluar_estado_sector, calcular_promedio
import random

app = FastAPI(title="AgroTech - Monitoreo Inteligente")

SECTORES_DB = {}

@app.post("/sectores/", status_code=201)
def crear_sector(nuevo_sector: Sector):
    if nuevo_sector.id in SECTORES_DB:
        raise HTTPException(status_code=400, detail="El ID ya existe")
    SECTORES_DB[nuevo_sector.id] = nuevo_sector
    return {"mensaje": "Sector creado", "data": nuevo_sector}

@app.post("/sectores/{sector_id}/sensores/", status_code=201)
def agregar_sensor(sector_id: int, nuevo_sensor: Sensor):
    if sector_id not in SECTORES_DB:
        raise HTTPException(status_code=404, detail="Sector no encontrado")
    SECTORES_DB[sector_id].sensores.append(nuevo_sensor)
    return {"mensaje": "Sensor vinculado"}

@app.get("/monitoreo/{sector_id}")
def monitorear(sector_id: int): # <--- FIJATE: ACÁ NO HAY NADA MÁS QUE EL ID
    sector = SECTORES_DB.get(sector_id)
    if not sector:
        raise HTTPException(status_code=404, detail="No existe el sector")
    
    if not sector.sensores:
        return {"error": "No hay sensores en este sector para medir"}

    # Generamos lecturas basadas en los sensores reales que cargaste
    lecturas = [random.randint(20, 70) for _ in sector.sensores]
    promedio = calcular_promedio(lecturas)
    analisis = evaluar_estado_sector(promedio, sector.humedad_minima)
    
    return {
        "sector": sector.nombre,
        "promedio_humedad": f"{promedio:.2f}%",
        "analisis": analisis
    }
@app.get("/sectores/")
def listar_sectores():
    return SECTORES_DB