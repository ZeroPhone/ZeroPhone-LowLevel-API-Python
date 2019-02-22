#!/usr/bin/env python2
import argparse

__all__ = ['get_hw_version_str', 'Charger', 'RGB_LED', 'USB_DCDC', "GSM_Modem"]
__version__ = '0.3.0'

import sys
from copy import copy
from time import sleep

import gpio

sys.excepthook = sys.__excepthook__
# GPIO library workaround - it sets excepthook
# to PDB debug, that's good by itself, but it's going to
# propagate through apps' code, and that's not good

gpio.log.setLevel(gpio.logging.INFO)
# Otherwise, a bunch of stuff is printed on the screen

def get_hw_version_str():
    # Only version there is for now =)
    # Next implementations will probably be getting version strings from onboard EEPROM
    return "delta"


class Charger(object):
    def __new__(cls, *args, **kwargs):
        if get_hw_version_str() == "gamma":
             return Charger_Gamma(*args, **kwargs)
        elif get_hw_version_str() in ["delta", "delta-b"]:
             return Charger_Delta(*args, **kwargs)

class Charger_Gamma(object):
    chg_sense_gpio = 503

    def __init__(self):
        self.chg_sense_gpio_setup = False
    def connected(self):
        if not self.chg_sense_gpio_setup:
            gpio.setup(self.chg_sense_gpio, gpio.IN)
            self.chg_sense_gpio_setup = True
        return bool(gpio.input(self.chg_sense_gpio))

class Charger_Delta(Charger_Gamma):
    chg_sense_gpio = 508


class USB_DCDC(object):
    def __new__(cls, *args, **kwargs):
        if get_hw_version_str() in ["gamma", "delta", "delta-b"]:
            return USB_DCDC_Gamma_Delta(*args, **kwargs)

class USB_DCDC_Gamma_Delta(object):
    """USB DCDC control for gamma/delta boards"""
    gpio_exported = False
    gpio_state = None
    gpio_num = 510

    def _set_state(self, state):
        if not self.gpio_exported:
            gpio.setup(self.gpio_num, gpio.OUT)
            self.gpio_exported = True
        self.gpio_state = state
        gpio.set(self.gpio_num, not state)

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
        elif get_hw_version_str() in ["delta", "delta-b"]:
            return GSM_Modem_Delta(*args, **kwargs)

class GSM_Modem_Gamma(object):
    """SIM800L modem control for the gamma board"""
    gpio_dict = {"exported": False, "state": None, "num": None}
    gpio_nums = {"ring": 501, "dtr": 500, "reset": 502}

    def __init__(self):
        self.gpios = {}
        self._set_gpio_nums()

    def _set_gpio_nums(self):
        self.gpios = {name: copy(self.gpio_dict) for name in self.gpio_nums}
        for name, num in self.gpio_nums.items():
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

class GSM_Modem_Delta(GSM_Modem_Gamma):
    """SIM800L modem control for the delta board"""
    gpio_nums = {"ring": 501, "dtr": 502, "reset": 496, "en": 500}

    def enable_uart(self):
        self._set_state("en", False)

    def disable_uart(self):
        self._set_state("en", True)


class RGB_LED(object):
    def __new__(cls, *args, **kwargs):
        if get_hw_version_str() == "gamma":
            return RGB_LED_Gamma(*args, **kwargs)
        elif get_hw_version_str() in ["delta", "delta-b"]:
            return RGB_LED_Delta(*args, **kwargs)

class RGB_LED_Base(object):
    color_mapping = {
        "white": (255, 255, 255),
        "red": (255, 0, 0),
        "green": (0, 255, 0),
        "blue": (0, 0, 255),
        "none": (0, 0, 0)}

    def __init__(self):
        pass

    def off(self):
        """Turns the led off"""
        self.set_rgb(0, 0, 0)

    def __getattr__(self, name):
        if name in self.color_mapping:
            return lambda x=name: self.set_color(x)

    def set_color(self, color_str):
        """Sets the color of the led from a string"""
        try:
            self.set_rgb(*self.color_mapping[color_str])
        except KeyError:
            raise ValueError("Color {} not found in color mapping!".format(color_str))

class RGB_LED_Gamma(RGB_LED_Base):
    """Controls the RGB led"""

    def _setup(self):
        for gpio_num in self._get_rgb_gpios():
            gpio.setup(gpio_num, gpio.HIGH)

    def _get_rgb_gpios(self):
        # returns GPIOs for red, green, blue
        return 498, 496, 497

    def set_rgb(self, *colors):
        """Sets the color of the led from RGB values [0-255] range"""
        colors = [int(c) for c in colors]
        if len(colors) != 3 or any([type(color) != int for color in colors]):
            raise TypeError("set_rgb expects three integer arguments - red, green and blue values!")
        if any([color < 0 or color > 255 for color in colors]):
            raise ValueError("set_rgb expects integers in range from 0 to 255!")
        gpios = self._get_rgb_gpios()
        for i, gpio_num in enumerate(gpios):
            gpio_state = colors[i] < 255  # Only 0 and 255 are respected
            gpio.set(gpio_num, gpio_state)

class RGB_LED_Delta(RGB_LED_Gamma):
    def _get_rgb_gpios(self):
        # returns GPIOs for red, green, blue
        return 497, 498, 499


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


def main():
    parser = argparse.ArgumentParser(prog='zerophone_hw', description='Zerophone Hardware Command Line Interface')
    parser.add_argument("-e",
           help="Silence the 'not for end-users' warning",
           action="store_true",
           dest="nonenduser",
           default=False)
    subparsers = parser.add_subparsers()
    add_object_subparser(Charger(), 'charger', subparsers)
    add_object_subparser(RGB_LED(), 'led', subparsers)
    add_object_subparser(USB_DCDC(), 'dcdc', subparsers)
    add_object_subparser(GSM_Modem(), 'modem', subparsers)
    args = parser.parse_args()
    if hasattr(args.__obj, '_setup'):
        getattr(args.__obj, '_setup')()
    if not args.nonenduser:
        print("------ NOT TO BE USED BY END-USERS, USE THE 'zp' API INSTEAD ------")
    status = getattr(args.__obj, args.command)(*args.params)
    if status is not None:
        print(status)
        sys.exit(status)


if __name__ == "__main__":
    main()
