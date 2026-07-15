"""
HandiSlide - Hand Detection Module
Uses MediaPipe Hands to detect 21 hand landmarks in real-time.
"""

import mediapipe as mp
import numpy as np

class HandDetector:
    def __init__(self, static_image_mode=False, max_num_hands=2, 
                 min_detection_confidence=0.5, min_tracking_confidence=0.5):
        """
        Initialize MediaPipe Hands detector.
        
        Args:
            static_image_mode: Set to False for video (tracking across frames)
            max_num_hands: Maximum number of hands to detect
            min_detection_confidence: Minimum confidence for hand detection
            min_tracking_confidence: Minimum confidence for hand tracking
        """
        self.mp_hands = mp.solutions.hands
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        
        self.hands = self.mp_hands.Hands(
            static_image_mode=static_image_mode,
            max_num_hands=max_num_hands,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence
        )
        
        self.results = None
        self.landmarks_list = []
        self.handedness_list = []
        self.confidence_scores = []
    
    def detect(self, frame_rgb):
        """
        Process a frame and detect hands.
        
        Args:
            frame_rgb: RGB image as numpy array
            
        Returns:
            True if hands were detected, False otherwise
        """
        # MediaPipe requires the image to be non-writable for performance
        frame_rgb.flags.writeable = False
        self.results = self.hands.process(frame_rgb)
        frame_rgb.flags.writeable = True
        
        self.landmarks_list = []
        self.handedness_list = []
        self.confidence_scores = []
        
        if self.results.multi_hand_landmarks:
            for idx, hand_landmarks in enumerate(self.results.multi_hand_landmarks):
                self.landmarks_list.append(hand_landmarks)
                
                if self.results.multi_handedness:
                    handedness = self.results.multi_handedness[idx].classification[0]
                    self.handedness_list.append(handedness.label)  # "Left" or "Right"
                    self.confidence_scores.append(handedness.score)
                else:
                    self.handedness_list.append("Unknown")
                    self.confidence_scores.append(0.0)
            
            return True
        else:
            return False
    
    def get_landmarks(self, hand_index=0):
        """
        Get normalized landmarks for a specific hand.
        
        Args:
            hand_index: Index of the hand (0 = first detected hand)
            
        Returns:
            List of (x, y, z) tuples normalized to [0, 1], or None if no hand
        """
        if hand_index >= len(self.landmarks_list):
            return None
        
        landmarks = self.landmarks_list[hand_index]
        return [(lm.x, lm.y, lm.z) for lm in landmarks.landmark]
    
    def get_landmark_points(self, hand_index=0):
        """
        Get landmarks as list of dictionaries with x, y, z values.
        
        Args:
            hand_index: Index of the hand
            
        Returns:
            List of dicts, each with 'x', 'y', 'z' keys, or None
        """
        if hand_index >= len(self.landmarks_list):
            return None
        
        landmarks = self.landmarks_list[hand_index]
        return [
            {'x': lm.x, 'y': lm.y, 'z': lm.z}
            for lm in landmarks.landmark
        ]
    
    def get_primary_hand_index(self, preferred_hand='right'):
        """
        Get the index of the preferred hand.
        
        Args:
            preferred_hand: 'left' or 'right'
            
        Returns:
            Index of the preferred hand in the landmarks list,
            or 0 if only one hand detected,
            or -1 if no hands detected
        """
        if len(self.landmarks_list) == 0:
            return -1
        
        if len(self.landmarks_list) == 1:
            return 0
        
        # Find the preferred hand
        for idx, handedness in enumerate(self.handedness_list):
            if handedness.lower() == preferred_hand.lower():
                return idx
        
        # Preferred hand not found, return first hand
        return 0
    
    def is_finger_extended(self, landmarks, finger_tip_idx, finger_pip_idx, wrist_idx=0):
        """
        Check if a finger is extended (straight).
        
        Compares the distance from tip to wrist vs pip to wrist.
        Extended finger: tip is further from wrist than pip joint.
        
        Args:
            landmarks: List of (x, y, z) tuples
            finger_tip_idx: Index of finger tip landmark
            finger_pip_idx: Index of finger PIP joint landmark
            wrist_idx: Index of wrist landmark
            
        Returns:
            True if finger is extended, False if curled
        """
        if landmarks is None:
            return False
        
        tip = landmarks[finger_tip_idx]
        pip = landmarks[finger_pip_idx]
        wrist = landmarks[wrist_idx]
        
        # Calculate distances (only x,y, ignore z for simplicity)
        tip_to_wrist = ((tip[0] - wrist[0])**2 + (tip[1] - wrist[1])**2)**0.5
        pip_to_wrist = ((pip[0] - wrist[0])**2 + (pip[1] - wrist[1])**2)**0.5
        
        # Also check that tip is further from pip (finger is straight, not curled)
        tip_to_pip = ((tip[0] - pip[0])**2 + (tip[1] - pip[1])**2)**0.5
        
        # Finger is extended if tip is further from wrist than pip
        # AND tip is some distance away from pip (not touching)
        return tip_to_wrist > pip_to_wrist and tip_to_pip > 0.03
    
    def is_finger_extended_simple(self, landmarks, tip_idx, pip_idx):
        """
        Simpler check: is the tip above (higher Y) than the PIP joint?
        Works well for most gestures.
        
        Args:
            landmarks: List of (x, y, z) tuples
            tip_idx: Index of finger tip
            pip_idx: Index of PIP joint
            
        Returns:
            True if finger appears extended
        """
        if landmarks is None:
            return False
        
        tip_y = landmarks[tip_idx][1]
        pip_y = landmarks[pip_idx][1]
        
        # In image coordinates, smaller Y = higher up
        # Extended finger: tip is higher (smaller Y) than PIP
        return tip_y < pip_y
    
    def get_wrist_position(self, hand_index=0):
        """Get wrist position (x, y) normalized [0, 1]."""
        landmarks = self.get_landmarks(hand_index)
        if landmarks is None:
            return None
        return (landmarks[0][0], landmarks[0][1])
    
    def get_index_tip_position(self, hand_index=0):
        """Get index finger tip position (x, y) normalized [0, 1]."""
        landmarks = self.get_landmarks(hand_index)
        if landmarks is None:
            return None
        return (landmarks[8][0], landmarks[8][1])
    
    def draw_landmarks(self, frame_bgr, hand_index=0):
        """
        Draw hand landmarks on a BGR frame (for debug visualization).
        
        Args:
            frame_bgr: BGR image to draw on
            hand_index: Which hand to draw
            
        Returns:
            Frame with landmarks drawn
        """
        if hand_index < len(self.landmarks_list):
            self.mp_drawing.draw_landmarks(
                frame_bgr,
                self.landmarks_list[hand_index],
                self.mp_hands.HAND_CONNECTIONS,
                self.mp_drawing_styles.get_default_hand_landmarks_style(),
                self.mp_drawing_styles.get_default_hand_connections_style()
            )
        return frame_bgr
    
    def get_hand_count(self):
        """Get number of hands currently detected."""
        return len(self.landmarks_list)
    
    def close(self):
        """Release MediaPipe resources."""
        self.hands.close()