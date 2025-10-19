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

### Adding New Dependencies

```bash
# Add a new package
uv add package-name

# Or manually add to requirements.txt and sync
uv sync
```

### Common Commands

```bash
# Show Python version
uv run python --version

# Run any Python script
uv run python your_script.py

# Install a specific package version
uv add package-name==1.2.3
```

## How It Works

The `uv` tool handles everything:
- Creates and manages a virtual environment automatically
- Installs packages without conflicts
- No need to activate/deactivate environments
- Just prefix commands with `uv run`

## Props

- PROP1 (`60:55:F9:7B:5F:2C`) - Phone Hall Sensor
- PROP2 (`60:55:F9:7B:98:14`) - Coffin
- PROP3 (`60:55:F9:7B:63:88`) - Werewolf
- PROP4 (`60:55:F9:7B:82:30`) - Coffin Hall Sensor
- PROP5 (`60:55:F9:7B:60:BC`) - Scarecrow
- PROP6 (`60:55:F9:7B:7F:98`) - Phone

## MQTT Broker

Default: `192.168.86.2`
