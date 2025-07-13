# filepath: /home/DoctorFerpy/Documents/WRO/Dr_Ferpy_WRO/main.py
import os
import json
import face_recognition_module
import Gemini_module
import time
from gtts import gTTS
import pygame
import threading
from comand_handler import RobotCommandHandler
import pyaudio
import wave
import speech_recognition as sr

# Intenta importar el módulo de la cámara. Si no se encuentra, imprime un mensaje de error y establece camera_module a None.
try:
    import camera_module
except ImportError:
    print("Módulo de cámara no encontrado. Asegúrate de que la cámara esté conectada y el módulo instalado.")
    camera_module = None

# Configura las variables de entorno para Pygame para usar ALSA en Debian y ocultar el mensaje de soporte.
os.environ['SDL_AUDIODRIVER'] = 'alsa'  # Usa ALSA para el audio en Debian
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'  # Elimina el mensaje de soporte de pygame

def speak_text(text, lang='es', tld='com'):
    """
    Convierte texto a voz usando gTTS y lo reproduce con pygame.
    Args:
        text (str): El texto a convertir en voz.
        lang (str): El idioma para la síntesis de voz (por defecto 'es' para español).
        tld (str): El dominio de nivel superior para gTTS (por defecto 'com' para voz estándar, 'com.mx' para voz masculina en español).
    """
    tts = gTTS(text=text, lang=lang, slow=False, tld=tld)
    temp_audio_file = "temp_audio.mp3"
    tts.save(temp_audio_file)
    pygame.mixer.init()
    pygame.mixer.music.load(temp_audio_file)
    pygame.mixer.music.play()
    # Espera hasta que la reproducción de audio termine.
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)

def record_voice_wave(filename="prompt.wav", record_seconds=5, chunk=1024, fmt=pyaudio.paInt16, channels=1, rate=44100):
    """
    Graba la voz del usuario desde el micrófono USB y la guarda como un archivo WAV.
    Esta función ya no se usa en el flujo principal, pero se mantiene por si acaso.
    Args:
        filename (str): El nombre del archivo donde se guardará la grabación.
        record_seconds (int): Duración máxima de la grabación en segundos.
        chunk (int): Tamaño del fragmento de audio.
        fmt (int): Formato de audio.
        channels (int): Número de canales de audio.
        rate (int): Frecuencia de muestreo.
    Returns:
        str: El nombre del archivo de audio grabado.
    """
    audio = pyaudio.PyAudio()
    stream = audio.open(format=fmt, channels=channels, rate=rate, input=True, frames_per_buffer=chunk)
    print("Grabando comando de voz... Por favor, habla ahora.")
    frames = []
    for _ in range(0, int(rate / chunk * record_seconds)):
        data = stream.read(chunk)
        frames.append(data)
    print("Grabación finalizada.")
    stream.stop_stream()
    stream.close()
    audio.terminate()
    wf = wave.open(filename, 'wb')
    wf.setnchannels(channels)
    wf.setsampwidth(audio.get_sample_size(fmt))
    wf.setframerate(rate)
    wf.writeframes(b''.join(frames))
    wf.close()
    return filename

def audio_to_text(audio_file):
    """
    Convierte un archivo de audio a texto usando SpeechRecognition.
    Esta función ya no se usa en el flujo principal, pero se mantiene por si acaso.
    Args:
        audio_file (str): La ruta al archivo de audio.
    Returns:
        str: El texto reconocido o un mensaje de error.
    """
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_file) as source:
        audio_data = recognizer.record(source)
    try:
        text = recognizer.recognize_google(audio_data, language="es-ES")
        return text
    except sr.UnknownValueError:
        return "No se pudo entender el audio."
    except sr.RequestError as e:
        return f"Error al conectar con el servicio de reconocimiento de voz: {e}"

