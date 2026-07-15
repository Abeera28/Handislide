"""
HandiSlide - Gesture Buffer
Provides debouncing and smoothing for gesture detection.
Prevents single-frame false positives by requiring gestures
to be held for a minimum number of consecutive frames.
"""

import time

class GestureBuffer:
    def __init__(self):
        """
        Initialize gesture buffer with debounce settings.
        """
        # Required consecutive frames for each gesture type
        self.required_frames = {
            "swipe_right": 5,
            "swipe_left": 5,
            "fist": 30,           # ~1 second at 30fps
            "open_palm_hold": 60,  # ~2 seconds at 30fps
            "thumbs_up": 10,       # ~0.3 seconds
            "thumbs_down": 10,
            "two_fingers": 15,     # ~0.5 seconds
            "three_fingers": 15,   # ~0.5 seconds
            "index_point_move": 1, # No debounce for drawing
        }
        
        # Cooldown between gestures to prevent rapid repeats
        self.gesture_cooldown = {
            "swipe_right": 0.3,
            "swipe_left": 0.3,
            "fist": 1.0,
            "open_palm_hold": 1.0,
            "thumbs_up": 1.0,
            "thumbs_down": 1.0,
            "two_fingers": 0.5,
            "three_fingers": 0.5,
            "index_point_move": 0.0,
        }
        
        # Current tracking state
        self.current_gesture = None
        self.consecutive_frames = 0
        self.last_confirmed_time = {}
        
        # For toggle gestures (two_fingers, three_fingers)
        # We only want to fire once per activation
        self.toggle_fired = {
            "two_fingers": False,
            "three_fingers": False,
            "fist": False,
            "open_palm_hold": False,
            "thumbs_up": False,
            "thumbs_down": False,
        }
    
    def process(self, gesture_name, fps=30):
        """
        Process a raw gesture detection and apply debouncing.
        
        Args:
            gesture_name: Raw gesture string from GestureClassifier
            fps: Current frames per second (for time-based calculations)
            
        Returns:
            Confirmed gesture name, or None if not confirmed yet
        """
        now = time.time()
        
        # If no gesture detected, reset everything
        if gesture_name is None:
            self.current_gesture = None
            self.consecutive_frames = 0
            # Reset toggle fired flags when hand returns to neutral
            for key in self.toggle_fired:
                self.toggle_fired[key] = False
            return None
        
        # Check cooldown
        if gesture_name in self.last_confirmed_time:
            elapsed = now - self.last_confirmed_time[gesture_name]
            cooldown = self.gesture_cooldown.get(gesture_name, 0.3)
            if elapsed < cooldown:
                return None
        
        # Check if gesture changed
        if gesture_name != self.current_gesture:
            self.current_gesture = gesture_name
            self.consecutive_frames = 1
            return None
        
        # Same gesture as previous frame
        self.consecutive_frames += 1
        
        # Calculate required frames based on FPS
        required = self.required_frames.get(gesture_name, 10)
        
        # Check if gesture has been held long enough
        if self.consecutive_frames >= required:
            # For toggle gestures, only fire once per activation
            if gesture_name in self.toggle_fired:
                if self.toggle_fired[gesture_name]:
                    return None
                self.toggle_fired[gesture_name] = True
            
            self.last_confirmed_time[gesture_name] = now
            return gesture_name
        
        return None
    
    def reset(self):
        """Reset all buffer state."""
        self.current_gesture = None
        self.consecutive_frames = 0
        self.last_confirmed_time = {}
        for key in self.toggle_fired:
            self.toggle_fired[key] = False