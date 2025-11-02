import rumps
from typing import Callable


class SmileVolumeApp(rumps.App):
    def __init__(self, on_toggle_enabled: Callable[[bool], None], on_calibrate: Callable[[], None], on_quit: Callable[[], None]):
        super().__init__("😐", quit_button=None)
        self._on_toggle_enabled = on_toggle_enabled
        self._on_calibrate = on_calibrate
        self._on_quit = on_quit
        self.enabled = True
        self.smiling = False
        
        self.menu = [
            rumps.MenuItem("Enabled", callback=self._toggle_enabled),
            rumps.separator,
            rumps.MenuItem("Calibrate...", callback=self._calibrate),
            rumps.separator,
            rumps.MenuItem("Quit", callback=self._quit),
        ]
        
        self.menu["Enabled"].state = True
        self._update_icon()
    
    def _update_icon(self) -> None:
        if not self.enabled:
            self.title = "⏸️"
        elif self.smiling:
            self.title = "😀"
        else:
            self.title = "😐"
    
    def set_smiling(self, smiling: bool) -> None:
        self.smiling = smiling
        self._update_icon()
    
    def set_enabled(self, enabled: bool) -> None:
        self.enabled = enabled
        self.menu["Enabled"].state = enabled
        self._update_icon()
    
    @rumps.clicked("Enabled")
    def _toggle_enabled(self, sender: rumps.MenuItem) -> None:
        self.enabled = not self.enabled
        sender.state = self.enabled
        self._update_icon()
        self._on_toggle_enabled(self.enabled)
    
    @rumps.clicked("Calibrate...")
    def _calibrate(self, _: rumps.MenuItem) -> None:
        self._on_calibrate()
    
    @rumps.clicked("Quit")
    def _quit(self, _: rumps.MenuItem) -> None:
        self._on_quit()
        rumps.quit_application()
