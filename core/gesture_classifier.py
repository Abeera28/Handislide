"""
HandiSlide - Gesture Classifier
Converts MediaPipe hand landmarks into gesture names.
Implements all 11 gestures using landmark geometry.
"""

import numpy as np

class GestureClassifier:
    # Gesture names (constants)
    SWIPE_RIGHT = "swipe_right"
    SWIPE_LEFT = "swipe_left"
    FIST = "fist"
    OPEN_PALM_HOLD = "open_palm_hold"
    THUMBS_UP = "thumbs_up"
    THUMBS_DOWN = "thumbs_down"
    TWO_FINGERS = "two_fingers"
    THREE_FINGERS = "three_fingers"
    INDEX_POINT_MOVE = "index_point_move"
    NONE = None
    
    def __init__(self, swipe_threshold=0.15):
        """
        Initialize gesture classifier.
        
        Args:
            swipe_threshold: Normalized distance wrist must move for a swipe
        """
        self.swipe_threshold = swipe_threshold
        
        # Tracking previous wrist positions for swipe detection
        self.wrist_history = []
        self.max_history = 15  # Store last 15 frames
        self.swipe_cooldown = 0
        self.swipe_cooldown_frames = 15  # Frames to wait after a swipe
        
        # Index finger history for drawing
        self.index_history = []
    
    def classify(self, landmarks, frame_width, frame_height):
        """
        Classify the current hand gesture.
        
        Args:
            landmarks: List of (x, y, z) tuples from MediaPipe
            frame_width: Camera frame width in pixels
            frame_height: Camera frame height in pixels
            
        Returns:
            Gesture name string, or None if no gesture detected
        """
        if landmarks is None or len(landmarks) < 21:
            return self.NONE
        
        # Update wrist history (for swipe detection)
        wrist = landmarks[0]
        self.wrist_history.append((wrist[0], wrist[1]))
        if len(self.wrist_history) > self.max_history:
            self.wrist_history.pop(0)
        
        # Update index finger history
        index_tip = landmarks[8]
        self.index_history.append((index_tip[0], index_tip[1]))
        if len(self.index_history) > self.max_history:
            self.index_history.pop(0)
        
        # Handle swipe cooldown
        if self.swipe_cooldown > 0:
            self.swipe_cooldown -= 1
        
        # Check each gesture type
        gesture = self.NONE
        
        # Swipe detection (only if not in cooldown)
        if self.swipe_cooldown <= 0:
            swipe = self._detect_swipe(frame_width, frame_height)
            if swipe:
                self.swipe_cooldown = self.swipe_cooldown_frames
                return swipe
        
        # Static gestures (checked every frame)
        if self._is_fist(landmarks):
            return self.FIST
        
        if self._is_thumbs_up(landmarks):
            return self.THUMBS_UP
        
        if self._is_thumbs_down(landmarks):
            return self.THUMBS_DOWN
        
        if self._is_two_fingers(landmarks):
            return self.TWO_FINGERS
        
        if self._is_three_fingers(landmarks):
            return self.THREE_FINGERS
        
        if self._is_open_palm(landmarks):
            return self.OPEN_PALM_HOLD
        
        # Index finger pointing (for drawing/erasing)
        if self._is_index_pointing(landmarks):
            return self.INDEX_POINT_MOVE
        
        return self.NONE
    
    def _detect_swipe(self, frame_width, frame_height):
        """Detect horizontal swipe gestures."""
        if len(self.wrist_history) < 10:
            return None
        
        # Get start and end positions
        start_x = self.wrist_history[0][0]
        end_x = self.wrist_history[-1][0]
        
        # Calculate movement in pixels
        dx = (end_x - start_x) * frame_width
        
        if abs(dx) > self.swipe_threshold * frame_width:
            if dx > 0:
                return self.SWIPE_RIGHT
            else:
                return self.SWIPE_LEFT
        
        return None
    
    def _is_fist(self, landmarks):
        """
        Check if hand is making a fist.
        All finger tips should be below their PIP joints (curled inward).
        """
        # Finger tip and PIP joint indices
        fingers = [
            (4, 3),   # Thumb: tip=4, IP=3
            (8, 6),   # Index: tip=8, PIP=6
            (12, 10), # Middle: tip=12, PIP=10
            (16, 14), # Ring: tip=16, PIP=14
            (20, 18), # Pinky: tip=20, PIP=18
        ]
        
        curled_count = 0
        for tip_idx, pip_idx in fingers:
            tip_y = landmarks[tip_idx][1]
            pip_y = landmarks[pip_idx][1]
            
            # For thumb, check X position (thumb curls differently)
            if tip_idx == 4:
                tip_x = landmarks[tip_idx][0]
                pip_x = landmarks[pip_idx][0]
                # Thumb is curled if tip is close to palm
                if abs(tip_x - landmarks[0][0]) < 0.08 and tip_y > pip_y:
                    curled_count += 1
            else:
                # Other fingers: tip Y > PIP Y means curled
                if tip_y > pip_y:
                    curled_count += 1
        
        # At least 4 fingers curled (allow some flexibility)
        return curled_count >= 4
    
    def _is_open_palm(self, landmarks):
        """
        Check if hand is fully open (all fingers extended).
        """
        fingers = [
            (4, 3),   # Thumb
            (8, 6),   # Index
            (12, 10), # Middle
            (16, 14), # Ring
            (20, 18), # Pinky
        ]
        
        extended_count = 0
        for tip_idx, pip_idx in fingers:
            tip_y = landmarks[tip_idx][1]
            pip_y = landmarks[pip_idx][1]
            
            if tip_idx == 4:
                # Thumb: check if extended outward
                tip_x = landmarks[tip_idx][0]
                wrist_x = landmarks[0][0]
                if abs(tip_x - wrist_x) > 0.1:
                    extended_count += 1
            else:
                # Other fingers: tip Y < PIP Y means extended
                if tip_y < pip_y:
                    extended_count += 1
        
        return extended_count >= 4
    
    def _is_thumbs_up(self, landmarks):
        """
        Check for thumbs up gesture.
        Thumb extended upward, other fingers curled.
        """
        thumb_tip = landmarks[4]
        thumb_ip = landmarks[3]
        wrist = landmarks[0]
        
        # Thumb should be above wrist
        thumb_up = thumb_tip[1] < wrist[1]
        
        # Thumb should be somewhat separated from palm
        thumb_extended = abs(thumb_tip[0] - wrist[0]) > 0.08
        
        # Other fingers should be curled
        other_curled = True
        for tip_idx, pip_idx in [(8, 6), (12, 10), (16, 14), (20, 18)]:
            if landmarks[tip_idx][1] < landmarks[pip_idx][1]:
                other_curled = False
                break
        
        return thumb_up and thumb_extended and other_curled
    
    def _is_thumbs_down(self, landmarks):
        """
        Check for thumbs down gesture.
        Thumb extended downward, other fingers curled.
        """
        thumb_tip = landmarks[4]
        thumb_ip = landmarks[3]
        wrist = landmarks[0]
        
        # Thumb should be below wrist
        thumb_down = thumb_tip[1] > wrist[1] + 0.05
        
        # Thumb should be somewhat separated
        thumb_extended = abs(thumb_tip[0] - wrist[0]) > 0.05
        
        # Other fingers should be curled
        other_curled = True
        for tip_idx, pip_idx in [(8, 6), (12, 10), (16, 14), (20, 18)]:
            if landmarks[tip_idx][1] < landmarks[pip_idx][1]:
                other_curled = False
                break
        
        return thumb_down and thumb_extended and other_curled
    
    def _is_two_fingers(self, landmarks):
        """
        Check for two fingers raised (peace sign).
        Index and middle extended, ring and pinky curled.
        """
        # Index and middle should be extended
        index_extended = landmarks[8][1] < landmarks[6][1]
        middle_extended = landmarks[12][1] < landmarks[10][1]
        
        # Ring and pinky should be curled
        ring_curled = landmarks[16][1] > landmarks[14][1]
        pinky_curled = landmarks[20][1] > landmarks[18][1]
        
        return index_extended and middle_extended and ring_curled and pinky_curled
    
    def _is_three_fingers(self, landmarks):
        """
        Check for three fingers raised.
        Index, middle, and ring extended, pinky curled.
        """
        index_extended = landmarks[8][1] < landmarks[6][1]
        middle_extended = landmarks[12][1] < landmarks[10][1]
        ring_extended = landmarks[16][1] < landmarks[14][1]
        pinky_curled = landmarks[20][1] > landmarks[18][1]
        
        return index_extended and middle_extended and ring_extended and pinky_curled
    
    def _is_index_pointing(self, landmarks):
        """
        Check if only the index finger is extended (pointing).
        """
        index_extended = landmarks[8][1] < landmarks[6][1]
        
        # Other fingers should be curled
        middle_curled = landmarks[12][1] > landmarks[10][1]
        ring_curled = landmarks[16][1] > landmarks[14][1]
        pinky_curled = landmarks[20][1] > landmarks[18][1]
        
        return index_extended and middle_curled and ring_curled and pinky_curled
    
    def get_index_position(self):
        """Get the current index finger tip position (normalized 0-1)."""
        if len(self.index_history) > 0:
            return self.index_history[-1]
        return None
    
    def get_wrist_position(self):
        """Get the current wrist position (normalized 0-1)."""
        if len(self.wrist_history) > 0:
            return self.wrist_history[-1]
        return None
    
    def reset(self):
        """Reset all history buffers."""
        self.wrist_history = []
        self.index_history = []
        self.swipe_cooldown = 0