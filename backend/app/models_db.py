from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base

class SectorDB(Base):
    __tablename__ = "sectores"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String)
    descripcion = Column(String)
    humedad_minima = Column(Integer)
    
    # Relación: Un sector tiene muchos sensores
    sensores = relationship("SensorDB", back_populates="sector")

class SensorDB(Base):
    __tablename__ = "sensores"

    id = Column(Integer, primary_key=True, index=True)
    marca = Column(String)
    modelo = Column(String)
    sector_id = Column(Integer, ForeignKey("sectores.id"))
    
    # Relación inversa
    sector = relationship("SectorDB", back_populates="sensores")