#include <Ethernet.h>
#include <SPI.h>
#include <ModbusEthernet.h>
#include <ESP32Servo.h>

byte mac[] = {
  0x00, 0x08, 0xDC, 0x78, 0xCD, 0xC7
};
IPAddress ip(192, 168, 75, 5);
ModbusEthernet mb;
Servo servo;

const int servoPin = 4;
const int relayPin = 5;
const int echoPin = 6;
const int trigPin = 7;

#define SOUND_SPEED 0.034


void setup() {
  Serial.begin(115200);

  // set up ethernet
  Ethernet.init(34);
  Ethernet.begin(mac, ip);
  if (Ethernet.hardwareStatus() == EthernetNoHardware) {
    Serial.println("Ethernet shield was not found.  Sorry, can't run without hardware. :(");
    while (true) {
      delay(1); // do nothing, no point running without Ethernet hardware
    }
  }

  // set up modbus TCP server
  mb.server(502);          
  for (int i=0; i < 2; i++) {
    mb.addCoil(i, 0);
  }
  for (int i=0; i < 1; i++) {
    mb.addIreg(i, 0);
  }

  // Set up servo
  ESP32PWM::allocateTimer(0);
	ESP32PWM::allocateTimer(1);
	ESP32PWM::allocateTimer(2);
	ESP32PWM::allocateTimer(3);
	servo.setPeriodHertz(50);  
	servo.attach(servoPin, 800, 2200); 

  // set up pins
  pinMode(relayPin, OUTPUT); 
  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);

  // initialise pump to be off and gate to be closed
  digitalWrite(relayPin, HIGH);
  servo.write(0);

  Serial.println("Setup completed.");
}

bool gate, pump;
bool gate_state = false;
bool pump_state = false; // current state of pump/gate 
uint16_t water_level;
double duration;
float distance;

void loop() {
  delay(500);
  mb.task();

  pump = mb.Coil(0);
  gate = mb.Coil(1);

  // pump changed 
  if (pump_state != pump){
    pump_state = pump;
    if (pump) { // pump needs to be turned on
      Serial.println("Turning on the pump.");
      digitalWrite(relayPin, LOW);
    }
    else { // pump needs to be turned off
      Serial.println("Turning off the pump.");
      digitalWrite(relayPin, HIGH);
    }
  }

  // gate changed
  if (gate_state != gate){
    gate_state = gate;
    if (gate) { // gate needs to be opened
      Serial.println("Opening the gate.");
      servo.write(0);
      servo.write(35);
    }
    else { // gate needs to be closed
      Serial.println("Closing the gate.");
      servo.write(35);
      servo.write(0);
    }
  }

  // measures water level
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);
  duration = pulseIn(echoPin, HIGH);
  distance = duration * SOUND_SPEED/2;
  
  water_level = max<float>((26.0 - distance),0.0)*100;

  // print values
  Serial.print("pump: ");
  Serial.print(pump);
  Serial.print(", gate: ");
  Serial.print(gate);
  Serial.print(", water level (cm): ");
  Serial.println((float)water_level/100);

  // based on water level, change gate and pump automatically
  if (water_level > 2100) {
    Serial.println("water level too high");
    // water level is too high, open the gate and turn off the pump
    gate = true;
    pump = false;
  } else if (water_level < 1700) {
    Serial.println("water level too low");
    // water level is too low, open the gate and turn off the pump
    gate = false;
    pump = true;
  }

  // update values
  mb.Ireg(0, water_level); 
  mb.Coil(0, pump);
  mb.Coil(1, gate);
}
