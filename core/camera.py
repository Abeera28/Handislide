"""
HandiSlide - Camera Module
Handles webcam capture, frame preprocessing, and lighting normalization.
"""

import cv2
import numpy as np
import time

class Camera:
    def __init__(self, camera_index=0, width=640, height=480, fps=30):
        """
        Initialize camera capture.
        
        Args:
            camera_index: Which webcam to use (0 = default)
            width: Frame width in pixels
            height: Frame height in pixels
            fps: Target frames per second
        """
        self.camera_index = camera_index
        self.width = width
        self.height = height
        self.fps = fps
        
        self.cap = None
        self.is_running = False
        self.clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        
        # Performance tracking
        self.frame_count = 0
        self.start_time = time.time()
        self.actual_fps = 0
    
    def start(self):
        """Open webcam connection and start capturing."""
        self.cap = cv2.VideoCapture(self.camera_index)
        
        if not self.cap.isOpened():
            raise RuntimeError(f"Cannot open camera {self.camera_index}")
        
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self.cap.set(cv2.CAP_PROP_FPS, self.fps)
        
        self.is_running = True
        self.frame_count = 0
        self.start_time = time.time()
        
        print(f"[Camera] Started: {self.width}x{self.height} @ {self.fps}fps")
    
    def read_frame(self):
        """
        Capture a single frame from the webcam.
        
        Returns:
            RGB frame as numpy array, or None if capture failed.
            Frame is mirrored (flipped horizontally) for natural feel.
            Lighting normalization applied for dark rooms.
        """
        if not self.is_running or self.cap is None:
            return None
        
        ret, frame = self.cap.read()
        
        if not ret:
            return None
        
        # Mirror the frame so left/right feels natural
        frame = cv2.flip(frame, 1)
        
        # Convert BGR (OpenCV default) to RGB (MediaPipe requirement)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Apply lighting normalization for dark classrooms
        frame_rgb = self._normalize_lighting(frame_rgb)
        
        # Update FPS counter
        self.frame_count += 1
        elapsed = time.time() - self.start_time
        if elapsed > 1.0:
            self.actual_fps = self.frame_count / elapsed
            self.frame_count = 0
            self.start_time = time.time()
        
        return frame_rgb
    
    def _normalize_lighting(self, frame):
        """
        Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
        to improve hand detection in dim lighting.
        
        Args:
            frame: RGB image
            
        Returns:
            Lighting-normalized RGB image
        """
        # Convert to LAB color space (better for brightness adjustments)
        lab = cv2.cvtColor(frame, cv2.COLOR_RGB2LAB)
        l_channel, a_channel, b_channel = cv2.split(lab)
        
        # Apply CLAHE to the lightness channel only
        l_channel = self.clahe.apply(l_channel)
        
        # Merge back
        lab = cv2.merge([l_channel, a_channel, b_channel])
        
        # Convert back to RGB
        return cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)
    
    def get_fps(self):
        """Get the actual FPS being achieved."""
        return self.actual_fps
    
    def stop(self):
        """Release the webcam and stop capturing."""
        self.is_running = False
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        print("[Camera] Stopped")
    
    def is_available(self):
        """Check if camera is connected and running."""
        return self.is_running and self.cap is not None and self.cap.isOpened()
    
    def get_resolution(self):
        """Get current camera resolution."""
        return (self.width, self.height)