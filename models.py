from sqlalchemy import Column, Integer, String, ForeignKey, DECIMAL, Date
from sqlalchemy.orm import relationship
from database import Base
from sqlalchemy import Column, Integer, String, JSON
from sqlalchemy import UniqueConstraint

class Empresa(Base):
    __tablename__ = "empresa"

    id = Column(Integer, primary_key=True, index=True)
    ruc = Column(String(20), nullable=False, unique=True)
    hashed_password = Column(String(255), nullable=False)
    usuarios = relationship("User", back_populates="empresa")
    ingresos = relationship("Ingreso", back_populates="empresa")
    autos = relationship("Auto", back_populates="empresa")  # <- ESTA LINEA DEBERÍA EXISTIR
    rutas = relationship("Ruta", back_populates="empresa")  # <- ESTA LINEA DEBERÍA EXISTIR
    turnos = relationship("Turno", back_populates="empresa")  # <- ESTA LINEA DEBERÍA EXISTIR


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    permisos_vistas = Column(JSON)

    empresa_id = Column(Integer, ForeignKey("empresa.id", ondelete="SET NULL"))
    empresa = relationship("Empresa", back_populates="usuarios")

class Auto(Base):
    __tablename__ = "auto"

    id = Column(Integer, primary_key=True, index=True)
    placa = Column(String(30), nullable=False)  # ❌ Quitamos unique=True
    proveedor = Column(String(30), nullable=False)
    ingresos = relationship("Ingreso", back_populates="auto")
    empresa_id = Column(Integer, ForeignKey("empresa.id", ondelete="SET NULL"))
    empresa = relationship("Empresa", back_populates="autos")

    __table_args__ = (
        UniqueConstraint("placa", "empresa_id", name="uq_placa_empresa"),
    )


class Ruta(Base):
    __tablename__ = "ruta"

    id = Column(Integer, primary_key=True, index=True)
    ciudad_inicial = Column(String(50), nullable=False)
    ciudad_final = Column(String(50), nullable=False)
    ingresos = relationship("Ingreso", back_populates="ruta")
    empresa_id = Column(Integer, ForeignKey("empresa.id", ondelete="SET NULL"))
    empresa = relationship("Empresa", back_populates="rutas")

    __table_args__ = (
        UniqueConstraint("ciudad_inicial", "ciudad_final", "empresa_id", name="uq_ruta_empresa"),
    )


class Turno(Base):
    __tablename__ = "turno"

    id = Column(Integer, primary_key=True, index=True)
    hora = Column(String(10), nullable=False)
    ingresos = relationship("Ingreso", back_populates="turno")
    empresa_id = Column(Integer, ForeignKey("empresa.id", ondelete="SET NULL"))
    empresa = relationship("Empresa", back_populates="turnos")

    __table_args__ = (
        UniqueConstraint("hora", "empresa_id", name="uq_turno_empresa"),
    )
class Ingreso(Base):
    __tablename__ = "ingreso"

    id = Column(Integer, primary_key=True, index=True)
    auto_id = Column(Integer, ForeignKey("auto.id", ondelete="CASCADE"), nullable=False)
    ruta_id = Column(Integer, ForeignKey("ruta.id", ondelete="CASCADE"), nullable=False)
    turno_id = Column(Integer, ForeignKey("turno.id", ondelete="CASCADE"), nullable=False)

    empresa_id = Column(Integer, ForeignKey("empresa.id", ondelete="SET NULL"))

    serial = Column(String(40), unique=True, nullable=False)
    servicio = Column(String(5), nullable=False)
    monto = Column(DECIMAL(10, 2), nullable=False)
    pasajero = Column(Integer, nullable=False)
    fecha = Column(Date, nullable=False)

    auto = relationship("Auto", back_populates="ingresos")
    ruta = relationship("Ruta", back_populates="ingresos")
    turno = relationship("Turno", back_populates="ingresos")
    empresa = relationship("Empresa", back_populates="ingresos")
