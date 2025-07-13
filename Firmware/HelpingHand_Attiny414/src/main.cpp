#include <Arduino.h>
#include <avr/sleep.h>

// These are the pin definitions for our helping hand.
#define ANALOG_SW_A0 8
#define ANALOG_SW_A1 9
#define MASTER_1 0
#define MASTER_2 1
#define MASTER_3 6
#define MASTER_4 3
#define SW_MUX_1 7
#define SW_MUX_2 10
#define SW_MUX_3 5
#define SW_MUX_4 4
#define MASTER_PMOS 2

// The master lines and sw mux lines are ordered in the same way as the master lines are defined.
const uint8_t MASTER_LINES[] = {MASTER_1, MASTER_2, MASTER_3, MASTER_4};
const uint8_t SW_MUX_LINES[] = {SW_MUX_1, SW_MUX_2, SW_MUX_3, SW_MUX_4};
const size_t NUM_MASTERS = sizeof(MASTER_LINES) / sizeof(MASTER_LINES[0]);

// put function declarations here:
void comsAnalogSwitch(uint8_t);
uint8_t waitForAnyMaster();
int8_t getMasterLine();

void setup()
{
  pinMode(ANALOG_SW_A0, OUTPUT);
  pinMode(ANALOG_SW_A1, OUTPUT);
  // using INPUT_PULLUP because I forgot to add a 10k ohm resistor to no leave dangling the pin.
  pinMode(MASTER_1, INPUT_PULLUP);
  pinMode(MASTER_2, INPUT_PULLUP);
  pinMode(MASTER_3, INPUT_PULLUP);
  pinMode(MASTER_4, INPUT_PULLUP);
  pinMode(SW_MUX_1, OUTPUT);
  pinMode(SW_MUX_2, OUTPUT);
  pinMode(SW_MUX_3, OUTPUT);
  pinMode(SW_MUX_4, OUTPUT);
  pinMode(MASTER_PMOS, OUTPUT);

  delay(10); // wait for the master lines to settle.

  // LOW -> Closed | HIGH -> Open
  // These are closed by default to avoid sending the coms back to its origin when not needed.
  digitalWrite(SW_MUX_1, LOW);
  digitalWrite(SW_MUX_2, LOW);
  digitalWrite(SW_MUX_3, LOW);
  digitalWrite(SW_MUX_4, LOW);

  uint8_t chosenLine = waitForAnyMaster();
  comsAnalogSwitch(chosenLine);

  // after choosing the master line we open the mux switches excluding the one we chose.
  for (uint8_t i = 0; i < NUM_MASTERS; i++)
  {
    if (i != chosenLine)
    {
      digitalWrite(SW_MUX_LINES[i], HIGH);
    }
    else
    {
      digitalWrite(SW_MUX_LINES[i], LOW); // just to be sure.
    }
  }
  delay(500); // wait for the attiny1616 to settle after the line selection. Might be a bit too much.

  // finally we open the PMOS switch
  digitalWrite(MASTER_PMOS, HIGH);
  // and we go to sleep for ever. zzz
  set_sleep_mode(SLEEP_MODE_PWR_DOWN);
  sleep_enable();
  sleep_cpu();
}

void loop()
{
  // put your main code here, to run repeatedly:
}

/// @brief Selects the I2C lines from the analog switch. This is used to select which master line is currently active.
/// @param channel
void comsAnalogSwitch(uint8_t channel)
{
  digitalWrite(ANALOG_SW_A0, channel & 0x01);
  digitalWrite(ANALOG_SW_A1, (channel >> 1) & 0x01);
}

/// @brief Loops until one of the master lines is HIGH. It's a blocking function.
/// @return The index of the master line that is HIGH
uint8_t waitForAnyMaster()
{
  while (true)
  {
    int chosenLine = getMasterLine();
    if (chosenLine >= 0)
    {
      return (uint8_t)chosenLine; // casting so I feel safe.
    }
    delay(10); // small delay between checks
  }
}

/// @brief Checks which master line is currently HIGH. If there are none, it returns -1.
/// If there's more than one, it returns the first one found.
/// @return The index of the master line
int8_t getMasterLine()
{
  for (uint8_t i = 0; i < NUM_MASTERS; i++)
  {
    if (digitalRead(MASTER_LINES[i]) == HIGH)
    {
      return i;
    }
  }

  return -1;
}
