from pydantic import BaseModel, EmailStr
from typing import Optional
from typing import List

class UserCreate(BaseModel):
    username: str
    password: str
    permisos_vistas: List[str]
    empresa_id:int

class EmpresaCreate(BaseModel):
    ruc: str
    password: str
    
class UserUpdate(BaseModel):
    username: Optional[str] = None
    password: Optional[str]= None
    permisos_vistas: List[str] = None
    empresa_id:int=None


class UserResponse(BaseModel):
    id: int
    username: str
    permisos_vistas: List[str]

    class Config:
        from_attributes = True
class UserVer(BaseModel):
    username: str
    permisos_vistas: List[str]
    empresa_id:int

class LoginRequest(BaseModel):
    username: str
    password: str
    empresa_id:int
    class Config:
        from_attributes = True

class LoginE(BaseModel):
    ruc: str
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
