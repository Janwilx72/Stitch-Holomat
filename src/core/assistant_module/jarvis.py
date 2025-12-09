from RealtimeSTT import AudioToTextRecorder
import time
import threading
from pygame import mixer
from core.assistant_module import jarvis_assist, jarvis_tools
import core.data.shared_variables as shared_variables


def listen_thread(recorder):
    while True:
        text = recorder.text()
        with shared_variables.latest_text_lock:
            shared_variables.latest_text = text


def init_jarvis():
    mixer.init()  # Initialize mixer for audio playback
    recorder = AudioToTextRecorder(spinner=False, model="base.en", language="en",
                                   post_speech_silence_duration=0.15, silero_sensitivity=0.4)
    hot_words = ["gideon"]
    expecting_user_response = False

    print("Say something...")

    # Start the recorder if not in silent mode
    if not jarvis_tools.is_silent_mode() and not recorder.is_recording:
        recorder.start()

    # Start the listener thread
    listener = threading.Thread(target=listen_thread, args=(recorder,), daemon=True)
    listener.start()

    # In the main loop, modify the while True section
    try:
        while True:
            if jarvis_tools.is_silent_mode():
                # Stop recorder if it's running
                if recorder.is_recording:
                    recorder.stop()
                # Switch to text input when in silent mode
                user_input = input("You: ")
                response = jarvis_assist.ask_question_memory(user_input + " " + time.strftime("%D:%H:%M:%S"))
                print("Jarvis:", response)

                # If this response indicates silent mode was disabled
                if "silent mode disabled" in response.lower():
                    # Start recorder before TTS
                    recorder.start()
                    jarvis_assist.TTS(response)
                continue
            else:
                # Start recorder if it's not running
                if not recorder.is_recording:
                    recorder.start()

            # Normal voice mode code
            time.sleep(0.1)
            with shared_variables.latest_text_lock:
                current_text = shared_variables.latest_text
                shared_variables.latest_text = ""

            if current_text:
                print("You:", current_text)
                # Interrupt handling during voice response
                if mixer.music.get_busy() and any(hot_word in current_text.lower() for hot_word in hot_words):
                    mixer.music.stop()
                    print("Jarvis interrupted. Listening for new command...")
                    continue

                # Main command processing
                if any(hot_word in current_text.lower() for hot_word in hot_words) or expecting_user_response:
                    response = jarvis_assist.ask_question_memory(current_text + " " + time.strftime("%D:%H:%M:%S"))
                    print("Jarvis:", response)

                    # Set expecting_user_response based on whether Jarvis's response ends with '?'
                    expecting_user_response = response.strip().endswith('?')

                    # Handle TTS response
                    if not jarvis_tools.is_silent_mode():
                        jarvis_assist.TTS_with_interrupt(response, hot_words)

    except KeyboardInterrupt:
        print("\nJarvis interrupted by user.")
        mixer.music.stop()
        recorder.stop()
    finally:
        print("Exiting Jarvis.")
        recorder.stop()

if __name__ == '__main__':
    init_jarvis