def listen_for_command():
    """
    Escucha continuamente en fragmentos de 1 segundo para detectar una frase de activación.
    Cuando se detecta la frase de activación ("Doctor Ferpy" o similar), comienza a grabar
    el comando completo hasta que haya 1 segundo de silencio.
    Returns:
        str: El comando de voz reconocido.
    """
    recognizer = sr.Recognizer()
    recognizer.pause_threshold = 1 # Segundos de silencio para considerar el fin de la frase
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source) # Ajusta el umbral de ruido ambiental
        print("Micrófono activo: Esperando comando de voz...")
        while True:
            try:
                # Escucha en fragmentos de 1 segundo para detectar la activación
                audio_chunk = recognizer.listen(source, phrase_time_limit=1)
                try:
                    chunk_text = recognizer.recognize_google(audio_chunk, language="es-ES").lower()
                    print(f"Escuchado: {chunk_text}")  # Muestra lo escuchado
                except sr.UnknownValueError:
                    continue # Si no se entiende el fragmento, sigue escuchando

                # Verificar si se detecta la frase de activación
                activation_phrases = ["doctor","dr", "dry","doctor f", "dr f","ferti","fermin","doctor ferpy", "dr fer", "doctor fer", "dr ferpi", "ferpi", "dr fairy", "ferpi"]
                if any(phrase in chunk_text for phrase in activation_phrases):
                    print("Frase de activación detectada. Comienza a grabar el comando completo...")
                    speak_text("Sí, dime.") # Responde al usuario para indicar que está escuchando
                    command_text = ""
                    last_audio_time = time.time() # Registra el tiempo del último audio detectado
                    # Bucle para grabar el comando completo hasta el silencio
                    while True:
                        try:
                            # Escucha fragmentos cortos; usamos timeout para detectar el silencio.
                            # phrase_time_limit es importante para evitar grabaciones excesivamente largas si no hay silencio.
                            command_audio = recognizer.listen(source, timeout=0.5, phrase_time_limit=5)
                            try:
                                part_text = recognizer.recognize_google(command_audio, language="es-ES")
                                print(f"Grabado: {part_text}")
                                command_text += " " + part_text
                                last_audio_time = time.time() # Reinicia el temporizador de silencio
                            except sr.UnknownValueError:
                                # No se entendió, pero se sigue el lazo para detectar silencio.
                                pass
                        except sr.WaitTimeoutError:
                            # Si no se obtiene audio en este fragmento (silencio), verificar cuánto tiempo ha pasado.
                            if time.time() - last_audio_time >= 1: # Si ha pasado 1 segundo de silencio
                                print("Silencio detectado. Fin del comando.")
                                break # Sale del bucle de grabación del comando
                    command_text = command_text.strip() # Elimina espacios en blanco al inicio y al final
                    print(f"Comando completo: {command_text}")
                    return command_text
            except sr.RequestError as e:
                print(f"Error con el servicio de reconocimiento de voz: {e}")
                continue # Continúa escuchando si hay un error en el servicio

def listen_for_name():
    """
    Captura el nombre del usuario sin requerir una frase de activación.
    El usuario habla, y su voz se graba hasta que se detecta 1 segundo de silencio.
    Imprime lo que se escucha. Si no se detecta un nombre, lo pide de nuevo.
    Returns:
        str: El nombre reconocido.
    """
    recognizer = sr.Recognizer()
    recognizer.pause_threshold = 1 # Segundos de silencio para considerar el fin de la frase
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source) # Ajusta el umbral de ruido ambiental
        while True:
            name_text = ""
            print("Escuchando tu nombre...")
            try:
                # Escucha hasta por 5 segundos o hasta que se detecte silencio
                audio_chunk = recognizer.listen(source, timeout=5, phrase_time_limit=5)
                try:
                    name_text = recognizer.recognize_google(audio_chunk, language="es-ES").strip()
                    print(f"Nombre capturado: {name_text}")
                    return name_text
                except sr.UnknownValueError:
                    print("No se pudo entender el audio. Por favor, intenta de nuevo.")
                    speak_text("No se entendió tu voz. Intenta de nuevo.")
            except sr.WaitTimeoutError:
                print("No se detectó ninguna voz. Por favor, intenta de nuevo.")
                speak_text("No se detectó ninguna voz. Intenta de nuevo.")

def load_patients_db(filename="patients_database.json"):
    """
    Carga la base de datos de pacientes desde un archivo JSON.
    Args:
        filename (str): El nombre del archivo de la base de datos.
    Returns:
        dict: Un diccionario con los datos de los pacientes.
    """
    if os.path.exists(filename):
        with open(filename, "r") as f:
            try:
                return json.load(f)
            except Exception as e:
                print(f"Error al cargar la base de datos de pacientes: {e}")
                return {}
    return {}

def save_patients_db(db, filename="patients_database.json"):
    """
    Guarda la base de datos de pacientes en un archivo JSON.
    Args:
        db (dict): El diccionario con los datos de los pacientes a guardar.
        filename (str): El nombre del archivo de la base de datos.
    """
    with open(filename, "w") as f:
        json.dump(db, f, indent=4)

