from backend.models import TipoSensorEnum

def test_alerta_humedad_critica(authorized_client):
    """
    Escenario: 
    1. Creamos un sector con humedad mínima de 30%.
    2. Creamos un sensor de Humedad.
    3. Cargamos lecturas de 10% (muy bajas).
    4. Verificamos que el sistema grite 'CRÍTICO'.
    """
    
    # 1. Crear Sector
    response = authorized_client.post("/sectores/", json={
        "nombre": "Sector Test",
        "humedad_minima": 30, # Umbral
        "temp_maxima": 40
    })
    assert response.status_code == 201
    sector_id = response.json()["id"]

    # 2. Crear Sensor
    # Notá que usamos el Enum o el string correcto 'Humedad'
    response = authorized_client.post("/sensores/", json={
        "nombre": "Sensor Test",
        "tipo": "Humedad",
        "marca": "TestBrand",
        "modelo": "X1",
        "sector_id": sector_id
    })
    assert response.status_code == 200
    sensor_id = response.json()["id"]

    # 3. Insertar Lecturas Bajas (Simular sequía)
    # Enviamos 3 lecturas de valor 10
    for _ in range(3):
        authorized_client.post("/lecturas/", json={
            "valor": 10.0,
            "sensor_id": sensor_id
        })

    # 4. CONSULTAR EL ORÁCULO (GET /sectores/)
    response = authorized_client.get("/sectores/")
    data = response.json()
    
    # --- MOMENTO DE LA VERDAD (ASSERTIONS) ---
    assert response.status_code == 200
    sector_data = data[0] # El primer sector
    
    print(f"Estado recibido: {sector_data['estado']}") # Para ver en consola si falla
    
    # Verificamos que el estado contenga la palabra clave
    assert "CRÍTICO" in sector_data["estado"]
    assert "Baja Humedad" in sector_data["estado"]
    # Verificamos que el promedio sea correcto (10.0)
    assert "(10.0%)" in sector_data["estado"]