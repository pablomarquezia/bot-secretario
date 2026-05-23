# Bot Secretario 🤖💈

Un bot de WhatsApp que atiende turnos automáticamente las 24 horas. El cliente escribe, el bot revisa la agenda, muestra horarios libres y reserva en Google Calendar sin intervención del dueño.

## Cómo funciona

```
Cliente escribe al WhatsApp del negocio
        ↓
Bot recibe el mensaje (Twilio)
        ↓
Analiza con IA (Groq / Llama 4) qué quiere el cliente
        ↓
Responde: muestra horarios, agenda turnos, o avisa al dueño si no entiende
        ↓
Turno agendado → se crea automáticamente en Google Calendar
        ↓
Al día siguiente → el cliente recibe un recordatorio automático
```

## Tecnología

| Componente | Qué hace |
|------------|----------|
| **Python** | Lenguaje del bot |
| **Groq + Llama 4** | IA que entiende los mensajes y extrae fecha, hora, nombre |
| **Google Calendar API** | Lee eventos (saber qué está ocupado) y escribe turnos nuevos |
| **Twilio** | Recibe y envía mensajes de WhatsApp |
| **FastAPI** | Servidor web que recibe los mensajes de Twilio |
| **Render** | Hosting 24/7 gratis del servidor |
| **SQLite** | Base de datos local para conversaciones y turnos |

## Para el dueño del negocio

1. El bot se conecta a tu Google Calendar
2. Configurás tus horarios laborales (lunes a viernes de 9 a 18, etc.)
3. Tus pacientes te escriben al WhatsApp y el bot los atiende solo
4. Los turnos aparecen automáticamente en tu calendario
5. Si alguien pregunta algo que el bot no entiende, te llega un aviso a tu WhatsApp

## Para desarrolladores

### Variables de entorno

| Variable | Default | Descripción |
|----------|---------|-------------|
| `GROQ_API_KEY` | — | API key de Groq |
| `GOOGLE_CREDENTIALS_B64` | — | Credenciales OAuth de Google en base64 |
| `GOOGLE_TOKEN_B64` | — | Token de Google Calendar en base64 |
| `TWILIO_ACCOUNT_SID` | — | SID de Twilio |
| `TWILIO_AUTH_TOKEN` | — | Token de Twilio |
| `TWILIO_WHATSAPP` | — | Número de Twilio (ej: `whatsapp:+14155238886`) |
| `BARBERO_PHONE` | — | WhatsApp del dueño para alertas |
| `NEGOCIO` | `barbería` | Tipo de negocio (cambia el prompt de la IA) |
| `INFO_NEGOCIO` | — | Info del negocio: dirección, precios, horarios, redes. Se lo contás a la IA para que responda preguntas |
| `DURACION_TURNO` | `60` | Minutos por turno |
| `HORA_APERTURA` | `8` | Hora de apertura |
| `HORA_CIERRE` | `18` | Hora de cierre |

### Comandos rápidos

```bash
# Servidor local
uvicorn servidor:app --reload

# Túnel público (para pruebas sin Render)
ngrok http 8000

# Autenticar calendario de un cliente
python auth_demo.py credenciales_cliente.json

# Recordatorios manuales
curl https://tu-url.onrender.com/recordatorios
```

### Deploy para un nuevo cliente

1. Cliente crea un Gmail
2. Generar credenciales OAuth + token
3. Crear Web Service en Render
4. Configurar variables de entorno
5. Apuntar webhook de Twilio a la URL de Render
