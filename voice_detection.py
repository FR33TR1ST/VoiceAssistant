import pyaudio
import numpy as np
import time

RATE = 44100  # Frecuencia de muestreo
CHUNK = 1024  # Tamaño de cada chunk de audio que se lee
THRESHOLD = 0.01  # Umbral de volumen mínimo para detectar voz
MAX_SILENCE_TIME = 2  # Tiempo máximo de silencio antes de detener la grabación (en segundos)
RECORDING_TIME = 5  # Tiempo máximo de grabación (en segundos)

p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16, channels=1, rate=RATE,
                input=True, output=True, frames_per_buffer=CHUNK)

print("Escuchando...")

# Variables de control
started = False
stopped = False
speaking = False
pause_count = 0
silence_count = 0

# Tiempo de inicio del programa
start_time = time.time()

# Variables de grabación
frames = []
recording_start_time = None

while not stopped:
    data = stream.read(CHUNK)
    # Convertir los datos en un array numpy
    data_array = np.frombuffer(data, dtype=np.int16)
    data_array = data_array.astype(float) / 32767.0
    # Calcular el volumen rms (root mean square)
    rms = np.sqrt(np.mean(np.square(data_array)))
    
    # Si el volumen rms es menor que el umbral, se considera que no hay voz
    if rms < THRESHOLD:
        if speaking:
            pause_count += 1
            if pause_count > 1 * RATE / CHUNK:
                print("Dejaste de hablar")
                speaking = False
                pause_count = 0
                silence_count += 1
                if silence_count > MAX_SILENCE_TIME * RATE / CHUNK:
                    print("Demasiado tiempo de silencio. Saliendo...")
                    stopped = True
                    break
        if recording_start_time is not None:
            if time.time() - recording_start_time >= RECORDING_TIME:
                print("Tiempo máximo de grabación alcanzado. Deteniendo grabación...")
                frames = []
                recording_start_time = None
    else:
        if not speaking:
            print("Comenzaste a hablar")
            speaking = True
            silence_count = 0
            if recording_start_time is None:
                print("Iniciando grabación...")
                recording_start_time = time.time()
        pause_count = 0
        if recording_start_time is not None:
            frames.append(data)
            if time.time() - recording_start_time >= RECORDING_TIME:
                print("Tiempo máximo de grabación alcanzado. Deteniendo grabación...")
                stopped = True
        
stream.stop_stream()
stream.close()
p.terminate()

if len(frames) > 0:
    print("Guardando grabación...")
    wf = wave.open("recording.wav", 'wb')
    wf.setnchannels(1)
    wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()
    print("Grabación guardada en recording.wav")    
else:
    print("No se grabó nada.")  
