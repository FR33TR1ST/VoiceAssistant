import whisper

model = whisper.load_model("base")
result = model.transcribe("recording.wav")
print(result["text"])
