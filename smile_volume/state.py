from enum import Enum
from typing import Optional


class SmileState(Enum):
    NOT_SMILING = "not_smiling"
    SMILING = "smiling"


class HysteresisStateMachine:
    def __init__(self, on_threshold: float, off_threshold: float, on_frames: int, off_frames: int):
        if off_threshold >= on_threshold:
            raise ValueError("off_threshold must be < on_threshold for hysteresis")
        
        self.on_threshold = on_threshold
        self.off_threshold = off_threshold
        self.on_frames = on_frames
        self.off_frames = off_frames
        self.state = SmileState.NOT_SMILING
        self._on_counter = 0
        self._off_counter = 0
    
    def update(self, score: Optional[float]) -> tuple[SmileState, bool]:
        score = score if score is not None else 0.0
        previous_state = self.state
        
        if self.state == SmileState.NOT_SMILING:
            if score >= self.on_threshold:
                self._on_counter += 1
                self._off_counter = 0
                if self._on_counter >= self.on_frames:
                    self.state = SmileState.SMILING
                    self._on_counter = 0
            else:
                self._on_counter = 0
        elif self.state == SmileState.SMILING:
            if score <= self.off_threshold:
                self._off_counter += 1
                self._on_counter = 0
                if self._off_counter >= self.off_frames:
                    self.state = SmileState.NOT_SMILING
                    self._off_counter = 0
            else:
                self._off_counter = 0
        
        return self.state, self.state != previous_state
    
    def get_state(self) -> SmileState:
        return self.state
