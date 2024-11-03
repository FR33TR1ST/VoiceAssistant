import datetime
import pyaudio
import pyjokes
import pyttsx3
import pywhatkit
import re
import torch
import wave
import webbrowser
import whisper
import wikipedia
import platform
import speech_recognition as sr
import yfinance as yf
from translate import Translator
from wikipedia import wikipedia
from youtubesearchpython import VideosSearch
from managers import InputManager, VolumeManager

OS = platform.system()
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
MODEL = whisper.load_model("medium.en", device=DEVICE)


def transform():
    # speaking('Talk')
    r = sr.Recognizer()
    with sr.Microphone() as source:
        r.pause_threshold = 0.5
        said = r.listen(source)
        try:
            q = r.recognize_google(said, language="en")
            return q
        except sr.UnknownValueError:
            print('Sorry I did not understand')
            return "I am waiting"
        except sr.RequestError:
            print('Sorry the service is down')
            return "I am waiting"
        except:
            return "I am waiting"


def speaking(message):
    engine = pyttsx3.init()
    engine.say(message)
    engine.runAndWait()


def whisper_ai(model):
    result = model.transcribe("voice.wav")
    return result['text']


def query_day():
    day = datetime.date.today()
    weekday = day.weekday()
    mapping = {
        0:'Monday',1:'Tuesday',2:'Wednesday',3:'Thursday',4:'Friday',5:'Saturday',6:'Sunday'
    }
    try:
        speaking(f'Today is {mapping[weekday]}')
    except Exception as e:
        pass


def query_time():
    time = datetime.datetime.now().strftime("%H:%M:%S")
    speaking(f"It is {time[0:2]} o'clock and {time[3:5]} minutes")


def startup():
    speaking("""Hi, my name is James; I'm a Virtual Assistant. How can I help you""")


def record_audio():
    chunk = 1024
    format = pyaudio.paInt16
    channels = 1
    rate = 44100
    record_seconds = 8
    wave_output_filename = "voice.wav"

    p = pyaudio.PyAudio()

    stream = p.open(format=format,
                    channels=channels,
                    rate=rate,
                    input=True,
                    frames_per_buffer=chunk)

    print("* recording")

    frames = []

    for i in range(0, int(rate / chunk * record_seconds)):
        data = stream.read(chunk)
        frames.append(data)

    print("* done recording")

    stream.stop_stream()
    stream.close()
    p.terminate()

    wf = wave.open(wave_output_filename, 'wb')
    wf.setnchannels(channels)
    wf.setsampwidth(p.get_sample_size(format))
    wf.setframerate(rate)
    wf.writeframes(b''.join(frames))
    wf.close()


