# See README.md for setup and usage instructions


import asyncio
import time
import paho.mqtt.client as mqtt
from paho.mqtt.client import CallbackAPIVersion

# Constants for device names
PROP3 = "54:32:04:46:61:88" # COFFIN SENSOR

SENSOR_THRESHOLD = 0
COOLDOWN_SECONDS = 80  # Minimum time between runs for each prop
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
                log("COFFIN SOUND")
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
