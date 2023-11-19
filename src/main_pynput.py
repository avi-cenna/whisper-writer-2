import json
import os
import queue
import threading
import time

from pynput import keyboard


def on_activate_f13():
    print("F13 pressed")


def on_activate_option_1():
    print("Option+1 pressed")


# For Windows/Linux, replace keyboard.Key.alt with keyboard.Key.alt_l
hotkey_f13 = {keyboard.Key.f13}
hotkey_option_1 = {keyboard.Key.alt, keyboard.KeyCode.from_char("1")}

if __name__ == "__main__":
    # this isn't working
    #
    with keyboard.GlobalHotKeys(
        {
            "<f13>": on_activate_f13,
            "<alt>+1": on_activate_option_1,
            "<alt>+j": on_activate_option_1,
            "<alt>+h": on_activate_option_1,
            "h": on_activate_option_1,
            "p": on_activate_option_1,
        }
    ) as h:
        h.join()
