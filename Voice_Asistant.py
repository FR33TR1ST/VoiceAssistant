import pyttsx3
import speech_recognition as sr
import pyaudio
import webbrowser
import datetime
import pywhatkit
import os
import yfinance as yf
import pyjokes
from youtubesearchpython import VideosSearch
import pyaudio
import wave
import whisper
import gradio as gr
import time
import warnings
import torch
device = "cuda" if torch.cuda.is_available() else "cpu"
model = whisper.load_model("medium.en", device=device)

def transform():
    #speaking('Talk')
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
    except:
        pass
        
def query_time():
    time = datetime.datetime.now().strftime("%H:%M:%S")
    speaking(f"It is {time[0:2]} o'clock and {time[3:5]} minutes")
    
def startup():
    speaking("""Hi, my name is James; I'm a Virtual Assistant. How can I help you""")
    
def Record_audio():
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100
    RECORD_SECONDS = 8
    WAVE_OUTPUT_FILENAME = "voice.wav"

    p = pyaudio.PyAudio()

    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)

    print("* recording")

    frames = []

    for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
        frames.append(data)

    print("* done recording")

    stream.stop_stream()
    stream.close()
    p.terminate()

    wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()
    
def querying():
    startup()
    start = True
    while(start):
        s = transform().lower()
        if "james"in s:
            Record_audio()
            q = whisper_ai(model).lower()
            print(q)
            #TODO: Make a Python 3.10 Version with Switch Statement and keep this one as 3.9/Legacy
            if "start youtube" in q:
                speaking("Starting youtube. Just a second")
                webbrowser.open("https://www.youtube.com")
                continue

            elif "start webbrowser" in q:
                speaking("opening browser")
                webbrowser.open("https://www.google.com")
                continue

            elif "what day is it" in q:
                query_day()
                continue

            elif "what time is it" in q:
                query_time()
                continue

            elif "shut down" in q or 'shutdown' in q:
                speaking("ok I am shuting down")
                break

            elif "from wikipedia" in q:
                speaking("checking wikipedia")
                q = q.replace("wikipedia", "")
                result = wikipedia.summary(q,sentences=2)
                speaking("found on wikipedia")
                speaking(result)
                continue

            elif "your name" in q:
                speaking("I am David. Your Voice Asistant")
                continue

            elif "search web" in q:
                q = q.replace("search web","")
                pywhatkit.search(q)
                speaking("this is what i found")
                continue

            elif "play" in q:
                q = q.replace("play","")
                speaking(f"playing {q}")
                pywhatkit.playonyt(q)
                continue

            elif "joke" in q:
                speaking(pyjokes.get_joke())
                continue

            elif "stock price" in q:
                search = q.split("of")[-1].strip()
                lookup = {"apple":"AAPL",
                         "amazon":"AMZN",
                         "google":"GOOGL"}
                try:
                    stock = lookup[search]
                    stock = yf.Ticker(stock)
                    currentprice = stock.info["regularMarketPrice"]
                    speaking(f"found it, the price for {search} is {currentprice}")
                    continue
                except:
                    speaking(f"sorry I have no data for {search}")
                continue
            elif 'play on youtube' in q:
                search = q.split('youtube')[-1].strip()
                videoSearch = VideosSearch(search, limit=1)
                videoSearch = VideosSearch.result()
                video_link = videosSearch['result'][0]['link']
                video_name = videosSearch['result'][0]['title']
                print(f'Playing {video_name}')
                webbrowser.open(video_link)
                continue
                #TODO: Default Case that resets the process and says "I'm sorry, I didn't quite understand - please use one of my Listed Functions
querying()
