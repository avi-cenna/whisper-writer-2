import json
import tempfile
import wave

import numpy as np
import sounddevice as sd
import os
import threading

import webrtcvad
from faster_whisper import WhisperModel
from loguru import logger



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


def record_and_transcribe_fw(status_queue, cancel_flag, config=None):
    sample_rate = 16000
    frame_duration = 30  # 30ms, supported values: 10, 20, 30
    buffer_duration = 300  # 300ms
    silence_duration = config["silence_duration"] if config else 900  # 900ms

    vad = webrtcvad.Vad(3)  # Aggressiveness mode: 3 (highest)
    buffer = []
    recording = []
    num_silent_frames = 0
    num_buffer_frames = buffer_duration // frame_duration
    silence_frames_threshold = silence_duration // frame_duration

    print("Recording...") if config["print_to_terminal"] else ""
    with sd.InputStream(
        samplerate=sample_rate,
        channels=1,
        dtype="int16",
        blocksize=sample_rate * frame_duration // 1000,
        callback=lambda indata, frames, time, status: buffer.extend(indata[:, 0]),
    ):
        while not cancel_flag():
            # logger.debug("Continuing recording")
            if len(buffer) < sample_rate * frame_duration // 1000:
                # logger.debug("Buffer not full")
                continue

            frame = buffer[: sample_rate * frame_duration // 1000]
            buffer = buffer[sample_rate * frame_duration // 1000:]

            is_speech = vad.is_speech(np.array(frame).tobytes(), sample_rate)
            if is_speech:
                logger.debug("Speech detected")
                recording.extend(frame)
                num_silent_frames = 0
            else:
                logger.debug("Silence detected")
                if len(recording) > 0:
                    num_silent_frames += 1

                if num_silent_frames >= silence_frames_threshold:
                    break

    audio_data = np.array(recording, dtype=np.int16)
    print("Recording finished. Size:", audio_data.size) if config[
        "print_to_terminal"
    ] else ""

    # Save the recorded audio as a temporary WAV file on disk
    with tempfile.NamedTemporaryFile(
        suffix=".wav", delete=False
    ) as temp_audio_file:
        with wave.open(temp_audio_file.name, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)  # 2 bytes (16 bits) per sample
            wf.setframerate(sample_rate)
            wf.writeframes(audio_data.tobytes())
        fw(temp_audio_file.name)
        os.remove(temp_audio_file.name)
    return ''


def on_shortcut():
    global status_queue

    recording_thread = ResultThread(
        target=record_and_transcribe_fw, args=(status_queue,), kwargs={"config": config}
    )
    recording_thread.start()
    recording_thread.join()

    # status_queue.put(("cancel", ""))

    transcribed_text = recording_thread.result
    print(f"Transcribed text: {transcribed_text}")
    # socket.send_string(transcribed_text)


def format_keystrokes(key_string):
    return "+".join(word.capitalize() for word in key_string.split("+"))


config = load_config_with_defaults()



def fw(waveform: np.ndarray | str):
    # model_size_or_path: Size of the model to use (tiny, tiny.en, base, base.en,
    #  small, small.en, medium, medium.en, large-v1, large-v2, or large), a path to a converted
    #  model directory, or a CTranslate2-converted Whisper model ID from the Hugging Face Hub.
    #  When a size or a model ID is configured, the converted model is downloaded
    #  from the Hugging Face Hub.
    logger.debug("Starting fw")
    model_size = "small.en"
    # or run on CPU with INT8
    # model = WhisperModel(model_size, device="cpu", compute_type="int8")
    model = WhisperModel(model_size)

    segments, info = model.transcribe(waveform, language="en", vad_filter=True)

    print(
        "Detected language '%s' with probability %f"
        % (info.language, info.language_probability)
    )

    for segment in segments:
        print("[%.2fs -> %.2fs] %s" % (segment.start, segment.end, segment.text))
    logger.debug("Finished fw")


if __name__ == "__main__":
    try:
        logger.debug("Starting main")
        on_shortcut()
    except KeyboardInterrupt:
        print("\nExiting the script...")
        os.system("exit")
