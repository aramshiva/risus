"""Hysteresis state machine for smile detection."""

from enum import Enum
from typing import Optional


class SmileState(Enum):
    """Current smile state."""
    NOT_SMILING = "not_smiling"
    SMILING = "smiling"


class HysteresisStateMachine:
    """State machine with hysteresis to prevent rapid toggling."""
    
    def __init__(
        self,
        on_threshold: float,
        off_threshold: float,
        on_frames: int,
        off_frames: int,
    ):
        """
        Args:
            on_threshold: Score threshold to transition to SMILING
            off_threshold: Score threshold to transition to NOT_SMILING
            on_frames: Consecutive frames needed to switch to SMILING
            off_frames: Consecutive frames needed to switch to NOT_SMILING
        """
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
        """
        Update state machine with new smile score.
        
        Args:
            score: Current smile score (None = no face detected)
        
        Returns:
            (current_state, state_changed)
        """
        if score is None:
            # No face detected - treat as not smiling
            score = 0.0
        
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
        
        state_changed = self.state != previous_state
        return self.state, state_changed
    
    def get_state(self) -> SmileState:
        """Get current state without updating."""
        return self.state
