"""
HandiSlide - PowerPoint COM Integration Module
Provides deep integration with Microsoft PowerPoint via COM automation.
Enables drawing, erasing, and managing annotations directly on slides.
"""

import pythoncom
import win32com.client
import time

class PowerPointController:
    def __init__(self):
        """Initialize PowerPoint COM controller."""
        self.app = None
        self.is_connected = False
        self.annotation_shapes = []  # Stack for undo
        self.erased_shapes = []      # Stack for undo erase
        
        # Try to initialize COM
        try:
            pythoncom.CoInitialize()
        except:
            pass
    
    def connect(self):
        """
        Connect to a running PowerPoint instance or launch a new one.
        
        Returns:
            True if connected successfully, False otherwise
        """
        try:
            try:
                # Try to connect to running instance
                self.app = win32com.client.GetActiveObject("PowerPoint.Application")
                print("[PowerPoint] Connected to running instance")
            except:
                # Launch new instance
                self.app = win32com.client.Dispatch("PowerPoint.Application")
                self.app.Visible = True
                print("[PowerPoint] Launched new instance")
            
            self.is_connected = True
            return True
        except Exception as e:
            print(f"[PowerPoint] Connection failed: {e}")
            self.is_connected = False
            return False
    
    def is_available(self):
        """Check if PowerPoint COM is available."""
        return self.is_connected and self.app is not None
    
    def get_presentation(self):
        """Get the active presentation object."""
        if not self.is_available():
            return None
        try:
            return self.app.ActivePresentation
        except:
            return None
    
    def get_current_slide(self):
        """Get the current slide (in slideshow or editor view)."""
        if not self.is_available():
            return None
        try:
            # Try slideshow view first
            if self.app.SlideShowWindows.Count > 0:
                window = self.app.SlideShowWindows(1)
                return window.View.Slide
            else:
                # Editor view
                window = self.app.ActiveWindow
                if window is not None:
                    return window.View.Slide
        except:
            pass
        return None
    
    def is_slideshow_running(self):
        """Check if a slideshow is currently active."""
        if not self.is_available():
            return False
        try:
            return self.app.SlideShowWindows.Count > 0
        except:
            return False
    
    def start_slideshow(self):
        """Start slideshow from the current slide."""
        if not self.is_available():
            return False
        try:
            presentation = self.get_presentation()
            if presentation:
                presentation.SlideShowSettings.Run()
                return True
        except Exception as e:
            print(f"[PowerPoint] Start slideshow failed: {e}")
        return False
    
    def end_slideshow(self):
        """End the current slideshow."""
        if not self.is_available():
            return False
        try:
            if self.app.SlideShowWindows.Count > 0:
                self.app.SlideShowWindows(1).View.Exit()
                return True
        except:
            pass
        return False
    
    def next_slide(self):
        """Advance to next slide or next animation build."""
        if not self.is_available():
            return False
        try:
            if self.app.SlideShowWindows.Count > 0:
                self.app.SlideShowWindows(1).View.Next()
                return True
        except:
            pass
        return False
    
    def previous_slide(self):
        """Go to previous slide."""
        if not self.is_available():
            return False
        try:
            if self.app.SlideShowWindows.Count > 0:
                self.app.SlideShowWindows(1).View.Previous()
                return True
        except:
            pass
        return False
    
    def draw_line(self, start_x, start_y, end_x, end_y, color_rgb=(255, 0, 0), line_width=3):
        """
        Draw a line on the current slide.
        
        Args:
            start_x, start_y: Start position in points (1/72 inch)
            end_x, end_y: End position in points
            color_rgb: (R, G, B) tuple (0-255)
            line_width: Line thickness in points
            
        Returns:
            Shape object if successful, None otherwise
        """
        slide = self.get_current_slide()
        if slide is None:
            return None
        
        try:
            # Convert RGB to BGR format used by PowerPoint
            color = color_rgb[0] | (color_rgb[1] << 8) | (color_rgb[2] << 16)
            
            # Add line shape
            line = slide.Shapes.AddLine(start_x, start_y, end_x, end_y)
            line.Line.ForeColor.RGB = color
            line.Line.Weight = line_width
            
            # Tag the shape so we know it was added by HandiSlide
            line.Tags.Add("AddedBy", "HandiSlide")
            line.Tags.Add("Type", "Annotation")
            
            # Add to undo stack
            self.annotation_shapes.append(line)
            
            return line
        except Exception as e:
            print(f"[PowerPoint] Draw line failed: {e}")
            return None
    
    def draw_circle(self, center_x, center_y, radius=10, color_rgb=(255, 0, 0)):
        """
        Draw a circle/dot on the slide.
        
        Args:
            center_x, center_y: Center position in points
            radius: Circle radius in points
            color_rgb: (R, G, B) tuple
            
        Returns:
            Shape object if successful, None otherwise
        """
        slide = self.get_current_slide()
        if slide is None:
            return None
        
        try:
            color = color_rgb[0] | (color_rgb[1] << 8) | (color_rgb[2] << 16)
            
            # Add oval shape (circle)
            shape = slide.Shapes.AddShape(
                9,  # msoShapeOval = 9
                center_x - radius,
                center_y - radius,
                radius * 2,
                radius * 2
            )
            shape.Fill.ForeColor.RGB = color
            shape.Line.Visible = 0  # No outline
            
            # Tag the shape
            shape.Tags.Add("AddedBy", "HandiSlide")
            shape.Tags.Add("Type", "Annotation")
            
            # Add to undo stack
            self.annotation_shapes.append(shape)
            
            return shape
        except Exception as e:
            print(f"[PowerPoint] Draw circle failed: {e}")
            return None
    
    def erase_at_position(self, x, y, threshold=20):
        """
        Erase annotation shapes near the given position.
        
        Args:
            x, y: Position in points
            threshold: Distance threshold for erasing (points)
            
        Returns:
            Number of shapes erased
        """
        slide = self.get_current_slide()
        if slide is None:
            return 0
        
        erased_count = 0
        shapes_to_delete = []
        
        try:
            for shape in slide.Shapes:
                try:
                    # Only erase shapes added by HandiSlide
                    if shape.Tags.Item("AddedBy") == "HandiSlide":
                        # Check if position is near the shape
                        shape_center_x = shape.Left + shape.Width / 2
                        shape_center_y = shape.Top + shape.Height / 2
                        
                        distance = ((x - shape_center_x)**2 + (y - shape_center_y)**2)**0.5
                        
                        if distance < threshold:
                            shapes_to_delete.append(shape)
                except:
                    # Shape might not have our tags, skip it
                    continue
            
            # Delete the shapes
            for shape in shapes_to_delete:
                self.erased_shapes.append(shape)  # Save for potential undo
                shape.Delete()
                erased_count += 1
                # Remove from annotation stack if present
                if shape in self.annotation_shapes:
                    self.annotation_shapes.remove(shape)
        
        except Exception as e:
            print(f"[PowerPoint] Erase failed: {e}")
        
        return erased_count
    
    def undo_last(self):
        """
        Undo the last annotation (remove it from slide).
        
        Returns:
            True if an annotation was undone
        """
        if len(self.annotation_shapes) == 0:
            return False
        
        try:
            shape = self.annotation_shapes.pop()
            self.erased_shapes.append(shape)  # Save for redo
            shape.Delete()
            return True
        except Exception as e:
            print(f"[PowerPoint] Undo failed: {e}")
            return False
    
    def undo_erase(self):
        """
        Restore the last erased shape (if possible).
        
        Note: Full restore is complex with COM. This is a best-effort.
        
        Returns:
            True if an erase was undone
        """
        # COM doesn't easily support restoring deleted shapes
        # This is a placeholder for future implementation
        print("[PowerPoint] Undo erase: full restore not supported")
        return False
    
    def clear_all_annotations(self):
        """
        Remove all HandiSlide annotations from the current slide.
        
        Returns:
            Number of shapes removed
        """
        slide = self.get_current_slide()
        if slide is None:
            return 0
        
        removed_count = 0
        shapes_to_delete = []
        
        try:
            for shape in slide.Shapes:
                try:
                    if shape.Tags.Item("AddedBy") == "HandiSlide":
                        shapes_to_delete.append(shape)
                except:
                    continue
            
            for shape in shapes_to_delete:
                shape.Delete()
                removed_count += 1
            
            # Clear undo stacks
            self.annotation_shapes.clear()
            self.erased_shapes.clear()
        
        except Exception as e:
            print(f"[PowerPoint] Clear all failed: {e}")
        
        return removed_count
    
    def get_slide_dimensions(self):
        """
        Get the dimensions of the current slide.
        
        Returns:
            (width, height) tuple in points, or (960, 540) as default
        """
        presentation = self.get_presentation()
        if presentation is None:
            return (960, 540)  # Default 16:9
        
        try:
            return (presentation.PageSetup.SlideWidth, presentation.PageSetup.SlideHeight)
        except:
            return (960, 540)
    
    def disconnect(self):
        """Disconnect from PowerPoint."""
        self.is_connected = False
        self.app = None
        self.annotation_shapes.clear()
        self.erased_shapes.clear()
        print("[PowerPoint] Disconnected")