import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

try:
	completion = client.chat.completions.create(
		model="llama-3.1-8b-instant",
		messages=[
			{
				"role": "user",
				"content": "Hola! Decime en una sola grase corta que estas corriendo con exito desde Groq."
			}
		],
	)

	print("\nRespuesta de la IA: ")
	print(completion.choices[0].message.content)

except Exception as e:
	print(f"\nError al conectar con Groq: {e}")
