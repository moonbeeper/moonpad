#include <Arduino.h>
#include <moduleBase.h>
#include <Wire.h>

uint8_t i2c_buffer[TWI_BUFFER_SIZE];
ModuleBase modBase(MOONPAD_MOD_SLIDERS);

#define NUM_SLIDERS 2
#define SLIDER0_PIN 5
#define SLIDER1_PIN 6

const uint8_t slider_pins[NUM_SLIDERS] = {SLIDER0_PIN, SLIDER1_PIN};
uint16_t slider_last[NUM_SLIDERS] = {0, 0};

struct SliderChanges
{
  uint16_t slider_value[NUM_SLIDERS];
  uint8_t slider_changed[NUM_SLIDERS];
};
volatile SliderChanges changes = {{0, 0}, {0, 0}};

void setup()
{
  modBase.begin();

  pinMode(SLIDER0_PIN, INPUT);
  pinMode(SLIDER1_PIN, INPUT);
}

void loop()
{
  for (uint8_t i = 0; i < NUM_SLIDERS; i++)
  {
    uint16_t val = analogRead(slider_pins[i]);
    if (abs((int)val - (int)slider_last[i]) > 3)
    {
      changes.slider_value[i] = val;
      changes.slider_changed[i] = 1;
      slider_last[i] = val;
    }
  }
}

void ModuleBase::onReceive(int bytes)
{
  uint8_t base_cmd = i2c_buffer[0];
  uint8_t module_cmd = i2c_buffer[1];
  if (base_cmd == MOONPAD_MOD_SLIDERS_CMD)
  {
    if (module_cmd == MOONPAD_SLIDERS_CLEAR_CHANGES)
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

  if (base_cmd == MOONPAD_MOD_SLIDERS_CMD)
  {
    if (module_cmd == MOONPAD_SLIDERS_GET_CHANGES)
    {
      Wire.write((uint8_t *)&changes, sizeof(changes));
      memset((void *)&changes, 0, sizeof(changes));
    }

    if (module_cmd == MOONPAD_SLIDERS_GET_SLIDER_NUMBER)
    {
      Wire.write((uint8_t *)NUM_SLIDERS, 1);
    }
  }
  return;
}