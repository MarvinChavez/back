from sqlalchemy.orm import Session
from models import User
from schemas import UserCreate
from security import get_password_hash
import json

def create_user(db: Session, user: UserCreate):
    db_user = User(
        username=user.username,
        hashed_password=get_password_hash(user.password),
        permisos_vistas=user.permisos_vistas  # No es necesario convertir a JSON
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