def identify_or_register_patient(database, patients_db, image_path):
    """
    Identifica o registra a un paciente basándose en el reconocimiento facial.
    Si no se reconoce, pide el nombre para registrarlo.
    Args:
        database (dict): La base de datos de reconocimiento facial.
        patients_db (dict): La base de datos de pacientes.
        image_path (str): La ruta de la imagen para el reconocimiento facial.
    Returns:
        tuple: Una tupla que contiene (user_name, patient_data).
    """
    user_name = None
    patient_data = {}

    if camera_module:
        print("Tomando foto para reconocimiento facial...")
        camera_module.capture_and_save_image(image_path) # Captura y guarda la imagen
        detected_face = face_recognition_module.detect_face(image_path) # Detecta caras en la imagen

        if detected_face:
            candidate = face_recognition_module.identify_user(image_path, database) # Intenta identificar al usuario
            if candidate:
                user_name = candidate
                print(f"Paciente reconocido: {user_name}")
                speak_text(f"Bienvenido de nuevo, {user_name}.")
            else:
                print("Cara detectada pero no reconocida. Pidiendo nombre para registrar.")
                speak_text("Se detectó una cara, pero no está registrada. Por favor, di tu nombre para registrarte.")
                for attempt in range(2): # Intenta capturar el nombre dos veces
                    user_name_text = listen_for_name()
                    if user_name_text:
                        user_name = user_name_text.strip()
                        face_recognition_module.register_user(user_name, image_path, database) # Registra al nuevo usuario
                        print(f"Usuario {user_name} registrado exitosamente.")
                        speak_text(f"Bienvenido, {user_name}. Te he registrado en mi sistema.")
                        break
                    else:
                        print("No se pudo capturar el nombre. Intentando de nuevo.")
                        speak_text("No se pudo capturar tu nombre. Intenta de nuevo.")
                if not user_name:
                    print("Fallo al capturar el nombre después de 2 intentos. Usando nombre por defecto 'Paciente Desconocido'.")
                    user_name = "Paciente Desconocido"
                    speak_text("No pude registrar tu nombre. Te llamaré Paciente Desconocido.")
        else:
            print("No se detectó ninguna cara. Pidiendo nombre por voz.")
            speak_text("No se detectó ninguna cara. Por favor, di tu nombre.")
            for attempt in range(2): # Intenta capturar el nombre dos veces
                user_name_text = listen_for_name()
                if user_name_text:
                    user_name = user_name_text.strip()
                    # No se registra la cara si no se detectó
                    print(f"Usuario identificado por voz: {user_name}")
                    speak_text(f"Hola, {user_name}.")
                    break
                else:
                    print("No se pudo capturar el nombre. Intentando de nuevo.")
                    speak_text("No se pudo capturar tu nombre. Intenta de nuevo.")
            if not user_name:
                print("Fallo al capturar el nombre después de 2 intentos. Usando nombre por defecto 'Paciente Desconocido'.")
                user_name = "Paciente Desconocido"
                speak_text("No pude identificar tu nombre. Te llamaré Paciente Desconocido.")
    else:
        print("Módulo de cámara no disponible. Usando 'Paciente Desconocido' por defecto.")
        user_name = "Paciente Desconocido"
        speak_text("El módulo de la cámara no está disponible. Te llamaré Paciente Desconocido.")

    # Carga o inicializa los datos del paciente en la base de datos de pacientes
    if user_name in patients_db:
        patient_data = patients_db[user_name]
    else:
        patient_data = {
            'nombre': user_name,
            'edad': 'desconocida',
            'peso': 'desconocido',
            'altura': 'desconocida',
            'temperatura': 'desconocida',
            'sexo': 'desconocido',
            'comentario_importante': 'desconocido'
        }
        patients_db[user_name] = patient_data
        save_patients_db(patients_db) # Guarda la base de datos actualizada

    return user_name, patient_data


def conversation_loop(robot, patients_db):
    """
    Ejecuta el bucle de conversación principal con Gemini.
    Escucha comandos, captura una imagen de interacción,
    identifica/registra al paciente, envía el prompt a Gemini,
    procesa la respuesta y actualiza los datos del paciente.
    Args:
        robot (RobotCommandHandler): Instancia del manejador de comandos del robot.
        patients_db (dict): La base de datos de pacientes.
    """
    conversation_messages = [] # Inicializa el historial de mensajes de la conversación
    while True:
        # Esperar el comando de voz del usuario
        user_prompt_text = listen_for_command()
        print(f"Comando reconocido: {user_prompt_text}")

        # Tomar foto para reconocimiento facial y contexto espacial
        interaction_image_path = "interaction.jpg"
        user_name, patient_data = identify_or_register_patient(
            face_recognition_module.load_database(), patients_db, interaction_image_path
        )
        robot.patient_data = patient_data # Asegura que los datos del paciente estén actualizados en el robot

        print("Enviando tu prompt a Gemini...")
        response_text, conversation_messages = Gemini_module.gemini_interaction(
            conversation_messages, user_prompt_text, interaction_image_path, robot.patient_data
        )
        print("Gemini responde:", response_text)
        print("Procesando la respuesta intercalando comandos y texto:")
        robot.execute_response_segments(response_text) # Ejecuta comandos y reproduce texto de la respuesta de Gemini

        # Actualiza los datos del paciente en la base de datos y guarda los cambios
        patients_db[user_name] = robot.patient_data
        save_patients_db(patients_db)


def main():
    """
    Función principal para iniciar el robot médico.
    Carga las bases de datos, inicializa el manejador de comandos del robot
    y comienza el bucle de conversación.
    """
    # Carga la base de datos de reconocimiento facial y la base de datos de pacientes
    database = face_recognition_module.load_database()
    patients_db = load_patients_db()

    # Inicializa el manejador de comandos del robot
    robot = RobotCommandHandler()

    # Inicia el bucle de conversación con Gemini
    conversation_loop(robot, patients_db)


if __name__ == '__main__':
    main()
