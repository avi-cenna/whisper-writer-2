import json
import os
import queue
import threading
import time

import keyboard
import zmq

from status_window import StatusWindow
from transcription import record_and_transcribe

# def on_shortcut():
#     global status_queue
#     clear_status_queue()
#
#     status_queue.put(('recording', 'Recording...'))
#     recording_thread = ResultThread(target=record_and_transcribe, args=(status_queue,), kwargs={'config': config})
#     recording_thread.start()
#
#     recording_thread.join()
#     status_queue.put(('cancel', ''))
#
#     transcribed_text = recording_thread.result
#     print(transcribed_text)
#
#     # if transcribed_text:
#     #     pyautogui.write(transcribed_text, interval=config['writing_key_press_delay'])


# keyboard.add_hotkey(config['activation_key'], on_shortcut)
# keyboard.add_hotkey('F13', on_shortcut)


class ResultThread(threading.Thread):
    def __init__(self, *args, **kwargs):
        super(ResultThread, self).__init__(*args, **kwargs)
        self.result = None
        self.stop_transcription = False

    def run(self):
        self.result = self._target(
            *self._args, cancel_flag=lambda: self.stop_transcription, **self._kwargs
        )

    def stop(self):
        self.stop_transcription = True


def load_config_with_defaults():
    default_config = {
        "use_api": True,
        "api_options": {
            "model": "whisper-1",
            "language": None,
            "temperature": 0.0,
            "initial_prompt": None,
        },
        "local_model_options": {
            "model": "base",
            "device": None,
            "language": None,
            "temperature": 0.0,
            "initial_prompt": None,
            "condition_on_previous_text": True,
            "verbose": False,
        },
        "activation_key": "ctrl+alt+space",
        "silence_duration": 900,
        "writing_key_press_delay": 0.008,
        "remove_trailing_period": True,
        "add_trailing_space": False,
        "remove_capitalization": False,
        "print_to_terminal": True,
    }

    config_path = os.path.join("src", "config.json")
    if os.path.isfile(config_path):
        with open(config_path, "r") as config_file:
            user_config = json.load(config_file)
            for key, value in user_config.items():
                if key in default_config and value is not None:
                    default_config[key] = value

    return default_config


def clear_status_queue():
    while not status_queue.empty():
        try:
            status_queue.get_nowait()
        except queue.Empty:
            break


def on_shortcut():
    global status_queue
    clear_status_queue()

    status_queue.put(("recording", "Recording..."))
    recording_thread = ResultThread(
        target=record_and_transcribe, args=(status_queue,), kwargs={"config": config}
    )
    recording_thread.start()

    recording_thread.join()

    status_queue.put(("cancel", ""))

    transcribed_text = recording_thread.result
    print(f"Transcribed text: {transcribed_text}")
    socket.send_string(transcribed_text)


def format_keystrokes(key_string):
    return "+".join(word.capitalize() for word in key_string.split("+"))


config = load_config_with_defaults()
method = "OpenAI's API" if config["use_api"] else "a local model"
status_queue = queue.Queue()

keyboard.add_hotkey("F13", on_shortcut)

# print(
#     f'Script activated. Whisper is set to run using {method}. To change this, modify the "use_api" value in the src\\config.json file.'
# )
# print(
#     f'Press {format_keystrokes(config["activation_key"])} to start recording and transcribing. Press Ctrl+C on the terminal window to quit.'
# )


context = zmq.Context()
socket = context.socket(zmq.REP)
socket.bind("tcp://*:5555")
print("Server started")


def main():
    while True:
        #  Wait for next request from client
        message = socket.recv().decode("utf-8")
        print(f"Received request: {message}")

        #  Do some 'work'
        time.sleep(0.01)
        on_shortcut()

        #  Send reply back to client
        # result = reverse_string(message)
        # print(result, type(result))
        # socket.send_string(result)


def reverse_string(string):
    return string[::-1]


if __name__ == "__main__":
    # f = 'foo'
    # print(reverse_string('foo'))
    main()
