import json
import os
import queue
import threading
import tkinter as tk

import keyboard
import pyautogui


def open_small_window():
    window = tk.Tk()
    window.title("Small Window")
    # window.getry("200x100")  # Adjust size as needed
    window.geometry("200x100")  # Adjust size as needed
    window.focus_force()
    window.grab_release()
    window.attributes("-topmost", True)
    window.after(4000, window.destroy)
    window.mainloop()


def open_small_window2():
    window = tk.Tk()
    # window.title("Small Window")
    window.after(2000, window.destroy)
    window.mainloop()


# keyboard.add_hotkey("F13", lambda: print("F13 pressed"))
# keyboard.add_hotkey("h", lambda: print("h pressed"))
# keyboard.add_hotkey("j", lambda: print("j pressed"))
# keyboard.add_hotkey("alt+j", lambda: print("alt+j pressed"))

try:
    open_small_window2()
    # keyboard.wait()  # Keep the script running to listen for the shortcut
except KeyboardInterrupt:
    print("\nExiting the script...")
    os.system("exit")
