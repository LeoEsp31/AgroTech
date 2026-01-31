from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import Dict, List
from .auth import crear_access_token, obtener_password_hash, verificar_password, SECRET_KEY, ALGORITHM
import random
from .database import engine, Base, get_db
from .models_db import SectorDB, SensorDB, UserDB, LecturaDB
from .models import (
    SectorCreate, SectorUpdate, SectorResponse,
    SectorListResponse,
    SensorCreate, SensorUpdate, SensorResponse,
    UserCreate, UserResponse,
    Token, TokenData,
    LecturaCreate, LecturaResponse
)
from .logic import evaluar_sensor, generar_resumen_estado
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from collections import defaultdict

# Creamos las tablas
Base.metadata.create_all(bind=engine)

app = FastAPI(title="AgroTech San Juan")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar la credencial",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # 1. Decodificamos el token usando tu SECRET_KEY
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        
        if username is None:
            raise credentials_exception
            
        token_data = TokenData(username=username)
    except JWTError:
        # Si el token expiró o la firma no coincide, saltamos acá
        raise credentials_exception

    # 2. Buscamos al usuario en Postgres para estar 100% seguros
    usuario = db.query(UserDB).filter(UserDB.username == token_data.username).first()
    
    if usuario is None:
        raise credentials_exception
        
    return usuario

# --- RUTAS DE SECTORES ---

@app.post("/sectores/", response_model=SectorResponse, status_code=status.HTTP_201_CREATED)
def crear_sector(sector: SectorCreate, db: Session = Depends(get_db), current_user: UserDB = Depends(get_current_user)):
    nuevo_sector = SectorDB(**sector.model_dump())
    db.add(nuevo_sector)
    db.commit()
    db.refresh(nuevo_sector)
    return nuevo_sector

@app.get("/sectores/", response_model=List[SectorListResponse])
def listar_sectores(db: Session = Depends(get_db), current_user: UserDB = Depends(get_current_user)):
    # 1. Traemos Sectores + Sensores
    sectores = db.query(SectorDB).options(joinedload(SectorDB.sensores)).all()
    
    # 2. Recolectamos IDs
    ids_sensores = [s.id for sector in sectores for s in sector.sensores]
    
    if not ids_sensores:
        return sectores

    # 3. Traemos lecturas bulk (últimas 24hs)
    limite_tiempo = datetime.now(timezone.utc) - timedelta(hours=24)
    lecturas_bulk = db.query(LecturaDB).filter(
        LecturaDB.sensor_id.in_(ids_sensores),
        LecturaDB.fecha >= limite_tiempo
    ).all()
    
    # 4. Organizamos en memoria
    lecturas_por_sensor = defaultdict(list)
    for lectura in lecturas_bulk:
        lecturas_por_sensor[lectura.sensor_id].append(lectura.valor)
    
    # 5. Procesamos usando la lógica extraída (Refactoring)
    for sector in sectores:
        alertas_agrupadas: Dict[str, List[float]] = {}
        
        for sensor in sector.sensores:
            valores = lecturas_por_sensor[sensor.id]
            if not valores:
                continue
            
            promedio = sum(valores) / len(valores)
            
            tipo_alerta = evaluar_sensor(
                sensor.tipo, 
                promedio, 
                sector.humedad_minima, 
                sector.temp_maxima
            )
            
            if tipo_alerta:
                if tipo_alerta not in alertas_agrupadas:
                    alertas_agrupadas[tipo_alerta] = []
                alertas_agrupadas[tipo_alerta].append(promedio)

        
        sector.estado = generar_resumen_estado(alertas_agrupadas)
                
    return sectores

@app.patch("/sectores/{sector_id}", response_model=SectorResponse)
def actualizar_parcial_sector(sector_id: int, datos: SectorUpdate, db: Session = Depends(get_db), current_user: UserDB = Depends(get_current_user)):
    sector_db = db.query(SectorDB).filter(SectorDB.id == sector_id).first()
    if not sector_db:
        raise HTTPException(status_code=404, detail="Sector no encontrado")
    
    # El bucle inteligente con setattr
    datos_dict = datos.model_dump(exclude_unset=True)
    for key, value in datos_dict.items():
        setattr(sector_db, key, value)
    
    db.commit()
    db.refresh(sector_db)
    return sector_db

