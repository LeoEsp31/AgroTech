from typing import List


def evaluar_estado_sector(humedad_actual: int, humedad_minima: int) -> dict:
    """
    Compara la humedad actual con el umbral mínimo y devuelve 
    un estado y una recomendación.
    """
    necesita_riego = humedad_actual < humedad_minima
    return {
        "alerta": necesita_riego,
        "estado": "CRÍTICO" if necesita_riego else "ÓPTIMO",
        "accion": "Activar riego" if necesita_riego else "Mantener apagado"
    }
    
def calcular_promedio(lecturas: List[int]) -> float:
    if not lecturas:
        return 0.0
    return sum(lecturas) / len(lecturas)    