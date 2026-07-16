"""
HandiSlide - Configuration Management
Reads and writes user settings from settings.json
"""

import json
import os

class Config:
    def __init__(self, config_path=None):
        """
        Initialize configuration manager.
        
        Args:
            config_path: Path to settings.json. If None, uses default location.
        """
        if config_path is None:
            # Default: settings.json in same directory as this file
            self.config_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                'settings.json'
            )
        else:
            self.config_path = config_path
        
        # Default settings
        self.defaults = {
            "hand_preference": "right",
            "sensitivity": 5,
            "annotation_color": [255, 0, 0],
            "camera_index": 0,
            "swipe_threshold": 100,
            "fist_hold_time": 1.0,
            "palm_hold_time": 2.0,
            "toggle_hold_time": 0.5,
            "zone_enter_time": 0.3,
            "zone_exit_time": 0.5,
            "border_enabled": True,
            "audio_enabled": True,
            "first_run": True
        }
        
        # Load settings
        self.settings = self._load()
    
    def _load(self):
        """Load settings from JSON file. If file doesn't exist, use defaults."""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    loaded = json.load(f)
                # Merge with defaults (in case new settings were added)
                settings = self.defaults.copy()
                settings.update(loaded)
                return settings
            except (json.JSONDecodeError, IOError):
                # If file is corrupted, use defaults
                return self.defaults.copy()
        else:
            # First run: create file with defaults
            settings = self.defaults.copy()
            self._save(settings)
            return settings
    
    def _save(self, settings):
        """Save settings to JSON file."""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(settings, f, indent=4)
        except IOError as e:
            print(f"[Config] Warning: Could not save settings: {e}")
    
    def get(self, key, default=None):
        """Get a setting value."""
        return self.settings.get(key, default)
    
    def set(self, key, value):
        """Set a setting value and save to file."""
        self.settings[key] = value
        self._save(self.settings)
    
    def reset(self):
        """Reset all settings to defaults."""
        self.settings = self.defaults.copy()
        self._save(self.settings)
    
    def reload(self):
        """Reload settings from file."""
        self.settings = self._load()