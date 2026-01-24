from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List

# ==========================================
# MODELOS PARA SENSORES
# ==========================================

class SensorBase(BaseModel):
    """Lo que define a cualquier sensor en AgroTech"""
    marca: str
    modelo: str
    sector_id: int

class SensorCreate(SensorBase):
    """Se usa en el POST: El ID es obligatorio al crear manualmente"""
    id: int

class SensorUpdate(BaseModel):
    """Se usa en PATCH/PUT: Todo es opcional para el bucle setattr"""
    marca: Optional[str] = None
    modelo: Optional[str] = None
    sector_id: Optional[int] = None

class SensorResponse(SensorBase):
    """Lo que la API devuelve (incluye el ID generado)"""
    id: int
    
    # Configuración para que Pydantic entienda a SQLAlchemy
    model_config = ConfigDict(from_attributes=True)


# ==========================================
# MODELOS PARA SECTORES
# ==========================================

class SectorBase(BaseModel):
    """Base para los sectores de riego en San Juan"""
    nombre: str
    descripcion: Optional[str] = None
    # Validación técnica: la humedad no puede ser negativa ni mayor a 100
    humedad_minima: int = Field(ge=0, le=100, description="Humedad entre 0 y 100%")

class SectorCreate(SectorBase):
    """Se usa en el POST"""
    id: int

class SectorUpdate(BaseModel):
    """Se usa en PATCH/PUT: Permite actualizaciones parciales inteligentes"""
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    humedad_minima: Optional[int] = Field(None, ge=0, le=100)

class SectorResponse(SectorBase):
    """Respuesta completa que incluye la lista de sus sensores"""
    id: int
    # Relación anidada: Un sector devuelve sus sensores vinculados
    sensores: List[SensorResponse] = []

    model_config = ConfigDict(from_attributes=True)