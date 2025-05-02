import speech_recognition as sr
import requests
import json
from utility import (
    tell_time,
    monitor_backlight_on,
    monitor_backlight_off,
    monitor_backlight_color,
    play_music,
    pause_music,
    music_next_track,
    music_previous_track
)
import pyttsx3
import time
import threading
import queue
import traceback

# Initialize TTS engine
engine = pyttsx3.init()
tts_lock = threading.Lock()
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[1].id)  # Zira
engine.setProperty('rate', 180)

# Create a thread-safe queue
tts_queue = queue.Queue()

# Background worker thread
def tts_worker():
    while True:
        text = tts_queue.get()
        if text is None:
            break
        with tts_lock:
            try:
                engine.say(text)
                engine.runAndWait()
            except Exception as e:
                print("[TTS ERROR]", e)
        tts_queue.task_done()

# Start the TTS thread
tts_thread = threading.Thread(target=tts_worker, daemon=True)
tts_thread.start()

def say(text):
    print(f"[DEBUG] Queuing TTS: {text}")
    tts_queue.put(text)

# Initialize list of valid wake words
WAKE_WORDS = [
    "hey athena", "okay athena", "athena",
    "yo athena", "good morning athena", "good afternoon athena"
]

# Create a Recognizer instance to process audio
recognizer = sr.Recognizer()






# ATHENA FUNCTIONS START -------------------------------------------------------------------------------------------------



# Function to check if the spoken text contains a wake word
def contains_wake_word(text):
    return any(wake in text.lower() for wake in WAKE_WORDS)

# Function to listen for a follow-up command after the wake word is detected
def listen_for_command():
    with sr.Microphone() as source:
        print("Listening for your command...")
        audio = recognizer.listen(source)  # Capture audio from the microphone

        try:
            # Use Google Speech Recognition to convert audio to text
            command = recognizer.recognize_google(audio)
            print("You said:", command)
            return command.lower()
        except:
            # Handle cases where the speech wasn't recognized
            print("Couldn't understand the command.")
            return None
        
# Function to send a prompt to Ollama
def send_to_ollama(command):
    url = "http://localhost:11434/api/generate"

    system_prompt = (
        """
        You are Athena, a local desktop voice assistant. Your job is to interpret user commands and return JSON instructions to trigger specific Python functions.

        You ONLY respond with a single, valid, parseable JSON object in this format:

        {
        "action": "<one of the actions listed below>",
        "params": { ... }
        }

        OR If the user says something confusing, unsupported, or unrelated to the actions below, respond with:

        {
        "action": "unclear_command",
        "params": {}
        }

        ---

        Here are the supoported actions and their schemas.
        
        SUPPORTED ACTIONS:

        1. "tell_time" — Tells the current time
        - Example:
            {
            "action": "tell_time",
            "params": {}
            }

        2. "monitor_backlight_on" — Turns on the Philips Hue monitor backlight
        - Example:
            {
            "action": "monitor_backlight_on",
            "params": {}
            }

        3. "monitor_backlight_off" — Turns off the Philips Hue monitor backlight
        - Example:
            {
            "action": "monitor_backlight_off",
            "params": {}
            }

        4. "monitor_backlight_color" — Sets the monitor backlight to a specific color
        - Accepted colors: red, green, blue, light blue, cyan, purple, white, warm white, orange, yellow, pink
        - Example:
            {
            "action": "monitor_backlight_color",
            "params": {
                "color_name": "blue"
            }
            }

        5. "play_music" — Toggles music playback (play/pause)
        - Example:
            {
            "action": "play_music",
            "params": {}
            }

        6. "pause_music" — Toggles music playback (play/pause)
        - Example:
            {
            "action": "pause_music",
            "params": {}
            }

        7. "music_next_track" — Skips to the next music track
        - Example:
            {
            "action": "music_next_track",
            "params": {}
            }

        8. "music_previous_track" — Returns to the previous music track
        - Example:
            {
            "action": "music_previous_track",
            "params": {}
            }

        ---

        💡 INSTRUCTIONS:

        - NEVER include explanations, greetings, or extra text.
        - ONLY return the JSON.
        - Always match the action name and parameter structure exactly.
        - Do NOT return actions not listed above.
        """)


    full_prompt = f"{system_prompt}\nUser command: {command}"

    payload = {
        "model": "mistral",
        "prompt": full_prompt,
        "stream": False
    }

    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            result = response.json()["response"]

            try:
                intent = json.loads(result)
                action = intent.get("action")
                params = intent.get("params", {})

                if action in intent_map:
                    print(f"Executing: {action} with params: {params}")
                    voice_response = get_voice_response(command, action)
                    handle_action_with_voice(action, params, voice_response or "")

                else:
                    print(f"Unknown action: {action}")
            except json.JSONDecodeError:
                print("Could not parse JSON from LLM:", result)
        else:
            print(f"Ollama returned status {response.status_code}: {response.text}")
    except Exception as e:
        print("Error talking to Ollama:", e)

