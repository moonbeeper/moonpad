#include <Arduino.h>
#include <moduleBase.h>
#include <RotaryEncoder.h>   // mathertel's library
#include <Adafruit_Keypad.h> // bad decision but oh well
#include <Wire.h>

uint8_t i2c_buffer[TWI_BUFFER_SIZE];
ModuleBase modBase(MOONPAD_MOD_KNOBS);

#define NUM_ENCODERS 3

const uint8_t ENC_A[NUM_ENCODERS] = {9, 11, 7};
const uint8_t ENC_B[NUM_ENCODERS] = {8, 10, 6};
byte BUTTON_COL_PINS[NUM_ENCODERS] = {4, 3, 2};
byte BUTTON_ROW_PIN[1] = {5};

char keys[1][NUM_ENCODERS] = {{'0', '1', '2'}};
Adafruit_Keypad customKeypad = Adafruit_Keypad(makeKeymap(keys), BUTTON_ROW_PIN, BUTTON_COL_PINS, 1, NUM_ENCODERS);

RotaryEncoder encoder0(ENC_A[0], ENC_B[0], RotaryEncoder::LatchMode::TWO03);
RotaryEncoder encoder1(ENC_A[1], ENC_B[1], RotaryEncoder::LatchMode::TWO03);
RotaryEncoder encoder2(ENC_A[2], ENC_B[2], RotaryEncoder::LatchMode::TWO03);

struct KnobChanges
{
  int8_t rotation_delta[NUM_ENCODERS];
  uint8_t button_pressed[NUM_ENCODERS];
  uint8_t button_released[NUM_ENCODERS];
};

KnobChanges changes = {{0}, {0}, {0}};
long encoder_positions[NUM_ENCODERS] = {0, 0, 0};

void setup()
{
  PORTMUX.CTRLB |= PORTMUX_TWI0_bm;
  modBase.begin();
  customKeypad.begin();

  encoder0.setPosition(0);
  encoder1.setPosition(0);
  encoder2.setPosition(0);
}

void loop()
{
  encoder0.tick();
  encoder1.tick();
  encoder2.tick();
  customKeypad.tick();

  while (customKeypad.available())
  {
    keypadEvent e = customKeypad.read();
    char key = e.bit.KEY;
    uint8_t encoder_idx = key - '0'; // converts '0', '1', '2' to 0, 1, 2. crazy

    if (encoder_idx < NUM_ENCODERS)
    {
      if (e.bit.EVENT == KEY_JUST_PRESSED)
      {
        changes.button_pressed[encoder_idx] = 1;
      }
      else if (e.bit.EVENT == KEY_JUST_RELEASED)
      {
        changes.button_released[encoder_idx] = 1;
      }
    }
  }

  long new_pos0 = encoder0.getPosition();
  long new_pos1 = encoder1.getPosition();
  long new_pos2 = encoder2.getPosition();

  int delta0 = new_pos0 - encoder_positions[0];
  int delta1 = new_pos1 - encoder_positions[1];
  int delta2 = new_pos2 - encoder_positions[2];

  changes.rotation_delta[0] = constrain(changes.rotation_delta[0] + delta0, -128, 127);
  changes.rotation_delta[1] = constrain(changes.rotation_delta[1] + delta1, -128, 127);
  changes.rotation_delta[2] = constrain(changes.rotation_delta[2] + delta2, -128, 127);

  encoder_positions[0] = new_pos0;
  encoder_positions[1] = new_pos1;
  encoder_positions[2] = new_pos2;
}

void ModuleBase::onReceive(int bytes)
{
  uint8_t base_cmd = i2c_buffer[0];
  uint8_t module_cmd = i2c_buffer[1];
  if (base_cmd == MOONPAD_MOD_KNOBS_CMD)
  {
    if (module_cmd == MOONPAD_KNOBS_CLEAR_CHANGES)
    {
      memset((void *)&changes, 0, sizeof(changes));
    }
  }
  return;
}

void ModuleBase::onRequest()
{
  uint8_t base_cmd = i2c_buffer[0];
  uint8_t module_cmd = i2c_buffer[1];

  if (base_cmd == MOONPAD_MOD_KNOBS_CMD)
  {
    if (module_cmd == MOONPAD_KNOBS_GET_CHANGES)
    {
      Wire.write((uint8_t *)&changes, sizeof(changes));
      memset((void *)&changes, 0, sizeof(changes));
    }

    if (module_cmd == MOONPAD_KNOBS_GET_ENCODER_NUMBER)
    {
      Wire.write((uint8_t *)NUM_ENCODERS, 1);
    }
  }
  return;
}