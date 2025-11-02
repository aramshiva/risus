"""Menu bar UI using rumps."""

import rumps
from typing import Callable, Optional


class SmileVolumeApp(rumps.App):
    """Menu bar application for smile-to-unmute control."""
    
    def __init__(
        self,
        on_toggle_enabled: Callable[[bool], None],
        on_calibrate: Callable[[], None],
        on_quit: Callable[[], None],
    ):
        """
        Args:
            on_toggle_enabled: Callback when enabled state toggled
            on_calibrate: Callback when calibration requested
            on_quit: Callback when quit requested
        """
        super().__init__("😐", quit_button=None)
        
        self._on_toggle_enabled = on_toggle_enabled
        self._on_calibrate = on_calibrate
        self._on_quit = on_quit
        
        self.enabled = True
        self.smiling = False
        
        # Build menu
        self.menu = [
            rumps.MenuItem("Enabled", callback=self._toggle_enabled),
            rumps.separator,
            rumps.MenuItem("Calibrate...", callback=self._calibrate),
            rumps.separator,
            rumps.MenuItem("Quit", callback=self._quit),
        ]
        
        # Set initial state
        self.menu["Enabled"].state = True
        self._update_icon()
    
    def _update_icon(self) -> None:
        """Update menu bar icon based on current state."""
        if not self.enabled:
            self.title = "⏸️"  # Paused
        elif self.smiling:
            self.title = "😀"  # Smiling/unmuted
        else:
            self.title = "😐"  # Not smiling/muted
    
    def set_smiling(self, smiling: bool) -> None:
        """Update smiling state indicator."""
        self.smiling = smiling
        self._update_icon()
    
    def set_enabled(self, enabled: bool) -> None:
        """Update enabled state."""
        self.enabled = enabled
        self.menu["Enabled"].state = enabled
        self._update_icon()
    
    @rumps.clicked("Enabled")
    def _toggle_enabled(self, sender: rumps.MenuItem) -> None:
        """Toggle enabled state."""
        self.enabled = not self.enabled
        sender.state = self.enabled
        self._update_icon()
        self._on_toggle_enabled(self.enabled)
    
    @rumps.clicked("Calibrate...")
    def _calibrate(self, _: rumps.MenuItem) -> None:
        """Start calibration."""
        self._on_calibrate()
    
    @rumps.clicked("Quit")
    def _quit(self, _: rumps.MenuItem) -> None:
        """Quit application."""
        self._on_quit()
        rumps.quit_application()
