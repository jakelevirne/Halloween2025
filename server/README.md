# Halloween Haunted House Server

MQTT-based server for controlling Halloween props with sensors and actuators.

## Quick Start

### First Time Setup

```bash
# Install dependencies (creates virtual environment automatically)
uv sync
```

### Running the Server

```bash
# Run the haunted house control loop
uv run hauntedHouseLoop.py
```

## Props & Sensors

All props use HC-SR501 PIR motion sensors with digital output (0 or 1).

1. **1-door** (`60:55:F9:7B:82:40`) - Entry door sensor
2. **2-witches** (`60:55:F9:7B:5F:2C`) - Witches area sensor
3. **3-coffin** (`54:32:04:46:61:88`) - Coffin sensor
4. **4-bubba** (`60:55:F9:7B:60:BC`) - Bubba sensor
5. **5-werewolf-front** (`60:55:F9:7B:7B:60`) - Werewolf front sensor
6. **6-scarecrow** (`60:55:F9:7B:82:30`) - Scarecrow sensor

### MQTT Topics

- Sensor data: `device/{MAC_ADDRESS}/sensor`
- Actuator control: `device/{MAC_ADDRESS}/actuator`

## Sensor Data Capture & Analysis

### Capturing Sensor Data

Record live sensor readings for analysis:

```bash
# Baseline noise capture (room empty)
# Automatically runs baseline analysis when stopped with Ctrl+C
uv run captureSensors.py

# Movement pattern capture (walk around the room)
# Automatically runs movement analysis when stopped with Ctrl+C
uv run captureSensors.py --movement

# Capture to specific file
uv run captureSensors.py data/my_capture.csv --movement

# Skip automatic analysis
uv run captureSensors.py --noanalyze

# Stop capture: Ctrl+C
```

The script captures all sensor readings with timestamps. Sensors report every ~500ms. **By default, analysis runs automatically when you stop the capture** unless you use the `--noanalyze` flag.

### Analyzing Sensor Data

The analysis runs automatically after capture, but you can also run it manually:

```bash
# Baseline noise analysis (for empty room captures)
uv run analyzeSensors.py data/sensor_data_20251021_221902.csv

# Movement pattern analysis (for walk-around captures)
uv run analyzeSensors.py data/sensor_data_20251021_221902.csv --movement
```

#### Baseline Noise Analysis

For captures when the room is empty. Identifies sensors with false positives.

**Output includes:**
- Console report: trigger %, noise levels, triggers/minute
- Visual plots:
  - Noise level by sensor (color-coded: green <1%, orange 1-5%, red >5%)
  - Total false trigger counts
  - Timeline of all false triggers
- Saved to: `data/sensor_data_YYYYMMDD_HHMMSS_analysis.png`

**Use for:**
- Identifying noisy sensors that need adjustment
- Verifying sensors aren't triggering when room is empty
- Debugging sensitivity issues

#### Movement Pattern Analysis

For captures while walking through the room. Analyzes sensor coverage and trigger sequences.

**Output includes:**
- Console report: sensor coverage, most/least active sensors
- Visual plots:
  - Activity level by sensor (green = active, gray = inactive)
  - Percentage of time each sensor was active
  - Movement timeline showing trigger sequences
- Saved to: `data/sensor_data_YYYYMMDD_HHMMSS_movement_analysis.png`

**Use for:**
- Understanding sensor coverage zones
- Finding gaps in sensor coverage
- Verifying all sensors trigger during walk-through
- Planning prop placement and trigger sequences

## Sound Playback

Play audio files to specific channels on the UMC1820 multi-channel audio interface. Supports playing up to 8 sounds simultaneously on different channels.

### List Available Audio Devices

```bash
uv run playSound.py --list
```

### Play Sounds

```bash
# Play single sound on channel 3
uv run playSound.py sound/creepy-whistles-66703.mp3:3 --device UMC1820

# Play multiple sounds simultaneously on different channels
uv run playSound.py sound/sound1.mp3:1 sound/sound2.mp3:3 sound/sound3.mp3:5 --device UMC1820

# Play up to 8 sounds at once with volume normalization
uv run playSound.py \
  sound/door.mp3:1 \
  sound/witch.mp3:2 \
  sound/scream.mp3:3 \
  sound/thunder.mp3:4 \
  sound/creepy.mp3:5 \
  --device UMC1820 \
  --normalize

# Use default audio device
uv run playSound.py sound/file.mp3:3
```

**Format:** `file.mp3:channel` (e.g., `sound/creepy.mp3:3`)

**Options:**
- `--normalize` or `-n`: Automatically equalize volume levels across all sounds (recommended when mixing multiple files)

**How it works:**
- Each audio file is routed to its designated channel
- Shorter files are padded with silence to match the longest file
- All sounds play simultaneously and stop when the longest one finishes
- Volume normalization ensures all sounds have the same peak level (prevents some from being too quiet/loud)
- Press Ctrl+C to stop playback gracefully

## Development

### Adding New Dependencies

```bash
# Add a package
uv add package-name

# Sync after manual pyproject.toml edits
uv sync
```

### How uv Works

The `uv` tool handles everything:
- Creates and manages a virtual environment automatically (`.venv/`)
- Installs packages without conflicts
- No need to activate/deactivate environments
- Just prefix commands with `uv run`

## MQTT Broker

Default: `192.168.86.2`
