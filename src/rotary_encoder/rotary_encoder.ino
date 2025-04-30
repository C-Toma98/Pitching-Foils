
#define ENC_A 2  
#define ENC_B 3  

volatile int encoderPos = 0;  // Encoder position (pulse count)

void encoderISR() {
    int stateA = digitalRead(ENC_A);
    int stateB = digitalRead(ENC_B);

    if (stateA == stateB) {
        encoderPos++;
    } else {
        encoderPos--;
    }
}

void setup() {
    Serial.begin(115200);
    Serial.flush();

    pinMode(ENC_A, INPUT_PULLUP);
    pinMode(ENC_B, INPUT_PULLUP);

    attachInterrupt(digitalPinToInterrupt(ENC_A), encoderISR, RISING);
}

void loop() {
    delay(10);
    Serial.println(encoderPos, DEC);
    
}
