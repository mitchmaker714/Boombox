import time
import numpy as np
import pyaudio
import requests
import json

# Pixelblaze IP in AP mode
PIXELBLAZE_IP = "192.168.4.1"

# Audio capture settings
CHUNK = 1024
RATE = 44100
BANDS = 12  # Number of frequency bins (matches your 12 columns)
SENSITIVITY = 25.0  # Adjust as needed

# PyAudio stream setup
p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16,
                channels=1,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK)

def get_fft_bands():
    data = stream.read(CHUNK, exception_on_overflow=False)
    samples = np.frombuffer(data, dtype=np.int16)
    fft = np.abs(np.fft.rfft(samples))
    fft = np.log10(fft + 1)
    bands = np.array_split(fft, BANDS)
    band_values = [float(np.mean(b)) * SENSITIVITY for b in bands]
    # Normalize to 0–1
    max_val = max(band_values)
    norm_bands = [min(b / max_val, 1.0) if max_val > 0 else 0.0 for b in band_values]
    return norm_bands

print("Streaming FFT to Pixelblaze...")

try:
    while True:
        bands = get_fft_bands()
        payload = json.dumps({"bands": bands})
        try:
            requests.post(f"http://{PIXELBLAZE_IP}/setvars", data=payload, timeout=0.1)
        except requests.exceptions.RequestException:
            print("Could not reach Pixelblaze...")
        time.sleep(0.02)

except KeyboardInterrupt:
    stream.stop_stream()
    stream.close()
    p.terminate()
    print("Stopped streaming.")
