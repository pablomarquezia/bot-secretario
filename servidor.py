from fastapi import FastAPI, Form, Response
from calendario import slots_libres, reservar_turno

app = FastAPI()
MEMORIA = {}

@app.get("/")
def root():
    return {"status": "Bot Secretario operativo"}

@app.post("/webhook")
async def webhook(From: str = Form(...), Body: str = Form(...)):
    if From not in MEMORIA:
        MEMORIA[From] = []

    MEMORIA[From].append({"rol": "usuario", "msg": Body})

    respuesta = f"Recibí: '{Body}'. Gracias {From}. En desarrollo..."
    MEMORIA[From].append({"rol": "bot", "msg": respuesta})

    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>{respuesta}</Message>
</Response>"""
    return Response(content=twiml, media_type="application/xml")
