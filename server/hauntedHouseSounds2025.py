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
WITCHES_SOUNDS = [
    ("sound/2025/2_Speaker1.mp3", 1),
    ("sound/2025/2_Speaker2.mp3", 2),
    ("sound/2025/2_Speaker3.mp3", 3),
    ("sound/2025/2_Speaker4.mp3", 4),
    ("sound/2025/2_Speaker5.mp3", 5),
]
COFFIN_SOUNDS = [
    ("sound/2025/3_Speaker1.mp3", 1),
    ("sound/2025/3_Speaker2.mp3", 2),
    ("sound/2025/3_Speaker3.mp3", 3),
    ("sound/2025/3_Speaker4.mp3", 4),
    ("sound/2025/3_Speaker5.mp3", 5),
]
BUBBA_SOUNDS = [
    ("sound/2025/4_Speaker1.mp3", 1),
    ("sound/2025/4_Speaker2.mp3", 2),
    ("sound/2025/4_Speaker3.mp3", 3),
    ("sound/2025/4_Speaker4.mp3", 4),
    ("sound/2025/4_Speaker5.mp3", 5),
]
SCARECROW_SOUNDS = [
    ("sound/2025/6_Speaker1.mp3", 1),
    ("sound/2025/6_Speaker2.mp3", 2),
    ("sound/2025/6_Speaker3.mp3", 3),
    ("sound/2025/6_Speaker4.mp3", 4),
    ("sound/2025/6_Speaker5.mp3", 5),
]

# Constants for device names
PROP2 = "60:55:F9:7B:5F:2C" # WITCHES AREA SENSOR
PROP3 = "54:32:04:46:61:88" # COFFIN SENSOR
PROP4 = "60:55:F9:7B:60:BC" # BUBBA SENSOR
PROP6 = "60:55:F9:7B:82:30" # SCARECROW SENSOR

SENSOR_THRESHOLD = 0
COOLDOWN_SECONDS = 10  # Minimum time between runs for each prop
MIN_SOUND_PLAY_TIME = 5  # Minimum seconds a sound must play before being interrupted
sound_started_time = 0  # Track when current sound started playing
last_run_time = {PROP2: 0, PROP3: 0, PROP4: 0, PROP6: 0}  # Track last run time for each prop

