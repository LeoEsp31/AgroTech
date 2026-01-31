import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Importamos tu app y la base de datos
from backend.main import app
from backend.database import Base, get_db
from backend.auth import crear_access_token

# 1. Configuración de Base de Datos en Memoria (SQLite)
# Esto crea una DB que vive solo mientras dura el test
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 2. Fixture de Base de Datos
@pytest.fixture(scope="function")
def db_session():
    """Crea las tablas, entrega una sesión y al final borra todo."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

# 3. Fixture del Cliente (El navegador falso)
@pytest.fixture(scope="function")
def client(db_session):
    """
    Sobreescribe la dependencia 'get_db' de FastAPI para usar 
    nuestra DB de prueba en lugar de la real.
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            db_session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c

# 4. Fixture de Usuario Autenticado (¡Nuevo!)
# Esto crea un usuario y te da un cliente ya logueado con token
@pytest.fixture(scope="function")
def authorized_client(client, db_session):
    # Creamos un usuario en la DB falsa
    from backend.models_db import UserDB
    user = UserDB(username="testuser", hashed_password="fakehash")
    db_session.add(user)
    db_session.commit()
    
    # Generamos un token válido para él
    token = crear_access_token(data={"sub": "testuser"})
    
    # Configuramos el cliente con el header de autorización
    client.headers = {
        **client.headers,
        "Authorization": f"Bearer {token}",
    }
    return client