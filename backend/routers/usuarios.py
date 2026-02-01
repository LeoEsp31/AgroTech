# backend/routers/usuarios.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ..database import get_db
from ..models_db import UserDB
from ..models import UserCreate, UserResponse, Token
from ..auth import verificar_password, obtener_password_hash, crear_access_token 

router = APIRouter(tags=["Usuarios y Auth"])

@router.post("/usuarios/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def registrar_usuario(usuario: UserCreate, db: Session = Depends(get_db)):
    usuario_existente = db.query(UserDB).filter(UserDB.username == usuario.username).first()
    if usuario_existente:
        raise HTTPException(status_code=400, detail="Usuario ya registrado")

    clave_hasheada = obtener_password_hash(usuario.password)
    nuevo_usuario = UserDB(username=usuario.username, hashed_password=clave_hasheada)
    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)
    return nuevo_usuario

@router.post("/token/", response_model=Token)
def login_para_obtener_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    usuario = db.query(UserDB).filter(UserDB.username == form_data.username).first()
    if not usuario or not verificar_password(form_data.password, usuario.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = crear_access_token(data={"sub": usuario.username})
    return {"access_token": access_token, "token_type": "bearer"}