import speech_recognition as sr
import requests
import json

# Initialize list of valid wake words
WAKE_WORDS = [
    "hey athena", "okay athena", "athena",
    "yo athena", "good morning athena", "good afternoon athena"
]

# Create a Recognizer instance to process audio
recognizer = sr.Recognizer()

# FUNCTIONS START -------------------------------------------------------------------------------------------------

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
        You are Athena, a local voice assistant that interprets user commands and returns structured JSON instructions to trigger pre-defined Python functions.

        Your job is to convert a natural language command into one of the following three actions:

        1. "turn_on_lights" — turns on lights in a specific location
        2. "turn_off_lights" — turns off lights in a specific location
        3. "run_script" — runs a named script on the user's system

        You must respond with ONLY a single JSON object in this format:

        {
        "action": "<one_of_the_three_above_or_unclear_command>",
        "params": {
            // for "turn_on_lights" or "turn_off_lights": { "location": "<location>" }
            // for "run_script": { "name": "<script_name>" }
        }
        }

        If the user command is vague, confusing, or does not clearly relate to one of the three supported actions, return:

        {
        "action": "unclear_command",
        "params": {}
        }

        DO NOT include any explanation, apology, greeting, or extra text.  
        Your entire response must be valid, parseable JSON."
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


def turn_on_lights(location=None):
    print(f"Lights turned ON at location: {location}")

def turn_off_lights(location=None):
    print(f"Lights turned OFF at location: {location}")

def run_script(name=None):
    print(f"Running script: {name}")

# Map action names to functions
intent_map = {
    "turn_on_lights": turn_on_lights,
    "turn_off_lights": turn_off_lights,
    "run_script": run_script
}


# FUNCTIONS END --------------------------------------------------------------------------------------------------

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
