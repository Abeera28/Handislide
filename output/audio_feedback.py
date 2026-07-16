"""
HandiSlide - Audio Feedback Module
Plays sound effects for gesture confirmation and zone changes.
Uses winsound on Windows — no extra dependencies needed.
"""

import os
import platform
import threading

class AudioFeedback:
    def __init__(self, assets_path=None):
        """
        Initialize audio feedback system.
        
        Args:
            assets_path: Path to the assets folder containing sound files
        """
        if assets_path is None:
            assets_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                'assets'
            )
        
        self.assets_path = assets_path
        self.enabled = True
        
        # Sound file paths
        self.click_sound = os.path.join(assets_path, 'click.wav')
        self.activate_sound = os.path.join(assets_path, 'activate.wav')
        
        # Check if we're on Windows (winsound is built-in)
        self.is_windows = platform.system() == 'Windows'
    
    def _play_file(self, filepath):
        """Play a sound file in a non-blocking way."""
        if not self.enabled:
            return
        
        if not os.path.exists(filepath):
            print(f"[Audio] Sound file not found: {filepath}")
            return
        
        def play():
            try:
                if self.is_windows:
                    import winsound
                    winsound.PlaySound(
                        filepath, 
                        winsound.SND_ASYNC | winsound.SND_FILENAME
                    )
                else:
                    # For Mac/Linux: silently skip (audio is optional)
                    pass
            except Exception as e:
                # Audio is optional, don't crash if it fails
                print(f"[Audio] Playback error: {e}")
        
        # Play in separate thread to avoid blocking
        thread = threading.Thread(target=play, daemon=True)
        thread.start()
    
    def play_gesture_success(self):
        """Play click sound when a gesture is successfully recognized."""
        self._play_file(self.click_sound)
    
    def play_zone_enter(self):
        """Play sound when entering active zone."""
        self._play_file(self.activate_sound)
    
    def play_zone_exit(self):
        """Play sound when leaving active zone."""
        pass  # Optional: can add a different sound later
    
    def enable(self):
        """Enable audio feedback."""
        self.enabled = True
    
    def disable(self):
        """Disable audio feedback."""
        self.enabled = False
    
    def is_enabled(self):
        """Check if audio is enabled."""
        return self.enabled