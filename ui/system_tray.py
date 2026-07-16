"""
HandiSlide - System Tray Module
Creates system tray icon with menu for controlling the application.
"""

import pystray
from PIL import Image, ImageDraw
import threading
import os

class SystemTray:
    def __init__(self, app_controller=None):
        """
        Initialize system tray.
        
        Args:
            app_controller: Reference to the main application controller
        """
        self.app = app_controller
        self.tray_icon = None
        self.is_running = False
        
        # Load icon
        self.icon_image = self._load_icon()
    
    def _load_icon(self):
        """Load or create the tray icon image."""
        assets_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'assets'
        )
        icon_path = os.path.join(assets_path, 'icon.ico')
        
        if os.path.exists(icon_path):
            try:
                return Image.open(icon_path)
            except:
                pass
        
        # Create a simple default icon
        return self._create_default_icon()
    
    def _create_default_icon(self):
        """Create a simple colored square as default icon."""
        size = 64
        image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        draw.rounded_rectangle([4, 4, size-4, size-4], radius=12, 
                               fill=(0, 120, 212, 255))
        return image
    
    def _create_menu(self):
        """Create the right-click menu."""
        from pystray import Menu, MenuItem
        
        def on_settings(icon, item):
            if self.app:
                self.app.open_settings()
        
        def on_tutorial(icon, item):
            if self.app:
                self.app.open_tutorial()
        
        def on_pause_resume(icon, item):
            if self.app:
                is_paused = self.app.toggle_pause()
                # Update menu text would require rebuilding menu
                # For simplicity, we handle state in the app
        
        def on_quit(icon, item):
            if self.app:
                self.app.quit()
            icon.stop()
        
        return Menu(
            MenuItem("Settings", on_settings, default=False),
            MenuItem("Tutorial", on_tutorial, default=False),
            MenuItem("Pause/Resume", on_pause_resume, default=False),
            Menu.SEPARATOR,
            MenuItem("Quit", on_quit, default=False),
        )
    
    def start(self):
        """Start the system tray icon."""
        self.tray_icon = pystray.Icon(
            "HandiSlide",
            self.icon_image,
            "HandiSlide - Gesture Control",
            menu=self._create_menu()
        )
        
        self.is_running = True
        
        # Run in separate thread
        tray_thread = threading.Thread(target=self.tray_icon.run, daemon=True)
        tray_thread.start()
        
        print("[SystemTray] Started")
    
    def stop(self):
        """Stop the system tray icon."""
        self.is_running = False
        if self.tray_icon:
            try:
                self.tray_icon.stop()
            except:
                pass
        print("[SystemTray] Stopped")
    
    def update_tooltip(self, text):
        """Update the tooltip text."""
        if self.tray_icon:
            self.tray_icon.title = text