#define in1 5
#define in2 6
#define in3 10
#define in4 11

#define modeSwitch 7 // Toggle for forward/reverse

#define light_FR 14  // A0
#define light_FL 15  // A1
#define light_BR 16  // A2
#define light_BL 17  // A3
#define horn_Buzz 18 // A4

#define trigPin 8
#define echoPin 9
#define redLED 3

int command;
int Speed = 100;
int Speedsec;
int buttonState = 0;
int lastButtonState = 0;
int Turnradius = 0;
int brakeTime = 45;
int brkonoff = 1;

boolean lightFront = false;
boolean lightBack = false;
boolean horn = false;
boolean obstacleNear = false;
boolean sonarEnabled = true;
long lastSonarCheck = 0;
long lastLEDBlink = 0;
boolean ledState = false;
int blinkInterval = 0;

void setup() {
  pinMode(modeSwitch, INPUT_PULLUP);

  pinMode(in1, OUTPUT);
  pinMode(in2, OUTPUT);
  pinMode(in3, OUTPUT);
  pinMode(in4, OUTPUT);

  pinMode(light_FR, OUTPUT);
  pinMode(light_FL, OUTPUT);
  pinMode(light_BR, OUTPUT);
  pinMode(light_BL, OUTPUT);
  pinMode(horn_Buzz, OUTPUT);

  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);
  pinMode(redLED, OUTPUT);

  Serial.begin(9600);
}

void loop() {
  // Check sonar only periodically (every 100ms)
  if (millis() - lastSonarCheck > 100) {
    lastSonarCheck = millis();

    sonarEnabled = (digitalRead(modeSwitch) == HIGH);

    if (sonarEnabled) {
      long duration, distance;
      digitalWrite(trigPin, LOW);
      delayMicroseconds(2);
      digitalWrite(trigPin, HIGH);
      delayMicroseconds(10);
      digitalWrite(trigPin, LOW);

      duration = pulseIn(echoPin, HIGH);
      distance = duration * 0.034 / 2;

      obstacleNear = (distance > 0 && distance <= 20);

      if (distance > 20 && distance <= 30) {
        blinkInterval = map(distance, 11, 30, 600, 100);
      } else {
        blinkInterval = 0;
        digitalWrite(redLED, LOW);
      }
    } else {
      obstacleNear = false;
      blinkInterval = 0;
      digitalWrite(redLED, LOW);
    }
  }

  // Handle LED blinking separately
  if (blinkInterval > 0 && millis() - lastLEDBlink >= blinkInterval) {
    lastLEDBlink = millis();
    ledState = !ledState;
    digitalWrite(redLED, ledState);
  }

  if (Serial.available() > 0) {
    command = Serial.read();
    Stop();

    if (lightFront) { digitalWrite(light_FR, HIGH); digitalWrite(light_FL, HIGH); }
    else { digitalWrite(light_FR, LOW); digitalWrite(light_FL, LOW); }

    if (lightBack) { digitalWrite(light_BR, HIGH); digitalWrite(light_BL, HIGH); }
    else { digitalWrite(light_BR, LOW); digitalWrite(light_BL, LOW); }

    if (horn) { digitalWrite(horn_Buzz, HIGH); }
    else { digitalWrite(horn_Buzz, LOW); }

    // Allow full control if no obstacle is near or sonar is disabled
    if (!obstacleNear || !sonarEnabled) {
      switch (command) {
        case 'F':
          if (digitalRead(modeSwitch) == HIGH) forward();
          else back();
          break;
        case 'B': back(); break;
        case 'L': left(); break;
        case 'R': right(); break;
        case 'G': forwardleft(); break;
        case 'I': forwardright(); break;
        case 'H': backleft(); break;
        case 'J': backright(); break;

        case '0': Speed = 100; break;
        case '1': Speed = 140; break;
        case '2': Speed = 153; break;
        case '3': Speed = 165; break;
        case '4': Speed = 178; break;
        case '5': Speed = 191; break;
        case '6': Speed = 204; break;
        case '7': Speed = 216; break;
        case '8': Speed = 229; break;
        case '9': Speed = 242; break;
        case 'q': Speed = 255; break;

        case 'W': lightFront = true; break;
        case 'w': lightFront = false; break;
        case 'U': lightBack = true; break;
        case 'u': lightBack = false; break;
        case 'V': horn = true; break;
        case 'v': horn = false; break;
      }

      Speedsec = Turnradius;
      if (brkonoff == 1) brakeOn();
      else brakeOff();
    } else {
      Stop();
    }
  }
}

void forward() {
  analogWrite(in1, Speed);
  analogWrite(in3, Speed);
}

void back() {
  analogWrite(in2, Speed);
  analogWrite(in4, Speed);
}

void left() {
  analogWrite(in3, Speed);
  analogWrite(in2, Speed);
}

void right() {
  analogWrite(in4, Speed);
  analogWrite(in1, Speed);
}

void forwardleft() {
  analogWrite(in1, Speedsec);
  analogWrite(in3, Speed);
}

void forwardright() {
  analogWrite(in1, Speed);
  analogWrite(in3, Speedsec);
}

void backright() {
  analogWrite(in2, Speed);
  analogWrite(in4, Speedsec);
}

void backleft() {
  analogWrite(in2, Speedsec);
  analogWrite(in4, Speed);
}

void Stop() {
  analogWrite(in1, 0);
  analogWrite(in2, 0);
  analogWrite(in3, 0);
  analogWrite(in4, 0);
}

void brakeOn() {
  buttonState = command;
  if (buttonState != lastButtonState) {
    if (buttonState == 'S') {
      if (lastButtonState != buttonState) {
        digitalWrite(in1, HIGH);
        digitalWrite(in2, HIGH);
        digitalWrite(in3, HIGH);
        digitalWrite(in4, HIGH);
        delay(brakeTime);
        Stop();
      }
    }
    lastButtonState = buttonState;
  }
}

void brakeOff() {
  // Nothing
}
