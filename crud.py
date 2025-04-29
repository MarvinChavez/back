from sqlalchemy.orm import Session
from models import User,Empresa
from schemas import UserCreate,EmpresaCreate
from security import get_password_hash
import json

def create_user(db: Session, user: UserCreate):
    db_user = User(
        username=user.username,
        hashed_password=get_password_hash(user.password),
        permisos_vistas=user.permisos_vistas,
        empresa_id=user.empresa_id
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def create_empresa(db: Session, user: EmpresaCreate):
    db_user = Empresa(
        ruc=user.ruc,
        hashed_password=get_password_hash(user.password),
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
def get_users(db: Session):
    return db.query(User).all()

def get_user_by_email(db: Session, username: str):
    user = db.query(User).filter(User.username == username).first()
    return user

def get_empresa_by_ruc(db: Session, ruc: str):
    empresa = db.query(Empresa).filter(Empresa.ruc == ruc).first()
    return empresa