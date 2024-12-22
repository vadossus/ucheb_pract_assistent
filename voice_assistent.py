import os
import speech_recognition as sr
import vosk
import sys
import queue
import sounddevice as sd
import pyttsx3
import random
import json
import pyaudio
import wave

q = queue.Queue()
recognizer = sr.Recognizer()

model_folder = r""

devices = sd.query_devices()
for i, device in enumerate(devices):
    print(f"Device {i}: {device['name']}")
    print(f"  Max input channels: {device['max_input_channels']}")
    print(f"  Max output channels: {device['max_output_channels']}")
    print(f"  Default sample rate: {device['default_samplerate']}")
    print()

model_path_ru = os.path.join(model_folder, "vosk-model-small-ru-0.22")
model_path_en = os.path.join(model_folder, "vosk-model-small-en-us-0.15")

if not os.path.exists(model_path_ru) or not os.path.exists(model_path_en):
    print("Одна из моделей не найдена. Пожалуйста, убедитесь, что пути указаны правильно.")
    sys.exit(1)

models = {"ru": vosk.Model(model_path_ru), "en": vosk.Model(model_path_en)}

current_language = "ru"
model = models[current_language]

microphone_index = 7
print(f"Используется микрофон с индексом: {microphone_index}")


def callback(indata, frames, time, status):
    q.put(bytes(indata))


def recognize_speech():
    try:
        with sd.RawInputStream(samplerate=44100, blocksize=8000, dtype="int16", channels=1, callback=callback, device=microphone_index):
            rec = vosk.KaldiRecognizer(model, 44100)
            while True:
                data = q.get()
                if rec.AcceptWaveform(data):
                    result = rec.Result()
                    result_json = json.loads(result)
                    return result_json["text"]
                else:
                    rec.PartialResult()
    except sd.PortAudioError as e:
        print(f"Ошибка PortAudio: {e}")
        sys.exit(1)


def speak(text, lang="ru"):
    engine = pyttsx3.init()
    voices = engine.getProperty("voices")

    if lang == "ru":
        for voice in voices:
            if "russian" in voice.languages:
                engine.setProperty("voice", voice.id)
                break
    else:
        engine.setProperty("voice", voices[0].id)

    file_path = "output.wav"
    engine.save_to_file(text, file_path)
    engine.runAndWait()

    if not os.path.exists(file_path) or os.path.getsize(file_path) <= 46:
        print("Ошибка при создании аудиофайла.")
        return

    play_audio(file_path)


def play_audio(file_path):
    try:
        if not os.path.exists(file_path):
            print(f"Файл {file_path} не найден.")
            return

        wf = wave.open(file_path, "rb")

        p = pyaudio.PyAudio()

        stream = p.open(
            format=p.get_format_from_width(wf.getsampwidth()),
            channels=wf.getnchannels(),
            rate=wf.getframerate(),
            output=True,
        )

        data = wf.readframes(1024)
        while data:
            stream.write(data)
            data = wf.readframes(1024)

        stream.stop_stream()
        stream.close()
        p.terminate()
        wf.close()
    except Exception as e:
        print(f"Ошибка воспроизведения аудио: {e}")


def greet():
    if current_language == "ru":
        speak("Привет! Как я могу помочь?", "ru")
    else:
        speak("Hello! How can I help?", "en")


def farewell():
    if current_language == "ru":
        speak("До свидания!", "ru")
    else:
        speak("Goodbye!", "en")
    sys.exit()


def main():
    global current_language, model
    greet()
    while True:
        user_input = recognize_speech()
        if user_input.strip():
            print(f"Вы сказали: {user_input}" if current_language == "ru" else f"You said: {user_input}")
            speak(f"Вы сказали: {user_input}" if current_language == "ru" else f"You said: {user_input}", current_language)

            if ("подбрось монетку" in user_input.lower() and current_language == "ru") or (
                "flip a coin" in user_input.lower() and current_language == "en"
            ):
                print("Команда 'подбрось монетку' распознана" if current_language == "ru" else "Command 'flip a coin' recognized")
                result = random.choice(["Орел", "Решка"] if current_language == "ru" else ["Heads", "Tails"])
                print(f"Выпало: {result}" if current_language == "ru" else f"It landed on: {result}")
                speak(f"Выпало: {result}" if current_language == "ru" else f"It landed on: {result}", current_language)

            elif ("пока" in user_input.lower() and current_language == "ru") or (
                "goodbye" in user_input.lower() and current_language == "en"
            ):
                farewell()

            elif ("смени язык" in user_input.lower() and current_language == "ru") or (
                "change language" in user_input.lower() and current_language == "en"
            ):
                new_lang = input("Введите новый язык (ru/en): " if current_language == "ru" else "Enter new language (ru/en): ")
                if new_lang in models:
                    current_language = new_lang
                    model = models[current_language]
                    speak(
                        "Язык изменен на русский" if current_language == "ru" else "Language changed to English",
                        current_language,
                    )
                else:
                    speak("Неверный выбор языка" if current_language == "ru" else "Invalid language choice", current_language)

            else:
                speak("Извините, я не понял вас." if current_language == "ru" else "Sorry, I didn't understand.", current_language)
        else:
            print("Нет речи, ничего не сказано." if current_language == "ru" else "No speech detected.")


if __name__ == "__main__":
    main()

