import json
import os
import queue
import threading

from loguru import logger

from transcription import record_and_transcribe


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


def rec():
    global status_queue
    clear_status_queue()

    status_queue.put(("recording", "Recording..."))
    recording_thread = ResultThread(
        target=record_and_transcribe, args=(status_queue,), kwargs={"config": config}
    )
    logger.debug(f"Starting recording thread")
    recording_thread.start()
    recording_thread.join()
    logger.debug(f"Finished recording")

    transcribed_text = recording_thread.result
    logger.debug(f"Transcribed text: {transcribed_text}")
    print(transcribed_text, end="")


config = load_config_with_defaults()
method = "OpenAI's API" if config["use_api"] else "a local model"
status_queue = queue.Queue()


def main():
    rec()


if __name__ == "__main__":
    logger.debug(f"Starting main")
    main()
