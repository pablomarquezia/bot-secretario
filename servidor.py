import os
from fastapi import FastAPI, Form, Response, Request
from twilio.rest import Client
from db import inicializar, guardar_mensaje, obtener_historial, guardar_turno, turnos_manana, marcar_recordatorio, guardar_alerta, alerta_pendiente, marcar_alerta_respondida
from bot import procesar

app = FastAPI()

TWILIO_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP = os.getenv("TWILIO_WHATSAPP")
BARBERO_PHONE = os.getenv("BARBERO_PHONE")
twilio_client = Client(TWILIO_SID, TWILIO_TOKEN) if TWILIO_SID and TWILIO_TOKEN else None


def enviar_whatsapp(destino: str, texto: str):
    if twilio_client and TWILIO_WHATSAPP:
        twilio_client.messages.create(
            from_=TWILIO_WHATSAPP, body=texto, to=destino
        )


@app.on_event("startup")
def startup():
    inicializar()

@app.get("/")
def root():
    return {"status": "Bot Secretario operativo"}

@app.post("/webhook")
async def webhook(From: str = Form(...), Body: str = Form(...)):
    if BARBERO_PHONE and From == BARBERO_PHONE:
        pendiente = alerta_pendiente()
        if pendiente:
            enviar_whatsapp(pendiente["telefono"], f"📲 {pendiente['nombre']} (el dueño) te respondió:\n\n{Body}")
            marcar_alerta_respondida(pendiente["id"])
            guardar_mensaje(From, "bot", f"Respondido a {pendiente['telefono']}: {Body}")
            return Response(content="""<?xml version="1.0" encoding="UTF-8"?><Response><Message>✅ Mensaje reenviado al cliente.</Message></Response>""", media_type="application/xml")



    guardar_mensaje(From, "usuario", Body)

    historial = obtener_historial(From, 15)
    analisis = procesar(historial, From)
    respuesta = analisis["respuesta"]

    guardar_mensaje(From, "bot", respuesta)

    if analisis["turno_agendado"]:
        guardar_turno(From, analisis["nombre"], analisis["fecha"], analisis["hora"])

    if analisis["alerta_barbero"] and BARBERO_PHONE:
        guardar_alerta(From, analisis["nombre"], Body)
        enviar_whatsapp(
            BARBERO_PHONE,
            f"⚠️ {analisis['nombre']} ({From}) preguntó:\n\n{Body}\n\nRespondé a este mensaje y se lo reenvío.",
        )
        respuesta = "Dame un toque que le consulto al dueño y te respondo."
        guardar_mensaje(From, "bot", respuesta)

    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>{respuesta}</Message>
</Response>"""
    return Response(content=twiml, media_type="application/xml")


@app.get("/recordatorios")
def recordatorios():
    if not twilio_client:
        return {"error": "Twilio no configurado"}
    enviados = 0
    for t in turnos_manana():
        enviar_whatsapp(
            t["telefono"],
            f"Recordatorio {t['nombre']}: tenés turno mañana {t['fecha']} a las {t['hora']}. Te esperamos.",
        )
        marcar_recordatorio(t["telefono"], t["fecha"], t["hora"])
        enviados += 1
    return {"recordatorios_enviados": enviados}


META_VERIFY_TOKEN = os.getenv("META_VERIFY_TOKEN", "botsecretario123")


@app.get("/meta-webhook")
def meta_verificar(request: Request):
    if request.query_params.get("hub.mode") == "subscribe" and request.query_params.get("hub.verify_token") == META_VERIFY_TOKEN:
        return Response(content=request.query_params.get("hub.challenge", ""), media_type="text/plain")
    return Response(status_code=403)


@app.post("/meta-webhook")
async def meta_recibir(request: Request):
    body = await request.json()
    for entry in body.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            for msg in value.get("messages", []):
                From = f'whatsapp:+{msg["from"]}'
                Body = msg.get("text", {}).get("body", "")
                await webhook(From=From, Body=Body)
    return {"status": "ok"}
