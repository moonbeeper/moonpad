#pragma once

#define TWI_BUFFER_SIZE 3

// This is a really bad place to put this, but it is the only place that comes to my mind
enum
{
    MOONPAD_BASE_CMD = 0x00,
    MOONPAD_MOD_KNOBS_CMD = 0x01,
    MOONPAD_MOD_SLIDERS_CMD = 0x02,
};

enum
{
    MOONPAD_BASE_FRIEND_CODE = 0x01,
    MOONPAD_BASE_SWAP_ADDRESS = 0x02,
};

enum
{
    MOONPAD_KNOBS_GET_CHANGES = 0x01,
    MOONPAD_KNOBS_CLEAR_CHANGES = 0x02,
    MOONPAD_KNOBS_GET_ENCODER_NUMBER = 0x03,
};

enum
{
    MOONPAD_SLIDERS_GET_CHANGES = 0x01,
    MOONPAD_SLIDERS_CLEAR_CHANGES = 0x02,
    MOONPAD_SLIDERS_GET_SLIDER_NUMBER = 0x03,
};

enum
{
    MOONPAD_MOD_KNOBS = 0x01,
    MOONPAD_MOD_SLIDERS = 0x02,
};