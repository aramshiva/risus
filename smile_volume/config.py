"""Persistent configuration storage."""

import json
from pathlib import Path
from typing import Any


class Config:
    """Manages app configuration in ~/Library/Application Support/SmileVolume."""
    
    DEFAULT_CONFIG = {
        "last_nonzero_volume": 50,
        "smile_on_threshold": 0.5,
        "smile_off_threshold": 0.15,
        "on_frames": 3,
        "off_frames": 5,
        "camera_index": 0,
        "poll_interval_ms": 30,
        "face_timeout_ms": 800,
        "ema_beta": 0.7,
    }
    
    def __init__(self):
        self.config_dir = Path.home() / "Library" / "Application Support" / "SmileVolume"
        self.config_file = self.config_dir / "config.json"
        self._data = self._load()
    
    def _load(self) -> dict[str, Any]:
        """Load config from disk or create default."""
        if self.config_file.exists():
            try:
                with open(self.config_file, "r") as f:
                    loaded = json.load(f)
                # Merge with defaults for any missing keys
                return {**self.DEFAULT_CONFIG, **loaded}
            except (json.JSONDecodeError, OSError):
                pass
        return self.DEFAULT_CONFIG.copy()
    
    def save(self) -> None:
        """Persist config to disk."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, "w") as f:
            json.dump(self._data, f, indent=2)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self._data.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value and save."""
        self._data[key] = value
        self.save()
    
    @property
    def last_nonzero_volume(self) -> int:
        return self._data["last_nonzero_volume"]
    
    @last_nonzero_volume.setter
    def last_nonzero_volume(self, value: int) -> None:
        self.set("last_nonzero_volume", max(1, min(100, value)))
    
    @property
    def smile_on_threshold(self) -> float:
        return self._data["smile_on_threshold"]
    
    @smile_on_threshold.setter
    def smile_on_threshold(self, value: float) -> None:
        self.set("smile_on_threshold", value)
    
    @property
    def smile_off_threshold(self) -> float:
        return self._data["smile_off_threshold"]
    
    @smile_off_threshold.setter
    def smile_off_threshold(self, value: float) -> None:
        self.set("smile_off_threshold", value)
