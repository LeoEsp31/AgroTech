from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base

from .routers import sectores, sensores, monitoreo, usuarios

Base.metadata.create_all(bind=engine)

app = FastAPI(title="AgroTech San Juan")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(usuarios.router)   
app.include_router(sectores.router)   
app.include_router(sensores.router)   
app.include_router(monitoreo.router)  

@app.get("/")
def root():
    return {
        "sistema": "AgroTech San Juan API",
        "estado": "En línea 🚀",
        "documentacion": "/docs"
    }