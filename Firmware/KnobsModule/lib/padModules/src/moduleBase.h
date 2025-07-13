#pragma once
#include <Arduino.h>
#include <moduleProtocol.h>

/// @brief The buffer for I2C data.
extern uint8_t i2c_buffer[TWI_BUFFER_SIZE]; // this shouldn't be in the header, but it works soo duh.

/// @brief The base class for all the modules.
/// This class handles the I2C communication and provides default commands for it.
class ModuleBase
{
public:
    explicit ModuleBase(uint8_t moduleType) : moduleType(moduleType)
    {
        instance = this;
        // gen the friend code once at startup
        generateFriendCode();
    }

    /// @brief Begins the communication with the specified I2C address. Defaults to 0x03.
    /// @param address
    void begin(uint8_t address = 0x03);

    /// @brief Gets the friend code array of the module.
    /// The friend code is a unique identifier for the module, consisting of the module type and the serial number.
    const uint8_t *getModuleCode() const;

private:
    // 1 byte for module type, 10 bytes from the serial number
    uint8_t friendCode[11];

    uint8_t moduleType;

    void generateFriendCode();
    void readUniqueSerial(uint8_t *buffer);
    void handleTWIReceive(int bytes);
    void handleTWIRequest();

    static ModuleBase *instance;
    static void redirectOnReceive(int bytes);
    static void redirectOnRequest();

    // shall the external guys override these methods.

    /// @brief Called when the master sends data to the module.
    /// @param bytes
    void onReceive(int bytes);
    /// @brief Called when the master wants data from the module.
    void onRequest();
};