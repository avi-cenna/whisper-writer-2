import os
import tempfile
import traceback
import wave
from pathlib import Path

import numpy as np
import openai
import sounddevice as sd
import webrtcvad
import whisper
from dotenv import load_dotenv
from faster_whisper import WhisperModel
from loguru import logger

if load_dotenv():
    openai.api_key = os.getenv("OPENAI_API_KEY")


def process_transcription(transcription, config=None):
    if config:
        if config["remove_trailing_period"] and transcription.endswith("."):
            transcription = transcription[:-1]
        if config["add_trailing_space"]:
            transcription += " "
        if config["remove_capitalization"]:
            transcription = transcription.lower()

    return transcription


"""
Record audio from the microphone and transcribe it using the OpenAI API.
Recording stops when the user stops speaking.
"""


def record_and_transcribe(status_queue, cancel_flag, config=None):
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
    try:
        print("Recording...") if config["print_to_terminal"] else ""
        with sd.InputStream(
            samplerate=sample_rate,
            channels=1,
            dtype="int16",
            blocksize=sample_rate * frame_duration // 1000,
            callback=lambda indata, frames, time, status: buffer.extend(indata[:, 0]),
        ):
            while not cancel_flag():
                logger.debug("Continuing recording")
                if len(buffer) < sample_rate * frame_duration // 1000:
                    logger.debug("Buffer not full")
                    continue

                frame = buffer[: sample_rate * frame_duration // 1000]
                buffer = buffer[sample_rate * frame_duration // 1000 :]

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

        # TODO: is this used?
        if cancel_flag():
            status_queue.put(("cancel", ""))
            return ""

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

        status_queue.put(("transcribing", "Transcribing..."))
        print("Transcribing audio file...") if config["print_to_terminal"] else ""

        # If configured, transcribe the temporary audio file using the OpenAI API
        if config["use_api"]:
            api_options = config["api_options"]
            with open(temp_audio_file.name, "rb") as audio_file:
                response = openai.Audio.transcribe(
                    model=api_options["model"],
                    file=audio_file,
                    language=api_options["language"],
                    prompt=api_options["initial_prompt"],
                    temperature=api_options["temperature"],
                )
        else:
            # TODO: does this work? the array is using int16
            fw(audio_data)
            model_options = config["local_model_options"]
            model = whisper.load_model(
                name=model_options["model"], device=model_options["device"]
            )
            response = model.transcribe(
                audio=temp_audio_file.name,
                language=model_options["language"],
                verbose=None
                if not config["print_to_terminal"]
                else model_options["verbose"],
                initial_prompt=model_options["initial_prompt"],
                condition_on_previous_text=model_options["condition_on_previous_text"],
                temperature=model_options["temperature"],
            )

        # Remove the temporary audio file
        os.remove(temp_audio_file.name)

        if cancel_flag():
            status_queue.put(("cancel", ""))
            return ""

        result = response.get("text")
        print("Transcription:", result) if config["print_to_terminal"] else ""
        status_queue.put(("idle", ""))

        return process_transcription(result.strip(), config) if result else ""

    except Exception as e:
        traceback.print_exc()
        status_queue.put(("error", "Error"))


def fw(waveform: np.ndarray):
    # model_size_or_path: Size of the model to use (tiny, tiny.en, base, base.en,
    #  small, small.en, medium, medium.en, large-v1, large-v2, or large), a path to a converted
    #  model directory, or a CTranslate2-converted Whisper model ID from the Hugging Face Hub.
    #  When a size or a model ID is configured, the converted model is downloaded
    #  from the Hugging Face Hub.
    model_size = "small.en"
    # or run on CPU with INT8
    model = WhisperModel(model_size, device="cpu", compute_type="int8")

    segments, info = model.transcribe(waveform, language="en", vad_filter=True)

    print(
        "Detected language '%s' with probability %f"
        % (info.language, info.language_probability)
    )

    for segment in segments:
        print("[%.2fs -> %.2fs] %s" % (segment.start, segment.end, segment.text))
