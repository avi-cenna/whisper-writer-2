import json
import os
import queue
import threading
from transcription import record_and_transcribe
from status_window import StatusWindow


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

def main():
    import time
    import zmq

    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind("tcp://*:5555")
    print("Server started")

    while True:
        #  Wait for next request from client
        message = socket.recv().decode('utf-8')
        print(f"Received request: {message}")

        #  Do some 'work'
        time.sleep(.01)

        #  Send reply back to client
        result = reverse_string(message)
        print(result, type(result))
        socket.send_string(result)


def reverse_string(string):
    return string[::-1]


if __name__ == '__main__':
    # f = 'foo'
    # print(reverse_string('foo'))
    main()
