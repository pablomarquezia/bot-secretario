import os
import json
from datetime import date, datetime
from dotenv import load_dotenv
from groq import Groq
from pydantic import BaseModel, Field
from calendario import slots_libres, reservar_turno

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
HOY = date.today().isoformat()


class AnalisisMensaje(BaseModel):
    intencion: str = Field(description="Valores: 'saludar', 'agendar_turno', 'cancelar_turno', 'consultar_disponibilidad' o 'fuera_de_tema'")
    fecha: str = Field(description="YYYY-MM-DD o 'no_aplica'")
    hora: str = Field(description="HH:MM o 'no_aplica'")
    nombre_cliente: str = Field(description="Nombre del cliente o 'desconocido'")
    respuesta_whatsapp: str = Field(description="Respuesta amigable usando voseo santafesino, menos de 200 caracteres")


SYSTEM_PROMPT = f"""
Hoy es {HOY}. Sos el secretario virtual de una barbería en Santa Fe.
Analizá el mensaje y respondé con JSON estructurado.

Reglas:
- Si te piden horarios disponibles, decí que consultes de nuevo para revisar la agenda.
- Si te piden agendar un turno con fecha y hora específica, confirmá el turno.
- Si saludan, responded amablemente.
- Si hablan de otra cosa, poné intención 'fuera_de_tema'.
- Usá 'vos' natural tipo santafesino.
- No des diagnósticos ni consejos médicos.
"""


def procesar(historial: list) -> dict:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for msg in historial:
        role = "user" if msg["rol"] == "usuario" else "assistant"
        messages.append({"role": role, "content": msg["msg"]})

    try:
        completion = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=messages,
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "AnalisisMensaje",
                    "schema": AnalisisMensaje.model_json_schema()
                }
            }
        )
        data = json.loads(completion.choices[0].message.content)
    except Exception as e:
        data = {
            "intencion": "error",
            "fecha": "no_aplica",
            "hora": "no_aplica",
            "nombre_cliente": "desconocido",
            "respuesta_whatsapp": "Disculpame, tuve un problema interno. ¿Me repetís?"
        }

    if data["intencion"] == "agendar_turno" and data["fecha"] != "no_aplica" and data["hora"] != "no_aplica":
        link = reservar_turno(data["fecha"], data["hora"], data["nombre_cliente"], "vía WhatsApp")
        data["respuesta_whatsapp"] += f" Te confirmo el turno para el {data['fecha']} a las {data['hora']}."

    if data["intencion"] == "consultar_disponibilidad":
        libres = slots_libres()
        if libres:
            dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
            meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
            dts = [datetime.fromisoformat(s) for s in libres]
            grupos = {}
            for dt in dts:
                clave = dt.date()
                grupos.setdefault(clave, []).append(dt)
            lineas = []
            for fecha, slots in grupos.items():
                slots.sort()
                inicio = slots[0]
                fin = slots[0]
                for s in slots[1:]:
                    if s.hour == fin.hour + 1:
                        fin = s
                    else:
                        lineas.append(f"{dias[inicio.weekday()]} {inicio.day} de {meses[inicio.month-1]} de {inicio.hour:02d}:{inicio.minute:02d} a {fin.hour + 1:02d}:00")
                        inicio = s
                        fin = s
                lineas.append(f"{dias[inicio.weekday()]} {inicio.day} de {meses[inicio.month-1]} de {inicio.hour:02d}:{inicio.minute:02d} a {fin.hour + 1:02d}:00")
            data["respuesta_whatsapp"] = "Horarios libres:\n" + "\n".join(lineas)
        else:
            data["respuesta_whatsapp"] = "No tengo horarios libres esta semana, disculpame."

    return data
