import subprocess
import time
from typing import Optional


class VolumeController:
    def __init__(self, min_interval_ms: int = 250):
        self.min_interval_ms = min_interval_ms
        self._last_set_time = 0.0
        self._last_set_value: Optional[int] = None
    
    @staticmethod
    def _run_osascript(script: str) -> str:
        return subprocess.check_output(["/usr/bin/osascript", "-e", script], text=True).strip()
    
    def get_volume(self) -> int:
        return int(self._run_osascript("output volume of (get volume settings)"))
    
    def set_volume(self, pct: int, force: bool = False) -> None:
        pct = max(0, min(100, int(pct)))
        now = time.time()
        elapsed_ms = (now - self._last_set_time) * 1000
        
        if not force and self._last_set_value == pct and elapsed_ms < self.min_interval_ms:
            return
        
        self._run_osascript(f"set volume output volume {pct}")
        self._last_set_time = now
        self._last_set_value = pct
