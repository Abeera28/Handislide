"""
HandiSlide - Tutorial Overlay
Shows a guide with all gestures and their functions.
"""

import tkinter as tk
from tkinter import ttk

class TutorialOverlay:
    def __init__(self):
        """Initialize tutorial overlay."""
        self.window = None
    
    def open(self):
        """Open the tutorial window."""
        if self.window is not None and self.window.winfo_exists():
            self.window.lift()
            self.window.focus_force()
            return
        
        self.window = tk.Toplevel()
        self.window.title("HandiSlide - Gesture Guide")
        self.window.geometry("500x600")
        self.window.resizable(False, False)
        
        self._build_ui()
    
    def _build_ui(self):
        """Build the tutorial UI."""
        # Title
        title = ttk.Label(
            self.window, 
            text="HandiSlide Gesture Guide",
            font=("Arial", 16, "bold")
        )
        title.pack(pady=10)
        
        # Subtitle
        subtitle = ttk.Label(
            self.window,
            text="Raise your hand to shoulder level to activate gestures",
            font=("Arial", 10)
        )
        subtitle.pack(pady=(0, 10))
        
        # Create scrollable frame
        canvas = tk.Canvas(self.window)
        scrollbar = ttk.Scrollbar(self.window, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True, padx=10)
        scrollbar.pack(side="right", fill="y")
        
        # Gesture list
        gestures = [
            ("✋ Swipe Right", "Next Slide"),
            ("✋ Swipe Left", "Previous Slide"),
            ("✊ Hold Fist (1s)", "Blackout Screen"),
            ("🖐 Hold Palm Open (2s)", "Whiteout Screen"),
            ("👍 Thumbs Up", "Start Slideshow"),
            ("👎 Thumbs Down", "End Slideshow"),
            ("✌️ Two Fingers", "Toggle Drawing Mode"),
            ("☝️ Index Point + Move", "Draw / Erase"),
            ("🤟 Three Fingers", "Toggle Erase Mode"),
            ("✊ Fist (in Draw/Erase)", "Undo Last Stroke"),
        ]
        
        for i, (gesture, action) in enumerate(gestures):
            frame = ttk.Frame(scrollable_frame)
            frame.pack(fill=tk.X, pady=3)
            
            gesture_label = ttk.Label(frame, text=gesture, width=30, anchor=tk.W,
                                      font=("Arial", 11))
            gesture_label.pack(side=tk.LEFT)
            
            arrow_label = ttk.Label(frame, text="→", width=5)
            arrow_label.pack(side=tk.LEFT)
            
            action_label = ttk.Label(frame, text=action, width=20, anchor=tk.W,
                                     font=("Arial", 11, "bold"))
            action_label.pack(side=tk.LEFT)
        
        # Tips section
        tips_frame = ttk.LabelFrame(scrollable_frame, text="Tips")
        tips_frame.pack(fill=tk.X, pady=(15, 5), padx=5)
        
        tips = [
            "• Keep your hand at shoulder/chest level for gestures",
            "• Return hand to your side to stop gesture detection",
            "• Look for the green border = system is listening",
            "• Orange border = drawing mode active",
            "• Red border = erase mode active",
            "• Drawings are saved with your PowerPoint file",
        ]
        
        for tip in tips:
            ttk.Label(tips_frame, text=tip, wraplength=420, 
                      font=("Arial", 9)).pack(anchor=tk.W, padx=5, pady=2)
        
        # Close button
        ttk.Button(self.window, text="Close", command=self.window.destroy).pack(pady=10)
    
    def close(self):
        """Close the tutorial window."""
        if self.window and self.window.winfo_exists():
            self.window.destroy()