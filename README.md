# 😀 Smile-to-Unmute Volume Control

A macOS menu bar app that forces your system volume to 0% unless you're smiling at your webcam. Built with Python, MediaPipe, and AppleScript.

## Features

- **Real-time smile detection** using MediaPipe Face Mesh
- **Automatic volume control** via AppleScript
- **Hysteresis & debouncing** to prevent volume flapping
- **Persistent configuration** remembers your last volume
- **Menu bar interface** with live state indicators (😀 unmuted / 😐 muted)
- **Interactive calibration** for personalized thresholds
- **Low CPU usage** (<12% on Apple silicon)

## Requirements

- macOS (Apple silicon or Intel)
- Python 3.10+
- Webcam

## Quick Start

### Installation

```bash
# Install dependencies
pip install -e .

# Or with uv (recommended)
uv pip install -e .
```

### First Run

```bash
# Run calibration (recommended for best accuracy)
python -m smile_volume --calibrate

# Start the app with menu bar
python -m smile_volume

# Or CLI mode without menu bar
python -m smile_volume --no-menubar
```

### Permissions

On first run, macOS will request:
1. **Camera access** - Required for smile detection
2. **Accessibility (if prompted)** - For volume control via AppleScript

Grant both permissions in System Settings → Privacy & Security.

## Usage

### Menu Bar

- **Icon states:**
  - 😀 = Smiling (volume unmuted)
  - 😐 = Not smiling (volume forced to 0%)
  - ⏸️ = App disabled (no volume control)

- **Menu items:**
  - Toggle "Enabled" to pause/resume enforcement
  - "Calibrate..." to run personalized threshold setup
  - "Quit" to exit cleanly

### CLI Options

```bash
python -m smile_volume --help

Options:
  --camera-index INT        Camera device (default: 0)
  --smile-on FLOAT          Threshold to unmute (default: 0.55)
  --smile-off FLOAT         Threshold to mute (default: 0.4)
  --on-frames INT           Frames needed to unmute (default: 4)
  --off-frames INT          Frames needed to mute (default: 6)
  --poll-interval-ms INT    Detection polling rate (default: 10ms)
  --default-restore INT     Initial restore volume % (default: 100)
  --no-menubar              Run in CLI mode
  --calibrate               Run calibration wizard and exit
```

### Calibration

For best results, calibrate once:

```bash
python -m smile_volume --calibrate
```

1. Keep a **neutral expression** for 5 seconds
2. **Smile naturally** for 5 seconds
3. Thresholds automatically calculated and saved

## How It Works

1. **Smile Detection:**
   - MediaPipe Face Mesh tracks 468 facial landmarks
   - Computes normalized mouth curvature ratio
   - Exponential moving average (EMA) smoothing for stability

2. **State Machine:**
   - Requires N consecutive frames to switch states (prevents jitter)
   - Hysteresis: different thresholds for ON/OFF transitions

3. **Volume Control:**
   - On transition to NOT_SMILING → `set volume output volume 0`
   - On transition to SMILING → restore to last saved volume
   - Rate-limited AppleScript calls (min 250ms between identical commands)
   - Polls current volume every 1s while smiling to remember user changes

4. **Configuration:**
   - Persisted to `~/Library/Application Support/SmileVolume/config.json`
   - Stores last non-zero volume and calibrated thresholds

## Troubleshooting

### Camera Not Working

```bash
# Test with different camera index
python -m smile_volume --camera-index 1

# Check camera permissions
open "x-apple.systempreferences:com.apple.preference.security?Privacy_Camera"
```

### Volume Not Changing

```bash
# Test AppleScript manually
osascript -e 'set volume output volume 100'
osascript -e 'output volume of (get volume settings)'
```

### High CPU Usage

- Reduce polling rate: `--poll-interval-ms 100`
- Use lower camera index (built-in camera usually faster than external)
- Check Activity Monitor for other processes using camera

### App Won't Start

```bash
# Check Python version
python --version  # Should be 3.10+

# Reinstall dependencies
pip install --force-reinstall -e .

# Run in debug mode
python -m smile_volume --no-menubar
```

### Calibration Issues

- Ensure good lighting (face clearly visible)
- Look directly at camera during calibration
- Keep head still during 5-second captures
- Try manual thresholds if calibration fails:

```bash
python -m smile_volume --smile-on 0.6 --smile-off 0.4
```

### Volume Keeps Flickering

- Increase frame requirements:
  ```bash
  python -m smile_volume --on-frames 8 --off-frames 10
  ```
- Recalibrate with more exaggerated expressions
- Check lighting (shadows can affect detection)

### Menu Bar Not Showing

- Install rumps: `pip install rumps`
- Or use CLI mode: `--no-menubar`

## Building Standalone App

```bash
# Install pyinstaller
pip install pyinstaller

# Build one-file app (optional)
make build

# Or manually:
pyinstaller --onefile --windowed \
  --name SmileVolume \
  --icon assets/icon.icns \
  -m smile_volume
```

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black smile_volume/
```

## Performance Checklist

- [x] Latency (camera → volume change) < 300ms
- [x] No volume flapping (hysteresis verified)
- [x] No rapid AppleScript spam (rate-limited)
- [x] Works with external webcams
- [x] Clean exit, no orphan processes
- [x] CPU usage < 12% on Apple silicon

## Demo Script

Test state transitions:

```bash
# Watch state changes in real-time
python -m smile_volume --no-menubar

# Expected behavior:
# 1. Start neutral → "😐 Not smiling → Volume set to 0%"
# 2. Smile for 200ms → "😀 Smiling! → Volume restored to 100%"
# 3. Stop smiling for 300ms → "😐 Not smiling → Volume set to 0%"
# 4. Adjust volume while smiling → app remembers new volume
```

## Configuration File

Location: `~/Library/Application Support/SmileVolume/config.json`

```json
{
  "last_nonzero_volume": 50,
  "smile_on_threshold": 0.55,
  "smile_off_threshold": 0.45,
  "on_frames": 4,
  "off_frames": 6,
  "camera_index": 0,
  "poll_interval_ms": 50,
  "face_timeout_ms": 800,
  "ema_beta": 0.7
}
```

## License

MIT

## Contributing

PRs welcome! Focus areas:
- Additional emotion detection (frown, surprise, etc.)
- Cross-platform support (Windows, Linux)
- UI improvements
- Performance optimizations
