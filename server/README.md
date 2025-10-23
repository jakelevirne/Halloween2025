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

Play audio files to specific channels on the UMC1820 multi-channel audio interface.

### List Available Audio Devices

```bash
uv run playSound.py --list
```

### Play Sound

```bash
# Play on default channel 3
uv run playSound.py sound/creepy-whistles-66703.mp3 --device UMC1820

# Play on specific channel
uv run playSound.py sound/file.mp3 --device UMC1820 --channel 5

# Use default audio device
uv run playSound.py sound/file.mp3 --channel 3
```

The script routes audio to a single channel while keeping other channels silent, allowing independent control of multiple speakers/props.

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
