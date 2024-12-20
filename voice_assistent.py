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

model_path = os.path.join(model_folder, "vosk-model-small-ru-0.22")

if not os.path.exists(model_path):
    print(f"Модель не найдена по пути: {model_path}. Пожалуйста, убедитесь, что путь указан правильно.")
    sys.exit(1)

model = vosk.Model(model_path)

microphone_index = 18
print(f"Используется микрофон с индексом: {microphone_index}")

def callback(indata, frames, time, status):
    q.put(bytes(indata))

def recognize_speech():
    try:
        with sd.RawInputStream(samplerate=48000, blocksize=8000, dtype='int16', channels=1, callback=callback, device=microphone_index):
            rec = vosk.KaldiRecognizer(model, 48000)
            while True:
                data = q.get()
                if rec.AcceptWaveform(data):
                    result = rec.Result()
                    result_json = json.loads(result)
                    return result_json['text']
                else:
                    rec.PartialResult()
    except sd.PortAudioError as e:
        print(f"Ошибка PortAudio: {e}")
        sys.exit(1)

def speak(text, lang='ru'):
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')

    if lang == 'ru':
        for voice in voices:
            if 'russian' in voice.languages:
                engine.setProperty('voice', voice.id)
                break
    else:
        engine.setProperty('voice', voices[0].id)

    file_path = 'output.wav'
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

        wf = wave.open(file_path, 'rb')

        p = pyaudio.PyAudio()

        stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                        channels=wf.getnchannels(),
                        rate=wf.getframerate(),
                        output=True)

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
    speak("Привет! Как я могу помочь?")

def farewell():
    speak("До свидания!")
    sys.exit()

def main():
    greet()
    while True:
        user_input = recognize_speech()
        if user_input.strip(): 
            print("Вы сказали: ", user_input)
            speak(f"Вы сказали: {user_input}")

            if "подбрось монетку" in user_input.lower():
                print("Команда 'подбрось монетку' распознана")
                result = random.choice(["Орел", "Решка"])
                print(f"Выпало: {result}")
                speak(f"Выпало: {result}")

            elif "пока" in user_input.lower():
                farewell()
            elif "смени язык" in user_input.lower():
                new_lang = input("Введите новый язык (ru/en): ")
                if new_lang == 'en':
                    speak("Language changed to English", 'en')
                else:
                    speak("Язык изменен на русский", 'ru')
            else:
                speak("Извините, я не понял вас.")
        else:
            print("Нет речи, ничего не сказано.")

if __name__ == "__main__":
    main()

