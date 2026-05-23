# Bot Secretario — Estado del Proyecto

## Stack
- Python 3 + Groq API (Llama 4 Scout)
- Pydantic para structured outputs
- Prompt con voseo santafesino

## Fase 1: Motor Local e IA ✅ COMPLETADA
- [x] 1.1 Entorno configurado (venv + .env + Groq)
- [x] 1.2 System Prompt hermético
- [x] 1.3 Structured Outputs con Pydantic (`AnalisisMensaje`)
- [x] 1.4 Mockup interactivo de consola

## Fase 2: Google Calendar ⏭️ SIGUIENTE
- 2.1 Alta en Google Cloud Console
- 2.2 Flujo OAuth + token.json
- 2.3 Algoritmo de slots libres
- 2.4 Función de reserva de turnos

## Archivos clave
- `main.py` — entry point con el mockup
- `test_groq.py` — prueba de conexión
- `.env` — API key de Groq

## Pendiente técnico
- Agregar `.gitignore` cuando se inicialice git
- Rotar API key antes de subir a GitHub
