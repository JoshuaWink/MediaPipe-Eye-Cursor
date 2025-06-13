import cv2
import time
import sys
from typing import Dict, Optional
from src.eye_tracker.detector import EyeDetector
from src.utils.config import Config

class CLIInterface:
    """Command line interface for the eye tracking application."""
    
    def __init__(self, config: Config):
        """Initialize the CLI interface."""
        self.config = config
        self.eye_detector = EyeDetector(config)
        self.cap = None
        self.running = False
    
    def _initialize_camera(self) -> bool:
        """Initialize the camera capture."""
        self.cap = cv2.VideoCapture(self.config.camera_index)
        
        if not self.cap.isOpened():
            print(f"Error: Could not open camera {self.config.camera_index}")
            return False
        
        # Set camera properties for better performance
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        
        print(f"Camera {self.config.camera_index} initialized successfully")
        return True
    
    def _format_gaze_output(self, gaze_data: Dict) -> str:
        """Format gaze data for console output."""
        lines = []
        lines.append(f"Face detected: {gaze_data['face_detected']}")
        
        if gaze_data['face_detected']:
            gaze_x, gaze_y = gaze_data['gaze_direction']
            lines.append(f"Gaze direction: ({gaze_x:.2f}, {gaze_y:.2f})")
            
            if gaze_data['left_eye']:
                left_center = gaze_data['left_eye']['center']
                lines.append(f"Left eye center: ({left_center[0]:.2f}, {left_center[1]:.2f})")
            
            if gaze_data['right_eye']:
                right_center = gaze_data['right_eye']['center']
                lines.append(f"Right eye center: ({right_center[0]:.2f}, {right_center[1]:.2f})")
        else:
            lines.append("No face detected")
        
        return " | ".join(lines)
    
    def _clear_line(self):
        """Clear the current line in the terminal."""
        print('\r' + ' ' * 80, end='')
        print('\r', end='')
    
    def start_tracking(self):
        """Start the eye tracking process."""
        if not self._initialize_camera():
            return False
        
        print("Starting eye tracking... Press 'q' to quit")
        print("=" * 60)
        
        self.running = True
        frame_count = 0
        start_time = time.time()
        
        try:
            while self.running:
                ret, frame = self.cap.read()
                
                if not ret:
                    print("Error: Could not read frame from camera")
                    break
                
                # Process the frame
                gaze_data = self.eye_detector.process_image(frame)
                
                # Update display
                self._clear_line()
                output = self._format_gaze_output(gaze_data)
                print(f"Frame {frame_count:04d}: {output}", end='', flush=True)
                
                frame_count += 1
                
                # Calculate and display FPS every 30 frames
                if frame_count % 30 == 0:
                    elapsed = time.time() - start_time
                    fps = frame_count / elapsed
                    print(f" | FPS: {fps:.1f}", end='', flush=True)
                
                # Check for quit condition (this is simplified for CLI)
                # In a real implementation, you'd use keyboard input handling
                time.sleep(0.033)  # ~30 FPS
                
        except KeyboardInterrupt:
            print("\nStopping eye tracking...")
        
        finally:
            self.stop_tracking()
        
        return True
    
    def stop_tracking(self):
        """Stop the eye tracking process."""
        self.running = False
        
        if self.cap:
            self.cap.release()
        
        if self.eye_detector:
            self.eye_detector.close()
        
        print("\nEye tracking stopped")
    
    def run_calibration_mode(self):
        """Run calibration mode (placeholder for now)."""
        print("Calibration mode not implemented yet")
        print("This will be implemented in the next phase")
    
    def show_help(self):
        """Show help information."""
        help_text = """
MediaPipe Eye Cursor - Command Line Interface

Commands:
  track       Start eye tracking
  calibrate   Run calibration mode (coming soon)
  help        Show this help message
  quit        Exit the application

During tracking:
  - The application will show real-time gaze direction
  - Press Ctrl+C to stop tracking
  
Configuration:
  - Camera index: {camera_index}
  - Model path: {model_path}
  - Calibration points: {calibration_points}
        """.format(
            camera_index=self.config.camera_index,
            model_path=self.config.model_path,
            calibration_points=self.config.calibration_points
        )
        print(help_text)
