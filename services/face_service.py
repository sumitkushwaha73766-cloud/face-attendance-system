"""
Face detection, encoding, and recognition service.
Supports:
  1. Built-in OpenCV LBPH (Local Binary Patterns Histograms) - 100% offline, zero C++ compiler needed,
     providing high discriminability between different individuals and resilience to lighting variations.
  2. Multi-face recognition in a single frame (supports multiple students simultaneously or sequentially).
  3. Optional dlib face_recognition (if installed).
"""
import os
import cv2
import numpy as np
from config import Config

# Try importing dlib-based face_recognition
try:
    import face_recognition
    FACE_RECOGNITION_LIB_AVAILABLE = True
except ImportError:
    face_recognition = None
    FACE_RECOGNITION_LIB_AVAILABLE = False

# Check if OpenCV LBPH face recognizer is available
HAS_CV2_FACE = hasattr(cv2, "face") and hasattr(cv2.face, "LBPHFaceRecognizer_create")

# Built-in OpenCV Haar Cascade face detector
HAAR_CASCADE_PATH = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
face_cascade = cv2.CascadeClassifier(HAAR_CASCADE_PATH)


def extract_opencv_embedding(face_img):
    """
    Extract a high-discriminability 16,384-dimensional LBPH histogram
    vector (or normalized spatial histogram fallback) from a detected face image.
    """
    if len(face_img.shape) == 3:
        gray = cv2.cvtColor(face_img, cv2.COLOR_BGR2GRAY)
    else:
        gray = face_img

    # Standardize to 120x120 and equalize illumination to remove shadows
    resized = cv2.resize(gray, (120, 120))
    equalized = cv2.equalizeHist(resized)

    if HAS_CV2_FACE:
        # True OpenCV LBPH Recognizer: 8x8 spatial grid, radius=1, neighbors=8
        # Output: 8*8*256 = 16,384 histogram bins with high spatial facial discrimination
        rec = cv2.face.LBPHFaceRecognizer_create(radius=1, neighbors=8, grid_x=8, grid_y=8)
        rec.train([equalized], np.array([1]))
        hist = rec.getHistograms()[0].flatten().astype(np.float32)
        return hist
    else:
        # Fallback spatial block histogram (456-d) if cv2.face is unavailable
        features = []
        cell_h, cell_w = 24, 24
        for r in range(5):
            for c in range(5):
                cell = equalized[r * cell_h:(r + 1) * cell_h, c * cell_w:(c + 1) * cell_w]
                h = cv2.calcHist([cell], [0], None, [8], [0, 256]).flatten()
                features.extend(h)
        struct = cv2.resize(equalized, (16, 16)).flatten().astype(np.float32)
        features.extend(struct)
        vec = np.array(features, dtype=np.float32)
        norm = np.linalg.norm(vec)
        return vec / norm if norm > 0 else vec


def detect_and_encode_face(image_path):
    """
    Detect a face in an image file and return its embedding.
    Returns (encoding, error_message) tuple.
    """
    # 1. Try face_recognition library if available
    if FACE_RECOGNITION_LIB_AVAILABLE:
        try:
            image = face_recognition.load_image_file(image_path)
            face_locations = face_recognition.face_locations(image, model=Config.FACE_RECOGNITION_MODEL)

            if len(face_locations) == 0:
                return None, "No face detected in the image. Please try a clearer front-facing photo."
            if len(face_locations) > 1:
                return None, "Multiple faces detected. Please ensure only one person is in the frame."

            encodings = face_recognition.face_encodings(image, face_locations)
            return encodings[0], None
        except Exception:
            pass

    # 2. Native OpenCV Engine
    try:
        img_array = np.fromfile(image_path, np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
    except Exception:
        img = cv2.imread(image_path)

    if img is None:
        return None, "Could not open image file. Please upload a valid JPG or PNG."

    # Check for completely black/dark image (e.g. webcam privacy shutter closed)
    if np.mean(img) < 15:
        return None, "Camera image is completely pitch black. Please check if your laptop's physical webcam privacy slider (shutter) above the screen is closed, or use 'Option B: Upload Photo'."

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(60, 60))

    if len(faces) == 0:
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.05, minNeighbors=3, minSize=(40, 40))

    if len(faces) == 0:
        return None, "No face detected in the image. Please use a clear, well-lit front-facing photo."

    # Select largest face
    largest_face = max(faces, key=lambda rect: rect[2] * rect[3])
    x, y, w, h = largest_face
    face_roi = gray[y:y + h, x:x + w]

    encoding = extract_opencv_embedding(face_roi)
    return encoding, None


