
#include <Arduino.h>
#include "moduleBase.h"
#include <Wire.h>

ModuleBase *ModuleBase::instance = nullptr;

void ModuleBase::readUniqueSerial(uint8_t *buffer)
{
    buffer[0] = SIGROW_SERNUM0; // could also use SIGROW.SERNUM0 that comes from the SIGROW struct.
    buffer[1] = SIGROW_SERNUM1;
    buffer[2] = SIGROW_SERNUM2;
    buffer[3] = SIGROW_SERNUM3;
    buffer[4] = SIGROW_SERNUM4;
    buffer[5] = SIGROW_SERNUM5;
    buffer[6] = SIGROW_SERNUM6;
    buffer[7] = SIGROW_SERNUM7;
    buffer[8] = SIGROW_SERNUM8;
    buffer[9] = SIGROW_SERNUM9;
}

void ModuleBase::generateFriendCode()
{
    friendCode[0] = moduleType;
    readUniqueSerial(&friendCode[1]);
}

const uint8_t *ModuleBase::getModuleCode() const
{
    return friendCode;
}

void ModuleBase::begin(uint8_t address)
{
    Wire.begin(address);
    Wire.setClock(400000);
    Wire.onRequest(redirectOnRequest);
    Wire.onReceive(redirectOnReceive);
}

// Master wants data from the module
void ModuleBase::handleTWIRequest()
{
    uint8_t base_cmd = i2c_buffer[0];
    uint8_t module_cmd = i2c_buffer[1];

    if (base_cmd == MOONPAD_BASE_CMD)
    {
        switch (module_cmd)
        {
        case MOONPAD_BASE_FRIEND_CODE:
            Wire.write(friendCode, sizeof(friendCode));
            break;

        case MOONPAD_BASE_SWAP_ADDRESS:
            Wire.end();
            Wire.begin(i2c_buffer[2]);
            Wire.setClock(400000);
            Wire.onRequest(redirectOnRequest);
            Wire.onReceive(redirectOnReceive);
        default:
            break;
        }
    }
    else
    {
        // pass the request to the module handler
        onRequest();
    }
}

// Master sends data to the module
void ModuleBase::handleTWIReceive(int bytes)
{
    memset(i2c_buffer, 0, sizeof(i2c_buffer));
    for (int i = 0; i < bytes && i < sizeof(i2c_buffer); ++i)
    {
        i2c_buffer[i] = Wire.read();
    }

    uint8_t base_cmd = i2c_buffer[0];
    uint8_t module_cmd = i2c_buffer[1];

    if (base_cmd == MOONPAD_BASE_CMD)
        return;
    // pass the receive to the module handler
    onReceive(bytes);
}

void ModuleBase::redirectOnRequest()
{
    if (instance)
    {
        instance->handleTWIRequest();
    }
}

void ModuleBase::redirectOnReceive(int bytes)
{
    if (instance)
    {
        instance->handleTWIReceive(bytes);
    }
}

// qmk does this
// these are weak methods that can be overridden

__attribute__((weak)) void ModuleBase::onReceive(int bytes) { return; };
__attribute__((weak)) void ModuleBase::onRequest() { return; };