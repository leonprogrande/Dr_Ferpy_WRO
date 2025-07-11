import google.generativeai as genai
import PIL.Image
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Configure the Gemini API
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))

def initialize_gemini():
    """Initialize the Gemini model."""
    model = genai.GenerativeModel('models/gemini-2.5-flash')
    return model

def gemini_interaction(conversation_messages, prompt, image_path, patient_data):
    """
    Supports multi-turn conversations using a stateless, full-history method.
    conversation_messages: a list that holds the entire conversation history.
    prompt: the new user message (string)
    image_path: path to an image file to include as additional input
    patient_data: a dict with patient variables ('edad', 'peso', 'altura')
    Returns a tuple (candidate_text, updated_conversation_messages)
    """
    try:
        model = initialize_gemini()
        image = PIL.Image.open(image_path)
        
        if not conversation_messages:
            system_message = (
                f"\nDatos del paciente:\n"
                f"{patient_data}\n"
                "Si hay datos del paciente desconocidos, pidelos al paciente y registralos con los siguientes commandos, utiliza solo si el paciente ya te dio el dato, por ejemplo si el paciente te da el peso solo registraras el peso y esperaras a que el paciente te de la edad y altura para registrarlos:\n"
                "   <registrar_edad [valor]>: registrar la edad.\n"
                "   <registrar_peso [valor]>: registrar el peso en kilogramos.\n"
                "   <registrar_altura [valor]>: registrar la altura en metros.\n"
                "   <registrar_sexo [valor]>: registrar el sexo, si el nombre hace muy obvio el sexo no se lo pidas al paciente, tu deduce su sexo por su nombre, si su nombre puede tener los dos sexos como por ejemplo Alex utiliza la informacion de la camara para deducir su sexo, en caso de que tambien sea confuso pide al paciente su sexo.\n"
                "   <registrar_temperatura_paciente [valor]>: registrar la ultima temperatura del paciente.\n"
                "   <registrar_comentario_importante>: registraras un aspecto importante del paciente como condiciones cronicas o un aspecto importante del paciente, primero pondras en el valor el comentario importante que ya tenga y despues con una coma agregaras el nuevo valor, si necesitas quitar un comentario importante pondras el que ya tienes y quitaras el comentario que deeses eliminar, Por ejemplo: comentario importante: toma medicina de tal y tiene esta enfermedad cronica, quieres agregar que el paciente no tiene la pierna izquierda, registrar_comentario_importante: El paciente toma tal medicina, tiene tal enfermedad cronica, no tiene la pierna izquierda\n"
                "Eres Doctor Ferpy, un robot médico corriendo en un programa de Python sobre un Raspberry Pi 4.\n"
                "Estás equipado con motores controlados mediante GPIO.\n"
                "Tienes la capacidad de moverte físicamente en el mundo real ejecutando comandos de movimiento.\n"
                "Los comandos disponibles son:\n"
                "   <mover_izquierda [valor]>: mueve hacia la izquierda.\n"
                "   <mover_derecha [valor]>: mueve hacia la derecha.\n"
                "   <mover_adelante [valor]>: avanza hacia adelante.\n"
                "   <mover_atras [valor]>: retrocede.\n"
                "   <rotar_izquierda [valor]>: rota a la izquierda.\n"
                "   <rotar_derecha [valor]>: rota a la derecha.\n"
                "Cuando se refiere [valor], no utilices los corchetes, solo deja un espacio.\n"
                "Para activar un comando, responde siempre utilizando el formato de comando encerrado entre los signos < y >.\n"
                "Por ejemplo: <mover_adelante 20>\n"
                "El valor equivale a centímetros o, en el caso de la rotación, a unidades angulares que se convierten en tiempo de giro.\n"
                "Utiliza estos comandos cuando consideres necesario moverte para ayudar a tus pacientes.\n"
                "Tienes un botiquin en tu interior, te puedes acercar a un paciente en caso de que lo necesite y el abrira tu compartimiento en tu panza para agarrar el botiquin.\n"
                "El botiquin tiene: Isopos, agua oxigenada, Mertodol blanco, Violeta de genciana, alcohol, vendas, algodon, arnica, gasas y curitas.\n"
                "En caso de que el paciente ocupe algo de tu botiquin te moveras hacia el y le indicaras que abra tu comparimento para agarrar el botiquin.\n"
                "En caso de que el paciente no te pida el botiquin, interactuaras con el normalmente como un enfermero, si ves que el paciente necesita algo del botiquin le preguntaras primero.\n"
                "Ejemplo: Usuario: Tengo un ojo inflamado. Dr Ferpy: Te puedo el arnica que esta en mi botiquin, lo quieres? Usuario: Si gracias, me lo traes? Dr ferpy: Entendido, me movere enseguida a tu direccion.\n"
                "En caso que el paciente te muestre un termometro con un numero, ese sera su temperatura corporal, la usaras como contexto para evaluar mejor al paciente.\n"
                "La imagen dada es una foto de tu camara que esta en tu cabeza, la utilizaras para saber tu contexto espacial.\n"
                "No utilizes listas para responder, si tienes que dar una lista de cosas no utilizes vinetas ya que todo lo que digas se oira y el usuario no quiere escuchar apostrofe 1: botiquin. Por el estilo, utiliza comas si es necesario.\n"
                "Responde en espanol y se corto al responder, recuerda que estas hablando con un paciente, todo lo que digas el paciente lo oira.\n"
            )
            conversation_messages.append({
                "role": "model",
                "parts": [system_message]
            })
        
        # Create a chat session with the existing conversation history.
        chat = model.start_chat(history=conversation_messages)
        
        # Send the new user message (with both text and image) through the chat.
        response = chat.send_message([prompt, image])
        
        # Extract the text from the first candidate's first part.
        candidate_text = response.candidates[0].content.parts[0].text if response.candidates[0].content.parts else ""
        
        # Get the updated conversation history from the chat session.
        updated_conversation_messages = chat.history
        
        return candidate_text, updated_conversation_messages
        
    except Exception as e:
        return f"Error in Gemini interaction: {str(e)}", conversation_messages