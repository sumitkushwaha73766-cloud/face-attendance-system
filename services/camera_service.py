"""
Camera service — webcam access and video streaming.
Supports:
  1. Auto-detection across camera indices (0, 1, 2) and backends (DSHOW, MSMF, ANY)
  2. Fallback biometric simulation frame when physical camera is unavailable
"""
import time
import threading
import cv2
import numpy as np
from config import Config


class Camera:
    """Manages webcam access for face detection and attendance."""

    def __init__(self):
        self.video = None
        self.lock = threading.Lock()
        self.is_simulated = False
        self.frame_counter = 0

    def _open_working_capture(self):
        """Attempts to open any working camera index and backend."""
        # DirectShow is fastest and non-blocking on Windows
        candidates = [
            (Config.CAMERA_INDEX, cv2.CAP_DSHOW),
            (Config.CAMERA_INDEX, cv2.CAP_ANY),
            (Config.CAMERA_INDEX, cv2.CAP_MSMF),
        ]

        for idx, backend in candidates:
            try:
                cap = cv2.VideoCapture(idx, backend)
                if cap.isOpened():
                    ret, frame = cap.read()
                    if ret and frame is not None and frame.size > 0:
                        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                        self.is_simulated = False
                        return cap
                    cap.release()
            except Exception:
                pass

        # If no physical hardware is returning frames
        self.is_simulated = True
        return None

    def start(self):
        """Start the webcam."""
        with self.lock:
            if self.video is None or not self.video.isOpened():
                self.video = self._open_working_capture()

    def get_frame(self):
        """Capture a frame. Returns (success, frame)."""
        with self.lock:
            if self.video is None or not self.video.isOpened():
                self.video = self._open_working_capture()

            if self.video and self.video.isOpened():
                ret, frame = self.video.read()
                if ret and frame is not None:
                    return True, frame

            # Fallback simulated frame if hardware camera is not available
            self.frame_counter += 1
            frame = self._generate_diagnostic_frame()
            return False, frame

    def _generate_diagnostic_frame(self):
        """Generates an informative diagnostic canvas for the camera feed."""
        h, w = 400, 600
        canvas = np.zeros((h, w, 3), dtype=np.uint8)
        canvas[:] = (20, 24, 33)  # Dark cyber background

        # Draw grid
        for x in range(0, w, 40):
            cv2.line(canvas, (x, 0), (x, h), (30, 36, 48), 1)
        for y in range(0, h, 40):
            cv2.line(canvas, (0, y), (w, y), (30, 36, 48), 1)

        # Draw pulsing reticle in center
        cx, cy = w // 2, h // 2 - 20
        radius = int(55 + 10 * np.sin(self.frame_counter * 0.1))
        cv2.circle(canvas, (cx, cy), radius, (230, 114, 68), 2)
        cv2.circle(canvas, (cx, cy), 6, (230, 114, 68), -1)

        # Crosshairs
        cv2.line(canvas, (cx - 75, cy), (cx + 75, cy), (230, 114, 68), 1)
        cv2.line(canvas, (cx, cy - 75), (cx, cy + 75), (230, 114, 68), 1)

        # Status text
        cv2.putText(canvas, "HARDWARE CAMERA UNAVAILABLE", (w // 2 - 165, h - 90),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (90, 110, 240), 2)
        cv2.putText(canvas, "Use 'Option 2: Photo Attendance' tab or enable laptop camera", (w // 2 - 225, h - 55),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (160, 160, 170), 1)
        cv2.putText(canvas, time.strftime("%Y-%m-%d %H:%M:%S"), (w // 2 - 75, h - 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (100, 200, 100), 1)

        return canvas

    def stop(self):
        """Release the webcam."""
        with self.lock:
            if self.video and self.video.isOpened():
                self.video.release()
                self.video = None
            self.is_simulated = False

    def is_running(self):
        """Check if camera is active."""
        with self.lock:
            return self.video is not None and self.video.isOpened()

    def generate_frames(self):
        """Generator that yields MJPEG frames for streaming."""
        while True:
            _, frame = self.get_frame()
            if frame is None:
                time.sleep(0.1)
                continue

            ret, buffer = cv2.imencode(".jpg", frame)
            if not ret:
                continue

            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n"
            )
            time.sleep(0.04)  # ~25 FPS


# Singleton camera instance
camera = Camera()
