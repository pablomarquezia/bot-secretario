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
    inicializar_turnos()
    inicializar_alertas()

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


def inicializar_turnos():
    with _conectar() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS turnos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telefono_cliente TEXT NOT NULL,
                nombre TEXT NOT NULL,
                fecha TEXT NOT NULL,
                hora TEXT NOT NULL,
                recordatorio_enviado INTEGER DEFAULT 0
            )
        """)

def guardar_turno(telefono: str, nombre: str, fecha: str, hora: str):
    with _conectar() as conn:
        conn.execute(
            "INSERT INTO turnos (telefono_cliente, nombre, fecha, hora) VALUES (?, ?, ?, ?)",
            (telefono, nombre, fecha, hora),
        )

def turnos_manana() -> list[dict]:
    from datetime import date, timedelta
    manana = (date.today() + timedelta(days=1)).isoformat()
    with _conectar() as conn:
        rows = conn.execute(
            "SELECT telefono_cliente, nombre, fecha, hora FROM turnos WHERE fecha = ? AND recordatorio_enviado = 0",
            (manana,),
        ).fetchall()
    return [{"telefono": r[0], "nombre": r[1], "fecha": r[2], "hora": r[3]} for r in rows]

def marcar_recordatorio(telefono: str, fecha: str, hora: str):
    with _conectar() as conn:
        conn.execute(
            "UPDATE turnos SET recordatorio_enviado = 1 WHERE telefono_cliente = ? AND fecha = ? AND hora = ?",
            (telefono, fecha, hora),
        )


def inicializar_alertas():
    with _conectar() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS alertas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telefono_cliente TEXT NOT NULL,
                nombre_cliente TEXT DEFAULT '',
                mensaje_cliente TEXT NOT NULL,
                respondida INTEGER DEFAULT 0,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

def guardar_alerta(telefono: str, nombre: str, mensaje: str):
    with _conectar() as conn:
        conn.execute(
            "INSERT INTO alertas (telefono_cliente, nombre_cliente, mensaje_cliente) VALUES (?, ?, ?)",
            (telefono, nombre, mensaje),
        )

def alerta_pendiente() -> dict | None:
    with _conectar() as conn:
        row = conn.execute(
            "SELECT id, telefono_cliente, nombre_cliente, mensaje_cliente FROM alertas WHERE respondida = 0 ORDER BY timestamp LIMIT 1"
        ).fetchone()
    if row:
        return {"id": row[0], "telefono": row[1], "nombre": row[2], "mensaje": row[3]}
    return None

def marcar_alerta_respondida(alerta_id: int):
    with _conectar() as conn:
        conn.execute("UPDATE alertas SET respondida = 1 WHERE id = ?", (alerta_id,))
