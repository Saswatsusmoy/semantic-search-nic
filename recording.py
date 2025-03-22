import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write
import threading
from transcription import transcribe_audio_file

sample_rate = 16000
channels = 1
recording = False
frames = []
recording_thread = None

def _record_loop():
    global recording, frames
    while recording:
        data = sd.rec(int(0.5 * sample_rate), samplerate=sample_rate, channels=channels)
        sd.wait()
        frames.append(data)

def start_recording():
    global recording, frames, recording_thread
    if not recording:
        print("Recording started.")
        recording = True
        frames = []
        recording_thread = threading.Thread(target=_record_loop)
        recording_thread.start()

def stop_recording(filename="Data Processing/output.wav"):
    global recording, frames, recording_thread
    if recording:
        recording = False
        recording_thread.join()
        audio = np.concatenate(frames, axis=0)
        write(filename, sample_rate, audio)
        print(f"Recording stopped. Saved to {filename}")
        transcript = transcribe_audio_file(filename)
        print(transcript)
        return transcript

# start_recording()
# input("Press Enter to stop recording")
# stop_recording()