#!/usr/bin/env python2
import argparse

__all__ = ['get_hw_version_str', 'is_charging', 'RGB_LED', 'USB_DCDC_Gamma', "GSM_Modem_Gamma"]
__version__ = '0.3.0'

import sys
from copy import copy
from time import sleep

import gpio

sys.excepthook = sys.__excepthook__
# GPIO library workaround - it sets excepthook
# to PDB debug, that's good but it's going to
# propagate through pyLCI code, and that's not good
gpio.log.setLevel(gpio.logging.INFO)


# Otherwise, a bunch of stuff is printed on the screen

def get_hw_version_str():
    # Only version there is for now =)
    # Next implementations will probably be getting version strings from onboard EEPROM
    return "gamma"


def is_charging():
    chg_sense_gpio = 503
    gpio.setup(chg_sense_gpio, gpio.IN)
    return bool(gpio.input(chg_sense_gpio))


class USB_DCDC(object):
    def __new__(cls, *args, **kwargs):
        if get_hw_version_str() == "gamma":
            return USB_DCDC_Gamma(*args, **kwargs)


class USB_DCDC_Gamma(object):
    """USB DCDC control for gamma board"""
    gpio_exported = False
    gpio_state = None

    def __init__(self, gpio_inverted=True):
        self.gpio_inverted = gpio_inverted
        self.gpio_num = self._get_gpio_num()

    def _get_gpio_num(self):
        return 510

    def _set_state(self, state):
        if not self.gpio_exported:
            gpio.setup(self.gpio_num, gpio.OUT)
            self.gpio_exported = True
        self.gpio_state = state
        if self.gpio_inverted:
            gpio.set(self.gpio_num, not state)
        else:
            gpio.set(self.gpio_num, state)

    def on(self):
        """Turns the DCDC on"""
        self._set_state(True)

    def off(self):
        """Turns the DCDC off"""
        self._set_state(False)

    def toggle(self):
        """Toggles DCDC state"""
        self._set_state(not self.gpio_state)


class GSM_Modem(object):
    def __new__(cls, *args, **kwargs):
        if get_hw_version_str() == "gamma":
            return GSM_Modem_Gamma(*args, **kwargs)


class GSM_Modem_Gamma(object):
    """SIM800L modem control for the gamma board"""
    gpio_dict = {"exported": False, "state": None, "num": None}
    gpio_names = ["ring", "reset", "dtr"]
    gpio_nums = {"gamma": {"ring": 501, "dtr": 500, "reset": 502}}

    def __init__(self):
        self.hw_v = get_hw_version_str()
        self.gpios = {}
        self._set_gpio_nums()

    def _set_gpio_nums(self):
        self.gpios = {name: copy(self.gpio_dict) for name in self.gpio_names}
        if self.hw_v not in self.gpio_nums:
            raise NotImplemented("Hardware version not supported!")
        gpio_nums = self.gpio_nums[self.hw_v]
        for name, num in gpio_nums.items():
            self.gpios[name]["num"] = num

    def _set_state(self, name, state):
        g = self.gpios[name]
        gpio_num = g["num"]
        if not g["exported"]:
            gpio.setup(gpio_num, gpio.OUT)
            g["exported"] = True
        g["state"] = state
        gpio.set(gpio_num, state)

    def reset(self):
        self._set_state("reset", False)
        sleep(1)
        self._set_state("reset", True)

    # TODO: add "get_ring_state" and "get_dtr_state" high-level functions


class RGB_LED(object):
    def __new__(cls, *args, **kwargs):
        if get_hw_version_str() == "gamma":
            return RGB_LED_Gamma(*args, **kwargs)


class RGB_LED_Gamma(object):
    """Controls the RGB led"""
    color_mapping = {
        "white": (255, 255, 255),
        "red": (255, 0, 0),
        "green": (0, 255, 0),
        "blue": (0, 0, 255),
        "none": (0, 0, 0)}

    led_types = {
        "gamma": "gpio_inverted"}

    def __init__(self):
        self.hw_v = get_hw_version_str()
        self.led_type = self._get_led_type(self.hw_v)

    def _get_led_type(self, version):
        if version in self.led_types:
            return self.led_types[version]
        else:
            raise NotImplemented("Hardware version not supported!")

    def _setup(self):
        if self.led_type in ["gpio", "gpio_inverted"]:
            for gpio_num in self._get_rgb_gpios():
                gpio.setup(gpio_num, gpio.HIGH)

    def _get_rgb_gpios(self):
        # returns GPIOs for red, green, blue
        if self.hw_v == "gamma":
            return 498, 496, 497
        else:
            raise NotImplemented("Hardware version not supported!")

    def set_color(self, color_str):
        """Sets the color of the led from a string"""
        try:
            self.set_rgb(*self.color_mapping[color_str])
        except KeyError:
            raise ValueError("Color {} not found in color mapping!".format(color_str))

    def off(self):
        """Turns the led off"""
        self.set_rgb(0, 0, 0)

    def set_rgb(self, *colors):
        """Sets the color of the led from RGB values [0-255] range"""
        colors = [int(c) for c in colors]
        if len(colors) != 3 or any([type(color) != int for color in colors]):
            raise TypeError("set_rgb expects three integer arguments - red, green and blue values!")
        if any([color < 0 or color > 255 for color in colors]):
            raise ValueError("set_rgb expects integers in range from 0 to 255!")
        if self.led_type in ["gpio", "gpio_inverted"]:  # HW versions that have GPIO-controlled LED
            gpios = self._get_rgb_gpios()
            for i, gpio_num in enumerate(gpios):
                gpio_state = colors[i] > 0  # Only 0 and 255 are respected
                if self.led_type == "gpio_inverted":
                    gpio_state = not gpio_state
                gpio.set(gpio_num, gpio_state)
        else:
            raise NotImplemented("LED control type not supported!")

    def __getattr__(self, name):
        if name in self.color_mapping:
            return lambda x=name: self.set_color(x)


def add_object_subparser(obj, name, sub_parsers):
    callable_functions = [func for func in dir(obj) if callable(getattr(obj, func)) and not func.startswith('_')]

    object_help = str(obj.__doc__)
    functions_help = '\n'.join(['\t{}\t{}'.format(func, getattr(obj, func).__doc__) for func in callable_functions if
                                getattr(obj, func).__doc__ is not None])
    custom_subparser = sub_parsers.add_parser(
        name,
        description="{}\n{}".format(object_help, functions_help),
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    custom_subparser.add_argument('command', type=str, choices=callable_functions)
    custom_subparser.add_argument('params', type=str, nargs='*')
    custom_subparser.set_defaults(__obj=obj)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='zerophone_hw', description='Zerophone Hardware Command Line Interface')
    subparsers = parser.add_subparsers()

    add_object_subparser(RGB_LED(), 'led', subparsers)
    add_object_subparser(USB_DCDC(), 'dcdc', subparsers)
    add_object_subparser(GSM_Modem(), 'modem', subparsers)

    args = parser.parse_args()
    if hasattr(args.__obj, '_setup'):
        getattr(args.__obj, '_setup')()
    getattr(args.__obj, args.command)(*args.params)
