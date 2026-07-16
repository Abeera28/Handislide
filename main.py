"""
HandiSlide - Main Application
Gesture-based PowerPoint controller using webcam.
"""

import time
import threading
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.camera import Camera
from core.hand_detector import HandDetector
from core.pose_detector import PoseDetector
from core.gesture_classifier import GestureClassifier
from core.zone_manager import ZoneManager
from core.gesture_buffer import GestureBuffer

from output.keystroke_emulator import KeystrokeEmulator
from output.powerpoint_com import PowerPointController
from output.audio_feedback import AudioFeedback

from ui.status_border import StatusBorder
from ui.system_tray import SystemTray
from ui.settings_window import SettingsWindow
from ui.tutorial_overlay import TutorialOverlay

from config import Config


class HandiSlideApp:
    # Application modes
    MODE_NORMAL = "normal"
    MODE_DRAW = "draw"
    MODE_ERASE = "erase"
    
    def __init__(self):
        """Initialize the HandiSlide application."""
        print("=" * 50)
        print("HandiSlide - Gesture-Based Presentation Controller")
        print("=" * 50)
        
        # Load configuration
        self.config = Config()
        
        # Initialize components
        self.camera = None
        self.hand_detector = None
        self.pose_detector = None
        self.gesture_classifier = None
        self.zone_manager = None
        self.gesture_buffer = None
        
        self.keystroke_emulator = KeystrokeEmulator()
        self.powerpoint = PowerPointController()
        self.audio = AudioFeedback()
        
        self.status_border = StatusBorder()
        self.settings_window = SettingsWindow(self.config, self._on_settings_saved)
        self.tutorial_overlay = TutorialOverlay()
        self.system_tray = SystemTray(self)
        
        # State
        self.is_running = False
        self.is_paused = False
        self.current_mode = self.MODE_NORMAL
        self.use_com = False  # Whether to use COM integration
        
        # Drawing state
        self.prev_index_pos = None
        self.drawing_points = []
        
        # Frame rate
        self.fps = 30
        self.frame_time = 1.0 / self.fps
    
    def start(self):
        """Start the application."""
        print("[App] Starting HandiSlide...")
        
        # Initialize detection modules
        self.camera = Camera(camera_index=self.config.get("camera_index", 0))
        self.hand_detector = HandDetector()
        self.pose_detector = PoseDetector()
        self.gesture_classifier = GestureClassifier(
            swipe_threshold=self.config.get("swipe_threshold", 100) / 640.0
        )
        self.zone_manager = ZoneManager(
            enter_time=self.config.get("zone_enter_time", 0.3),
            exit_time=self.config.get("zone_exit_time", 0.5)
        )
        self.gesture_buffer = GestureBuffer()
        
        # Apply settings
        self._apply_settings()
        
        # Try to connect to PowerPoint
        if self.powerpoint.connect():
            self.use_com = True
            print("[App] PowerPoint COM integration active")
        else:
            self.use_com = False
            print("[App] Using keystroke mode (COM not available)")
        
        # Start camera
        try:
            self.camera.start()
        except Exception as e:
            print(f"[App] Camera error: {e}")
            print("[App] Please check your webcam connection")
            return
        
        # Start system tray
        self.system_tray.start()
        
        # Start status border (in separate thread)
        border_thread = threading.Thread(target=self.status_border.start, daemon=True)
        border_thread.start()
        time.sleep(0.5)  # Wait for border to initialize
        
        # Set initial border state
        self.status_border.set_rest()
        
        # Audio feedback for startup
        if self.config.get("audio_enabled", True):
            self.audio.play_gesture_success()
        
        # Main loop
        self.is_running = True
        self._main_loop()
    
    def _main_loop(self):
        """Main application loop."""
        print("[App] Main loop started")
        
        while self.is_running:
            loop_start = time.time()
            
            if self.is_paused:
                time.sleep(0.1)
                continue
            
            try:
                # Step 1: Capture frame
                frame = self.camera.read_frame()
                if frame is None:
                    time.sleep(0.01)
                    continue
                
                # Step 2: Detect hands
                hands_detected = self.hand_detector.detect(frame)
                
                # Step 3: Detect pose (shoulders)
                shoulders_detected = self.pose_detector.detect(frame)
                
                if not hands_detected or not shoulders_detected:
                    # No hand or shoulders — reset state
                    self.zone_manager.update(None, None)
                    self.gesture_buffer.reset()
                    self._update_border()
                    time.sleep(0.01)
                    continue
                
                # Get primary hand
                hand_idx = self.hand_detector.get_primary_hand_index(
                    self.config.get("hand_preference", "right")
                )
                
                if hand_idx < 0:
                    time.sleep(0.01)
                    continue
                
                landmarks = self.hand_detector.get_landmarks(hand_idx)
                wrist = self.hand_detector.get_wrist_position(hand_idx)
                shoulder_y = self.pose_detector.get_shoulder_y()
                
                # Step 4: Update zone
                zone_state = self.zone_manager.update(
                    wrist[1] if wrist else None,
                    shoulder_y
                )
                
                # Step 5: Classify gesture (only in active zone)
                if self.zone_manager.is_active():
                    gesture = self.gesture_classifier.classify(
                        landmarks, 
                        self.camera.width, 
                        self.camera.height
                    )
                    
                    # Step 6: Apply debounce
                    confirmed_gesture = self.gesture_buffer.process(gesture, self.fps)
                    
                    # Step 7: Route action
                    if confirmed_gesture:
                        self._handle_gesture(confirmed_gesture, hand_idx)
                else:
                    # Reset gesture state when not active
                    self.gesture_buffer.reset()
                
                # Update border
                self._update_border()
                
            except Exception as e:
                print(f"[App] Error in main loop: {e}")
            
            # Maintain frame rate
            elapsed = time.time() - loop_start
            if elapsed < self.frame_time:
                time.sleep(self.frame_time - elapsed)
    
    def _handle_gesture(self, gesture, hand_index):
        """
        Route a confirmed gesture to the appropriate handler.
        
        Args:
            gesture: Gesture name string
            hand_index: Index of the hand making the gesture
        """
        print(f"[Gesture] {gesture} (mode: {self.current_mode})")
        
        # Get index finger position for drawing/erasing
        index_pos = self.hand_detector.get_index_tip_position(hand_index)
        
        if self.current_mode == self.MODE_NORMAL:
            self._handle_normal_gesture(gesture, index_pos)
        elif self.current_mode == self.MODE_DRAW:
            self._handle_draw_gesture(gesture, index_pos)
        elif self.current_mode == self.MODE_ERASE:
            self._handle_erase_gesture(gesture, index_pos)
    
    def _handle_normal_gesture(self, gesture, index_pos):
        """Handle gestures in normal mode."""
        if gesture == GestureClassifier.SWIPE_RIGHT:
            self.keystroke_emulator.next_slide()
            self._on_success()
        
        elif gesture == GestureClassifier.SWIPE_LEFT:
            self.keystroke_emulator.previous_slide()
            self._on_success()
        
        elif gesture == GestureClassifier.FIST:
            self.keystroke_emulator.blackout()
            self._on_success()
        
        elif gesture == GestureClassifier.OPEN_PALM_HOLD:
            self.keystroke_emulator.whiteout()
            self._on_success()
        
        elif gesture == GestureClassifier.THUMBS_UP:
            self.keystroke_emulator.start_slideshow()
            self._on_success()
        
        elif gesture == GestureClassifier.THUMBS_DOWN:
            self.keystroke_emulator.end_slideshow()
            self._on_success()
        
        elif gesture == GestureClassifier.TWO_FINGERS:
            self.current_mode = self.MODE_DRAW
            self.prev_index_pos = None
            print("[Mode] Drawing mode ON")
            self._on_success()
        
        elif gesture == GestureClassifier.THREE_FINGERS:
            self.current_mode = self.MODE_ERASE
            self.prev_index_pos = None
            print("[Mode] Erase mode ON")
            self._on_success()
    
    def _handle_draw_gesture(self, gesture, index_pos):
        """Handle gestures in drawing mode."""
        if gesture == GestureClassifier.TWO_FINGERS:
            self.current_mode = self.MODE_NORMAL
            self.prev_index_pos = None
            print("[Mode] Drawing mode OFF")
            self._on_success()
        
        elif gesture == GestureClassifier.THREE_FINGERS:
            self.current_mode = self.MODE_ERASE
            self.prev_index_pos = None
            print("[Mode] Switched to Erase mode")
            self._on_success()
        
        elif gesture == GestureClassifier.FIST:
            if self.use_com:
                self.powerpoint.undo_last()
            self.prev_index_pos = None
            self._on_success()
        
        elif gesture == GestureClassifier.INDEX_POINT_MOVE:
            if index_pos and self.use_com:
                self._draw(index_pos)
    
    def _handle_erase_gesture(self, gesture, index_pos):
        """Handle gestures in erase mode."""
        if gesture == GestureClassifier.THREE_FINGERS:
            self.current_mode = self.MODE_NORMAL
            self.prev_index_pos = None
            print("[Mode] Erase mode OFF")
            self._on_success()
        
        elif gesture == GestureClassifier.TWO_FINGERS:
            self.current_mode = self.MODE_DRAW
            self.prev_index_pos = None
            print("[Mode] Switched to Draw mode")
            self._on_success()
        
        elif gesture == GestureClassifier.FIST:
            if self.use_com:
                self.powerpoint.undo_erase()
            self._on_success()
        
        elif gesture == GestureClassifier.INDEX_POINT_MOVE:
            if index_pos and self.use_com:
                self._erase(index_pos)
    
    def _draw(self, index_pos):
        """Draw a line segment on the slide."""
        if not self.use_com:
            return
        
        # Convert normalized coordinates to slide coordinates
        slide_width, slide_height = self.powerpoint.get_slide_dimensions()
        
        current_x = index_pos[0] * slide_width
        current_y = index_pos[1] * slide_height
        
        if self.prev_index_pos is not None:
            prev_x = self.prev_index_pos[0] * slide_width
            prev_y = self.prev_index_pos[1] * slide_height
            
            color = self.config.get("annotation_color", [255, 0, 0])
            self.powerpoint.draw_line(prev_x, prev_y, current_x, current_y, color)
        
        self.prev_index_pos = (index_pos[0], index_pos[1])
    
    def _erase(self, index_pos):
        """Erase annotations near the given position."""
        if not self.use_com:
            return
        
        slide_width, slide_height = self.powerpoint.get_slide_dimensions()
        
        current_x = index_pos[0] * slide_width
        current_y = index_pos[1] * slide_height
        
        sensitivity = self.config.get("sensitivity", 5)
        threshold = 50 - (sensitivity * 3)  # 47 to 20 points
        
        self.powerpoint.erase_at_position(current_x, current_y, threshold)
        self.prev_index_pos = (index_pos[0], index_pos[1])
    
    def _on_success(self):
        """Called when a gesture is successfully executed."""
        if self.config.get("audio_enabled", True):
            self.audio.play_gesture_success()
        if self.config.get("border_enabled", True):
            self.status_border.flash_success()
    
    def _update_border(self):
        """Update the status border based on current state."""
        if not self.config.get("border_enabled", True):
            return
        
        if self.is_paused:
            self.status_border.hide()
        elif self.current_mode == self.MODE_DRAW:
            self.status_border.set_draw()
        elif self.current_mode == self.MODE_ERASE:
            self.status_border.set_erase()
        elif self.zone_manager.is_active():
            self.status_border.set_active()
        else:
            self.status_border.set_rest()
    
    def _apply_settings(self):
        """Apply current settings to all modules."""
        # Update zone manager timing
        self.zone_manager.enter_time = self.config.get("zone_enter_time", 0.3)
        self.zone_manager.exit_time = self.config.get("zone_exit_time", 0.5)
        
        # Update audio
        self.audio.enabled = self.config.get("audio_enabled", True)
    
    def _on_settings_saved(self):
        """Callback when settings are saved."""
        self._apply_settings()
        print("[App] Settings updated")
    
    def open_settings(self):
        """Open the settings window."""
        self.settings_window.open()
    
    def open_tutorial(self):
        """Open the tutorial overlay."""
        self.tutorial_overlay.open()
    
    def toggle_pause(self):
        """Toggle pause/resume detection."""
        self.is_paused = not self.is_paused
        state = "paused" if self.is_paused else "resumed"
        print(f"[App] Detection {state}")
        
        if self.is_paused:
            self.status_border.hide()
        else:
            self._update_border()
        
        return self.is_paused
    
    def quit(self):
        """Shutdown the application."""
        print("[App] Shutting down...")
        self.is_running = False
        
        # Cleanup
        if self.camera:
            self.camera.stop()
        if self.hand_detector:
            self.hand_detector.close()
        if self.pose_detector:
            self.pose_detector.close()
        if self.powerpoint:
            self.powerpoint.disconnect()
        if self.status_border:
            self.status_border.stop()
        
        print("[App] Goodbye!")


def main():
    """Entry point for the application."""
    app = HandiSlideApp()
    
    try:
        app.start()
    except KeyboardInterrupt:
        print("\n[App] Interrupted by user")
    except Exception as e:
        print(f"[App] Fatal error: {e}")
    finally:
        app.quit()


if __name__ == "__main__":
    main()