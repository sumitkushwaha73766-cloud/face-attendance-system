"""Camera service — webcam access and video streaming."""
import threading
import cv2
from config import Config


class Camera:
    """
    Manages webcam access for face detection and attendance.
    [FIX M2] Thread-safe with locking around frame capture.
    """

    def __init__(self):
        self.video = None
        self.lock = threading.Lock()

    def start(self):
        """Start the webcam."""
        with self.lock:
            if self.video is None or not self.video.isOpened():
                self.video = cv2.VideoCapture(Config.CAMERA_INDEX)
                self.video.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                self.video.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    def get_frame(self):
        """Capture a single frame from the webcam. Returns (success, frame)."""
        with self.lock:
            if self.video is None or not self.video.isOpened():
                self._start_unlocked()
            return self.video.read()

    def _start_unlocked(self):
        """Internal start without acquiring lock (called when lock is held)."""
        if self.video is None or not self.video.isOpened():
            self.video = cv2.VideoCapture(Config.CAMERA_INDEX)
            self.video.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.video.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    def stop(self):
        """Release the webcam."""
        with self.lock:
            if self.video and self.video.isOpened():
                self.video.release()
                self.video = None

    def is_running(self):
        """Check if camera is active."""
        with self.lock:
            return self.video is not None and self.video.isOpened()

    def generate_frames(self):
        """Generator that yields MJPEG frames for streaming."""
        while True:
            success, frame = self.get_frame()
            if not success:
                break

            ret, buffer = cv2.imencode(".jpg", frame)
            if not ret:
                continue

            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n"
            )


# Singleton camera instance
camera = Camera()
