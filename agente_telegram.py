from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import asyncio
import re
import openai
import os
from dotenv import load_dotenv

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

# ID de tu asistente personalizado
ASSISTANT_ID = os.getenv("ASSISTANT_ID")
api_key = os.getenv("API_KEY")
client = openai.Client(api_key=api_key)
# Función para interactuar con el asistente de OpenAI
def generar_respuesta_asistente(pregunta: str):
    try:
        # Crear un hilo de conversación
        thread = client.beta.threads.create()

        # Enviar el mensaje del usuario al hilo
        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=pregunta
        )

        # Iniciar una ejecución (run) para que el asistente procese el mensaje
        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=ASSISTANT_ID
        )

        # Esperar a que el asistente termine de procesar
        while run.status != "completed":
            run = client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            )

        # Obtener los mensajes del hilo
        messages = client.beta.threads.messages.list(thread_id=thread.id)
        for message in messages.data:
            if message.role == "assistant":
                return message.content
    except Exception as e:
        print(f"Error al generar la respuesta: {str(e)}")
        pass

# Función para procesar la respuesta y separar texto e imágenes
def procesar_respuesta(respuesta):
    objetos = []
    for content in respuesta:
        if content.type == "text":
            texto = content.text.value
            # Expresión regular para encontrar URLs de imágenes de Google Drive
            patron_imagen = r"!\[.*?\]\((https://drive\.google\.com/uc\?export=view&id=.*?)\)"
            # Dividir el texto en partes usando las URLs de imágenes como separadores
            partes = re.split(patron_imagen, texto)
            # Iterar sobre las partes y agregarlas a la lista de objetos
            for i in range(0, len(partes), 2):
                texto_parte = partes[i].strip()
                if texto_parte:
                    objetos.append({"value": texto_parte, "type": "text"})
                if i + 1 < len(partes):
                    imagen_url = partes[i + 1]
                    objetos.append({"value": imagen_url, "type": "image"})
    return objetos

# Función para manejar los mensajes entrantes
async def manejar_mensaje(update: Update, context: CallbackContext):
    print(f"Mensaje recibido: {update.message.text}")  # Depuración
    pregunta = update.message.text  # Obtener el texto del mensaje
    respuesta = generar_respuesta_asistente(pregunta)  # Generar respuesta con el asistente
    print(f"Respuesta generada: {respuesta}")  # Depuración

    # Procesar la respuesta para separar texto e imágenes
    objetos = procesar_respuesta(respuesta)

    # Enviar cada objeto según su tipo
    for obj in objetos:
        if obj["type"] == "text":
            print(f"Objeto texto mensaje {obj['value']}")	
            await update.message.reply_text(obj["value"])
        elif obj["type"] == "image":
            print(f"Objeto imagen mensaje {obj['value']}")	
            await update.message.reply_photo(obj["value"])

# Función para manejar el comando /start
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("¡Hola! Soy tu asistente de IA. Envíame tus preguntas.")

# Configurar el bot
def main():
    # Reemplaza 'TU_TOKEN' con el token que te dio @BotFather
    token = "8166547609:AAEXfHrxSz9K0TDEac4MMarGi6k5V9NpIIw"
    # Crear la aplicación
    application = Application.builder().token(token).build()

    # Registrar manejadores para comandos y mensajes
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, manejar_mensaje))

    # Iniciar el bot
    application.run_polling()

if __name__ == "__main__":
    main()
