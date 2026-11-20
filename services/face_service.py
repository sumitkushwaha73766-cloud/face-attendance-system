"""Face detection, encoding, and recognition service."""
import os
import cv2
import numpy as np
from config import Config

try:
    import face_recognition
    FACE_RECOGNITION_AVAILABLE = True
except ImportError:
    face_recognition = None
    FACE_RECOGNITION_AVAILABLE = False


def detect_and_encode_face(image_path):
    """
    Detect a face in an image and return its 128-d encoding.
    Returns (encoding, error_message) tuple.
    """
    if not FACE_RECOGNITION_AVAILABLE:
        return None, "face_recognition is not installed. Please install dlib and face_recognition."

    image = face_recognition.load_image_file(image_path)
    face_locations = face_recognition.face_locations(image, model=Config.FACE_RECOGNITION_MODEL)

    if len(face_locations) == 0:
        return None, "No face detected in the image. Please try again."
    if len(face_locations) > 1:
        return None, "Multiple faces detected. Please ensure only one face is visible."

    encodings = face_recognition.face_encodings(image, face_locations)
    return encodings[0], None


def encode_face_from_frame(frame):
    """
    Detect and encode a face from an OpenCV frame (BGR).
    Returns (encoding, face_location, error_message).
    """
    if not FACE_RECOGNITION_AVAILABLE:
        return None, None, "face_recognition is not installed."

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    small_frame = cv2.resize(rgb_frame, (0, 0), fx=0.5, fy=0.5)

    face_locations = face_recognition.face_locations(small_frame, model=Config.FACE_RECOGNITION_MODEL)

    if len(face_locations) == 0:
        return None, None, "No face detected"

    encodings = face_recognition.face_encodings(small_frame, face_locations)

    # Scale back face location to original size
    top, right, bottom, left = face_locations[0]
    face_location = (top * 2, right * 2, bottom * 2, left * 2)

    return encodings[0], face_location, None


def recognize_face(unknown_encoding, known_faces):
    """
    Compare an unknown face encoding against known faces.
    Returns matched student info or None.

    known_faces: list of dicts with 'id', 'name', 'roll_no', 'encoding'
    """
    if not known_faces:
        return None

    if not FACE_RECOGNITION_AVAILABLE:
        return None

    known_encodings = [f["encoding"] for f in known_faces]
    distances = face_recognition.face_distance(known_encodings, unknown_encoding)
    best_match_idx = np.argmin(distances)

    if distances[best_match_idx] <= Config.FACE_RECOGNITION_TOLERANCE:
        match = known_faces[best_match_idx]
        confidence = round((1 - distances[best_match_idx]) * 100, 1)
        return {
            "id": match["id"],
            "name": match["name"],
            "roll_no": match["roll_no"],
            "confidence": confidence,
        }

    return None


def save_captured_photo(frame, roll_no):
    """Save a captured frame as a student photo. Returns the saved file path."""
    filename = f"{roll_no}.jpg"
    filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
    cv2.imwrite(filepath, frame)
    return filepath
