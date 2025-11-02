import time
from pathlib import Path
from typing import Optional
import cv2
import numpy as np
import onnxruntime as ort


class SmileDetector:
    def __init__(self, camera_index: int = 0, ema_beta: float = 0.7, face_timeout_ms: int = 800):
        self.camera_index = camera_index
        self.ema_beta = ema_beta
        self.face_timeout_ms = face_timeout_ms
        self.cap: Optional[cv2.VideoCapture] = None
        self.face_cascade: Optional[cv2.CascadeClassifier] = None
        self.emotion_session: Optional[ort.InferenceSession] = None
        self.smoothed_score = 0.0
        self.last_face_time = 0.0
        self.img_size = 260
        self.mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
        self.std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
        self.HAPPINESS_IDX = 3
    
    def start(self) -> None:
        self.cap = cv2.VideoCapture(self.camera_index)
        if not self.cap.isOpened():
            raise RuntimeError(f"Failed to open camera {self.camera_index}")
        
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        
        model_path = Path(__file__).parent / "weights" / "emotion.onnx"
        if not model_path.exists():
            raise RuntimeError(f"Emotion model not found at {model_path}")
        
        self.emotion_session = ort.InferenceSession(str(model_path), providers=['CPUExecutionProvider'])
        self.last_face_time = time.time()
    
    def stop(self) -> None:
        if self.cap:
            self.cap.release()
    
    def _preprocess_face(self, face_img: np.ndarray) -> np.ndarray:
        x = cv2.resize(face_img, (self.img_size, self.img_size)).astype(np.float32) / 255.0
        x = (x - self.mean) / self.std
        return x.transpose(2, 0, 1)[np.newaxis, ...]
    
    def _get_happiness_score(self, face_rgb: np.ndarray) -> float:
        input_tensor = self._preprocess_face(face_rgb)
        logits = self.emotion_session.run(None, {"input": input_tensor})[0][0]
        e_x = np.exp(logits - np.max(logits))
        probs = e_x / e_x.sum()
        return float(probs[self.HAPPINESS_IDX])
    
    def get_smile_score(self) -> Optional[float]:
        if not self.cap or not self.face_cascade or not self.emotion_session:
            return None
        
        ret, frame = self.cap.read()
        if not ret:
            return None
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(100, 100))
        
        if len(faces) > 0:
            x, y, w, h = faces[0]
            face_roi = cv2.cvtColor(frame[y:y+h, x:x+w], cv2.COLOR_BGR2RGB)
            raw_score = self._get_happiness_score(face_roi)
            self.smoothed_score = self.ema_beta * raw_score + (1 - self.ema_beta) * self.smoothed_score
            self.last_face_time = time.time()
            return self.smoothed_score
        
        if (time.time() - self.last_face_time) * 1000 > self.face_timeout_ms:
            return None
        
        return self.smoothed_score
