import os
import speech_recognition as sr
from gtts import gTTS
from playsound import playsound
from uuid import uuid4

def speak(text):
    print(f"Emma says: {text}")
        tts = gTTS(text=text, lang="en")
            filename = f"/tmp/voice_{uuid4().hex}.mp3"
                tts.save(filename)
                    playsound(filename)
                        os.remove(filename)

                        def listen():
                            r = sr.Recognizer()
                                with sr.Microphone() as source:
                                        print("Listening...")
                                                audio = r.listen(source)
                                                        try:
                                                                    return r.recognize_google(audio)
                                                                            except sr.UnknownValueError:
                                                                                        return "Sorry, I didn't catch that."
                                                                                                except sr.RequestError:
                                                                                                            return "Speech recognition service is down."