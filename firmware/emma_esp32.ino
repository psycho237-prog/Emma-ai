/**
 * EMMA v2.0 - Firmware ESP32
 * Gestion des yeux OLED (SSD1306) et communication PC.
 * Librairies requises : Adafruit SSD1306, Adafruit GFX
 */

#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_RESET    -1
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

// Etats d'EMMA
enum State { NEUTRAL, LISTENING, THINKING, SPEAKING };
State currentState = NEUTRAL;

void setup() {
  Serial.begin(115200);

  // Initialisation OLED
  if(!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    Serial.println(F("Erreur OLED"));
    for(;;);
  }
  
  display.clearDisplay();
  display.display();
}

void drawEyes(int offset_x, int offset_y, int eye_width, int eye_height, bool blinking) {
  display.clearDisplay();
  
  if (!blinking) {
    // Oeil Gauche
    display.fillRoundRect(30 + offset_x, 20 + offset_y, eye_width, eye_height, 10, WHITE);
    // Oeil Droit
    display.fillRoundRect(SCREEN_WIDTH - 30 - eye_width + offset_x, 20 + offset_y, eye_width, eye_height, 10, WHITE);
  } else {
    // Yeux fermes (clignement)
    display.drawFastHLine(30, 32, eye_width, WHITE);
    display.drawFastHLine(SCREEN_WIDTH - 30 - eye_width, 32, eye_width, WHITE);
  }
  
  display.display();
}

void loop() {
  // Lecture des commandes via Serial (Envoyees par le script Python)
  if (Serial.available() > 0) {
    char cmd = Serial.read();
    if (cmd == 'N') currentState = NEUTRAL;
    if (cmd == 'L') currentState = LISTENING;
    if (cmd == 'T') currentState = THINKING;
    if (cmd == 'S') currentState = SPEAKING;
  }

  // Gestion des animations selon l'etat
  switch (currentState) {
    case NEUTRAL:
      static unsigned long nextBlink = 0;
      if (millis() > nextBlink) {
        drawEyes(0, 0, 25, 30, true);
        delay(150);
        nextBlink = millis() + random(2000, 5000);
      } else {
        drawEyes(0, 0, 25, 30, false);
      }
      break;

    case LISTENING:
      // Les yeux sont grands et fixes
      drawEyes(0, -5, 30, 35, false);
      break;

    case THINKING:
      // Les yeux scannent de gauche a droite
      for (int i = -10; i <= 10; i += 2) {
        drawEyes(i, 0, 25, 30, false);
        delay(50);
      }
      for (int i = 10; i >= -10; i -= 2) {
        drawEyes(i, 0, 25, 30, false);
        delay(50);
      }
      break;

    case SPEAKING:
      // Les yeux vibrent legerement
      drawEyes(random(-2, 2), random(-2, 2), 25, 30, false);
      delay(80);
      break;
  }
}
