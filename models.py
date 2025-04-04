from sqlalchemy import Column, Integer, String, ForeignKey, DECIMAL, Date
from sqlalchemy.orm import relationship
from database import Base
from sqlalchemy import Column, Integer, String, JSON

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    permisos_vistas = Column(JSON)  
class Auto(Base):
    __tablename__ = "auto"

    id = Column(Integer, primary_key=True, index=True)
    placa = Column(String(30), unique=True, nullable=False)
    proveedor = Column(String(30), nullable=False)
    ingresos = relationship("Ingreso", back_populates="auto")


class Ruta(Base):
    __tablename__ = "ruta"

    id = Column(Integer, primary_key=True, index=True)
    ciudad_inicial = Column(String(50), nullable=False)
    ciudad_final = Column(String(50), nullable=False)
    ingresos = relationship("Ingreso", back_populates="ruta")


class Turno(Base):
    __tablename__ = "turno"

    id = Column(Integer, primary_key=True, index=True)
    hora = Column(String(10), nullable=False)
    ingresos = relationship("Ingreso", back_populates="turno")


class Ingreso(Base):
    __tablename__ = "ingreso"

    id = Column(Integer, primary_key=True, index=True)
    auto_id = Column(Integer, ForeignKey("auto.id", ondelete="CASCADE"), nullable=False)
    ruta_id = Column(Integer, ForeignKey("ruta.id", ondelete="CASCADE"), nullable=False)
    turno_id = Column(Integer, ForeignKey("turno.id", ondelete="CASCADE"), nullable=False)
    
    serial = Column(String(40), unique=True, nullable=False)
    servicio = Column(String(5), nullable=False)
    monto = Column(DECIMAL(10, 2), nullable=False)
    pasajero = Column(Integer, nullable=False)
    fecha = Column(Date, nullable=False)

    auto = relationship("Auto", back_populates="ingresos")
    ruta = relationship("Ruta", back_populates="ingresos")
    turno = relationship("Turno", back_populates="ingresos")
