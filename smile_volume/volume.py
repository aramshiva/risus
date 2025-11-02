"""AppleScript-based macOS volume control with rate limiting."""

import subprocess
import time
from typing import Optional


class VolumeController:
    """Controls macOS system volume via AppleScript with rate limiting."""
    
    def __init__(self, min_interval_ms: int = 250):
        """
        Args:
            min_interval_ms: Minimum milliseconds between identical commands
        """
        self.min_interval_ms = min_interval_ms
        self._last_set_time: float = 0
        self._last_set_value: Optional[int] = None
    
    @staticmethod
    def _run_osascript(script: str) -> str:
        """Execute AppleScript and return output."""
        return subprocess.check_output(
            ["/usr/bin/osascript", "-e", script],
            text=True
        ).strip()
    
    def get_volume(self) -> int:
        """Get current system output volume (0-100)."""
        out = self._run_osascript("output volume of (get volume settings)")
        return int(out)
    
    def set_volume(self, pct: int, force: bool = False) -> None:
        """
        Set system output volume with rate limiting.
        
        Args:
            pct: Volume percentage (0-100)
            force: Bypass rate limiting
        """
        pct = max(0, min(100, int(pct)))
        
        now = time.time()
        elapsed_ms = (now - self._last_set_time) * 1000
        
        # Rate limit: skip if same value set too recently
        if not force and self._last_set_value == pct and elapsed_ms < self.min_interval_ms:
            return
        
        self._run_osascript(f"set volume output volume {pct}")
        self._last_set_time = now
        self._last_set_value = pct