def querying():
    input_manager = InputManager()
    volume_manager = VolumeManager(OS)
    start = True
    startup()

    while start:
        print('Listening...')
        s = transform().lower()

        if "james" in s:
            record_audio()
            user_input = whisper_ai(MODEL).lower()
            print(user_input)
            df = input_manager.split_and_categorize(user_input)

            if "shut down" in user_input or 'shutdown' in user_input:
                    speaking("ok I am shuting down")
                    break
            
            df = input_manager.split_and_categorize(user_input)

            # Loop through each row in the DataFrame
            for _, row in df.iterrows():
                category = row['Predicted Intent']
                sentence = row['sentences']
                keywords = sentence.split()
                #TODO: Make a Python 3.10 Version with Switch Statement and keep this one as 3.9/Legacy
                if category == "Initialize":
                    if "google" in keywords:
                        speaking("Starting google. Just a second")
                        webbrowser.open("https://www.google.com")
                        continue
                    elif "youtube" in keywords:
                        speaking("Starting youtube. Just a second")
                        webbrowser.open("https://www.youtube.com")
                        continue
                    elif "amazon" in keywords:
                        speaking("Starting amazon. Just a second")
                        webbrowser.open("https://www.amazon.com")
                        continue
                    elif "wikipedia" in keywords:
                        speaking("Starting wikipedia. Just a second")
                        webbrowser.open("https://www.wikipedia.org")
                        continue

                elif category == "YouTubeVideos" or category == "PlayMusic":
                    if "start" in keywords and "youtube" in keywords:
                        speaking("Starting youtube. Just a second")
                        webbrowser.open("https://www.youtube.com")
                        continue

                    elif "play" in keywords or "watch" in keywords:
                        search = ""
                        try:
                            search = " ".join(keywords[keywords.index("play") + 1:])
                        except:
                            search = " ".join(keywords[keywords.index("watch") + 1:])
                        video_search = VideosSearch(search, limit=1)
                        video_search = VideosSearch.result()
                        video_link = video_search['result'][0]['link']
                        video_name = video_search['result'][0]['title']
                        print(f'Playing {video_name}')
                        webbrowser.open(video_link)
                        continue

                elif category == "InternetSearch":
                    if "wikipedia" in keywords:
                        speaking("checking wikipedia")
                        q = " ".join(keywords[keywords.index("wikipedia") + 1:])
                        result = wikipedia.summary(q, sentences=2)
                        speaking("found on wikipedia")
                        speaking(result)
                        continue

                    elif "google" in keywords:
                        speaking("checking on google")
                        q = " ".join(keywords[keywords.index("google") + 1:])
                        result = pywhatkit.search(q)
                        speaking("this is what i found")
                        speaking(result)
                        continue

                    elif "search" in keywords:
                        speaking("checking on google")
                        q = " ".join(keywords[keywords.index("search") + 1:])
                        result = pywhatkit.search(q)
                        speaking("this is what i found")
                        speaking(result)
                        continue

                    else:
                        speaking("checking on google")
                        result = pywhatkit.search(sentence)
                        speaking("this is what i found")
                        speaking(result)
                        continue

                elif category == "Time":
                    if "day" in keywords:
                        query_day()
                        continue

                    elif "time" in keywords:
                        query_time()
                        continue

                    elif "reminder" in keywords:
                        speaking("Sorry, I cannot set reminders at the moment")
                        continue


                elif category == "Translate":
                    translator = Translator(to_lang='es')
                    try:
                        translation = translator.translate(user_input[keywords.index("translate") + 1:])
                        speaking(f"Here is the translation: {translation}")
                    except Exception as e:
                        speaking(f"An error occurred during translation: {e}")
                    continue

                elif category == "StockMarketQuery":
                    # Predefined stock lookup dictionary
                    lookup = {
                        "Apple": "AAPL",
                        "Amazon": "AMZN",
                        "Google": "GOOGL",
                    }
                    for company, symbol in lookup.items():
                        try:
                            stock = yf.Ticker(symbol)
                            current_price = stock.info.get("regularMarketPrice", "unavailable")

                            if current_price != "unavailable":
                                speaking(f"The current price for {company} is {current_price}.")
                            else:
                                speaking(f"Price data for {company} is currently unavailable.")
                        except Exception as e:
                            speaking(f"Sorry, I couldn't retrieve data for {company}.")

                elif category == "Joke":
                    speaking(pyjokes.get_joke())
                    continue

                elif category == "Maps":
                    speaking("Sorry, I cannot provide directions at the moment")
                    continue

                elif category == "SetVolume":
                    string = re.search(r'-?\d+\.?\d*', user_input)
                    if string:
                        number_str = string.group()
                        number = float(number_str) if '.' in number_str else int(number_str)
                        speaking(volume_manager.increase(number))
                    else:
                        speaking(volume_manager.increase(10))
                    continue

                elif category == "IncreaseVolume":
                    string = re.search(r'-?\d+\.?\d*', user_input)
                    if string:
                        number_str = string.group()
                        number = float(number_str) if '.' in number_str else int(number_str)
                        speaking(volume_manager.increase(number))
                    else:
                        speaking(volume_manager.increase(10))
                    continue

                elif category == "DecreaseVolume":
                    string = re.search(r'-?\d+\.?\d*', user_input)
                    if string:
                        number_str = string.group()
                        number = float(number_str) if '.' in number_str else int(number_str)
                        speaking(volume_manager.decrease(number))
                    else:
                        speaking(volume_manager.decrease(10))
                    continue

                elif category == "MuteVolume":
                    if volume_manager.is_muted():
                        volume_manager.mute()
                        speaking("Volume muted")
                    else:
                        speaking("Volume is already muted")
                    continue

            else:
                speaking("I am not sure what you are asking. Can you repeat?")
                continue


querying()
