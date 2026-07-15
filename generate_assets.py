"""
Generate asset files for HandiSlide.
Run this ONCE: python generate_assets.py
"""

import os
import wave
import struct
import math
from PIL import Image, ImageDraw

# Create assets folder
if not os.path.exists("assets"):
    os.makedirs("assets")
    print("Created 'assets' folder")

def generate_click_sound(filename, duration=0.05, frequency=800, volume=0.5):
    """Generate a short click sound."""
    sample_rate = 44100
    num_samples = int(sample_rate * duration)
    
    with wave.open(filename, 'w') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        
        for i in range(num_samples):
            envelope = 1.0 - (i / num_samples)
            value = volume * envelope * math.sin(2 * math.pi * frequency * i / sample_rate)
            value += volume * envelope * 0.3 * math.sin(2 * math.pi * 2000 * i / sample_rate)
            value = max(-1.0, min(1.0, value))
            packed_value = struct.pack('<h', int(value * 32767))
            wav_file.writeframes(packed_value)

def generate_icon():
    """Create a simple icon."""
    img = Image.new('RGBA', (256, 256), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Blue circle background
    draw.ellipse([20, 20, 236, 236], fill=(0, 120, 212, 255))
    
    # White hand shape
    draw.rounded_rectangle([90, 100, 166, 210], radius=20, fill=(255, 255, 255, 255))
    
    for x_offset in [-25, -8, 9, 26]:
        draw.rounded_rectangle([128+x_offset-8, 45, 128+x_offset+8, 115], 
                               radius=8, fill=(255, 255, 255, 255))
    
    draw.rounded_rectangle([55, 120, 85, 165], radius=10, fill=(255, 255, 255, 255))
    
    img.save("assets/icon.ico", format="ICO", 
             sizes=[(256, 256), (64, 64), (32, 32), (16, 16)])

# Generate everything
print("Generating click.wav...")
generate_click_sound("assets/click.wav")
print("  ✅ Done!")

print("Generating activate.wav...")
generate_click_sound("assets/activate.wav", duration=0.08, frequency=600)
print("  ✅ Done!")

print("Generating icon.ico...")
generate_icon()
print("  ✅ Done!")

print("\n✅ All assets generated successfully!")