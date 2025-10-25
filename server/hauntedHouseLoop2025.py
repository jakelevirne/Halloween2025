# See README.md for setup and usage instructions


import asyncio
import time
import paho.mqtt.client as mqtt
from paho.mqtt.client import CallbackAPIVersion
import random

# Constants for device names
PROP1 = "60:55:F9:7B:98:14" # DOOR SENSOR
PROP2 = "60:55:F9:7B:5F:2C" # WITCHES AREA SENSOR
PROP3 = "54:32:04:46:61:88" # COFFIN SENSOR
PROP4 = "60:55:F9:7B:60:BC" # BUBBA SENSOR
PROP5 = "60:55:F9:7B:7B:60" # WEREWOLF SENSOR
PROP6 = "60:55:F9:7B:82:30" # SCARECROW SENSOR  
PROP7 = "54:32:04:46:61:40" # COFFIN ACTUATOR

SENSOR_THRESHOLD = 0
fogFlipper = True

# Dictionary to store lists for each device
queues = {
    PROP1: [],
    PROP2: [],
    PROP3: [],
    PROP4: [],
    PROP5: [],
    PROP6: []
}

# Define MQTT parameters
mqtt_broker = "192.168.86.2"
client = mqtt.Client(CallbackAPIVersion.VERSION2, client_id="server")
client.connect(mqtt_broker)

# Simple logging function with timestamp
def log(message):
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()) + f".{int(time.time() * 1000) % 1000:03d}"
    print(f"[{timestamp}] {message}")

# Function to publish MQTT events
def publish_event(topic, message):
    client.publish(topic, message)
    log(f"Published event: {message} to topic {topic}")

# Function to handle MQTT messages
def on_message(client, userdata, message, properties=None):
    device_id = message.topic.split("/")[1]  # Extract device ID from the topic
    if device_id in queues:
        queues[device_id].append(message)

# Set up MQTT subscription with updated topic names
for device_id in queues:
    client.subscribe(f"device/{device_id}/sensor")  # Updated topic for subscription
client.on_message = on_message


# WEREWOLF
async def process_queue_PROP5():
    while True:
        await asyncio.sleep(0.3)
        if len(queues[PROP5]) >= 2:
            # Copy the queue and keep the last message for next cycle
            messages = queues[PROP5][:]
            queues[PROP5] = [messages[-1]]  # Keep last message to check consecutive across cycles

            payloads = [int(message.payload.decode()) for message in messages]  # Extract payloads as integers
            log(f"PROP5 Payloads: {payloads}  # WEREWOLF")

            # Check for two consecutive payloads > SENSOR_THRESHOLD
            consecutive_high = False
            for i in range(len(payloads) - 1):
                if payloads[i] > SENSOR_THRESHOLD and payloads[i + 1] > SENSOR_THRESHOLD:
                    consecutive_high = True
                    break

            if consecutive_high:
                publish_event(f"device/{PROP5}/actuator", "X30")  # Publish event when two consecutive readings exceed threshold
                await asyncio.sleep(60)  # Delay after running the werewolf
                queues[PROP5] = []  # Clear all events that came in during the delay


# SCARECROW
async def process_queue_PROP6():
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

            if consecutive_high:
                publish_event(f"device/{PROP6}/actuator", "X2")  # Publish event when two consecutive readings exceed threshold
                await asyncio.sleep(60)  # Delay after running the werewolf
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
    loop.create_task(process_queue_PROP5())
    loop.create_task(process_queue_PROP6())
    client.loop_start()
    loop.run_forever()
