from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional

# Instancia de la aplicación
app = FastAPI(title="AgroTech San Juan API")

# --- Modelos de Datos (Pydantic) ---

class Sensor(BaseModel):
    id: int
    marca: str
    modelo: str
    estado: str
    tipo: str
    sector_id: int
    
class Sector(BaseModel):
    id: int
    nombre: str
    descripcion: str
    humedad_minima: float
    sensores: List[Sensor] = []
    
# --- Endpoints ---
@app.get("/")
def inicio():
    return {
        "mensaje": "Bienvenido al Sistema de Monitoreo AgroTech",
        "ubicacion": "San Juan, Argentina",
        "estado": "Operativo"
    }
    
@app.get("/check-riego")
def verificar_riego():
    return {"alerta_riego": False, "humedad_actual":55}


@app.get("/sensor-ejemplo", response_model=Sensor)
def obtener_sensor_ejemplo():
    # Creamos una instancia de tu clase Sensor
    return Sensor(
        id=1, 
        marca="Bosch", 
        modelo="Soil-Z1", 
        estado="Activo", 
        tipo="Humedad", 
        sector_id=10
    )
