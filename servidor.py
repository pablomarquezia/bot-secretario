import os
from fastapi import FastAPI, Form, Response, Request
from twilio.rest import Client
from db import inicializar, guardar_mensaje, obtener_historial, teléfonos_con_chats, guardar_turno, turnos_manana, marcar_recordatorio, guardar_alerta, alerta_pendiente, marcar_alerta_respondida, obtener_config, guardar_config
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
            return Response(content="""<?xml version="1.0" encoding="UTF-8"?><Response><Message><![CDATA[✅ Mensaje reenviado al cliente.]]></Message></Response>""", media_type="text/xml")



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
    <Message><![CDATA[{respuesta}]]></Message>
</Response>"""
    return Response(content=twiml, media_type="text/xml")


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
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "")


@app.get("/admin/chats")
def admin_chats(token: str = ""):
    if not ADMIN_TOKEN or token != ADMIN_TOKEN:
        return Response(status_code=401)
    teléfonos = teléfonos_con_chats()
    html = "<h1>Chats</h1><p><a href='/admin/info?token=" + token + "'>Editar info del negocio</a></p>"
    for tel in teléfonos:
        msgs = obtener_historial(tel, 50)
        html += f"<details><summary><b>{tel}</b> ({len(msgs)} msgs)</summary>"
        for m in msgs:
            color = "#2ecc71" if m["rol"] == "bot" else "#3498db"
            html += f"<p><b style='color:{color}'>{m['rol']}:</b> {m['msg']}</p>"
        html += "</details><hr>"
    return Response(content=html, media_type="text/html")


@app.get("/admin/info")
def admin_info(token: str = ""):
    if not ADMIN_TOKEN or token != ADMIN_TOKEN:
        return Response(status_code=401)
    valor = obtener_config("info_negocio")
    html = f"""<h1>Info del negocio</h1>
<form method='post'>
<textarea name='info' rows='6' cols='60'>{valor}</textarea><br>
<input type='hidden' name='token' value='{token}'>
<button type='submit'>Guardar</button>
</form>
<p><a href='/admin/chats?token={token}'>← Volver a chats</a></p>"""
    return Response(content=html, media_type="text/html")


@app.post("/admin/info")
async def admin_info_post(request: Request):
    form = await request.form()
    token = form.get("token", "")
    if not ADMIN_TOKEN or token != ADMIN_TOKEN:
        return Response(status_code=401)
    guardar_config("info_negocio", form.get("info", ""))
    return Response(content="<h1>Guardado ✅</h1><p><a href='/admin/info?token=" + token + "'>Volver</a></p>", media_type="text/html")


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
