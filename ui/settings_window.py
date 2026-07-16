"""
HandiSlide - Settings Window
Provides a simple UI for configuring user preferences.
"""

import tkinter as tk
from tkinter import ttk

class SettingsWindow:
    def __init__(self, config, on_save_callback=None):
        """
        Initialize settings window.
        
        Args:
            config: Config object for reading/writing settings
            on_save_callback: Function to call when settings are saved
        """
        self.config = config
        self.on_save_callback = on_save_callback
        self.window = None
    
    def open(self):
        """Open the settings window."""
        if self.window is not None and self.window.winfo_exists():
            self.window.lift()
            self.window.focus_force()
            return
        
        self.window = tk.Toplevel()
        self.window.title("HandiSlide Settings")
        self.window.geometry("400x500")
        self.window.resizable(False, False)
        
        # Set icon if available
        try:
            import os
            icon_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                'assets', 'icon.ico'
            )
            if os.path.exists(icon_path):
                self.window.iconbitmap(icon_path)
        except:
            pass
        
        self._build_ui()
    
    def _build_ui(self):
        """Build the settings UI."""
        # Create notebook (tabs)
        notebook = ttk.Notebook(self.window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # === General Tab ===
        general_frame = ttk.Frame(notebook)
        notebook.add(general_frame, text="General")
        
        # Hand preference
        ttk.Label(general_frame, text="Hand Preference:").pack(anchor=tk.W, pady=(10, 0))
        hand_var = tk.StringVar(value=self.config.get("hand_preference", "right"))
        hand_frame = ttk.Frame(general_frame)
        hand_frame.pack(anchor=tk.W, pady=5)
        ttk.Radiobutton(hand_frame, text="Right Hand", variable=hand_var, 
                        value="right").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Radiobutton(hand_frame, text="Left Hand", variable=hand_var, 
                        value="left").pack(side=tk.LEFT)
        
        # Sensitivity
        ttk.Label(general_frame, text="Gesture Sensitivity:").pack(anchor=tk.W, pady=(15, 0))
        sensitivity_var = tk.IntVar(value=self.config.get("sensitivity", 5))
        sensitivity_scale = ttk.Scale(
            general_frame, from_=1, to=10, variable=sensitivity_var,
            orient=tk.HORIZONTAL, length=200
        )
        sensitivity_scale.pack(anchor=tk.W, pady=5)
        ttk.Label(general_frame, text="1 (Low) ← → 10 (High)").pack(anchor=tk.W)
        
        # Swipe threshold
        ttk.Label(general_frame, text="Swipe Distance:").pack(anchor=tk.W, pady=(15, 0))
        swipe_var = tk.IntVar(value=self.config.get("swipe_threshold", 100))
        swipe_scale = ttk.Scale(
            general_frame, from_=50, to=200, variable=swipe_var,
            orient=tk.HORIZONTAL, length=200
        )
        swipe_scale.pack(anchor=tk.W, pady=5)
        ttk.Label(general_frame, text="50 (Short) ← → 200 (Long)").pack(anchor=tk.W)
        
        # Camera selection
        ttk.Label(general_frame, text="Camera:").pack(anchor=tk.W, pady=(15, 0))
        camera_var = tk.IntVar(value=self.config.get("camera_index", 0))
        camera_spin = ttk.Spinbox(general_frame, from_=0, to=5, 
                                  textvariable=camera_var, width=5)
        camera_spin.pack(anchor=tk.W, pady=5)
        
        # === Feedback Tab ===
        feedback_frame = ttk.Frame(notebook)
        notebook.add(feedback_frame, text="Feedback")
        
        # Audio toggle
        audio_var = tk.BooleanVar(value=self.config.get("audio_enabled", True))
        ttk.Checkbutton(feedback_frame, text="Enable Sound Effects", 
                        variable=audio_var).pack(anchor=tk.W, pady=10)
        
        # Border toggle
        border_var = tk.BooleanVar(value=self.config.get("border_enabled", True))
        ttk.Checkbutton(feedback_frame, text="Show Status Border", 
                        variable=border_var).pack(anchor=tk.W, pady=10)
        
        # === Annotation Tab ===
        annotation_frame = ttk.Frame(notebook)
        notebook.add(annotation_frame, text="Annotation")
        
        # Color selection
        ttk.Label(annotation_frame, text="Annotation Color:").pack(anchor=tk.W, pady=(10, 0))
        
        colors = ["Red", "Blue", "Green", "Yellow", "White", "Black"]
        color_var = tk.StringVar(value="Red")
        color_combo = ttk.Combobox(annotation_frame, values=colors, 
                                   textvariable=color_var, state="readonly", width=15)
        color_combo.pack(anchor=tk.W, pady=5)
        
        # Color mapping
        self.color_map = {
            "Red": [255, 0, 0],
            "Blue": [0, 0, 255],
            "Green": [0, 255, 0],
            "Yellow": [255, 255, 0],
            "White": [255, 255, 255],
            "Black": [0, 0, 0],
        }
        
        # Set current color
        current_color = self.config.get("annotation_color", [255, 0, 0])
        for name, rgb in self.color_map.items():
            if rgb == current_color:
                color_var.set(name)
                break
        
        # === Save Button ===
        save_frame = ttk.Frame(self.window)
        save_frame.pack(fill=tk.X, padx=10, pady=10)
        
        def save_settings():
            self.config.set("hand_preference", hand_var.get())
            self.config.set("sensitivity", sensitivity_var.get())
            self.config.set("swipe_threshold", swipe_var.get())
            self.config.set("camera_index", camera_var.get())
            self.config.set("audio_enabled", audio_var.get())
            self.config.set("border_enabled", border_var.get())
            
            color_name = color_var.get()
            self.config.set("annotation_color", self.color_map.get(color_name, [255, 0, 0]))
            
            self.config.set("first_run", False)
            
            if self.on_save_callback:
                self.on_save_callback()
            
            self.window.destroy()
        
        ttk.Button(save_frame, text="Save", command=save_settings).pack(side=tk.RIGHT, padx=5)
        ttk.Button(save_frame, text="Cancel", command=self.window.destroy).pack(side=tk.RIGHT, padx=5)
    
    def close(self):
        """Close the settings window."""
        if self.window and self.window.winfo_exists():
            self.window.destroy()