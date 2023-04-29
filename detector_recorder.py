import pyaudio
import wave
import numpy as np

# set up the audio input stream
chunk_size = 1024
sample_rate = 44100
pa = pyaudio.PyAudio()
stream = pa.open(format=pyaudio.paInt16, channels=1, rate=sample_rate, input=True, frames_per_buffer=chunk_size)

# set up recording parameters
threshold = 0.001  # adjust this to set the sensitivity of the recording
max_silence = 2.0  # adjust this to set the maximum silence in seconds

# start recording
recording = False
silence = 0.0
frames = []
wf = None
running = True
while running :
    # read a chunk of audio data from the stream
    data = np.fromstring(stream.read(chunk_size), dtype=np.int16)

    # check if the volume is above the threshold
    volume = np.max(np.abs(data)) / 32767.0
    if volume > threshold:
        # start or continue recording
        if not recording:
            print("Recording started.")
            recording = True
            wf = wave.open("recording.wav", "wb")
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
        frames.append(data)
        silence = 0.0
    else:
        # stop recording if there is enough silence
        if recording:
            silence += chunk_size / float(sample_rate)
            if silence > max_silence:
                print("Recording stopped.")
                recording = False
                wf.writeframes(b''.join(frames))
                wf.close()
                frames = []
                silence = 0.0
                running = False

    # write the recorded audio frames to the WAV file
    if len(frames) > 0:
        wf.writeframes(b''.join(frames))
        frames = []

# clean up the audio input stream
stream.stop_stream()
stream.close()
pa.terminate()
