# Halloween2024

This was year 2 of the MQTT-based messaging architecture. The key components are:
- Common firmware on all of the controllers (ESP32-C3s) that
  - output messages for their connected sensors, mainly PIR proximity sensors
  - respond to commands for activating props through various actuators (relays, pneumatic solenoid valves, audio players)
- A centralized server that acts as a mediator between all the various props and sensors
  - subscribe to sensor messages from all the components
  - orchestrate a scene in response to a given sensor input
    - combine actuation commands and timing sequences to achieve maximum scare!

[<img width="569" alt="HalloweenHauntedHouse2024Preview" src="https://github.com/jakelevirne/Halloween2024/assets/51732/c691ddff-7fa9-4cad-8407-8cfbed17d607">](https://drive.google.com/file/d/1zwmoVLYiJhM9uvdrN-SONa0KXk6m6njB/preview)

