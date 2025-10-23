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

1. **1-door** (`60:55:F9:7B:98:14`) - Entry door sensor
2. **2-witches** (`60:55:F9:7B:63:88`) - Witches area sensor
3. **3-mask-wall** (`60:55:F9:7B:5F:2C`) - Mask wall sensor
4. **4-coffin** (`54:32:04:46:61:88`) - Coffin sensor
5. **5-bubba-garage-door** (`60:55:F9:7B:60:BC`) - Bubba/garage door sensor
6. **6-creepy-window** (`60:55:F9:7B:7F:98`) - Creepy window sensor
7. **7-werewolf-rear** (`60:55:F9:7B:82:40`) - Werewolf rear sensor
8. **8-werewolf-front** (`60:55:F9:7B:7B:60`) - Werewolf front sensor
9. **9-scarecrow** (`60:55:F9:7B:82:30`) - Scarecrow sensor

### MQTT Topics

- Sensor data: `device/{MAC_ADDRESS}/sensor`
- Actuator control: `device/{MAC_ADDRESS}/actuator`

## Sensor Data Capture & Analysis

### Capturing Sensor Data

Record live sensor readings for analysis:

```bash
# Start capturing (saves to data/sensor_data_YYYYMMDD_HHMMSS.csv)
uv run captureSensors.py

# Capture to specific file
uv run captureSensors.py data/my_capture.csv

# Stop capture: Ctrl+C
```

The script captures all sensor readings with timestamps. Sensors report every ~500ms.

### Analyzing Sensor Data

Analyze captured data to understand noise patterns and sensor behavior:

```bash
# Analyze a capture file
uv run analyzeSensors.py data/sensor_data_20251021_221902.csv
```

The analysis generates:
- Console report with statistics (trigger %, noise levels, triggers/minute)
- Visual plots showing:
  - Noise level by sensor (color-coded: green <1%, orange 1-5%, red >5%)
  - Total trigger counts
  - Timeline of all triggers
- Output saved to: `data/sensor_data_YYYYMMDD_HHMMSS_analysis.png`

**Use Cases:**
- **Baseline noise analysis**: Capture when room is empty to identify noisy sensors
- **Movement tracking**: Capture while walking through to understand sensor coverage
- **Debugging**: Identify sensors that need sensitivity adjustment

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

# Play up to 8 sounds at once
uv run playSound.py \
  sound/door.mp3:1 \
  sound/witch.mp3:2 \
  sound/scream.mp3:3 \
  sound/thunder.mp3:4 \
  sound/creepy.mp3:5 \
  --device UMC1820

# Use default audio device
uv run playSound.py sound/file.mp3:3
```

**Format:** `file.mp3:channel` (e.g., `sound/creepy.mp3:3`)

**How it works:**
- Each audio file is routed to its designated channel
- Shorter files are padded with silence to match the longest file
- All sounds play simultaneously and stop when the longest one finishes
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
