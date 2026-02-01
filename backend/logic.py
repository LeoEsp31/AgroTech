from typing import List, Dict, Optional

def evaluar_sensor(tipo: str, valor: float, humedad_min: float, temp_max: float) -> Optional[str]:
    """
    Devuelve el tipo de alerta si el valor viola los umbrales.
    Si está todo OK, devuelve None.
    """
    tipo_normalizado = tipo.lower()
    
    if tipo_normalizado == "humedad" and valor < humedad_min:
        return "Baja Humedad (Sequía)"
    
    if tipo_normalizado == "temperatura":
        if valor > temp_max:
            return "Alta Temperatura"
        if valor < 2.0: 
            return "Peligro de Helada"
        
    return None

def generar_resumen_estado(alertas: Dict[str, List[float]]) -> str:
    """
    Toma un diccionario de alertas y construye el string final.
    """
    if not alertas:
        return "OK"
        
    resumen_alertas = []
    for tipo, valores in alertas.items():
        promedio_final = sum(valores) / len(valores)
        unidad = "%" if "Humedad" in tipo else "°C"
        resumen_alertas.append(f"{tipo} ({promedio_final:.1f}{unidad})")
    
    return f"CRÍTICO - {', '.join(resumen_alertas)}"