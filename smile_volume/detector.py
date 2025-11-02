"""Smile detection using ONNX emotion recognition model."""

import time
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
import onnxruntime as ort


class SmileDetector:
    """Detects smiling from webcam using ONNX HSEmotion model."""
    
    def __init__(
        self,
        camera_index: int = 0,
        ema_beta: float = 0.7,
        face_timeout_ms: int = 800,
    ):
        """
        Args:
            camera_index: Webcam device index
            ema_beta: Exponential moving average smoothing factor (0-1)
            face_timeout_ms: Time without face detection before treating as not smiling
        """
        self.camera_index = camera_index
        self.ema_beta = ema_beta
        self.face_timeout_ms = face_timeout_ms
        
        self.cap: Optional[cv2.VideoCapture] = None
        self.face_cascade: Optional[cv2.CascadeClassifier] = None
        self.emotion_session: Optional[ort.InferenceSession] = None
        self.smoothed_score: float = 0.0
        self.last_face_time: float = 0.0
        
        # HSEmotion preprocessing params
        self.img_size = 260
        self.mean = np.array([0.485, 0.456, 0.406])
        self.std = np.array([0.229, 0.224, 0.225])
        
        # Emotion indices (HAPPINESS is index 3)
        self.HAPPINESS_IDX = 3
    
    def start(self) -> None:
        """Initialize camera and ONNX model."""
        self.cap = cv2.VideoCapture(self.camera_index)
        if not self.cap.isOpened():
            raise RuntimeError(f"Failed to open camera {self.camera_index}")
        
        # Optimize for performance
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        
        # Load Haar Cascade for face detection
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        
        # Load ONNX emotion model
        model_path = Path(__file__).parent / "weights" / "emotion.onnx"
        if not model_path.exists():
            raise RuntimeError(f"Emotion model not found at {model_path}")
        
        self.emotion_session = ort.InferenceSession(
            str(model_path),
            providers=['CPUExecutionProvider']
        )
        
        self.last_face_time = time.time()
    
    def stop(self) -> None:
        """Release camera resources."""
        if self.cap:
            self.cap.release()
    
    def _preprocess_face(self, face_img: np.ndarray) -> np.ndarray:
        """
        Preprocess face image for HSEmotion model.
        
        Args:
            face_img: Face RGB image
            
        Returns:
            Preprocessed tensor (1, 3, 260, 260)
        """
        # Resize to model input size
        x = cv2.resize(face_img, (self.img_size, self.img_size)) / 255.0
        
        # Normalize with ImageNet stats
        for i in range(3):
            x[..., i] = (x[..., i] - self.mean[i]) / self.std[i]
        
        # Convert to NCHW format
        return x.transpose(2, 0, 1).astype("float32")[np.newaxis, ...]
    
    def _get_happiness_score(self, face_rgb: np.ndarray) -> float:
        """
        Run emotion inference and extract happiness score.
        
        Args:
            face_rgb: Face image in RGB format
            
        Returns:
            Happiness probability (0.0-1.0)
        """
        # Preprocess
        input_tensor = self._preprocess_face(face_rgb)
        
        # Run inference
        logits = self.emotion_session.run(None, {"input": input_tensor})[0][0]
        
        # Convert logits to probabilities with softmax
        e_x = np.exp(logits - np.max(logits))
        probs = e_x / e_x.sum()
        
        # Return happiness probability
        return float(probs[self.HAPPINESS_IDX])
    
    def get_smile_score(self) -> Optional[float]:
        """
        Capture frame and return current smile score.
        
        Returns:
            Smoothed happiness score (0.0-1.0), or None if camera error or face timeout
        """
        if not self.cap or not self.face_cascade or not self.emotion_session:
            return None
        
        ret, frame = self.cap.read()
        if not ret:
            return None
        
        # Convert to RGB and grayscale
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(100, 100),
        )
        
        if len(faces) > 0:
            # Use first (largest) face
            (x, y, w, h) = faces[0]
            face_roi = rgb_frame[y:y+h, x:x+w]
            
            # Get happiness score from ONNX model
            raw_score = self._get_happiness_score(face_roi)
            
            # Exponential moving average smoothing
            self.smoothed_score = (
                self.ema_beta * raw_score + (1 - self.ema_beta) * self.smoothed_score
            )
            
            self.last_face_time = time.time()
            return self.smoothed_score
        
        # No face detected - check timeout
        elapsed_ms = (time.time() - self.last_face_time) * 1000
        if elapsed_ms > self.face_timeout_ms:
            return None  # Treat as not smiling
        
        # Return last known score during brief face loss
        return self.smoothed_score
