"""Main entry point for smile-to-unmute volume control."""

import argparse
import sys
import threading
import time

from .calibration import Calibrator
from .config import Config
from .detector import SmileDetector
from .state import HysteresisStateMachine, SmileState
from .volume import VolumeController


class SmileVolumeController:
    """Main controller orchestrating smile detection and volume control."""
    
    def __init__(self, config: Config, no_menubar: bool = False):
        """
        Args:
            config: Configuration instance
            no_menubar: Run in CLI mode without menu bar
        """
        self.config = config
        self.no_menubar = no_menubar
        
        self.detector = SmileDetector(
            camera_index=config.get("camera_index"),
            ema_beta=config.get("ema_beta"),
            face_timeout_ms=config.get("face_timeout_ms"),
        )
        
        self.volume = VolumeController(min_interval_ms=250)
        
        self.state_machine = HysteresisStateMachine(
            on_threshold=config.smile_on_threshold,
            off_threshold=config.smile_off_threshold,
            on_frames=config.get("on_frames"),
            off_frames=config.get("off_frames"),
        )
        
        self.enabled = True
        self.running = False
        self.menu_app = None
        self._last_volume_check = 0.0
    
    def _update_last_nonzero_volume(self) -> None:
        """Poll and save current volume if non-zero (only when smiling)."""
        now = time.time()
        if now - self._last_volume_check < 1.0:  # Poll every 1s max
            return
        
        self._last_volume_check = now
        
        if self.state_machine.get_state() == SmileState.SMILING:
            try:
                current = self.volume.get_volume()
                if current > 0:
                    self.config.last_nonzero_volume = current
            except Exception:
                pass  # Ignore volume read errors
    
    def _detection_loop(self) -> None:
        """Main detection and control loop."""
        poll_interval = self.config.get("poll_interval_ms") / 1000.0
        
        try:
            self.detector.start()
            print("🎥 Camera started")
            
            while self.running:
                if not self.enabled:
                    time.sleep(poll_interval)
                    continue
                
                # Get current smile score
                score = self.detector.get_smile_score()
                
                # Update state machine
                state, state_changed = self.state_machine.update(score)
                
                # Handle state transitions
                if state_changed:
                    if state == SmileState.NOT_SMILING:
                        print("😐 Not smiling → Volume set to 0%")
                        self.volume.set_volume(0)
                        if self.menu_app:
                            self.menu_app.set_smiling(False)
                    
                    elif state == SmileState.SMILING:
                        print(f"😀 Smiling! → Volume set to 100%")
                        self.volume.set_volume(100)
                        if self.menu_app:
                            self.menu_app.set_smiling(True)
                
                # Update saved volume periodically when smiling
                self._update_last_nonzero_volume()
                
                time.sleep(poll_interval)
        
        except Exception as e:
            print(f"❌ Error in detection loop: {e}")
        
        finally:
            self.detector.stop()
            print("🛑 Camera stopped")
    
    def start(self) -> None:
        """Start the controller."""
        self.running = True
        
        # Start detection in background thread
        detection_thread = threading.Thread(target=self._detection_loop, daemon=True)
        detection_thread.start()
        
        print("✅ Smile-to-unmute started")
        print(f"   Smile ON threshold:  {self.config.smile_on_threshold:.3f}")
        print(f"   Smile OFF threshold: {self.config.smile_off_threshold:.3f}")
        print(f"   Restore volume: {self.config.last_nonzero_volume}%")
        print()
    
    def stop(self) -> None:
        """Stop the controller gracefully."""
        print("\n🛑 Stopping...")
        self.running = False
        time.sleep(0.5)  # Allow detection loop to exit
    
    def toggle_enabled(self, enabled: bool) -> None:
        """Toggle enforcement on/off."""
        self.enabled = enabled
        print(f"{'✅ Enabled' if enabled else '⏸️ Disabled'}")
    
    def calibrate(self) -> None:
        """Run calibration wizard."""
        print("\n⏸️ Pausing detection for calibration...")
        was_running = self.running
        self.running = False
        time.sleep(0.5)
        
        try:
            self.detector.start()
            calibrator = Calibrator(self.detector)
            smile_on, smile_off = calibrator.run()
            
            if smile_on is not None and smile_off is not None:
                self.config.smile_on_threshold = smile_on
                self.config.smile_off_threshold = smile_off
                
                # Update state machine with new thresholds
                self.state_machine.on_threshold = smile_on
                self.state_machine.off_threshold = smile_off
                
                print("💾 Thresholds saved to config")
        
        finally:
            self.detector.stop()
            
            if was_running:
                self.running = True
                detection_thread = threading.Thread(target=self._detection_loop, daemon=True)
                detection_thread.start()
                print("▶️ Detection resumed\n")


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Smile-to-unmute volume control")
    parser.add_argument("--camera-index", type=int, help="Camera device index")
    parser.add_argument("--smile-on", type=float, help="Smile ON threshold")
    parser.add_argument("--smile-off", type=float, help="Smile OFF threshold")
    parser.add_argument("--on-frames", type=int, help="Consecutive frames for smile ON")
    parser.add_argument("--off-frames", type=int, help="Consecutive frames for smile OFF")
    parser.add_argument("--poll-interval-ms", type=int, help="Polling interval (ms)")
    parser.add_argument("--default-restore", type=int, help="Default restore volume %")
    parser.add_argument("--no-menubar", action="store_true", help="Run in CLI mode")
    parser.add_argument("--calibrate", action="store_true", help="Run calibration and exit")
    
    args = parser.parse_args()
    
    # Load config and apply CLI overrides
    config = Config()
    
    if args.camera_index is not None:
        config.set("camera_index", args.camera_index)
    if args.smile_on is not None:
        config.smile_on_threshold = args.smile_on
    if args.smile_off is not None:
        config.smile_off_threshold = args.smile_off
    if args.on_frames is not None:
        config.set("on_frames", args.on_frames)
    if args.off_frames is not None:
        config.set("off_frames", args.off_frames)
    if args.poll_interval_ms is not None:
        config.set("poll_interval_ms", args.poll_interval_ms)
    if args.default_restore is not None:
        config.last_nonzero_volume = args.default_restore
    
    # Create controller
    controller = SmileVolumeController(config, no_menubar=args.no_menubar)
    
    # Calibration mode
    if args.calibrate:
        controller.calibrate()
        return
    
    # Start detection
    controller.start()
    
    # Menu bar mode
    if not args.no_menubar:
        try:
            from .ui_menubar import SmileVolumeApp
            
            app = SmileVolumeApp(
                on_toggle_enabled=controller.toggle_enabled,
                on_calibrate=controller.calibrate,
                on_quit=controller.stop,
            )
            controller.menu_app = app
            
            print("🍎 Menu bar app running (Cmd+C to quit)")
            app.run()
        
        except ImportError:
            print("⚠️ rumps not available, falling back to CLI mode")
            args.no_menubar = True
    
    # CLI mode
    if args.no_menubar:
        try:
            print("⌨️ CLI mode (Ctrl+C to quit)")
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            controller.stop()


if __name__ == "__main__":
    main()
