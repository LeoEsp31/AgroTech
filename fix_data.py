from backend.database import SessionLocal
from sqlalchemy import text

def arreglar_datos():
    db = SessionLocal()
    try:
        print("🚑 Iniciando reparación de datos...")
        
        # 1. Corregir 'humedad' -> 'Humedad'
        # Usamos SQL directo para ser más rápidos y efectivos
        filas_h = db.execute(text("UPDATE sensores SET tipo = 'Humedad' WHERE tipo = 'humedad'"))
        print(f"✅ Se corrigieron {filas_h.rowcount} sensores de Humedad.")

        # 2. Corregir 'temperatura' -> 'Temperatura'
        filas_t = db.execute(text("UPDATE sensores SET tipo = 'Temperatura' WHERE tipo = 'temperatura'"))
        print(f"✅ Se corrigieron {filas_t.rowcount} sensores de Temperatura.")
        
        db.commit()
        print("🎉 Base de datos actualizada y lista para el Enum estricto.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    arreglar_datos()