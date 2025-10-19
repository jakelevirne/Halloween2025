/*
For the ESP32-C3 board from LuaTOS (https://wiki.luatos.com/chips/esp32c3/board.html) though may work with other ESP32 board with pin adjustments
For logging to an attached LCD, use aSerial TFT LCD Module Display Screen (Driver IC ILI9488) like this one: https://www.aliexpress.us/item/3256803897163557.html
Wiring of LCD to ESP32-C3 requires 8 connections: VCC, GND, TFT_CS, TFT_RESET, TFT_DC, TFT_MOSI, TFT_SCK, TFT_LED, TFT_MISO
These map naturally to the SPI pins of the ESP32 board, with the RESET and LED pins mapping wherever is conventient. All mappings #defined in constants.

For these boards, in Arduino IDE, Tools->Board should be set to "ESP32C3 Dev Module", Tools->Flash Mode should be set to DIO, Tools->USB CDC on Boot should be Enabled

The core functionality is that the device will connect to an MQTT server, based on the connection secrets SECRET_SSID, SECRET_PASS, MQTT_BROKER_IP defined in secrets.h
It will subscribe to topics of the form device/<MAC ADDRESS>/actuator (e.g. device/60:55:F9:7B:5F:2C/actuator) and it will listen for messages A<#>, B<#>, X<#>, Y<#> (e.g. A5)
Where A and B messages will interact with A_PIN and B_PIN, which are normally set HIGH but which will go LOW for <#> cycles when receiving an A<#> or B<#> actuator message
and where X and Y messages will interact with X_PIN and Y_PIN, which are normally set LOW but which will go HIGH for <#> cycles when receiving an X<#> or Y<#> actuator message
Cycles are defined by the constant TIMER0_INTERVAL_MS, which is used by the ESP32TimerInterrupt code to create non-blocking digitalWrites to the appropriate pins

It will also publish to the topic device/<MAC ADDRESS>/sensor (e.g. device/60:55:F9:7B:5F:2C/actuator) once every TIMER0_INTERVAL_MS with the current value of pin A0
This is useful for connecting a sensor, such as an IR sensor, to the board


Define SECRET_SSID, SECRET_PASS, MQTT_BROKER_IP in a separate secrets.h that gets included
*/


#if !defined( ESP32 )
	#error This code is intended to run on the ESP32 platform! Please check your Tools->Board setting.
#endif

// These define's must be placed at the beginning before #include "ESP32_New_TimerInterrupt.h"
// _TIMERINTERRUPT_LOGLEVEL_ from 0 to 4
#define _TIMERINTERRUPT_LOGLEVEL_     4


// To be included only in main(), .ino with setup() to avoid `Multiple Definitions` Linker Error
#include "ESP32TimerInterrupt.h"

 

#include <Arduino_GFX_Library.h>
#include "EspMQTTClient.h"
#include "secrets.h"

#define A_PIN   13
#define B_PIN   9
#define X_PIN   12
#define Y_PIN   8

String mac = WiFi.macAddress();

EspMQTTClient client(
  SECRET_SSID,
  SECRET_PASS,
  MQTT_BROKER_IP,  // MQTT Broker server ip
  "",   // Can be omitted if not needed
  "",   // Can be omitted if not needed
  mac.c_str()      // Client name that uniquely identify your device
);

#define TFT_CS    7  
#define TFT_RESET 11 
#define TFT_DC    6  
#define TFT_MOSI  3 
#define TFT_SCK   2 
#define TFT_LED   5 
#define TFT_MISO  -1  // not used for TFT

#define DISPLAY_LINES 40

#define GFX_BL TFT_LED // default backlight pin, you may replace DF_GFX_BL to actual backlight pin

/* More dev device declaration: https://github.com/moononournation/Arduino_GFX/wiki/Dev-Device-Declaration */
Arduino_DataBus *bus = new Arduino_ESP32SPI(TFT_DC, TFT_CS, TFT_SCK, TFT_MOSI, GFX_NOT_DEFINED /* MISO */);

/* More display class: https://github.com/moononournation/Arduino_GFX/wiki/Display-Class */
Arduino_GFX *gfx = new Arduino_ILI9488_18bit(bus, TFT_RESET, 1 /* rotation */, false /* IPS */);


/*******************************************************************************
 * End of Arduino_GFX setting
 ******************************************************************************/

int analogPin = A0;
volatile int sensorValue = 0;
int previousSensorValue = 0;

int displayLineCount = 0;

// Four output pins are supported, named A, B, X, Y.
// A and B are normally HIGH and go LOW when a message is received.
// X and Y are normally LOW and go HIGH when a message is received.
int pinA = A_PIN;
int pinB = B_PIN;

int pinX = X_PIN;
int pinY = Y_PIN;

int AtimerCount, BtimerCount, XtimerCount, YtimerCount = 0;



// With core v2.0.0+, you can't use Serial.print/println in ISR or crash.
// and you can't use float calculation inside ISR
// Only OK in core v1.0.6-

