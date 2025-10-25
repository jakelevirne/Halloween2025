# See README.md for setup and usage instructions


import asyncio
import time
import numpy as np
import sounddevice as sd
import soundfile as sf
import paho.mqtt.client as mqtt
from paho.mqtt.client import CallbackAPIVersion

# Speaker channel mapping:
# 1-door
# 2-werewolf
# 3-bubba
# 4-coffin
# 5-witches

# ===== AUDIO CONFIGURATION =====
AUDIO_DEVICE = "UMC1820"  # Audio device name
COFFIN_SOUND_FILE = "sound/witch-laugh-189108.mp3"  # Change this to switch sounds
COFFIN_SPEAKER_CHANNEL = 4  # Speaker channel for coffin

# Constants for device names
PROP3 = "54:32:04:46:61:88" # COFFIN SENSOR

SENSOR_THRESHOLD = 0
COOLDOWN_SECONDS = 10  # Minimum time between runs for each prop
prop_active = False  # Track if any prop is currently running
last_run_time = {PROP3: 0}  # Track last run time for each prop

# Dictionary to store lists for each device
queues = {
    PROP3: []
}

# Define MQTT parameters
mqtt_broker = "192.168.86.2"
client = mqtt.Client(CallbackAPIVersion.VERSION2, client_id="server_sounds")
client.connect(mqtt_broker)

# Simple logging function with timestamp
def log(message):
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()) + f".{int(time.time() * 1000) % 1000:03d}"
    print(f"[{timestamp}] {message}")

# Audio playback functions
def find_device_by_name(name):
    """Find device index by name (partial match)."""
    devices = sd.query_devices()
    for idx, device in enumerate(devices):
        if name.lower() in device['name'].lower():
            return idx
    return None

def play_sound_on_channel(audio_file, channel, device_name):
    """
    Play an audio file on a specific channel.
    Stops any currently playing audio first.
    """
    # Stop any currently playing audio
    sd.stop()

    # Find device
    device_idx = find_device_by_name(device_name)
    if device_idx is None:
        log(f"Error: Audio device '{device_name}' not found")
        return

    device_info = sd.query_devices(device_idx)
    max_channels = device_info['max_output_channels']

    if channel < 1 or channel > max_channels:
        log(f"Error: Channel {channel} out of range (1-{max_channels})")
        return

    # Load audio file
    data, sample_rate = sf.read(audio_file, dtype='float32')

    # Handle stereo/mono - mix to mono
    if len(data.shape) == 2:  # Stereo
        samples = data.mean(axis=1)
    else:  # Mono
        samples = data

    # Create multi-channel output array (all channels silent except target)
    output = np.zeros((len(samples), max_channels), dtype=np.float32)
    output[:, channel - 1] = samples  # channel-1 for 0-indexed

    # Play audio in the background (non-blocking)
    sd.play(output, samplerate=sample_rate, device=device_idx)

    duration = len(samples) / sample_rate
    log(f"Playing {audio_file} on channel {channel} ({duration:.2f}s)")

# Function to handle MQTT messages
def on_message(client, userdata, message, properties=None):
    device_id = message.topic.split("/")[1]  # Extract device ID from the topic
    if device_id in queues:
        queues[device_id].append(message)

# Set up MQTT subscription with updated topic names
for device_id in queues:
    client.subscribe(f"device/{device_id}/sensor")  # Updated topic for subscription
client.on_message = on_message


# COFFIN
async def process_queue_PROP3():
    global prop_active
    while True:
        await asyncio.sleep(0.3)
        if len(queues[PROP3]) >= 2:
            # Copy the queue and keep the last message for next cycle
            messages = queues[PROP3][:]
            queues[PROP3] = [messages[-1]]  # Keep last message to check consecutive across cycles

            payloads = [int(message.payload.decode()) for message in messages]  # Extract payloads as integers
            log(f"PROP3 Payloads: {payloads}  # COFFIN")

            # Check for two consecutive payloads > SENSOR_THRESHOLD
            consecutive_high = False
            for i in range(len(payloads) - 1):
                if payloads[i] > SENSOR_THRESHOLD and payloads[i + 1] > SENSOR_THRESHOLD:
                    consecutive_high = True
                    break

            # Check cooldown and prop_active before triggering
            current_time = time.time()
            time_since_last_run = current_time - last_run_time[PROP3]
            if consecutive_high and not prop_active and time_since_last_run >= COOLDOWN_SECONDS:
                prop_active = True
                last_run_time[PROP3] = current_time
                log("COFFIN triggered")
                # Play sound on coffin speaker channel
                play_sound_on_channel(COFFIN_SOUND_FILE, COFFIN_SPEAKER_CHANNEL, AUDIO_DEVICE)
                await asyncio.sleep(10)  # Delay after running the prop
                queues[PROP3] = []  # Clear all events that came in during the delay
                prop_active = False


# Define the event loop
async def event_loop():
    while True:
        # All this main loop does is print the current time every .5 seconds
        await asyncio.sleep(0.5)
        current_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()) + f".{int(time.time() * 1000) % 1000:03d}"
        # print(current_time)


# Start the event loop
if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.create_task(event_loop())
    loop.create_task(process_queue_PROP3())

    client.loop_start()
    loop.run_forever()