def encode_face_from_frame(frame):
    """
    Detect and encode a face from an OpenCV video frame (BGR).
    Returns (encoding, face_location, error_message).
    """
    if frame is None or frame.size == 0:
        return None, None, "Invalid camera frame received."

    # Check for pitch black frame (e.g. privacy shutter closed)
    if np.mean(frame) < 15:
        return None, None, "Camera feed is black/dark. Check laptop webcam shutter or use Photo Attendance."

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.12, minNeighbors=4, minSize=(60, 60))

    if len(faces) == 0:
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.05, minNeighbors=3, minSize=(40, 40))

    if len(faces) == 0:
        return None, None, "No face detected in camera viewfinder."

    # Select largest face
    x, y, w, h = max(faces, key=lambda rect: rect[2] * rect[3])
    face_roi = gray[y:y + h, x:x + w]
    encoding = extract_opencv_embedding(face_roi)
    face_location = (y, x + w, y + h, x)  # (top, right, bottom, left)

    return encoding, face_location, None


def detect_all_faces_and_encode(frame):
    """
    Detect ALL faces present in a video frame.
    Returns list of dicts: [{'encoding': ..., 'location': (top, right, bottom, left), 'box': (x,y,w,h)}]
    """
    if frame is None or frame.size == 0:
        return []

    if np.mean(frame) < 15:
        return []

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.12, minNeighbors=4, minSize=(55, 55))

    detected = []
    for (x, y, w, h) in faces:
        face_roi = gray[y:y + h, x:x + w]
        enc = extract_opencv_embedding(face_roi)
        loc = (int(y), int(x + w), int(y + h), int(x))
        detected.append({
            "encoding": enc,
            "location": loc,
            "box": (int(x), int(y), int(w), int(h))
        })
    return detected


def recognize_face(unknown_encoding, known_faces, threshold=None):
    """
    Compare an unknown face encoding against registered faces.
    Returns matched student dict with confidence or None.

    `threshold`, if given, is applied ONLY when it matches the encoding
    type actually in use (LBPH / dlib / legacy each operate on a different
    distance scale, so a single fixed threshold is never safe to apply
    across all three — see [FIX S1]).
    """
    if not known_faces or unknown_encoding is None:
        return None

    best_match = None
    min_dist = float("inf")
    eff_threshold = None
    enc_len = len(unknown_encoding)

    for student in known_faces:
        stored_enc = student.get("encoding")
        if stored_enc is None or len(stored_enc) != enc_len:
            continue

        if enc_len == 16384:
            # OpenCV LBPH Chi-Square distance
            s_vec = np.ascontiguousarray(stored_enc, dtype=np.float32)
            u_vec = np.ascontiguousarray(unknown_encoding, dtype=np.float32)
            dist = float(cv2.compareHist(s_vec, u_vec, cv2.HISTCMP_CHISQR))
            default_threshold = 85.0
        elif enc_len == 128:
            # dlib Euclidean distance
            dist = float(np.linalg.norm(stored_enc - unknown_encoding))
            default_threshold = 0.50
        else:
            # Cosine distance
            sim = float(np.dot(stored_enc, unknown_encoding))
            dist = 1.0 - sim
            default_threshold = 0.38

        # [FIX S1] A caller-supplied threshold only applies to the LBPH
        # scale (0-100ish distances) it was designed for; dlib/cosine
        # distances live on a 0-1 scale and must always use their own
        # type-correct default, or every face would incorrectly match.
        if threshold is not None and enc_len == 16384:
            candidate_threshold = threshold
        else:
            candidate_threshold = default_threshold

        if dist < min_dist:
            min_dist = dist
            best_match = student
            eff_threshold = candidate_threshold

    if best_match is not None and min_dist <= eff_threshold:
        if enc_len == 16384:
            # Scale confidence: 0 distance -> 99.5%, 85.0 distance -> 70.0%
            conf = max(70.0, 100.0 - (min_dist / eff_threshold) * 30.0)
        elif enc_len == 128:
            conf = max(70.0, (1.0 - (min_dist / eff_threshold)) * 100.0)
        else:
            conf = max(70.0, (1.0 - (min_dist / eff_threshold)) * 100.0)

        return {
            "id": best_match["id"],
            "name": best_match["name"],
            "roll_no": best_match["roll_no"],
            "confidence": min(round(conf, 1), 99.5),
            "distance": round(float(min_dist), 2),
        }

    return None


def recognize_all_faces(frame, known_faces, threshold=85.0):
    """
    Detect and recognize ALL faces in a frame against known registered students.
    Returns tuple: (list_of_matched_students, total_detected_faces_count)
    Matches are deduplicated by student ID.
    """
    detected_faces = detect_all_faces_and_encode(frame)
    if not detected_faces:
        return [], 0

    matched = []
    seen_ids = set()

    for item in detected_faces:
        enc = item["encoding"]
        match = recognize_face(enc, known_faces, threshold=threshold)
        if match and match["id"] not in seen_ids:
            seen_ids.add(match["id"])
            match["box"] = item["box"]
            match["location"] = item["location"]
            matched.append(match)

    return matched, len(detected_faces)


def save_captured_photo(frame, roll_no):
    """Save a captured frame as a student photo."""
    filename = f"{roll_no}.jpg"
    filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
    cv2.imwrite(filepath, frame)
    return filepath