bool IRAM_ATTR TimerHandler0(void * timerNo)
{
	//timer interrupt reads the value of the analogPin every time the timer ticks
  sensorValue = analogRead(analogPin);

  //and sets the diital pin HIGH if that message came in, and keeps it high for count cycles of this timer (i.e. count * TIMER0_INTERVAL_MS)
  if (AtimerCount > 0) {
    digitalWrite(pinA, LOW);
    AtimerCount--;
  } else {
    digitalWrite(pinA, HIGH);
  }

  //and sets the diital pin HIGH if that message came in, and keeps it high for count cycles of this timer (i.e. count * TIMER0_INTERVAL_MS)
  if (BtimerCount > 0) {
    digitalWrite(pinB, LOW);
    BtimerCount--;
  } else {
    digitalWrite(pinB, HIGH);
  }

  //and sets the diital pin HIGH if that message came in, and keeps it high for count cycles of this timer (i.e. count * TIMER0_INTERVAL_MS)
  if (XtimerCount > 0) {
    digitalWrite(pinX, HIGH);
    XtimerCount--;
  } else {
    digitalWrite(pinX, LOW);
  }

  //and sets the diital pin HIGH if that message came in, and keeps it high for count cycles of this timer (i.e. count * TIMER0_INTERVAL_MS)
  if (YtimerCount > 0) {
    digitalWrite(pinY, HIGH);
    YtimerCount--;
  } else {
    digitalWrite(pinY, LOW);
  }

	return true;
}

#define TIMER0_INTERVAL_MS        500
// Init ESP32 timer 0
ESP32Timer ITimer0(0);


void setup(void)
{
  delay(2000);
  pinMode(pinA, OUTPUT);
  digitalWrite(pinA, HIGH);
  pinMode(pinB, OUTPUT);
  digitalWrite(pinB, HIGH);
  pinMode(pinX, OUTPUT);
  digitalWrite(pinX, HIGH);
  pinMode(pinY, OUTPUT);
  digitalWrite(pinY, HIGH);
  Serial.begin(115200);
  // Serial.setDebugOutput(true);
  // while(!Serial);
  Serial.println("Arduino_GFX Hello World example");
  Serial.println(ESP.getHeapSize());
  Serial.println(ESP.getFreeHeap());
  Serial.println(ESP.getFreeSketchSpace());
  Serial.println(mac);
  Serial.print(F("\nStarting TimerInterrupt on "));
	Serial.println(ARDUINO_BOARD);
	Serial.println(ESP32_TIMER_INTERRUPT_VERSION);
	Serial.print(F("CPU Frequency = "));
	Serial.print(F_CPU / 1000000);
	Serial.println(F(" MHz"));


	// Interval in microsecs
	if (ITimer0.attachInterruptInterval(TIMER0_INTERVAL_MS * 1000, TimerHandler0))
	{
		Serial.print(F("Starting  ITimer0 OK, millis() = "));
		Serial.println(millis());
	}
	else
		Serial.println(F("Can't set ITimer0. Select another freq. or timer"));



  // Init Display
  if (!gfx->begin())
  {
    Serial.println("gfx->begin() failed!");
  }
#ifdef GFX_BL
  pinMode(GFX_BL, OUTPUT);
  digitalWrite(GFX_BL, HIGH);
#endif
  gfxClear();
}

void gfxClear() {

  gfx->fillScreen(BLACK);
  gfx->setTextWrap(false);

  gfx->setCursor(0, 0);
  gfx->setTextColor(RED);  
  displayLineCount = 0;
}

void gfxPrintlnAndClear(String msg) {
  if (displayLineCount >= DISPLAY_LINES){
    gfxClear();
  }
  gfx->println(msg);
  displayLineCount++;
}

void onConnectionEstablished() {

    client.subscribe("device/"+mac+"/actuator", [] (const String &payload)  {
    Serial.println(payload);
    String outputString = "device/"+ mac + "/" + payload;
    gfxPrintlnAndClear(outputString);
    Serial.println(ESP.getHeapSize());
    Serial.println(ESP.getFreeHeap());
    Serial.println(ESP.getFreeSketchSpace());
    if (payload.charAt(0) == 'A') {
        String numberString = payload.substring(1); // Extract the remaining characters
        AtimerCount = numberString.toInt(); // Convert the remaining characters to an integer
    }

    if (payload.charAt(0) == 'B') {
        String numberString = payload.substring(1); // Extract the remaining characters
        BtimerCount = numberString.toInt(); // Convert the remaining characters to an integer
    }

    if (payload.charAt(0) == 'X') {
        String numberString = payload.substring(1); // Extract the remaining characters
        XtimerCount = numberString.toInt(); // Convert the remaining characters to an integer
    }

    if (payload.charAt(0) == 'Y') {
        String numberString = payload.substring(1); // Extract the remaining characters
        YtimerCount = numberString.toInt(); // Convert the remaining characters to an integer
    }
});


}

void loop()
{
  client.loop();
  
  if (previousSensorValue != sensorValue) {
    // print out the value you read:
    Serial.println(sensorValue);
    client.publish("device/"+ mac + "/sensor", String(sensorValue));
    previousSensorValue = sensorValue;
  }

}
