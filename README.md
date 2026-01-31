# 🍇 AgroTech San Juan - API de Monitoreo Agrícola

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791)
![Docker](https://img.shields.io/badge/Docker-Enabled-2496ED)
![Tests](https://img.shields.io/badge/Tests-Pytest-yellow)

Sistema Backend para el monitoreo IoT de cultivos (cultivos intensivos como vid u olivos) en la provincia de San Juan, Argentina. Esta API REST permite gestionar sectores, sensores y lecturas en tiempo real, evaluando automáticamente condiciones críticas para optimizar el riego y prevenir heladas.

## 🚀 Características Principales

* **Gestión de Dispositivos:** CRUD completo de Sectores y Sensores.
* **Lógica de Negocio Inteligente:** Análisis automático de lecturas (Humedad/Temperatura) para detectar estados críticos (Sequía, Altas temperaturas).
* **Performance Optimizada:** Implementación de *Bulk Fetching* para evitar problemas de N+1 queries en listados masivos.
* **Seguridad:** Autenticación robusta mediante JWT (JSON Web Tokens) y hashing de contraseñas.
* **Arquitectura Limpia:** Separación de responsabilidades (Rutas, Lógica, Modelos, Base de Datos).
* **Testing:** Tests de integración automatizados con Pytest.

## 🛠️ Stack Tecnológico

* **Lenguaje:** Python 3.10+
* **Framework Web:** FastAPI
* **ORM:** SQLAlchemy
* **Base de Datos:** PostgreSQL
* **Validación:** Pydantic V2
* **DevOps:** Docker & Docker Compose
* **Testing:** Pytest & Httpx

## ⚙️ Instalación y Ejecución

Tienes dos formas de correr el proyecto: usando **Docker** (recomendado) o manualmente en tu entorno local.

### Opción A: Docker 🐳 (Rápido y Fácil)

Si tienes Docker instalado, levanta la aplicación y la base de datos con un solo comando:

```bash
docker-compose up --build
```

La API estará disponible en: `http://localhost:8000`

### Opción B: Instalación Manual 🔧

1.  **Clonar el repositorio:**
    ```bash
    git clone [https://github.com/TU_USUARIO/agrotech-sanjuan.git](https://github.com/TU_USUARIO/agrotech-sanjuan.git)
    cd agrotech-sanjuan
    ```

2.  **Crear y activar entorno virtual:**
    ```bash
    python -m venv venv
    # En Windows:
    .\venv\Scripts\activate
    # En Mac/Linux:
    source venv/bin/activate
    ```

3.  **Instalar dependencias:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configurar Variables de Entorno:**
    Crea un archivo `.env` en la raíz del proyecto con el siguiente contenido (ajusta los valores según tu DB local):
    ```ini
    DATABASE_URL=postgresql://postgres:tu_password@localhost:5432/agrotech_db
    SECRET_KEY=clave_secreta_super_segura
    ALGORITHM=HS256
    ACCESS_TOKEN_EXPIRE_MINUTES=30
    ```

5.  **Ejecutar el servidor:**
    ```bash
    uvicorn backend.main:app --reload
    ```

## 📖 Documentación de la API

FastAPI genera documentación interactiva automáticamente. Una vez corriendo el servidor, visita:

* **Swagger UI:** `http://127.0.0.1:8000/docs` (Para probar endpoints)
* **ReDoc:** `http://127.0.0.1:8000/redoc` (Documentación estática)

### Endpoints Clave
* `POST /token`: Login para obtener Access Token.
* `GET /sectores/`: Listado optimizado con estado de alertas calculado.
* `POST /lecturas/`: Ingreso de datos de sensores.
* `GET /monitoreo/{id}`: Análisis detallado de un sector específico.

## 🧪 Ejecutar Tests

El proyecto incluye tests de integración para asegurar que la lógica de alertas funciona correctamente.

```bash
# Ejecutar todos los tests
pytest

# Ver salida detallada
pytest -v
```

## 📂 Estructura del Proyecto

```text
agrotech-sanjuan/
├── backend/
│   ├── tests/          # Tests de integración (Pytest)
│   ├── auth.py         # Lógica de seguridad (JWT)
│   ├── database.py     # Configuración de DB
│   ├── logic.py        # Lógica de negocio pura (Alertas)
│   ├── main.py         # Entrypoint y Rutas (API)
│   ├── models.py       # Esquemas Pydantic (Request/Response)
│   └── models_db.py    # Modelos SQLAlchemy (Tablas)
├── docker-compose.yml  # Orquestación de contenedores
├── Dockerfile          # Imagen de la App
├── requirements.txt    # Dependencias
└── README.md           # Documentación
```

## 👤 Autor

Desarrollado como proyecto de portafolio y práctica de arquitectura backend.
**Estudiante de Cs. de la Computación - UNSJ**