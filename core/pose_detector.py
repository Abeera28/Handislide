"""
HandiSlide - Pose Detection Module
Uses MediaPipe Pose to detect shoulder position for the zone system.
We only need shoulder landmarks — lightweight detection.
"""

import mediapipe as mp

class PoseDetector:
    def __init__(self, min_detection_confidence=0.5, min_tracking_confidence=0.5):
        """
        Initialize MediaPipe Pose detector.
        
        We use the full pose model but only extract shoulder landmarks.
        This is lightweight enough for real-time use alongside hand detection.
        
        Args:
            min_detection_confidence: Minimum confidence for detection
            min_tracking_confidence: Minimum confidence for tracking
        """
        self.mp_pose = mp.solutions.pose
        
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=0,  # 0 = fastest, less accurate (good enough for shoulders)
            smooth_landmarks=True,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence
        )
        
        self.results = None
        self.shoulder_y = None
        self.shoulder_detected = False
    
    def detect(self, frame_rgb):
        """
        Process a frame and detect pose landmarks.
        
        Args:
            frame_rgb: RGB image as numpy array
            
        Returns:
            True if shoulders were detected, False otherwise
        """
        frame_rgb.flags.writeable = False
        self.results = self.pose.process(frame_rgb)
        frame_rgb.flags.writeable = True
        
        self.shoulder_detected = False
        self.shoulder_y = None
        
        if self.results.pose_landmarks:
            # Landmark indices for shoulders:
            # 11 = Left shoulder
            # 12 = Right shoulder
            left_shoulder = self.results.pose_landmarks.landmark[11]
            right_shoulder = self.results.pose_landmarks.landmark[12]
            
            # Check visibility (MediaPipe gives visibility score)
            left_visible = left_shoulder.visibility > 0.5
            right_visible = right_shoulder.visibility > 0.5
            
            if left_visible and right_visible:
                # Average the Y positions of both shoulders
                self.shoulder_y = (left_shoulder.y + right_shoulder.y) / 2.0
                self.shoulder_detected = True
            elif left_visible:
                self.shoulder_y = left_shoulder.y
                self.shoulder_detected = True
            elif right_visible:
                self.shoulder_y = right_shoulder.y
                self.shoulder_detected = True
            
            return self.shoulder_detected
        else:
            return False
    
    def get_shoulder_y(self):
        """
        Get the normalized Y position of the shoulders.
        
        Returns:
            Float (0.0 to 1.0) representing shoulder height,
            or None if not detected.
            Lower values = higher on screen.
        """
        return self.shoulder_y
    
    def is_shoulder_detected(self):
        """Check if shoulders are currently detected."""
        return self.shoulder_detected
    
    def close(self):
        """Release MediaPipe resources."""
        self.pose.close()