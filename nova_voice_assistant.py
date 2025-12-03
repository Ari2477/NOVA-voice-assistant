import os
import re
import webbrowser
from datetime import datetime
from pathlib import Path

import speech_recognition as sr
from googletrans import Translator

# --------------------- SETTINGS ---------------------

NAME = "Nova"
WAKE_WORDS = [r"\bhey nova\b", r"\bokay nova\b", r"\bhi nova\b"]

translator = Translator()

# --------------------- UTILITIES ---------------------

def say(text: str):
    """Use espeak (works on Android Termux)."""
    os.system(f'espeak "{text}"')

def clean_text(t: str) -> str:
    return re.sub(r"[^a-z0-9 ?!.,'-]+", " ", t.lower()).strip()

def heard_wake_word(text: str) -> bool:
    for pat in WAKE_WORDS:
        if re.search(pat, text):
            return True
    return False

def extract_after_wake_word(text: str) -> str:
    t = text
    for pat in WAKE_WORDS:
        t = re.sub(pat, " ", t)
    return clean_text(t).strip()

def now_time_str():
    return datetime.now().strftime("%I:%M %p").lstrip("0")

def now_date_str():
    return datetime.now().strftime("%A, %B %d, %Y")

def open_quick_site(cmd: str) -> bool:
    sites = {
        "youtube": "https://www.youtube.com",
        "google": "https://www.google.com",
        "facebook": "https://www.facebook.com",
        "gmail": "https://mail.google.com",
        "spotify": "https://open.spotify.com",
        "tiktok": "https://www.tiktok.com",
        "twitter": "https://x.com",
        "reddit": "https://www.reddit.com",
        "github": "https://github.com",
    }
    for key, url in sites.items():
        if key in cmd:
            webbrowser.open(url)
            say(f"Opening {key}")
            return True
    return False

def do_web_search(query: str):
    webbrowser.open("https://www.google.com/search?q=" + query)
    say("Here is what I found on the web.")

def small_talk(cmd: str) -> bool:
    replies = {
        r"\bwho are you\b": f"I'm {NAME}, your assistant.",
        r"\bwhat('?| i)s your name\b": f"My name is {NAME}.",
        r"\bhow are you\b": "I'm doing great!",
        r"\bthank(s| you)\b": "You're welcome!",
        r"\btell me a joke\b": "Why do programmers hate nature? Too many bugs!",
    }
    for pat, reply in replies.items():
        if re.search(pat, cmd):
            say(reply)
            return True
    return False

# --------------------- MAIN COMMAND HANDLER ---------------------

def handle_command(cmd: str):
    if not cmd:
        return True

    # Exit
    if "stop" in cmd or "goodbye" in cmd or "exit" in cmd:
        say("Goodbye!")
        raise SystemExit

    # Time / date
    if "time" in cmd:
        say(f"The time is {now_time_str()}")
        return True
    if "date" in cmd or "day" in cmd:
        say(f"Today is {now_date_str()}")
        return True

    # open site
    if "open" in cmd and open_quick_site(cmd):
        return True

    # search
    m = re.search(r"(search|look up|google)\s+(.*)", cmd)
    if m:
        do_web_search(m.group(2))
        return True

    # translate
    if "translate" in cmd:
        try:
            text = cmd.split("translate", 1)[1].strip()

            if "to tagalog" in text:
                text = text.replace("to tagalog", "").strip()
                result = translator.translate(text, dest="tl").text
                say(result)
                return True

            if "to english" in text:
                text = text.replace("to english", "").strip()
                result = translator.translate(text, dest="en").text
                say(result)
                return True

            say("Please say translate then the language.")
            return True
        except:
            say("Translation failed.")
            return True

    # small talk
    if small_talk(cmd):
        return True

    # fallback
    say("I didn't understand. Searching it.")
    do_web_search(cmd)
    return True

# --------------------- SPEECH RECOGNITION (Termux API) ---------------------

def listen_and_transcribe():
    """
    Record audio using Termux API and transcribe it.
    """
    audio_file = Path.home() / "nova_record.wav"

    print("Listening... Speak now!")
    os.system(f"termux-microphone-record -r {audio_file} -l 5")

    r = sr.Recognizer()
    with sr.AudioFile(str(audio_file)) as source:
        audio = r.record(source)

    # Delete file after reading
    if audio_file.exists():
        os.remove(audio_file)

    try:
        text = r.recognize_google(audio)
        return clean_text(text)
    except:
        return ""

# --------------------- MAIN LOOP ---------------------

def main():
    say(f"Hello! I'm {NAME}. Say 'Hey Nova' to talk to me.")

    while True:
        utterance = listen_and_transcribe()
        if not utterance:
            continue

        print("Heard:", utterance)

        if not heard_wake_word(utterance):
            continue

        cmd = extract_after_wake_word(utterance)

        if not cmd:
            say("Yes?")
            cmd = listen_and_transcribe()

        print("Command:", cmd)
        handle_command(cmd)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Exiting...")
