from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
# ==========================================
class LecturaBase(BaseModel):
    valor: float
    sensor_id: int

class LecturaCreate(LecturaBase):
    pass 

class LecturaResponse(BaseModel):
    id: int
    valor: float
    fecha: datetime
    sensor_id: int

    model_config = ConfigDict(from_attributes=True)

# ==========================================
# MODELOS PARA SENSORES
# ==========================================

class SensorBase(BaseModel):
    """Lo que define a cualquier sensor en AgroTech"""
    marca: str
    modelo: str
    sector_id: int
    nombre: str   
    tipo: str

class SensorCreate(SensorBase):
    """Se usa en el POST"""
    pass

class SensorUpdate(BaseModel):
    """Se usa en PATCH/PUT: Todo es opcional para el bucle setattr"""
    marca: Optional[str] = None
    modelo: Optional[str] = None
    sector_id: Optional[int] = None

class SensorResponse(BaseModel):
    id: int
    nombre: str
    tipo: str
    sector_id: int
    lecturas: List[LecturaResponse] = []

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
    temp_maxima: float = 40.0
class SectorCreate(SectorBase):
    """Se usa en el POST"""
    pass

class SectorUpdate(BaseModel):
    """Se usa en PATCH/PUT: Permite actualizaciones parciales inteligentes"""
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    humedad_minima: Optional[int] = Field(None, ge=0, le=100)

class SectorResponse(BaseModel):
    """Respuesta detallada de un sector con sus sensores"""
    id: int
    nombre: str
    descripcion: Optional[str]
    humedad_minima: float
    estado: str = "OK" 
    sensores: List[SensorResponse] = []

    model_config = ConfigDict(from_attributes=True)
    
class SectorDetalle(BaseModel):
    id: int
    nombre: str
    cultivo: str
    estado_critico: bool
    alertas: List[str]
    cantidad_sensores: int

    class Config:
        from_attributes = True
    
# ==========================================
# MODELOS PARA USUARIOS
# ==========================================

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    is_active: bool

    model_config = ConfigDict(from_attributes=True)

# ==========================================
# MODELOS PARA TOKENS
# ==========================================   
    
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
    
    
