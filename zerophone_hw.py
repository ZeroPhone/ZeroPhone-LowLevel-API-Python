#!/usr/bin/env python

__all__ = ['get_hw_version_str', 'is_charging', 'RGB_LED', 'USB_DCDC']
__version__ = '0.1'

import sys
import gpio
sys.excepthook = sys.__excepthook__ 
#GPIO library workaround - it sets excepthook 
#to PDB debug, that's good but it's going to 
#propagate through pyLCI code, and that's not good
gpio.log.setLevel(gpio.logging.INFO) 
#Otherwise, a bunch of stuff is printed on the screen

def get_hw_version_str():
    #Only version there is for now =)
    #Next implementations will probably be getting version strings from onboard EEPROM
    return "gamma"

def is_charging():
    hw_v = get_hw_version_str()
    if hw_v == "gamma":
        chg_sense_gpio = 503
        gpio.setup(chg_sense_gpio, gpio.IN)
        return bool(gpio.input(chg_sense_gpio))
    else:
        raise NotImplementedException("Version not supported!")


class USB_DCDC():
    gpio_exported = False
    gpio_state = None

    switch_types = {
        "gamma":"gpio_inverted"}

    def __init__(self):
        self.hw_v = get_hw_version_str()
        self.gpio_num = self.get_gpio_num()

    def get_gpio_num(self):
        if self.hw_v == "gamma":
            return 510
        else:
            raise NotImplementedException("Hardware version not supported!")

    def set_state(self, state):
        if not self.gpio_exported:
            gpio.setup(self.gpio_num, gpio.OUT)
            self.gpio_exported = True
        self.gpio_state = state
        if self.switch_types[self.hw_v] == "gpio_inverted":
            gpio.set(self.gpio_num, not state)
        elif self.switch_types[self.hw_v] == "gpio":
            gpio.set(self.gpio_num, state)
        else:
            raise NotImplementedException("DC-DC switch type not supported!")

    def on(self):
        self.set_state(True)

    def off(self):
        self.set_state(False)

    def toggle(self):
        self.set_state(not self.gpio_state)


class RGB_LED():
    color_mapping = {
        "white": (255, 255, 255),
        "red":   (255,   0,   0),
        "green": (  0, 255,   0),
        "blue":  (  0,   0, 255),
        "none":  (  0,   0,   0)}

    led_types = {
        "gamma":"gpio_inverted"}

    def __init__(self):
        self.hw_v = get_hw_version_str()
        self.led_type = self.get_led_type(self.hw_v)
        self.setup()
            
    def get_led_type(self, version):
        if version in self.led_types:
            return self.led_types[version]
        else:
            raise NotImplementedException("Hardware version not supported!")

    def setup(self):
        if self.led_type in ["gpio", "gpio_inverted"]:
            for gpio_num in self.get_rgb_gpios():
                gpio.setup(gpio_num, gpio.HIGH)

    def get_rgb_gpios(self):
        #returns GPIOs for red, green, blue
        if self.hw_v == "gamma":
            return (498, 496, 497)
        else:
            raise NotImplementedException("Hardware version not supported!")

    def set_color(self, color_str):
        try:
            self.set_rgb(*self.color_mapping[color_str])
        except KeyError:
            raise ArgumentError("Color {} not found in color mapping!".format(color_str))

    def set_rgb(self, *colors):
        if len(colors) != 3 or any([type(color)!=int for color in colors]):
            raise TypeError("set_rgb expects three integer arguments - red, green and blue values!")
        if any([color<0 or color>255 for color in colors]):
            raise ValueError("set_rgb expects integers in range from 0 to 255!")
        if self.led_type in ["gpio", "gpio_inverted"]: #HW versions that have GPIO-controlled LED
            gpios = self.get_rgb_gpios()
            for i, gpio_num in enumerate(gpios):
                gpio_state = colors[i]>0 #Only 0 and 255 are respected
                if self.led_type == "gpio_inverted": gpio_state = not gpio_state
                gpio.set(gpio_num, gpio_state)
        else:
            raise NotImplementedException("LED control type not supported!")

    def __getattr__(self, name):
        if name in self.color_mapping:
            return lambda x=name: self.set_color(x)

if __name__ == "__main__":
    led = RGB_LED()
    dcdc = USB_DCDC()
    from time import sleep
    while True:
        print(is_charging())
        sleep(1)
