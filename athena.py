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
                    intent_map[action](**params)
                else:
                    print(f"Unknown action: {action}")
            except json.JSONDecodeError:
                print("Could not parse JSON from LLM:", result)
        else:
            print(f"Ollama returned status {response.status_code}: {response.text}")
    except Exception as e:
        print("Error talking to Ollama:", e)


# ATHENA FUNCTIONS END --------------------------------------------------------------------------------------------------

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

