---
title: "moon pad v2.1"
author: "moonbeeper"
description: "the second version of mah modular macropad"
created_at: "2026-05-16"
---

# May 16: The BOM and approximate architecture

While practically all the research was done before to make my t1 pitch (this is not a t1 project. I really don't know why I though that while i was researching), I am going to regurgitate it here for the sake of making a journal entry for my beautiful t2 project.

Right, ALL of this comes from me wanting to make a modular macropad with my first try being a complete failure (not on the macropad department, instead on the modular one) because of me not really paying attention at the obvious signs that it really couldnt work how I wanted it to work. It might had worked if I hadnt used analog switches for the i2c stuff... who knows.

First of all, good bye I2C and hello can bus (even though I think I will be using it wrong) for the communication between the mainboard (macropad) and the modules. 
The current plan for this thing is to make the mainboard just listen to updates coming from the modules by using interrupts from the canbus controller instead of polling like in the i2c version (more sleep!!!). While modules just send updates when they need to, and thanks to mr canbus they can do it at the same time because of the arbitration included with canbus. I will also be using my own teeny tiny protocol for the communication between the mainboard and the modules, for example, the typical handshake using the unique id of the module and what they have to offer (buttons, knobs or sliders) and then the mainboard will just do the rest of the magic (and also a keep alive by the modules to let the mainboard know that they are still there).

The mainboard (macropad) will be using the NRF52840 as the brains to provide both USB (first priority) and Bluetooth (second) via the comp usb stuff (to let you configure it via serial and still be a hid device) with a npm1300 as the power management for only feeding the mcu. Because the canbus controller, transceiver and the modules will be fed by a buck boost (probs these tps from ti for 1.5A) from the vsys of the npm1300 to leave alone the nrf52840 "clean" power wise from the canbus spikes and hungry modules.
As for the modules, I will simply be using a STM32G0x1 to be able to remove the can controller becuase its integrated into the mcu.

I only have planned modules like the knobs (classic ec11), sliders (pots) and maybe a big knob encoder (??, probbaly not because there's a chance I go over the budget with my hours... and deducted ones lol). But the idea is that the modules can have whatever you want, as long as they have a canbus connection and tell the mainboard what do they have to offer (knobs, buttons....).

Sadly I wont be using ZMK for this project because of its static device tree, which is a big no no for this project because of the dynamic nature of mah modules. Instead, I will be using pure as water Zephyr to make the firmware for the mainboard and the modules... which will be hard and not fun anymore and i will be screaming and crying and rethinking my decision of not using ZMK and making a frankenstein firmware or even worse, not using a esp32 to be able use arduino stuff... Bah, I like to suffer, what can I say :3.

AH, and let's not forget that I WILL not be using those rgb gamer leds because of probable power constraints because I want to use this via bluetooth and that needs a battery (not huge please), and those things are very power hungry (at max brightness. not that i would run them at max brightness). And that I will be using an oled screen to have (i hope) "a pretty boot screen" and the battery status stuff. GOD now i want to add a tiny buzzer to make stupid sounds lol.

As for final words, gosh how I'd liked for past me to make a thousand different screenshots (or use lapse... nope) to justify my hours spent in researching. WELL, have this beautiful screenshot of the uhh nRF comparison table showing me saying "no, no, no, no, yes":

![drawn nRF comparison table](.github/images/1.png)

**Total time spent: 4 hours**