# Function to get a spoken responce from Athena
def get_voice_response(command_text, action_name):
    system_prompt = f"""
    You are Athena, a warm and professional voice assistant. 
    A user has just said: "{command_text}"

    Your task is to generate a short, natural spoken response for this action: {action_name}

    Respond in 1 sentence or less, friendly and clear.

    DO NOT repeat the user's command. DO NOT mention your name. 
    Just say what you're doing in a natural way.
    Example: "Turning off the monitor backlight now."

    Your response should be strictly text with no code or quotation marks.
    """

    payload = {
        "model": "mistral",
        "prompt": system_prompt,
        "stream": False
    }

    try:
        response = requests.post("http://localhost:11434/api/generate", json=payload)
        if response.status_code == 200:
            return response.json()["response"].strip()
        else:
            return None
    except Exception as e:
        print(f"Error getting voice response: {e}")
        return None

# Function that runs the function/speaks with the correct timing
def handle_action_with_voice(action, params, voice_text):
    func = intent_map.get(action)
    timing = timing_map.get(action, "speak_then_act")  # default if not listed

    if not func:
        print(f"Unknown action: {action}")
        return

    if timing == "speak_then_act":
        say(voice_text)
        time.sleep(1.2)
        func(**params)

    elif timing == "act_then_speak":
        func(**params)
        time.sleep(0.6)
        say(voice_text)

    elif timing == "parallel":
        say(voice_text)
        func(**params)

    else:
        # fallback to speak then act
        say(voice_text)
        func(**params)




# ATHENA FUNCTIONS END --------------------------------------------------------------------------------------------------



timing_map = {
    "play_music": "speak_then_act",
    "pause_music": "act_then_speak",
    "monitor_backlight_color": "parallel",
    "monitor_backlight_on": "parallel",
    "monitor_backlight_off": "parallel",
    "music_next_track": "parallel",
    "music_previous_track": "parallel",
    "tell_time": "act_then_speak"
}

intent_map = {
    "tell_time": tell_time,
    "monitor_backlight_on": monitor_backlight_on,
    "monitor_backlight_off": monitor_backlight_off,
    "monitor_backlight_color": monitor_backlight_color,
    "play_music": play_music,
    "pause_music": pause_music,
    "music_next_track": music_next_track,
    "music_previous_track": music_previous_track
}

# Main loop: listen continuously for wake words
with sr.Microphone() as source:
    # Adjust for ambient noise to improve recognition accuracy
    recognizer.adjust_for_ambient_noise(source)
    print("Athena is listening for wake word...")

    while True:
        try:
            print("Listening...")
            audio = recognizer.listen(source)  # Listen for a short audio segment
            text = recognizer.recognize_google(audio)  # Transcribe the audio
            print("Heard:", text)

            # If the wake word is detected, respond accordingly
            if contains_wake_word(text):
                print("Wake word detected! Ready for your command.")
                
                # Use the listen_for_command func to grab next audio snip and save as a var
                command = listen_for_command()
                
                # Pass the command into Mistral
                if command:
                    send_to_ollama(command)

        except sr.UnknownValueError:
            # Speech was detected, but couldn't be understood
            print("Didn't catch that.")
        except sr.RequestError as e:
            # Something went wrong when trying to reach Google's API
            print(f"Could not reach Google: {e}")

