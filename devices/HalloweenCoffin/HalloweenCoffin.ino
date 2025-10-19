// HalloweenCoffin.ino
// This code controls the Halloween coffin.
// It listens for a trigger from a controller and bangs/opens the coffin door when triggered.
// The coffin door then closes after a delay.
// This is meant to run on an Arduino Uno with a 10k pull-down resistor on the trigger pin.
// One end of a 10kΩ resistor to the trigger pin (pin 3)
// Other end of the resistor to GND
// Your button/trigger between pin 3 and +5V
// This ensures the pin stays LOW until actively pulled HIGH by your trigger.


const int triggerPin = 3;     // the number of the blue pushbutton pin
const int doorPin =  7;      // the number of the coffin door relay in pin

void setup() {
  // initialize the door pin as an output
  pinMode(doorPin, OUTPUT);
  digitalWrite(doorPin, LOW);
  
  // initialize the trigger pin as an input
  pinMode(triggerPin, INPUT);
  
  Serial.begin(9600);               // starts the serial monitor
  delay(3000);
}

void loop() {
  // Only run when triggerPin is HIGH
  if (digitalRead(triggerPin) == HIGH) {
    Serial.println("BOO");

    digitalWrite(doorPin, HIGH);
    delay(300);
    digitalWrite(doorPin, LOW);
    delay(500);

    digitalWrite(doorPin, HIGH);
    delay(300);
    digitalWrite(doorPin, LOW);
    delay(500);

    digitalWrite(doorPin, HIGH);
    delay(300);
    digitalWrite(doorPin, LOW);
    delay(500);

    digitalWrite(doorPin, HIGH);
    delay(300);
    digitalWrite(doorPin, LOW);
    delay(500);

    digitalWrite(doorPin, HIGH);
    delay(300);
    digitalWrite(doorPin, LOW);
    delay(500);

    digitalWrite(doorPin, HIGH);
    delay(7000);
    digitalWrite(doorPin, LOW);
    delay(1000);
    
  }
}