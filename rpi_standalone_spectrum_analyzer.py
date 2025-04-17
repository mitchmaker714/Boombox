import time
import numpy as np
import pyaudio
from rpi_ws281x import PixelStrip, Color

# Configuration for 5 rows x 12 columns
ROWS = 5
COLS = 12
LED_COUNT = ROWS * COLS

# LED strip configuration:
LED_PIN        = 18
LED_FREQ_HZ    = 800000
LED_DMA        = 10
LED_BRIGHTNESS = 200  # Set lower to reduce power draw
LED_INVERT     = False
LED_CHANNEL    = 0

# Audio settings:
CHUNK = 1024
RATE = 44100
SENSITIVITY = 20.0  # You may tweak this later

# Set up strip
strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA,
                   LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
strip.begin()

# Set up microphone
p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16,
                channels=1,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK)

def pixel_index(col, row):
    """Convert (col, row) to LED index, serpentine layout."""
    if row % 2 == 0:
        return row * COLS + col
    else:
        return row * COLS + (COLS - 1 - col)

def get_color(row, max_row=ROWS - 1):
    """Color gradient bottom (red) to top (green)."""
    ratio = row / max_row
    r = int(255 * (1 - ratio))
    g = int(255 * ratio)
    return Color(r, g, 0)

try:
    print("Running 5x12 Spectrum Analyzer... Ctrl+C to stop.")
    while True:
        data = stream.read(CHUNK, exception_on_overflow=False)
        samples = np.frombuffer(data, dtype=np.int16)
        fft = np.abs(np.fft.rfft(samples))
        fft = np.log10(fft + 1)
        bins = np.array_split(fft, COLS)

        for col, b in enumerate(bins):
            avg = np.mean(b)
            height = int(np.clip(avg * SENSITIVITY, 0, ROWS))

            for row in range(ROWS):
                idx = pixel_index(col, row)
                if row < height:
                    strip.setPixelColor(idx, get_color(row))
                else:
                    strip.setPixelColor(idx, Color(0, 0, 0))

        strip.show()
        time.sleep(0.02)

except KeyboardInterrupt:
    for i in range(LED_COUNT):
        strip.setPixelColor(i, Color(0, 0, 0))
    strip.show()
    stream.stop_stream()
    stream.close()
    p.terminate()
    print("Spectrum analyzer exited.")
