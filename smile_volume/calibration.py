import time
from typing import Optional
from .detector import SmileDetector


class Calibrator:
    def __init__(self, detector: SmileDetector):
        self.detector = detector
    
    def _capture_average_score(self, duration_sec: float, label: str) -> Optional[float]:
        print(f"Calibrating {label}... ({duration_sec:.0f}s)")
        scores = []
        start_time = time.time()
        
        while time.time() - start_time < duration_sec:
            score = self.detector.get_smile_score()
            if score is not None:
                scores.append(score)
            
            remaining = duration_sec - (time.time() - start_time)
            print(f"\r  {remaining:.1f}s remaining...", end="", flush=True)
            time.sleep(0.05)
        
        print()
        
        if not scores:
            print("  ❌ No face detected!")
            return None
        
        avg = sum(scores) / len(scores)
        print(f"  ✓ Average score: {avg:.3f}")
        return avg
    
    def run(self) -> tuple[Optional[float], Optional[float]]:
        print("\n=== Smile Detection Calibration ===\n")
        
        print("1️⃣  Keep a NEUTRAL expression (no smile)")
        input("   Press Enter when ready...")
        neutral_score = self._capture_average_score(5.0, "neutral face")
        
        if neutral_score is None:
            return None, None
        
        print()
        
        print("2️⃣  Now SMILE naturally")
        input("   Press Enter when ready...")
        smile_score = self._capture_average_score(5.0, "smiling face")
        
        if smile_score is None:
            return None, None
        
        margin = (smile_score - neutral_score) * 0.15
        smile_off = neutral_score + margin
        smile_on = smile_score - margin
        
        print(f"\n✅ Calibration complete!")
        print(f"   Neutral:  {neutral_score:.3f}")
        print(f"   Smiling:  {smile_score:.3f}")
        print(f"   Threshold OFF: {smile_off:.3f}")
        print(f"   Threshold ON:  {smile_on:.3f}\n")
        
        return smile_on, smile_off
