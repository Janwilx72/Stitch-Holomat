import json

from openai import OpenAI
import time
from pygame import mixer
import os
from googlesearch import search

from core.assistant_module import jarvis_tools
from core.data import shared_variables

# Initialize the client and mixer
client = OpenAI(default_headers={"OpenAI-Beta": "assistants=v2"},
                api_key='')
mixer.init()

assistant_id = ""
thread_id = ""

# Retrieve the assistant and thread
assistant = client.beta.assistants.retrieve(assistant_id)
thread = client.beta.threads.retrieve(thread_id)

conversation_history = [
    {
        "role": "system",
        "content": (
            "You are an assistant named Jarvis. Keep your responses short yet human, don't be robotic. "
            "You can execute commands. Only ever execute these commands upon given explicit instruction from the user. "
            "Here are the commands:\n\n"
            "* #lights-1/0 - this command triggers the lights, 1 meaning on while 0 means off.\n"
            "* {google} - whenever a user asks for something relative to real-time information, you reply with: '{google} (summarized query)'. You will then get a set of results, which you have to interpret and tell the user in natural language \n\n"
            "It is imperative that you end your sentence with these triggers and do not say anything after them. "
            "The hashtag is the trigger character, and whatever is after the tag is the command to be triggered."
        )
    }
]

# Load functions to the model
current_dir = os.path.dirname(os.path.abspath(__file__))

# Load functions to the model
functions_path = os.path.join(current_dir, 'functions.json')

with open(functions_path, 'r') as f:
    functions = json.load(f)['functions']

# Maps the actual functions in the code to the functions provided in the json file
function_map = {}
for func_name in dir(jarvis_tools):
    if not func_name.startswith('_'):
        func = getattr(jarvis_tools, func_name)
        if callable(func):
            function_map[func_name] = func


def perform_web_search(query, num_results=3):
    try:
        results = list(search(query, num_results=num_results, advanced=True))
        return [{'title': r.title, 'description': r.description, 'url': r.url} for r in results]
    except Exception as e:
        print(f"Error performing web search: {e}")
        return []


def process_response(response):
    if response.startswith("{google}"):
        search_query = response[8:].strip()
        print(f"Performing web search for: {search_query}")
        search_results = perform_web_search(search_query)

        if search_results:
            search_info = "\n".join(
                [f"Title: {r['title']}\nDescription: {r['description']}" for r in search_results]
            )
            follow_up_message = (
                f"Here are the search results for '{search_query}':\n\n{search_info}\n\n"
                "Please provide a response based on this information."
            )
            return ask_question_memory(follow_up_message)
        else:
            return f"I'm sorry, but I couldn't find any relevant search results for '{search_query}'."
    else:
        return response


def ask_question_memory(question):
    """
    Processes a user's question, updates conversation history,
    and fetches a response from OpenAI.
    """
    try:
        conversation_history.append({"role": "user", "content": question})
        print("\n[DEV] Sending request to OpenAI...")
        # Response section - adjust settings however you like
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=conversation_history,
            functions=functions,
            function_call="auto",
            temperature=0.5,
            max_tokens=4096  # 4K is recommended, adjust if you sincerely can't afford token usage
        )

        message = response.choices[0].message

        if hasattr(message, 'function_call') and message.function_call:
            function_name = message.function_call.name
            function_args = json.loads(message.function_call.arguments)
            print(f"\n[DEV] Function called: {function_name}")
            print(f"[DEV] Arguments: {function_args}")

            if function_name in function_map:
                result = function_map[function_name](**function_args)
                print(f"[DEV] Function result: {result}")
            else:
                result = f"Function {function_name} not found"

            conversation_history.append({
                "role": "assistant",
                "content": None,
                "function_call": {
                    "name": function_name,
                    "arguments": message.function_call.arguments
                }
            })

            conversation_history.append({
                "role": "function",
                "name": function_name,
                "content": str(result)
            })
            # Final response after commencing function call
            print("[DEV] Getting final response after function call...")
            final_response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=conversation_history,
                temperature=0.5,
                max_tokens=4096  # 4K is recommended, adjust if you sincerely can't afford token usage
            )
            ai_response = final_response.choices[0].message.content
        else:
            print("[DEV] No function called, normal response")
            ai_response = message.content

        conversation_history.append({"role": "assistant", "content": ai_response})
        return ai_response

    except Exception as e:
        print(f"[DEV] Error occurred: {str(e)}")
        return f"An error occurred: {str(e)}"


# From here on and below it's all TTS settings
def generate_tts(sentence, speech_file_path):
    """
    Generates Text-to-Speech audio and saves it to a file.
    """
    response = client.audio.speech.create(
        model="tts-1",
        voice="echo", # Adjust to change Jarvis' voice
        input=sentence
    )
    response.stream_to_file(speech_file_path)
    return str(speech_file_path)


def play_sound(file_path):
    """
    Plays the given audio file using the mixer module.
    """
    mixer.music.load(file_path)
    mixer.music.play()


def TTS(text):
    """
    Plays the Text-to-Speech response unless Silent Mode is active.
    """
    if jarvis_tools.is_silent_mode():
        print(f"Jarvis: {text}")  # Print response instead of speaking
        return "Silent mode active. Response printed only."
    speech_file_path = generate_tts(text, "speech.mp3")
    play_sound(speech_file_path)
    while mixer.music.get_busy():
        time.sleep(0.1)
    mixer.music.unload()
    if os.path.exists(speech_file_path):
        os.remove(speech_file_path)
    return "done"


def TTS_with_interrupt(text, hot_words):
    """
    Plays the response with interrupt handling during playback.
    """
    speech_file_path = generate_tts(text, "speech.mp3")
    play_sound(speech_file_path)

    try:
        while mixer.music.get_busy():
            # Non-blocking check for interrupt signal
            with shared_variables.latest_text_lock:
                current_text = shared_variables.latest_text
                # Clear latest_text to avoid processing the same text multiple times
                shared_variables.latest_text = ""

            if current_text and any(hot_word in current_text.lower() for hot_word in hot_words):
                print("Jarvis interrupted.")
                mixer.music.stop()
                break  # Exit the loop to proceed to cleanup
            time.sleep(0.1)
    finally:
        # Ensure resources are cleaned up whether interrupted or not
        mixer.music.unload()
        if os.path.exists(speech_file_path):
            os.remove(speech_file_path)
    return "done"


if __name__ == "__main__":
    while True:
        user_input = input("You: ")
        if user_input.lower() == 'exit':
            break
        response = ask_question_memory(user_input)
        print("Assistant:", response)
        TTS(response)