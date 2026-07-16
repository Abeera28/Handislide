"""
HandiSlide - Status Border Module
Creates a subtle, transparent, always-on-top border around the screen
that changes color to indicate system state.
"""

import tkinter as tk
import threading

class StatusBorder:
    # Border colors for different states
    COLORS = {
        "rest": "#404040",        # Dim gray
        "active": "#00AA00",      # Green
        "draw": "#FF8800",        # Orange
        "erase": "#FF0000",       # Red
        "flash": "#FFFFFF",       # White (brief flash on gesture)
        "off": "#000000",         # Completely hidden
    }
    
    def __init__(self, border_width=4):
        """
        Initialize status border.
        
        Args:
            border_width: Width of the border in pixels
        """
        self.border_width = border_width
        self.current_color = self.COLORS["off"]
        self.window = None
        self.is_running = False
        
        # Flash timer
        self.flash_active = False
        self.flash_duration = 200  # milliseconds
    
    def start(self):
        """Create and show the status border window."""
        self.window = tk.Tk()
        self.window.title("HandiSlide Border")
        self.window.overrideredirect(True)  # No title bar
        
        # Make window transparent and click-through
        self.window.attributes('-topmost', True)
        self.window.attributes('-transparentcolor', self.COLORS["off"])
        
        # Try to make click-through (Windows-specific)
        try:
            self.window.attributes('-disabled', True)
        except:
            pass
        
        # Get screen dimensions
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        
        # Position window to cover entire screen
        self.window.geometry(f"{screen_width}x{screen_height}+0+0")
        
        # Create canvas for drawing border
        self.canvas = tk.Canvas(
            self.window,
            width=screen_width,
            height=screen_height,
            highlightthickness=0,
            bg=self.COLORS["off"]
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Make canvas transparent
        try:
            self.window.wm_attributes('-transparentcolor', self.COLORS["off"])
        except:
            pass
        
        self.is_running = True
        
        # Run the Tkinter main loop
        self.window.mainloop()
    
    def _draw_border(self, color):
        """Draw the border with the specified color."""
        if not self.is_running or self.window is None:
            return
        
        try:
            self.canvas.delete("all")
            
            screen_width = self.window.winfo_screenwidth()
            screen_height = self.window.winfo_screenheight()
            
            # Draw top border
            self.canvas.create_rectangle(
                0, 0, screen_width, self.border_width,
                fill=color, outline=""
            )
            # Draw bottom border
            self.canvas.create_rectangle(
                0, screen_height - self.border_width,
                screen_width, screen_height,
                fill=color, outline=""
            )
            # Draw left border
            self.canvas.create_rectangle(
                0, 0, self.border_width, screen_height,
                fill=color, outline=""
            )
            # Draw right border
            self.canvas.create_rectangle(
                screen_width - self.border_width, 0,
                screen_width, screen_height,
                fill=color, outline=""
            )
            
            self.current_color = color
        except Exception:
            pass  # Window might be closing
    
    def set_rest(self):
        """Set border to rest color (dim gray)."""
        self._draw_border(self.COLORS["rest"])
    
    def set_active(self):
        """Set border to active color (green)."""
        self._draw_border(self.COLORS["active"])
    
    def set_draw(self):
        """Set border to drawing mode color (orange)."""
        self._draw_border(self.COLORS["draw"])
    
    def set_erase(self):
        """Set border to erase mode color (red)."""
        self._draw_border(self.COLORS["erase"])
    
    def flash_success(self):
        """Briefly flash white to indicate gesture recognized."""
        if not self.is_running or self.flash_active:
            return
        
        self.flash_active = True
        
        # Save current color
        previous_color = self.current_color
        
        # Show flash
        self._draw_border(self.COLORS["flash"])
        
        # Schedule return to previous color
        def reset():
            import time
            time.sleep(self.flash_duration / 1000.0)
            if self.is_running:
                self._draw_border(previous_color)
            self.flash_active = False
        
        threading.Thread(target=reset, daemon=True).start()
    
    def hide(self):
        """Hide the border completely."""
        self._draw_border(self.COLORS["off"])
    
    def stop(self):
        """Close the border window."""
        self.is_running = False
        if self.window:
            try:
                self.window.destroy()
            except:
                pass