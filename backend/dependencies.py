# backend/dependencies.py
import os
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

# Importamos tus configuraciones de DB y Modelos
from .database import get_db
from .models_db import UserDB
from .models import TokenData

load_dotenv()

# Recuperamos las variables de entorno otra vez (porque este archivo corre aislado)
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

# Esto le dice a FastAPI dónde buscar el token (en la URL /token)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar la credencial",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # 1. Decodificar el token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception

    # 2. Validar contra la base de datos
    usuario = db.query(UserDB).filter(UserDB.username == token_data.username).first()
    if usuario is None:
        raise credentials_exception
        
    return usuario