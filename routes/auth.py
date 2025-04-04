from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal
from schemas import UserCreate,LoginRequest,UserVer,UserUpdate
from crud import create_user, get_user_by_email
from security import verify_password, create_access_token
from models import User 
from security import get_password_hash

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = get_user_by_email(db, user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="user already registered")
    return create_user(db, user)

@router.post("/login")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = get_user_by_email(db, request.username)
    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    access_token = create_access_token(data={"sub": user.username})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "permisos": user.permisos_vistas  # Agregamos los permisos
    }
@router.get("/users")
def get_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return users


@router.get("/users/{username}", response_model=UserVer)
def get_user(username: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user

@router.put("/users/{username}", response_model=UserVer)  # Se devuelve UserVer sin password
def update_user(username: str, user_data: UserUpdate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    if user_data.permisos_vistas:
        user.permisos_vistas = user_data.permisos_vistas
    if user_data.username:
        user.username = user_data.username
    if user_data.password:
        user.hashed_password = get_password_hash(user_data.password) 

    db.commit()
    db.refresh(user)
    return user

@router.delete("/{username}/delete")
def delete_user(username: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()

    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # Eliminar el usuario
    db.delete(user)
    db.commit()

    return {"detail": "Usuario eliminado correctamente"}  # Mensaje de éxito
