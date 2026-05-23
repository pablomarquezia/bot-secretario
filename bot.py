import os
import json
from datetime import date, datetime
from dotenv import load_dotenv
from groq import Groq
from pydantic import BaseModel, Field
from calendario import slots_libres, slot_libre, reservar_turno, cancelar_turno, obtener_service
from config import NEGOCIO, INFO_NEGOCIO

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
HOY = date.today().isoformat()

DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
MESES = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]


class AnalisisMensaje(BaseModel):
    intencion: str = Field(description="Valores: 'saludar', 'agendar_turno', 'cancelar_turno', 'consultar_disponibilidad' o 'fuera_de_tema'")
    fecha: str = Field(description="YYYY-MM-DD o 'no_aplica'")
    hora: str = Field(description="HH:MM o 'no_aplica'")
    nombre_cliente: str = Field(description="Nombre del cliente o 'desconocido'")
    respuesta_whatsapp: str = Field(description="Respuesta amigable usando voseo santafesino, menos de 200 caracteres")


SYSTEM_PROMPT = f"""
Hoy es {HOY}. Sos el secretario virtual de una {NEGOCIO} en Santa Fe.
{('Información del negocio: ' + INFO_NEGOCIO) if INFO_NEGOCIO else ''}

Analizá el mensaje y respondé JSON con estas claves exactas:
- intencion: elegí UNA de estas: 'saludar', 'consultar_disponibilidad', 'agendar_turno', 'cancelar_turno', o 'fuera_de_tema'
- fecha: extraé la fecha que pida (YYYY-MM-DD). Si no menciona, poné 'no_aplica'.
- hora: extraé la hora que pida (HH:MM). Si no menciona, poné 'no_aplica'.
- nombre_cliente: el nombre de quien escribe. Si no lo dice, poné 'desconocido'.
- respuesta_whatsapp: respondé corto, amigable, usando 'vos' santafesino. Máximo 200 caracteres.

Como funcionan las intenciones:
- 'saludar': si te saludan, saludá amablemente y ofrete para ayudar.
- 'consultar_disponibilidad': si preguntan por horarios libres, precios, dirección, horarios del negocio, o alguna info general. Respondé algo como "Dame un toque y reviso la agenda" o respondé con la info si la tenés.
- 'agendar_turno': si piden turno con fecha y hora específica. Si no dan fecha, hora o nombre, igual poné esta intención y pedí los datos que falten en la respuesta.
- 'cancelar_turno': si quieren cancelar un turno existente. Necesitás fecha, hora y nombre. Si falta algún dato, pedilo.
- 'fuera_de_tema': cualquier cosa que no sea de agendar, cancelar o consultar turnos. Rechazá amablemente y decí que solo gestionás turnos.
"""


def _formatear_libres(libres: list) -> str:
    dts = [datetime.fromisoformat(s) for s in libres]
    grupos = {}
    for dt in dts:
        grupos.setdefault(dt.date(), []).append(dt)
    lineas = []
    for fecha, slots in grupos.items():
        slots.sort()
        inicio = slots[0]
        fin = slots[0]
        for s in slots[1:]:
            if s.hour == fin.hour + 1:
                fin = s
            else:
                lineas.append(f"{DIAS[inicio.weekday()]} {inicio.day} de {MESES[inicio.month-1]} de {inicio.hour:02d}:{inicio.minute:02d} a {fin.hour + 1:02d}:00")
                inicio = s
                fin = s
        lineas.append(f"{DIAS[inicio.weekday()]} {inicio.day} de {MESES[inicio.month-1]} de {inicio.hour:02d}:{inicio.minute:02d} a {fin.hour + 1:02d}:00")
    return "Horarios libres:\n" + "\n".join(lineas)


def procesar(historial: list, telefono_cliente: str = "") -> dict:
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
    except Exception:
        data = {
            "intencion": "error",
            "fecha": "no_aplica",
            "hora": "no_aplica",
            "nombre_cliente": "desconocido",
            "respuesta_whatsapp": "Disculpame, tuve un problema interno. ¿Me repetís?"
        }

    resultado = {
        "respuesta": data["respuesta_whatsapp"],
        "intencion": data["intencion"],
        "fecha": data.get("fecha", "no_aplica"),
        "hora": data.get("hora", "no_aplica"),
        "nombre": data.get("nombre_cliente", "desconocido"),
        "alerta_barbero": False,
        "turno_agendado": False,
    }

    service = obtener_service()

    if data["intencion"] == "agendar_turno" and data["fecha"] != "no_aplica" and data["hora"] != "no_aplica":
        if data["nombre_cliente"] == "desconocido":
            resultado["respuesta"] = "Decime tu nombre y te agendo el turno."
        elif slot_libre(service, data["fecha"], data["hora"]):
            reservar_turno(data["fecha"], data["hora"], data["nombre_cliente"], telefono_cliente)
            resultado["respuesta"] = f"Listo {data['nombre_cliente']}, te confirmo el turno para el {data['fecha']} a las {data['hora']}."
            resultado["turno_agendado"] = True
        else:
            resultado["respuesta"] = "Ese horario ya no está disponible, perdón. ¿Querés que te muestre los libres?"

    if data["intencion"] == "cancelar_turno":
        if data["fecha"] != "no_aplica" and data["hora"] != "no_aplica" and data["nombre_cliente"] != "desconocido":
            if cancelar_turno(data["fecha"], data["hora"], data["nombre_cliente"]):
                resultado["respuesta"] = f"Listo {data['nombre_cliente']}, cancelé tu turno del {data['fecha']} a las {data['hora']}."
            else:
                resultado["respuesta"] = "No encontré un turno a tu nombre en esa fecha y horario."
        else:
            resultado["respuesta"] = "Decime fecha, hora y tu nombre y te cancelo el turno."

    if data["intencion"] == "consultar_disponibilidad":
        libres = slots_libres(service)
        if libres:
            resultado["respuesta"] = _formatear_libres(libres)
        else:
            resultado["respuesta"] = "No tengo horarios libres esta semana, disculpame."

    if data["intencion"] in ("fuera_de_tema", "error"):
        resultado["alerta_barbero"] = True

    return resultado
