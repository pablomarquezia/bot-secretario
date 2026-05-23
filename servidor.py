from fastapi import FastAPI, Form, Response
from calendario import slots_libres, reservar_turno
from db import inicializar, guardar_mensaje, obtener_historial
from bot import procesar

app = FastAPI()

@app.on_event("startup")
def startup():
    inicializar()

@app.get("/")
def root():
    return {"status": "Bot Secretario operativo"}

@app.post("/webhook")
async def webhook(From: str = Form(...), Body: str = Form(...)):
    guardar_mensaje(From, "usuario", Body)

    historial = obtener_historial(From)
    analisis = procesar(historial)
    respuesta = analisis["respuesta_whatsapp"]

    guardar_mensaje(From, "bot", respuesta)

    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>{respuesta}</Message>
</Response>"""
    return Response(content=twiml, media_type="application/xml")
