import json
import os
import queue
import threading

import keyboard
import pyautogui

keyboard.add_hotkey("F13", lambda: print("F13 pressed"))
keyboard.add_hotkey("h", lambda: print("h pressed"))
keyboard.add_hotkey("j", lambda: print("j pressed"))
keyboard.add_hotkey("alt+j", lambda: print("alt+j pressed"))

try:
    keyboard.wait()  # Keep the script running to listen for the shortcut
except KeyboardInterrupt:
    print("\nExiting the script...")
    os.system("exit")
