from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

# 1. USUARIOS (Seguridad)
class UserDB(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)

# 2. SECTORES (La Finca)
class SectorDB(Base):
    __tablename__ = "sectores"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, index=True)
    descripcion = Column(String)
    humedad_minima = Column(Float, default=20.0) 
    temp_maxima = Column(Float, default=40.0)
    sensores = relationship("SensorDB", back_populates="sector", cascade="all, delete-orphan")

# 3. SENSORES (Dispositivos)
class SensorDB(Base):
    __tablename__ = "sensores"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, index=True)
    tipo = Column(String)  # Humedad, Temperatura, etc.
    marca = Column(String)
    sector_id = Column(Integer, ForeignKey("sectores.id"))
    modelo = Column(String)
    # Relaciones
    sector = relationship("SectorDB", back_populates="sensores")
    lecturas = relationship("LecturaDB", back_populates="sensor", cascade="all, delete-orphan")

# 4. LECTURAS (Datos históricos)
class LecturaDB(Base):
    __tablename__ = "lecturas"
    id = Column(Integer, primary_key=True, index=True)
    valor = Column(Float, nullable=False)
    fecha = Column(DateTime(timezone=True), server_default=func.now())
    
    sensor_id = Column(Integer, ForeignKey("sensores.id"))
    
    # Relación: Una lectura pertenece a un solo sensor
    sensor = relationship("SensorDB", back_populates="lecturas")