@app.delete("/sectores/{sector_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_sector(sector_id: int, db: Session = Depends(get_db), current_user: UserDB = Depends(get_current_user)):
    sector = db.query(SectorDB).filter(SectorDB.id == sector_id).first()
    if not sector:
        raise HTTPException(status_code=404, detail="Sector no encontrado")
    db.delete(sector)
    db.commit()
    return None

# --- RUTAS DE MONITOREO ---

@app.get("/monitoreo/alertas")
def obtener_alertas_riego(
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(get_current_user)
):
    sectores = db.query(SectorDB).all()
    alertas = []

    for sector in sectores:
        for sensor in sector.sensores:
            # Solo nos interesan los sensores de Humedad
            if sensor.tipo.lower() == "humedad":
                # Obtenemos la última lectura (la más reciente por fecha)
                ultima_lectura = db.query(LecturaDB).filter(
                    LecturaDB.sensor_id == sensor.id
                ).order_by(LecturaDB.fecha.desc()).first()

                # Verificamos si existe la lectura y si es menor al umbral
                if ultima_lectura and ultima_lectura.valor < sector.humedad_minima:
                    alertas.append({
                        "ubicacion": f"{sector.nombre} - {sector.descripcion}", # Combinamos ambos
                        "sensor": sensor.nombre,
                        "valor_actual": ultima_lectura.valor,
                        "minimo_requerido": sector.humedad_minima,
                        "mensaje": f"¡Alerta! En {sector.nombre} ({sector.descripcion}), el sensor {sensor.nombre} marca {ultima_lectura.valor}%. El mínimo es {sector.humedad_minima}%."
                    })
    
    return {"total_alertas": len(alertas), "detalles": alertas}

@app.get("/monitoreo/{sector_id}")
def monitorear_sector(sector_id: int, db: Session = Depends(get_db)):
    sector = db.query(SectorDB).filter(SectorDB.id == sector_id).first()
    if not sector or not sector.sensores:
        raise HTTPException(status_code=404, detail="Sector sin sensores o inexistente")
    
    lecturas = [random.randint(20, 80) for _ in sector.sensores]
    promedio = calcular_promedio(lecturas)
    analisis = evaluar_estado_sector(promedio, sector.humedad_minima)
    
    return {
        "sector": sector.nombre,
        "humedad_promedio": f"{promedio:.2f}%",
        "analisis": analisis,
        "sensores_activos": len(sector.sensores)
    }
    
@app.put("/sectores/{sector_id}", response_model=SectorResponse)
def reemplazar_sector_completo(sector_id: int, datos: SectorCreate, db: Session = Depends(get_db), current_user: UserDB = Depends(get_current_user)):
    if datos.id != sector_id:
        raise HTTPException(status_code=400, detail="El ID del cuerpo no coincide con el de la URL")
    # 1. Buscamos el registro existente
    sector_db = db.query(SectorDB).filter(SectorDB.id == sector_id).first()
    
    if not sector_db:
        raise HTTPException(status_code=404, detail="El sector no existe, no se puede reemplazar.")

    # 2. Convertimos todo el modelo a diccionario
    # NO usamos exclude_unset=True porque en PUT queremos procesar todos los campos
    datos_dict = datos.model_dump()

    # 3. Aplicamos el bucle setattr
    for key, value in datos_dict.items():
        setattr(sector_db, key, value)

    # 4. Guardamos los cambios
    db.commit()
    db.refresh(sector_db)
    
    return sector_db

# --- RUTAS DE SENSORES ---

@app.post("/sensores/", response_model=SensorResponse)
def crear_sensor(
    sensor: SensorCreate,db: Session = Depends(get_db), 
    current_user: UserDB = Depends(get_current_user)
):
    # El **sensor.model_dump() expande nombre, tipo y sector_id
    nuevo_sensor = SensorDB(**sensor.model_dump()) 
    db.add(nuevo_sensor)
    db.commit()
    db.refresh(nuevo_sensor)
    return nuevo_sensor

@app.get("/sensores/", response_model=List[SensorResponse])
def listar_sensores(db: Session = Depends(get_db), current_user: UserDB = Depends(get_current_user)):
    return db.query(SensorDB).all()

@app.get("/sensores/{sensor_id}", response_model=SensorResponse)
def obtener_sensor(sensor_id: int, db: Session = Depends(get_db)):
    sensor = db.query(SensorDB).filter(SensorDB.id == sensor_id).first()
    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor no encontrado")
    return sensor

@app.patch("/sensores/{sensor_id}", response_model=SensorResponse)
def actualizar_parcial_sensor(sensor_id: int, datos: SensorUpdate, db: Session = Depends(get_db), current_user: UserDB = Depends(get_current_user)):
    sensor_db = db.query(SensorDB).filter(SensorDB.id == sensor_id).first()
    if not sensor_db:
        raise HTTPException(status_code=404, detail="Sensor no encontrado")

    # Si se intenta cambiar el sector_id, validamos que el nuevo sector exista
    if datos.sector_id is not None:
        sector_existe = db.query(SectorDB).filter(SectorDB.id == datos.sector_id).first()
        if not sector_existe:
            raise HTTPException(status_code=404, detail="El nuevo sector_id no existe")

    # El bucle inteligente que ya es tu marca registrada
    datos_dict = datos.model_dump(exclude_unset=True)
    for key, value in datos_dict.items():
        setattr(sensor_db, key, value)

    db.commit()
    db.refresh(sensor_db)
    return sensor_db

@app.delete("/sensores/{sensor_id}")
def eliminar_sensor(
    sensor_id: int, 
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(get_current_user)
):
    sensor = db.query(SensorDB).filter(SensorDB.id == sensor_id).first()
    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor no encontrado")
        
    db.delete(sensor)
    db.commit()
    return {"detail": f"Sensor {sensor_id} eliminado por {current_user.username}"}

# --- RUTAS DE USUARIOS ---


@app.post("/usuarios/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def registrar_usuario(usuario: UserCreate, db: Session = Depends(get_db)):
    # 1. ¿El usuario ya existe? (Validación de integridad)
    usuario_existente = db.query(UserDB).filter(UserDB.username == usuario.username).first()
    if usuario_existente:
        raise HTTPException(
            status_code=400, 
            detail="Este nombre de usuario ya está registrado en AgroTech"
        )

    # 2. Convertimos la clave en un Hash (Seguridad)
    clave_hasheada = obtener_password_hash(usuario.password)

    # 3. Creamos la instancia para la DB
    nuevo_usuario = UserDB(
        username=usuario.username,
        hashed_password=clave_hasheada
    )

    # 4. Impactamos en la base de datos
    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)

    # FastAPI usa UserResponse para no devolver la contraseña en el JSON
    return nuevo_usuario

# --- RUTAS DE TOKENS ---
@app.post("/token/", response_model=Token)
def login_para_obtener_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: Session = Depends(get_db)
    ):
    # 1. Buscar al usuario en la base de datos
    usuario = db.query(UserDB).filter(UserDB.username == form_data.username).first()
    
    # 2. Verificar existencia y contraseña
    # Usamos la función de auth.py para comparar el texto plano con el hash
    if not usuario or not verificar_password(form_data.password, usuario.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 3. Si todo está bien, crear el token
    # Guardamos el username dentro del "sub" (subject) del token
    access_token = crear_access_token(data={"sub": usuario.username})
    
    return {"access_token": access_token, "token_type": "bearer"}

# --- RUTAS DE LECTURAS ---

@app.post("/lecturas/", response_model=LecturaResponse)
def crear_lectura(
    lectura: LecturaCreate, 
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(get_current_user) # Solo usuarios logueados
):
    # Verificamos que el sensor exista antes de pegarle la lectura
    sensor = db.query(SensorDB).filter(SensorDB.id == lectura.sensor_id).first()
    if not sensor:
        raise HTTPException(status_code=404, detail="El sensor no existe")

    nueva_lectura = LecturaDB(**lectura.model_dump())
    db.add(nueva_lectura)
    db.commit()
    db.refresh(nueva_lectura)
    return nueva_lectura

# 2. Obtener el historial de un sensor
@app.get("/sensores/{sensor_id}/lecturas", response_model=List[LecturaResponse])
def obtener_historial_sensor(
    sensor_id: int, 
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(get_current_user)
):
    lecturas = db.query(LecturaDB).filter(LecturaDB.sensor_id == sensor_id).all()
    return lecturas