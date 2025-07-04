import asyncio
import edge_tts
import speech_recognition as sr
from playsound import playsound
import tempfile
from deep_translator import GoogleTranslator
import wikipedia  # kept since original code imported it (but unused now)
import google.generativeai as genai
import os

# === Gemini Configuration ===
GEMINI_API_KEY = 'AIzaSyB8rGHTzqAVXSXfjhLrnyRS1RiXh3ekVJo'  # Replace with your actual key
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")
model.last_response_text = ""  # Cache for Gemini response if needed

# === Voice Map ===
voice_map = {
    "en": "en-IN-NeerjaNeural",
    "hi": "hi-IN-SwaraNeural",
    "bn": "bn-IN-TanishaaNeural"
}

# === Speak using edge-tts ===
async def speak(text, lang="en"):
    try:
        voice = voice_map.get(lang, "en-IN-NeerjaNeural")
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
            temp_path = fp.name
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(temp_path)
        playsound(temp_path)
        os.remove(temp_path)
    except Exception as e:
        print(f"Speech error: {e}")

# === Sync wrapper with print (keep previous debug prints) ===
def say(text, lang="en"):
    print(f"\nSpoken ({lang}): {text}\n")
    asyncio.run(speak(text, lang))

# === Speech recognition ===
def listen(language="en-US"):
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print(f"Listening ({language})...")
        recognizer.adjust_for_ambient_noise(source, duration=1)
        audio = recognizer.listen(source)
    try:
        text = recognizer.recognize_google(audio, language=language)
        print(f"Recognized: {text}")
        return text
    except sr.UnknownValueError:
        print("Could not understand audio.")
        return None

# === Language Maps ===
lang_map = {
    "english": "en",
    "hindi": "hi",
    "bengali": "bn"
}

speech_lang_map = {
    "en": "en-US",
    "hi": "hi-IN",
    "bn": "bn-IN"
}

# === Translation ===
def translate_text(text, target_lang):
    try:
        translated = GoogleTranslator(source='auto', target=target_lang).translate(text)
        return translated
    except Exception as e:
        return f"Translation error: {e}"

# === Tour Guide Function (Gemini Only, no Wikipedia) ===
def get_city_recommendations(city, mode="places"):
    try:
        if mode == "places":
            prompt = f"Give me a numbered list of exactly 5 famous tourist places in {city}. Only the names, no descriptions."
        else:
            prompt = f"Give me a numbered list of exactly 5 well-known restaurants in {city}. Only the names."

        response = model.generate_content(prompt)

        if response and response.text:
            full_text = response.text.strip()
            # Do NOT print Gemini full raw response to terminal anymore (per your request)
            # But keep cached for speaking if needed
            model.last_response_text = full_text

            # Extract cleaned list of place/restaurant names
            lines = full_text.split('\n')
            info = []
            for line in lines:
                cleaned = line.strip("-•*1234567890. ").strip()
                if cleaned and 1 <= len(cleaned.split()) <= 12:
                    info.append(cleaned)

            return info or [f"Sorry, no {mode} info found for {city}."]
        else:
            return [f"Sorry, no {mode} info found for {city}."]
    except Exception as e:
        return [f"Error fetching {mode} info for {city}. {str(e)}"]

# === Translator Mode ===
def translator_mode():
    say("Would you like to speak or type your sentence? Type voice or type.", "en")
    input_mode = input("Enter mode (voice/type): ").strip().lower()

    if input_mode == "voice":
        say("Choose your speaking language: English, Hindi or Bengali.", "en")
        lang_input = input("Enter language: ").strip().lower()
        if lang_input in lang_map:
            input_lang_code = lang_map[lang_input]
            spoken_lang = speech_lang_map[input_lang_code]
        else:
            say("Invalid input language, using English.", "en")
            input_lang_code = "en"
            spoken_lang = "en-US"

        user_text = listen(spoken_lang)
        if not user_text:
            say("Sorry, I couldn't understand what you said.", "en")
            return
    else:
        user_text = input("Please type your sentence: ")

    print(f"Input: {user_text}")
    say("Which language do you want to translate it to? Hindi, English or Bengali?", "en")
    target_lang = input("Translate to: ").strip().lower()

    if target_lang in lang_map:
        target_code = lang_map[target_lang]
    else:
        say("Invalid target language. Exiting.", "en")
        return

    translated = translate_text(user_text, target_code)
    print(f"Translated: {translated}")
    say(translated, target_code)

# === Tour Guide Mode (Speak intro + speak names one by one, print cleaned list) ===
def tour_guide_mode():
    say("Which city or place are you visiting?", "en")
    city = listen("en-US") or input("Enter city name: ")

    say("Would you like to know must-visit places or famous restaurants?", "en")
    choice = input("Enter 'places' or 'restaurants': ").strip().lower()

    if "restaurant" in choice:
        mode = "restaurants"
        prompt_type = "popular restaurants"
    elif "place" in choice:
        mode = "places"
        prompt_type = "must-visit places"
    else:
        say("Invalid choice. Please choose either places or restaurants next time.", "en")
        return

    # Get cleaned list of names from Gemini
    data = get_city_recommendations(city, mode=mode)

    # Print cleaned list in terminal (as before)
    print(f"\n{prompt_type.capitalize()} in {city}:")
    for i, item in enumerate(data, 1):
        print(f"{i}. {item}")

    # Speak intro line
    say(f"Here are some {prompt_type} in {city}:", "en")
    # Speak each place/restaurant name with numbering
    for i, item in enumerate(data, 1):
        say(f"{i}. {item}", "en")

# === Main Menu ===
def main():
    say("Welcome! Type 'tour' for tour guide or 'translate' for translation.", "en")
    choice = input("Enter your choice (tour/translate): ").strip().lower()

    if "tour" in choice:
        tour_guide_mode()
    elif "translate" in choice:
        translator_mode()
    else:
        say("Sorry, I didn't understand that.", "en")

if __name__ == "__main__":
    main()
