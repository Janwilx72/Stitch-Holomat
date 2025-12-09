import pygame
import sys
import numpy as np
import sounddevice as sd
from scipy.fftpack import fft

# Initialize pygame
pygame.init()

# Screen dimensions
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)

# Guitar string names and their standard frequencies (in Hz)
strings = [
    {"name": "E (6th)", "frequency": 82.41},
    {"name": "A (5th)", "frequency": 110.00},
    {"name": "D (4th)", "frequency": 146.83},
    {"name": "G (3rd)", "frequency": 196.00},
    {"name": "B (2nd)", "frequency": 246.94},
    {"name": "E (1st)", "frequency": 329.63},
]

# Create screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Guitar Tuning Application")

# Font
font = pygame.font.SysFont("Arial", 24)
large_font = pygame.font.SysFont("Arial", 36)

# Minimum volume threshold to filter out noise
VOLUME_THRESHOLD = 0.001

# Function to draw guitar strings
def draw_strings(selected_string=None, frequency=None):
    for i, string in enumerate(strings):
        y_pos = 100 + i * 80

        if selected_string == i and frequency:
            diff = abs(string["frequency"] - frequency)
            if diff < 1.0:  # Tuning is correct
                color = GREEN
            elif diff < 5.0:  # Tuning is close
                color = YELLOW
            else:  # Tuning is off
                color = RED
        else:
            color = BLACK

        text = font.render(string["name"], True, color)
        pygame.draw.line(screen, GRAY, (100, y_pos), (700, y_pos), 4)
        screen.blit(text, (50, y_pos - 15))

        if selected_string == i and frequency:
            freq_text = large_font.render(f"Freq: {frequency:.2f} Hz", True, color)
            screen.blit(freq_text, (300, y_pos - 25))

# Function to calculate the dominant frequency from audio data
def get_frequency(data, samplerate):
    # Apply FFT
    fft_data = fft(data)
    magnitude = np.abs(fft_data[:len(fft_data)//2])
    freqs = np.fft.fftfreq(len(data), 1/samplerate)[:len(fft_data)//2]

    # Find peak frequency
    peak_idx = np.argmax(magnitude)
    return freqs[peak_idx]

# Function to match frequency to the closest string
def match_string(frequency):
    closest_string = None
    closest_diff = float('inf')

    for i, string in enumerate(strings):
        diff = abs(string["frequency"] - frequency)
        if diff < closest_diff:
            closest_diff = diff
            closest_string = i

    return closest_string

# Audio stream callback
def audio_callback(indata, frames, time, status):
    global detected_frequency, selected_string

    if status:
        print(status)

    # Get mono audio data
    mono_data = np.mean(indata, axis=1)

    # Calculate volume
    volume = np.linalg.norm(mono_data) / len(mono_data)
    print(f"Volume: {volume}")  # Debug: Print volume

    if volume > VOLUME_THRESHOLD:  # Only process if volume is above threshold
        detected_frequency = get_frequency(mono_data, samplerate)
        selected_string = match_string(detected_frequency)
        print(f"Detected Frequency: {detected_frequency}")  # Debug: Print frequency
        print(f"Selected String: {selected_string}")  # Debug: Print selected string
    else:
        detected_frequency = None
        selected_string = None

# Initialize audio stream
detected_frequency = None
selected_string = None
samplerate = 44100
stream = sd.InputStream(callback=audio_callback, channels=1, samplerate=samplerate)
stream.start()

# Main loop
running = True
while running:
    screen.fill(WHITE)

    # Draw guitar strings
    draw_strings(selected_string, detected_frequency)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    pygame.display.flip()

# Stop audio stream and quit pygame
stream.stop()
stream.close()
pygame.quit()
sys.exit()
