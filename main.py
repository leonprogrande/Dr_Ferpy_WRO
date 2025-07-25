# filepath: /home/DoctorFerpy/Documents/WRO/Doctor_ferpy_V9.4/main.py
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
try:
    import camera_module
except ImportError:
    print("Camera module not found. Please ensure the camera is connected and the module is installed.")
    camera_module = None

# --- Add display import ---
import display_ferpy

display_ferpy.start_display()

os.environ['SDL_AUDIODRIVER'] = 'alsa'  # Use ALSA for audio on Debian
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'  # Delete pygame support prompt

def speak_text(text, lang='es', tld='com'):
    """Convert text to speech using gTTS and play it using pygame."""
    display_ferpy.set_display_state('stationary')  # Show stationary circle when speaking
    tts = gTTS(text=text, lang=lang, slow=False, tld=tld)  # Use 'com.mx' for a male-like voice in Spanish
    temp_audio_file = "temp_audio.mp3"
    tts.save(temp_audio_file)
    pygame.mixer.init()
    pygame.mixer.music.load(temp_audio_file)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)
    display_ferpy.set_display_state('loading')  # Return to loading after speaking

def record_voice_wave(filename="prompt.wav", record_seconds=5, chunk=1024, fmt=pyaudio.paInt16, channels=1, rate=44100):
    """
    Record the user's voice from the USB microphone and save it as a WAV file.
    Returns the filename.
    """
    audio = pyaudio.PyAudio()
    stream = audio.open(format=fmt, channels=channels, rate=rate, input=True, frames_per_buffer=chunk)
    print("Recording voice prompt... Please speak now.")
    frames = []
    for _ in range(0, int(rate / chunk * record_seconds)):
        data = stream.read(chunk)
        frames.append(data)
    print("Recording finished.")
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
    """Convert audio file to text using SpeechRecognition."""
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
    Escucha continuamente en fragmentos de 1 segundo y muestra lo que se está escuchando.
    Cuando detecta el trigger ("doctor ferpi" o similar) en un fragmento, comienza a grabar el comando completo.
    La grabación continúa sin ciclos intermedios hasta que transcurre 1 segundo sin escuchar voz.
    Retorna el comando reconocido.
    """
    recognizer = sr.Recognizer()
    recognizer.pause_threshold = 1
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source)
        print("Micrófono activo: Esperando comando de voz...")
        display_ferpy.set_display_state('loading')  # Show spinning circle while listening
        while True:
            try:
                # Escucha en fragmentos de 1 segundo
                audio_chunk = recognizer.listen(source, phrase_time_limit=1)
                try:
                    chunk_text = recognizer.recognize_google(audio_chunk, language="es-ES").lower()
                    print(f"Escuchado: {chunk_text}")  # Muestra lo escuchado
                except sr.UnknownValueError:
                    continue
                # Verificar si se detecta la frase de activación
                activation_phrases = ["doctor","dr", "dry","doctor f", "dr f","ferti","fermin","doctor ferpi", "dr fer", "doctor fer", "dr ferpi", "ferpi", "dr fairy", "ferpi"]
                if any(phrase in chunk_text for phrase in activation_phrases):
                    print("Frase de activación detectada.")
                    print("Comienza a grabar el comando completo...")
                    display_ferpy.set_display_state('line')  # Show line when command is detected
                    command_text = ""
                    last_audio_time = time.time()
                    # Se ingresa a un bucle sin ciclos intermedios. Se va actualizando
                    # el tiempo en que se recibió voz y se acumulan las partes.
                    while True:
                        try:
                            # Escucha fragmentos cortos; usamos timeout corto para detectar el silencio.
                            command_audio = recognizer.listen(source, timeout=0.5, phrase_time_limit=5)
                            try:
                                part_text = recognizer.recognize_google(command_audio, language="es-ES")
                                print(f"Grabado: {part_text}")
                                command_text += " " + part_text
                                last_audio_time = time.time()
                            except sr.UnknownValueError:
                                # No se entendió, pero se sigue el lazo para detectar silencio.
                                pass
                        except sr.WaitTimeoutError:
                            # Si no se obtiene audio en este fragmento, verificar cuánto tiempo ha pasado.
                            if time.time() - last_audio_time >= 1:
                                print("Silencio detectado. Fin del comando.")
                                break
                    command_text = command_text.strip()
                    print(f"Comando completo: {command_text}")
                    display_ferpy.set_display_state('loading')  # Return to loading after command
                    return command_text
            except sr.RequestError as e:
                print(f"Error con el servicio de reconocimiento de voz: {e}")
                continue

def listen_for_name():
    """
    Captures the user's name without requiring a trigger phrase.
    The user speaks, and their voice is recorded until 1 second of silence is detected.
    Prints what is heard. If no name is detected, it asks again.
    Returns the recognized name.
    """
    recognizer = sr.Recognizer()
    recognizer.pause_threshold = 1
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source)
        while True:
            name_text = ""
            print("Listening for your name...")
            try:
                # Listen for up to 5 seconds or until silence is detected
                audio_chunk = recognizer.listen(source, timeout=5, phrase_time_limit=5)
                try:
                    name_text = recognizer.recognize_google(audio_chunk, language="es-ES").strip()
                    print(f"Captured name: {name_text}")
                    return name_text
                except sr.UnknownValueError:
                    print("Could not understand the audio. Please try again.")
                    speak_text("No se entendió tu voz. Intenta de nuevo.")
            except sr.WaitTimeoutError:
                print("No voice detected. Please try again.")
                speak_text("No se detectó ninguna voz. Intenta de nuevo.")

def load_patients_db(filename="patients_database.json"):
    if os.path.exists(filename):
        with open(filename, "r") as f:
            try:
                return json.load(f)
            except Exception as e:
                print(f"Error loading patients database: {e}")
                return {}
    return {}

def save_patients_db(db, filename="patients_database.json"):
    with open(filename, "w") as f:
        json.dump(db, f, indent=4)

def main():
    # Load the face database
    database = face_recognition_module.load_database()

    # Load patients database from file
    patients_db = load_patients_db()

    # Define the initial image path
    initial_image = "initial.jpg"
    print("Capturing initial image for face recognition...")
    if camera_module:
        camera_module.capture_and_save_image(initial_image)
    else:
        print("Camera module unavailable. Using existing 'initial.jpg'.")

    user_name = None
    identify_user_try = 0
    # Initialize the robot command handler
    robot = RobotCommandHandler()

    while not user_name:
        if camera_module:
            print("Please look at the camera.")
            speak_text("Por favor, mire a la cámara.")
            print("Taking a new image in 3...")
            speak_text("Tomando una nueva imagen en 3...")
            print("2...")
            speak_text("2...")
            print("1")
            speak_text("1...")
            camera_module.capture_and_save_image(initial_image)
            detected_face = face_recognition_module.detect_face(initial_image)
            if detected_face:
                user_name = face_recognition_module.identify_user(initial_image, database)
                if not user_name:
                    print("Face detected but not recognized. Asking for name to register.")
                    speak_text("Se detectó una cara, pero no está registrada por favor di tu nombre para registrarte.")
                    time.sleep(1)
                    for attempt in range(2):  # Allow 2 attempts to capture the name
                        time.sleep(1)
                        user_name_text = listen_for_name()
                        if user_name_text:
                            print(f"Received name: {user_name_text}")
                            user_name = user_name_text.strip()
                            face_recognition_module.register_user(user_name, initial_image, database)
                            print(f"User {user_name} registered successfully.")
                            break
                        else:
                            print("Could not capture the name. Asking again.")
                            speak_text("No se pudo capturar tu nombre. Intenta de nuevo.")
                    if not user_name:
                        print("Failed to capture name after 2 attempts. Setting default name 'Paciente'.")
                        user_name = "Paciente"
                        break
            else:
                print("No face detected. Asking for name via voice.")
                speak_text("No se detectó ninguna cara. Por favor, di tu nombre.")
                for attempt in range(2):  # Allow 2 attempts to capture the name
                    user_name_text = listen_for_name()
                    if user_name_text:
                        print(f"Received name: {user_name_text}")
                        user_name = user_name_text.strip()
                        break
                    else:
                        print("Could not capture the name. Asking again.")
                        speak_text("No se pudo capturar tu nombre. Intenta de nuevo.")
                        time.sleep(1)
                if not user_name:
                    print("Failed to capture name after 2 attempts. Setting default name 'Paciente'.")
                    user_name = "Paciente"
                    break

        identify_user_try += 1
        if identify_user_try >= 10:
            print("Maximum attempts reached. Exiting.")
            break
        time.sleep(1)

    print(f"Welcome, {user_name}!")
    speak_text(f"Bienvenido, {user_name}!")

    # Load or initialize the patient data using patients_db:
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
        save_patients_db(patients_db)

    # Assign the loaded patient_data to the robot so that registration commands update it
    robot.patient_data = patient_data

    # Loop for Gemini interaction
    conversation_messages = []
    while True:
        print("Esperando 'Doctor Ferpy' para iniciar el comando...")
        user_prompt_text = listen_for_command()
        print(f"Comando reconocido: {user_prompt_text}")

        interaction_image_path = "interaction.jpg"
        if camera_module:
            camera_module.capture_and_save_image(interaction_image_path)
            time.sleep(0.1)
        else:
            interaction_image_path = "initial.jpg"
            print("Camera module unavailable. Using 'initial.jpg' for interaction.")

        print("Enviando tu prompt a Gemini...")
        response_text, conversation_messages = Gemini_module.gemini_interaction(
            conversation_messages, user_prompt_text, interaction_image_path, robot.patient_data
        )
        print("Gemini responde:", response_text)
        print("Procesando la respuesta intercalando comandos y texto:")
        robot.execute_response_segments(response_text)

        # Update patient data in the patients_db and save changes
        patients_db[user_name] = robot.patient_data
        save_patients_db(patients_db)

if __name__ == '__main__':
    try:
        main()
    finally:
        display_ferpy.stop_display()
