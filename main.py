import os
import json
from datetime import date
from dotenv import load_dotenv
from groq import Groq
from pydantic import BaseModel, Field

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
HOY = date.today().isoformat()

# 1. Molde estricto de Pydantic
class AnalisisMensaje(BaseModel):
    intencion: str = Field(description="Valores posibles de forma estricta: 'saludar', 'agendar_turno', 'cancelar_turno' o 'fuera_de_tema'")
    fecha: str = Field(description="Fecha del turno solicitado en formato YYYY-MM-DD. Si no se especifica, poner 'no_aplica'")
    hora: str = Field(description="Hora del turno en formato HH:MM. Si no se especifica, poner 'no_aplica'")
    nombre_cliente: str = Field(description="Nombre de pila del cliente. Si no lo dice, poner 'desconocido'")
    respuesta_whatsapp: str = Field(description="Mensaje de respuesta amigable y corto para el cliente usando el voseo de Santa Fe.")

SYSTEM_PROMPT = f"""
Hoy es {HOY}.

Eres el secretario virtual de una barberia en Santa Fe. Tu único trabajo es gestionar la agenda.
Debes analizar el mensaje del usuario y responder OBLIGATORIAMENTE con un objeto estructurado en formato JSON que cumpla de forma estricta con las siguientes llaves:
- intencion
- fecha
- hora
- nombre_cliente
- respuesta_whatsapp

No inventes campos como 'apellido' o 'telefono'. Usa el 'vos' de forma natural en 'respuesta_whatsapp'. Si te hablan de otra cosa, pon intencion 'fuera_de_tema' y rechaza amablemente.
"""

def analizar_mensaje_cliente(mensaje_usuario):
    try:
        completion = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": mensaje_usuario}
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "AnalisisMensaje",
                    "schema": AnalisisMensaje.model_json_schema()
                }
            }
        )
        
        respuesta_cruda = completion.choices[0].message.content
        datos_parseados = json.loads(respuesta_cruda)
        return datos_parseados
        
    except Exception as e:
        # En caso de error, devolvemos un diccionario con la estructura básica para que no rompa el bucle
        return {
            "intencion": "error",
            "fecha": "no_aplica",
            "hora": "no_aplica",
            "nombre_cliente": "desconocido",
            "respuesta_whatsapp": f"Error interno en el servidor: {e}"
        }

# =====================================================================
# MOCKUP INTERACTIVO EN CONSOLA (Tarea 1.4)
# =====================================================================

print("=" * 60)
print("📱 SIMULADOR DE WHATSAPP - BOT SECRETARIO".center(60))
print("=" * 60)
print("Instrucciones: Chatea como si fueras un cliente de la barberia.")
print("Escribí 'salir' para cerrar el simulador.\n")

while True:
    user_input = input("👤 Cliente: ")
    if user_input.lower() == "salir":
        print("\n👋 Saliendo del simulador. ¡Buen progreso!")
        break
        
    if not user_input.strip():
        continue

    print("⏳ [Procesando con Llama 4 Scout en Groq]...")
    resultado = analizar_mensaje_cliente(user_input)
    
    # Usamos .get() con valores por defecto para evitar que Python tire error si falta una llave
    respuesta_bot = resultado.get("respuesta_whatsapp", "Disculpame, se me cruzaron los cables. ¿Me repetís?")
    
    print("\n" + "-" * 40)
    print(f"🤖 Bot Secretario: {respuesta_bot}")
    print("-" * 40)
    
    print("⚙️ [DATOS DE BACKGROUND PARA PYTHON]")
    print(f"   🔹 Intención detectada:  {resultado.get('intencion')}")
    print(f"   🔹 Fecha extraída:     {resultado.get('fecha')}")
    print(f"   🔹 Hora extraída:      {resultado.get('hora')}")
    print(f"   🔹 Nombre cliente:     {resultado.get('nombre_cliente')}")
    print("=" * 60 + "\n")