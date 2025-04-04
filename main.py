from fastapi import FastAPI
from routes import auth, users, ingreso  # Asegúrate de importar ingreso correctamente
from database import engine, Base
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Crear tablas en la base de datos
Base.metadata.create_all(bind=engine)

# Incluir rutas
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(ingreso.router, prefix="/ingreso", tags=["Ingreso"])  # ✅ Corrección aquí

origins = [
    "http://localhost:8100",  # Ionic local
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
)

@app.get("/")
def home():
    return {"message": "API funcionando"}
