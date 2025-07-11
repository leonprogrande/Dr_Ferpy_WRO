# face_recognition_module.py
import face_recognition
import json
import os
import numpy as np

DATABASE_FILE = "face_database.json"

def load_database():
    """
    Load the face database from a JSON file.
    """
    if os.path.exists(DATABASE_FILE):
        with open(DATABASE_FILE, "r") as file:
            return json.load(file)
    return {}

def save_database(database):
    """
    Save the face database to a JSON file.
    """
    with open(DATABASE_FILE, "w") as file:
        json.dump(database, file, indent=4)

def detect_face(image_path):
    """
    Loads an image file and returns face encodings if at least one face is detected.
    """
    image = face_recognition.load_image_file(image_path)
    face_locations = face_recognition.face_locations(image)
    if len(face_locations) > 0:
        face_encodings = face_recognition.face_encodings(image, face_locations)
        return face_encodings
    return None

def identify_user(image_path, database):
    """
    Identify the user by comparing the face encoding with the database.
    Returns the user name if recognized, otherwise returns None.
    """
    face_encodings = detect_face(image_path)
    if not face_encodings:
        return None

    face_encoding = face_encodings[0]
    for user_name, data in database.items():
        known_encoding = np.array(data["encoding"])
        if face_recognition.compare_faces([known_encoding], face_encoding)[0]:
            return user_name

    return None

def register_user(user_name, image_path, database):
    """
    Register a new user using their provided name and face image.
    Returns the user name if registration is successful, otherwise returns None.
    """
    face_encodings = detect_face(image_path)
    if not face_encodings:
        print("No face detected in the image. Registration failed.")
        return None

    face_encoding = face_encodings[0]
    database[user_name] = {"encoding": face_encoding.tolist()}
    save_database(database)
    return user_name
