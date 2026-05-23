import sqlite3
import json

DB_FILE = "conversaciones.db"

def _conectar():
    return sqlite3.connect(DB_FILE)

def inicializar():
    with _conectar() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS conversaciones (
                telefono TEXT NOT NULL,
                rol TEXT NOT NULL,
                mensaje TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

def guardar_mensaje(telefono: str, rol: str, mensaje: str):
    with _conectar() as conn:
        conn.execute(
            "INSERT INTO conversaciones (telefono, rol, mensaje) VALUES (?, ?, ?)",
            (telefono, rol, mensaje),
        )

def obtener_historial(telefono: str) -> list[dict]:
    with _conectar() as conn:
        rows = conn.execute(
            "SELECT rol, mensaje FROM conversaciones WHERE telefono = ? ORDER BY timestamp",
            (telefono,),
        ).fetchall()
    return [{"rol": r, "msg": m} for r, m in rows]
