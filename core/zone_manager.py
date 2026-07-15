"""
HandiSlide - Zone Manager
Manages the Rest Zone vs Active Zone state machine.
Prevents accidental gesture triggers when presenter is just talking.
"""

import time

class ZoneManager:
    # Possible states
    REST = "rest"
    TRANSITIONING_UP = "transitioning_up"
    ACTIVE = "active"
    TRANSITIONING_DOWN = "transitioning_down"
    
    def __init__(self, enter_time=0.3, exit_time=0.5):
        """
        Initialize zone manager.
        
        Args:
            enter_time: Seconds hand must be raised before entering active zone
            exit_time: Seconds hand must be lowered before returning to rest zone
        """
        self.enter_time = enter_time
        self.exit_time = exit_time
        
        self.state = self.REST
        self.transition_start_time = None
        
        # For tracking hand position
        self.current_wrist_y = None
        self.current_shoulder_y = None
    
    def update(self, wrist_y, shoulder_y):
        """
        Update zone state based on current hand and shoulder positions.
        
        Args:
            wrist_y: Normalized Y position of wrist (0-1, lower = higher on screen)
            shoulder_y: Normalized Y position of shoulders (0-1)
            
        Returns:
            Current state string: "rest", "active", "transitioning_up", "transitioning_down"
        """
        self.current_wrist_y = wrist_y
        self.current_shoulder_y = shoulder_y
        
        if wrist_y is None or shoulder_y is None:
            # No hand or shoulder detected — go to rest
            self.state = self.REST
            self.transition_start_time = None
            return self.state
        
        # Determine if hand is above shoulder (active position)
        is_hand_raised = wrist_y < shoulder_y
        
        now = time.time()
        
        if self.state == self.REST:
            if is_hand_raised:
                # Start transition to active
                self.state = self.TRANSITIONING_UP
                self.transition_start_time = now
        
        elif self.state == self.TRANSITIONING_UP:
            if not is_hand_raised:
                # Hand dropped before timer expired
                self.state = self.REST
                self.transition_start_time = None
            elif now - self.transition_start_time >= self.enter_time:
                # Timer complete — enter active zone
                self.state = self.ACTIVE
                self.transition_start_time = None
        
        elif self.state == self.ACTIVE:
            if not is_hand_raised:
                # Start transition to rest
                self.state = self.TRANSITIONING_DOWN
                self.transition_start_time = now
        
        elif self.state == self.TRANSITIONING_DOWN:
            if is_hand_raised:
                # Hand raised again before timer expired
                self.state = self.ACTIVE
                self.transition_start_time = None
            elif now - self.transition_start_time >= self.exit_time:
                # Timer complete — return to rest
                self.state = self.REST
                self.transition_start_time = None
        
        return self.state
    
    def is_active(self):
        """Check if currently in active zone."""
        return self.state == self.ACTIVE
    
    def is_rest(self):
        """Check if currently in rest zone."""
        return self.state == self.REST
    
    def is_transitioning(self):
        """Check if currently transitioning between zones."""
        return self.state in [self.TRANSITIONING_UP, self.TRANSITIONING_DOWN]
    
    def get_state(self):
        """Get current state string."""
        return self.state
    
    def reset(self):
        """Reset to rest state."""
        self.state = self.REST
        self.transition_start_time = None