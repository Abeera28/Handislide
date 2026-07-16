"""
HandiSlide - Keystroke Emulator
Sends OS-level keyboard events using PyAutoGUI.
Universal fallback that works with any presentation software.
"""

import pyautogui
import time

# Safety: PyAutoGUI has a fail-safe - moving mouse to corner raises exception
pyautogui.FAILSAFE = False

class KeystrokeEmulator:
    def __init__(self, press_duration=0.05):
        """
        Initialize keystroke emulator.
        
        Args:
            press_duration: How long to hold each key press (seconds)
        """
        self.press_duration = press_duration
        self.enabled = True
    
    def next_slide(self):
        """Advance to next slide (Right Arrow)."""
        if self.enabled:
            pyautogui.press('right')
    
    def previous_slide(self):
        """Go to previous slide (Left Arrow)."""
        if self.enabled:
            pyautogui.press('left')
    
    def blackout(self):
        """Toggle black screen (B key in PowerPoint)."""
        if self.enabled:
            pyautogui.press('b')
    
    def whiteout(self):
        """Toggle white screen (W key in PowerPoint)."""
        if self.enabled:
            pyautogui.press('w')
    
    def start_slideshow(self):
        """Start slideshow from beginning (F5)."""
        if self.enabled:
            pyautogui.press('f5')
    
    def end_slideshow(self):
        """End slideshow (Escape)."""
        if self.enabled:
            pyautogui.press('escape')
    
    def goto_slide(self, slide_number):
        """
        Jump to a specific slide number.
        Types the number and presses Enter.
        """
        if self.enabled and 1 <= slide_number <= 999:
            pyautogui.typewrite(str(slide_number), interval=0.05)
            time.sleep(0.1)
            pyautogui.press('enter')
    
    def press_key(self, key):
        """Press any key."""
        if self.enabled:
            pyautogui.press(key)
    
    def enable(self):
        """Enable keystroke output."""
        self.enabled = True
    
    def disable(self):
        """Disable keystroke output (for safety)."""
        self.enabled = False
    
    def is_enabled(self):
        """Check if keystroke output is enabled."""
        return self.enabled