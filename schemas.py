from pydantic import BaseModel, EmailStr
from typing import Optional
from typing import List

class UserCreate(BaseModel):
    username: str
    password: str
    permisos_vistas: List[str]
    
class UserUpdate(BaseModel):
    username: Optional[str] = None
    password: Optional[str]= None
    permisos_vistas: List[str] = None

class UserResponse(BaseModel):
    id: int
    username: str
    permisos_vistas: List[str]

    class Config:
        from_attributes = True
class UserVer(BaseModel):
    username: str
    permisos_vistas: List[str]

class LoginRequest(BaseModel):
    username: str
    password: str

    class Config:
        from_attributes = True
class RutaResponse(BaseModel):
    id: int
    ciudad_inicial: str
    ciudad_final: str
class AutoResponse(BaseModel):
    id: int
    placa: str
