# Usamos una imagen liviana de Python oficial
FROM python:3.10-slim

# Evita que Python genere archivos .pyc y fuerza logs en tiempo real
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Creamos la carpeta de trabajo adentro del contenedor
WORKDIR /app

# Copiamos solo los requirements primero (para aprovechar el caché de Docker)
COPY requirements.txt .

# Instalamos las librerías
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos todo el resto del código
COPY . .

# Exponemos el puerto 8000
EXPOSE 8000

# Comando para arrancar la app
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]