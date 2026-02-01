# 🍇 AgroTech San Juan - API de Monitoreo Agrícola

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791)
![Docker](https://img.shields.io/badge/Docker-Enabled-2496ED)
![Tests](https://img.shields.io/badge/Tests-Pytest-yellow)

Sistema Backend para el monitoreo IoT de cultivos intensivos (vid y olivo) en la provincia de San Juan, Argentina. Esta API REST permite gestionar sectores, sensores y lecturas en tiempo real, evaluando automáticamente condiciones críticas para optimizar el riego y prevenir heladas.

## 🚀 Características y Optimizaciones

Este proyecto va más allá de un CRUD básico. Se han implementado patrones de diseño y optimizaciones de rendimiento:

* **Arquitectura Modular:** Refactorización completa de monolito a **APIRouter**. Separación estricta de responsabilidades entre Rutas, Lógica de Negocio y Acceso a Datos.
* **Optimización de Consultas (Performance):** Solución al problema de *N+1 Queries* utilizando **Eager Loading** (`joinedload`) y **Bulk Fetching** en SQLAlchemy. Reducción drástica de latencia en endpoints de monitoreo masivo.
* **Inyección de Dependencias:** Gestión de autenticación y sesiones de base de datos mediante el sistema de inyección de dependencias de FastAPI (`Depends`), desacoplando la lógica de seguridad.
* **Lógica de Negocio Aislada:** El núcleo de decisiones (alertas de riego/helada) reside en módulos puros, permitiendo testeo unitario sin depender de la base de datos.
* **Seguridad:** Autenticación JWT (JSON Web Tokens) con hashing de contraseñas (Bcrypt).

## 🛠️ Stack Tecnológico

* **Lenguaje:** Python 3.10+
* **Framework Web:** FastAPI
* **ORM:** SQLAlchemy
* **Base de Datos:** PostgreSQL
* **Validación:** Pydantic V2
* **DevOps:** Docker & Docker Compose
* **Testing:** Pytest & Httpx

## 📂 Estructura del Proyecto (Arquitectura)

El código sigue una estructura limpia y escalable:

```text
agrotech-sanjuan/
├── backend/
│   ├── routers/        # CONTROLADORES: Endpoints organizados por dominio
│   │   ├── usuarios.py   # Auth y Registro
│   │   ├── sectores.py   # Gestión de la finca
│   │   ├── sensores.py   # Gestión de dispositivos
│   │   └── monitoreo.py  # Dashboard y Alertas (Optimized)
│   ├── auth.py         # SEGURIDAD: Lógica criptográfica (Hash & JWT)
│   ├── dependencies.py # MIDDLEWARE: Validación de tokens e inyección de usuario
│   ├── logic.py        # DOMINIO: Reglas de negocio puras (Cálculo de alertas)
│   ├── models_db.py    # DATA: Modelos ORM (Tablas)
│   ├── models.py       # SCHEMAS: DTOs Pydantic (Request/Response)
│   ├── database.py     # INFRA: Configuración de conexión DB
│   └── main.py         # APP: Punto de entrada y configuración global
├── tests/              # Tests de Integración
├── docker-compose.yml  # Orquestación
└── requirements.txt    # Dependencias
```

## ⚙️ Instalación y Ejecución

### Opción A: Docker 🐳 (Recomendado)

Levanta la aplicación y la base de datos automáticamente:

```bash
docker-compose up --build
```

La API estará disponible en: `http://localhost:8000`

### Opción B: Ejecución Local

1.  **Instalar dependencias:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Configurar Variables:**
    Crear archivo `.env` basado en la configuración de tu DB local.

3.  **Ejecutar Servidor:**
    ```bash
    uvicorn backend.main:app --reload
    ```

4.  **Correr Tests:**
    Para verificar que la refactorización mantiene la integridad del sistema:
    ```bash
    pytest
    ```

## 📖 Documentación Automática

FastAPI genera documentación interactiva. Una vez corriendo, visita:

* **Swagger UI:** `http://127.0.0.1:8000/docs` (Para probar endpoints)
* **ReDoc:** `http://127.0.0.1:8000/redoc` (Documentación estática)

## 👤 Autor

Desarrollado como proyecto de portafolio, demostrando capacidades de ingeniería de software backend.
**Estudiante de Cs. de la Computación - UNSJ**