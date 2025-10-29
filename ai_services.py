import speech_recognition as sr
import re


# --- Part 1: Speech-to-Text ---

def listen_for_command():
    """
    Listens for audio from the user's microphone and converts it to text.
    """
    recognizer = sr.Recognizer()
    recognizer.pause_threshold = 0.8  # How long to wait for silence

    with sr.Microphone() as source:
        print("Listening...")
        recognizer.adjust_for_ambient_noise(source, duration=0.5)

        try:
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)

            print("Recognizing...")
            command = recognizer.recognize_google(audio)
            print(f"You said: {command}")
            return command

        except sr.WaitTimeoutError:
            print("Listening timed out. Please try again.")
            return None
        except sr.UnknownValueError:
            print("Google Speech Recognition could not understand audio.")
            return None
        except sr.RequestError as e:
            print(f"Could not request results from Google service; {e}")
            return None
        except Exception as e:
            print(f"An unknown error occurred: {e}")
            return None


# --- Part 2: Natural Language Processing (NLP) ---

def parse_command(command: str) -> str:
    """
    Parses the raw text command into a valid mathematical expression.
    e.g., "what is five times three" -> "5 * 3"
    """
    if command is None:
        return ""

    text = command.lower()

    # --- Word-to-Symbol Mappings ---
    number_map = {
        'zero': '0', 'one': '1', 'two': '2', 'to': '2', 'too': '2',
        'three': '3', 'four': '4', 'for': '4', 'five': '5', 'six': '6',
        'seven': '7', 'eight': '8', 'nine': '9', 'ten': '10',
    }

    operator_map = {
        'plus': '+', 'add': '+', 'minus': '-', 'subtract': '-',
        'times': '*', 'multiplied by': '*', 'divided by': '/', 'over': '/',
        'to the power of': '**',  # <-- Use **
        'power': '**',  # <-- Use **
        'square root of': 'sqrt(', 'open bracket': '(', 'open parentheses': '(',
        'close bracket': ')', 'close parentheses': ')', 'point': '.', 'dot': '.',
    }

    # --- Step 1: Remove "stop words" ---
    stop_words = ["what is", "what's", "calculate", "compute", "can you tell me"]
    for word in stop_words:
        text = text.replace(word, "")

    # --- Step 2: Replace operator phrases ---
    for word, symbol in operator_map.items():
        text = text.replace(word, symbol)

    # --- Step 3: Replace number words ---
    for word, symbol in number_map.items():
        text = text.replace(word, symbol)

    # --- Step 4: Clean up ---
    # This keeps: digits, operators (+-*/), parentheses, 's' 'q' 'r' 't', and spaces.
    # We must now also keep '*' (for the ** operator).
    text = re.sub(r'[^0-9\+\-\*\/\.\(\)sqrt ]', '', text)

    # --- Step 5: Handle 'sqrt(' ---
    if 'sqrt(' in text and ')' not in text.split('sqrt(')[-1]:
        text += ')'

    # Remove extra whitespace
    text = ' '.join(text.split())

    print(f"Parsed command: {text}")
    return text


# --- Main block for testing this file directly ---
if __name__ == "__main__":
    print("--- Testing AI Services ---")
    print("\n--- Test 1: Parsing ---")
    test_cmd = "what is five to the power of three"
    print(f"Input: {test_cmd}")
    print(f"Output: {parse_command(test_cmd)}")  # Should be 5 ** 3

    test_cmd_2 = "calculate the square root of nine"
    print(f"\nInput: {test_cmd_2}")
    print(f"Output: {parse_command(test_cmd_2)}")

