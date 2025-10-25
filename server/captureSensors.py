#!/usr/bin/env python3
"""
Capture sensor data from PIR motion sensors for analysis.

This script subscribes to all sensor MQTT topics and logs the data stream
to a CSV file with timestamps. The sensors are HC-SR501 PIR sensors configured
for digital reads (0 or 1).

Usage:
    uv run captureSensors.py [output_file] [--noanalyze]

    Default output: data/sensor_data_YYYYMMDD_HHMMSS.csv
    --noanalyze: Skip automatic analysis after capture

To stop capture: Ctrl+C

The output CSV format is:
    timestamp,device_id,device_name,sensor_value

After capture stops, analyzeSensors.py will automatically run unless --noanalyze is specified.
"""

import paho.mqtt.client as mqtt
from paho.mqtt.client import CallbackAPIVersion
import time
import sys
import csv
from datetime import datetime
import signal
import subprocess

# Sensor definitions with friendly names
SENSORS = {
    "60:55:F9:7B:98:14": "1-door",
    "60:55:F9:7B:5F:2C": "2-witches",
    "54:32:04:46:61:88": "3-coffin",
    "60:55:F9:7B:60:BC": "4-bubba",
    "60:55:F9:7B:7B:60": "5-werewolf-front",
    "60:55:F9:7B:82:30": "6-scarecrow",
}

# MQTT broker configuration
MQTT_BROKER = "192.168.86.2"
MQTT_CLIENT_ID = "sensor_capture"

# Global variables
csv_writer = None
csv_file = None
message_count = 0
start_time = None
run_analysis = True
output_filename = None


def on_connect(client, userdata, flags, rc, properties=None):
    """Callback when connected to MQTT broker."""
    if rc == 0:
        print(f"Connected to MQTT broker at {MQTT_BROKER}")
        print("Subscribing to sensor topics...")

        # Subscribe to all sensor topics
        for device_id, device_name in SENSORS.items():
            topic = f"device/{device_id}/sensor"
            client.subscribe(topic)
            print(f"  {device_name}: {topic}")

        print("\nCapturing sensor data... (Press Ctrl+C to stop)")
        print("-" * 60)
    else:
        print(f"Failed to connect to MQTT broker. Return code: {rc}")
        sys.exit(1)


def on_message(client, userdata, message, properties=None):
    """Callback when a message is received."""
    global csv_writer, message_count, start_time

    # Extract device ID from topic (format: device/MAC_ADDRESS/sensor)
    topic_parts = message.topic.split("/")
    if len(topic_parts) >= 2:
        device_id = topic_parts[1]
        device_name = SENSORS.get(device_id, "unknown")

        # Decode sensor value (should be 0 or 1)
        try:
            sensor_value = int(message.payload.decode().strip())
        except ValueError:
            sensor_value = message.payload.decode().strip()

        # Get high-precision timestamp
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]  # millisecond precision

        # Write to CSV
        if csv_writer:
            csv_writer.writerow([timestamp, device_id, device_name, sensor_value])
            csv_file.flush()  # Ensure data is written immediately

            message_count += 1

            # Print periodic status updates
            if message_count % 100 == 0:
                elapsed = time.time() - start_time
                rate = message_count / elapsed if elapsed > 0 else 0
                print(f"Captured {message_count} messages ({rate:.1f} msg/sec)")


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully."""
    global output_filename

    print("\n" + "-" * 60)
    print(f"\nCapture stopped. Total messages captured: {message_count}")

    if start_time:
        elapsed = time.time() - start_time
        print(f"Capture duration: {elapsed:.1f} seconds")
        print(f"Average rate: {message_count / elapsed:.1f} messages/second")

    if csv_file:
        print(f"\nData saved to: {csv_file.name}")
        output_filename = csv_file.name
        csv_file.close()

    # Run analysis unless --noanalyze was specified
    if run_analysis and output_filename and message_count > 0:
        print("\n" + "=" * 60)
        print("Running automatic analysis...")
        print("=" * 60)
        try:
            subprocess.run(["uv", "run", "analyzeSensors.py", output_filename])
        except Exception as e:
            print(f"Error running analysis: {e}")
            print(f"You can manually run: uv run analyzeSensors.py {output_filename}")

    sys.exit(0)


def main():
    global csv_writer, csv_file, start_time, run_analysis, output_filename

    # Set up signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)

    # Ensure data directory exists
    import os
    os.makedirs('data', exist_ok=True)

    # Parse command line arguments
    args = [arg for arg in sys.argv[1:] if not arg.startswith('--')]
    flags = [arg for arg in sys.argv[1:] if arg.startswith('--')]

    # Check for --noanalyze flag
    if '--noanalyze' in flags:
        run_analysis = False

    # Determine output filename
    if len(args) > 0:
        output_filename = args[0]
    else:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_filename = f"data/sensor_data_{timestamp}.csv"

    # Open CSV file for writing
    csv_file = open(output_filename, 'w', newline='')
    csv_writer = csv.writer(csv_file)

    # Write CSV header
    csv_writer.writerow(['timestamp', 'device_id', 'device_name', 'sensor_value'])
    csv_file.flush()

    print(f"Sensor Data Capture")
    print("=" * 60)
    print(f"Output file: {output_filename}")
    print(f"MQTT Broker: {MQTT_BROKER}")
    print(f"Sensors: {len(SENSORS)}")
    print()

    # Connect to MQTT broker
    # Use clean_session=True to avoid receiving any queued/retained messages
    client = mqtt.Client(
        CallbackAPIVersion.VERSION2,
        client_id=MQTT_CLIENT_ID,
        clean_session=True
    )
    client.on_connect = on_connect
    client.on_message = on_message

    try:
        client.connect(MQTT_BROKER)
    except Exception as e:
        print(f"Error connecting to MQTT broker: {e}")
        csv_file.close()
        sys.exit(1)

    # Record start time
    start_time = time.time()

    # Start MQTT loop (blocking)
    client.loop_forever()


if __name__ == "__main__":
    main()
