from pydantic import BaseModel
from typing import List
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