# Dictionary to store lists for each device
queues = {
    PROP2: [],
    PROP3: [],
    PROP4: [],
    PROP6: []
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

def play_sound_on_multiple_channels(audio_file, channels, device_name):
    """
    Play an audio file on multiple channels simultaneously.
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

    # Validate all channels
    for channel in channels:
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

    # Create multi-channel output array
    output = np.zeros((len(samples), max_channels), dtype=np.float32)

    # Add the same audio to all specified channels
    for channel in channels:
        output[:, channel - 1] = samples  # channel-1 for 0-indexed

    # Play audio in the background (non-blocking)
    sd.play(output, samplerate=sample_rate, device=device_idx)

    duration = len(samples) / sample_rate
    channel_str = ', '.join(map(str, channels))
    log(f"Playing {audio_file} on channels {channel_str} ({duration:.2f}s)")

def play_different_sounds_on_channels(audio_specs, device_name):
    """
    Play different audio files on different channels simultaneously.
    Stops any currently playing audio first.

    Args:
        audio_specs: List of (audio_file, channel) tuples
        device_name: Audio device name
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

    # Load all audio files
    loaded_audio = []
    max_sample_rate = 0
    max_length = 0

    for audio_file, channel in audio_specs:
        if channel < 1 or channel > max_channels:
            log(f"Error: Channel {channel} out of range (1-{max_channels})")
            return

        try:
            # Load audio file
            data, sample_rate = sf.read(audio_file, dtype='float32')

            # Handle stereo/mono - mix to mono
            if len(data.shape) == 2:  # Stereo
                samples = data.mean(axis=1)
            else:  # Mono
                samples = data

            loaded_audio.append({
                'samples': samples,
                'sample_rate': sample_rate,
                'channel': channel,
                'file': audio_file
            })

            max_sample_rate = max(max_sample_rate, sample_rate)
            max_length = max(max_length, len(samples))

        except Exception as e:
            log(f"Error loading {audio_file}: {e}")
            return

    if not loaded_audio:
        log("Error: No audio files loaded successfully")
        return

    # Resample all audio to the highest sample rate if needed
    for audio in loaded_audio:
        if audio['sample_rate'] != max_sample_rate:
            ratio = max_sample_rate / audio['sample_rate']
            new_length = int(len(audio['samples']) * ratio)
            audio['samples'] = np.interp(
                np.linspace(0, len(audio['samples']) - 1, new_length),
                np.arange(len(audio['samples'])),
                audio['samples']
            )
            audio['sample_rate'] = max_sample_rate
            max_length = max(max_length, len(audio['samples']))

    # Create multi-channel output array
    output = np.zeros((max_length, max_channels), dtype=np.float32)

    # Mix each audio file into its designated channel
    for audio in loaded_audio:
        channel_idx = audio['channel'] - 1  # Convert to 0-indexed
        samples = audio['samples']

        # Pad with silence if shorter than max_length
        if len(samples) < max_length:
            padded = np.zeros(max_length, dtype=np.float32)
            padded[:len(samples)] = samples
            samples = padded

        # Add to the output channel
        output[:, channel_idx] = samples

    # Play audio in the background (non-blocking)
    sd.play(output, samplerate=max_sample_rate, device=device_idx)

    duration = max_length / max_sample_rate
    channel_str = ', '.join(str(ch) for _, ch in audio_specs)
    log(f"Playing {len(audio_specs)} sounds on channels {channel_str} ({duration:.2f}s)")

# Function to handle MQTT messages
def on_message(client, userdata, message, properties=None):
    device_id = message.topic.split("/")[1]  # Extract device ID from the topic
    if device_id in queues:
        queues[device_id].append(message)

# Set up MQTT subscription with updated topic names
for device_id in queues:
    client.subscribe(f"device/{device_id}/sensor")  # Updated topic for subscription
client.on_message = on_message


# WITCHES
async def process_queue_PROP2():
    global sound_started_time
    while True:
        await asyncio.sleep(0.3)
        if len(queues[PROP2]) >= 2:
            # Copy the queue and keep the last message for next cycle
            messages = queues[PROP2][:]
            queues[PROP2] = [messages[-1]]  # Keep last message to check consecutive across cycles

            payloads = [int(message.payload.decode()) for message in messages]  # Extract payloads as integers
            log(f"PROP2 Payloads: {payloads}  # WITCHES")

            # Check for two consecutive payloads > SENSOR_THRESHOLD
            consecutive_high = False
            for i in range(len(payloads) - 1):
                if payloads[i] > SENSOR_THRESHOLD and payloads[i + 1] > SENSOR_THRESHOLD:
                    consecutive_high = True
                    break

            # Check cooldown and if current sound has played long enough
            current_time = time.time()
            time_since_last_run = current_time - last_run_time[PROP2]
            time_since_sound_started = current_time - sound_started_time

            if consecutive_high and time_since_last_run >= COOLDOWN_SECONDS and time_since_sound_started >= MIN_SOUND_PLAY_TIME:
                last_run_time[PROP2] = current_time
                sound_started_time = current_time
                log("WITCHES triggered")
                # Play different sounds on each speaker channel
                play_different_sounds_on_channels(WITCHES_SOUNDS, AUDIO_DEVICE)
                await asyncio.sleep(10)  # Delay after running the prop
                queues[PROP2] = []  # Clear all events that came in during the delay


# COFFIN
async def process_queue_PROP3():
    global sound_started_time
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

            # Check cooldown and if current sound has played long enough
            current_time = time.time()
            time_since_last_run = current_time - last_run_time[PROP3]
            time_since_sound_started = current_time - sound_started_time

            if consecutive_high and time_since_last_run >= COOLDOWN_SECONDS and time_since_sound_started >= MIN_SOUND_PLAY_TIME:
                last_run_time[PROP3] = current_time
                sound_started_time = current_time
                log("COFFIN triggered")
                # Play different sounds on each speaker channel
                play_different_sounds_on_channels(COFFIN_SOUNDS, AUDIO_DEVICE)
                await asyncio.sleep(10)  # Delay after running the prop
                queues[PROP3] = []  # Clear all events that came in during the delay


# BUBBA
async def process_queue_PROP4():
    global sound_started_time
    while True:
        await asyncio.sleep(0.3)
        if len(queues[PROP4]) >= 2:
            # Copy the queue and keep the last message for next cycle
            messages = queues[PROP4][:]
            queues[PROP4] = [messages[-1]]  # Keep last message to check consecutive across cycles

            payloads = [int(message.payload.decode()) for message in messages]  # Extract payloads as integers
            log(f"PROP4 Payloads: {payloads}  # BUBBA")

            # Check for two consecutive payloads > SENSOR_THRESHOLD
            consecutive_high = False
            for i in range(len(payloads) - 1):
                if payloads[i] > SENSOR_THRESHOLD and payloads[i + 1] > SENSOR_THRESHOLD:
                    consecutive_high = True
                    break

            # Check cooldown and if current sound has played long enough
            current_time = time.time()
            time_since_last_run = current_time - last_run_time[PROP4]
            time_since_sound_started = current_time - sound_started_time

            if consecutive_high and time_since_last_run >= COOLDOWN_SECONDS and time_since_sound_started >= MIN_SOUND_PLAY_TIME:
                last_run_time[PROP4] = current_time
                sound_started_time = current_time
                log("BUBBA triggered")
                # Play different sounds on each speaker channel
                play_different_sounds_on_channels(BUBBA_SOUNDS, AUDIO_DEVICE)
                await asyncio.sleep(10)  # Delay after running the prop
                queues[PROP4] = []  # Clear all events that came in during the delay


# SCARECROW
async def process_queue_PROP6():
    global sound_started_time
    while True:
        await asyncio.sleep(0.3)
        if len(queues[PROP6]) >= 2:
            # Copy the queue and keep the last message for next cycle
            messages = queues[PROP6][:]
            queues[PROP6] = [messages[-1]]  # Keep last message to check consecutive across cycles

            payloads = [int(message.payload.decode()) for message in messages]  # Extract payloads as integers
            log(f"PROP6 Payloads: {payloads}  # SCARECROW")

            # Check for two consecutive payloads > SENSOR_THRESHOLD
            consecutive_high = False
            for i in range(len(payloads) - 1):
                if payloads[i] > SENSOR_THRESHOLD and payloads[i + 1] > SENSOR_THRESHOLD:
                    consecutive_high = True
                    break

            # Check cooldown and if current sound has played long enough
            current_time = time.time()
            time_since_last_run = current_time - last_run_time[PROP6]
            time_since_sound_started = current_time - sound_started_time

            if consecutive_high and time_since_last_run >= COOLDOWN_SECONDS and time_since_sound_started >= MIN_SOUND_PLAY_TIME:
                last_run_time[PROP6] = current_time
                sound_started_time = current_time
                log("SCARECROW triggered")
                # Play different sounds on each speaker channel
                play_different_sounds_on_channels(SCARECROW_SOUNDS, AUDIO_DEVICE)
                await asyncio.sleep(10)  # Delay after running the prop
                queues[PROP6] = []  # Clear all events that came in during the delay


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
    loop.create_task(process_queue_PROP2())
    loop.create_task(process_queue_PROP3())
    loop.create_task(process_queue_PROP4())
    loop.create_task(process_queue_PROP6())

    client.loop_start()
    loop.run_forever()
