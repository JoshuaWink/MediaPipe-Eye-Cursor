import cv2
import numpy as np
import mediapipe as mp
from typing import Dict, List, Tuple, Optional
from src.utils.config import Config

class EyeDetector:
    """MediaPipe-based eye detection and gaze estimation."""
    
    # MediaPipe face mesh landmark indices for eyes
    LEFT_EYE_LANDMARKS = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246]
    RIGHT_EYE_LANDMARKS = [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398]
    
    def __init__(self, config: Config):
        """Initialize the eye detector with MediaPipe face landmarker."""
        self.config = config
        self.landmarker = self._create_landmarker()
    
    def _create_landmarker(self):
        """Create MediaPipe face landmarker instance."""
        BaseOptions = mp.tasks.BaseOptions
        FaceLandmarker = mp.tasks.vision.FaceLandmarker
        FaceLandmarkerOptions = mp.tasks.vision.FaceLandmarkerOptions
        VisionRunningMode = mp.tasks.vision.RunningMode
        
        options = FaceLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=self.config.model_path),
            running_mode=VisionRunningMode.IMAGE,
            num_faces=1,
            min_face_detection_confidence=self.config.confidence_threshold,
            min_face_presence_confidence=self.config.presence_threshold,
            min_tracking_confidence=self.config.tracking_confidence
        )
        
        return FaceLandmarker.create_from_options(options)
    
    def process_image(self, image: np.ndarray) -> Dict:
        """Process an image and extract eye landmarks and gaze direction."""
        # Convert BGR to RGB (MediaPipe expects RGB)
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_image)
        
        # Detect face landmarks
        result = self.landmarker.detect(mp_image)
        
        if not result.face_landmarks:
            return {
                'face_detected': False,
                'left_eye': None,
                'right_eye': None,
                'gaze_direction': (0.0, 0.0)
            }
        
        # Extract eye landmarks from the first detected face
        face_landmarks = result.face_landmarks[0]
        left_eye, right_eye = self._extract_eye_landmarks(face_landmarks)
        
        # Calculate gaze direction
        gaze_x, gaze_y = self._calculate_gaze_direction(left_eye, right_eye)
        
        return {
            'face_detected': True,
            'left_eye': left_eye,
            'right_eye': right_eye,
            'gaze_direction': (gaze_x, gaze_y)
        }
    
    def _extract_eye_landmarks(self, face_landmarks) -> Tuple[Dict, Dict]:
        """Extract eye landmark coordinates from face landmarks."""
        left_eye_points = []
        right_eye_points = []
        
        # Extract left eye landmarks
        for idx in self.LEFT_EYE_LANDMARKS:
            landmark = face_landmarks.landmark[idx]
            left_eye_points.append((landmark.x, landmark.y))
        
        # Extract right eye landmarks
        for idx in self.RIGHT_EYE_LANDMARKS:
            landmark = face_landmarks.landmark[idx]
            right_eye_points.append((landmark.x, landmark.y))
        
        # Calculate eye centers
        left_eye_center = self._calculate_center(left_eye_points)
        right_eye_center = self._calculate_center(right_eye_points)
        
        left_eye = {
            'center': left_eye_center,
            'landmarks': left_eye_points
        }
        
        right_eye = {
            'center': right_eye_center,
            'landmarks': right_eye_points
        }
        
        return left_eye, right_eye
    
    def _calculate_center(self, points: List[Tuple[float, float]]) -> Tuple[float, float]:
        """Calculate the center point of a list of coordinates."""
        if not points:
            return (0.0, 0.0)
        
        x_coords = [p[0] for p in points]
        y_coords = [p[1] for p in points]
        
        center_x = sum(x_coords) / len(x_coords)
        center_y = sum(y_coords) / len(y_coords)
        
        return (center_x, center_y)
    
    def _calculate_gaze_direction(self, left_eye: Dict, right_eye: Dict) -> Tuple[float, float]:
        """Calculate gaze direction based on eye positions."""
        if not left_eye or not right_eye:
            return (0.0, 0.0)
        
        # Simple gaze estimation based on eye centers
        # This is a basic implementation - more sophisticated methods would analyze
        # pupil position relative to eye corners
        
        left_center = left_eye['center']
        right_center = right_eye['center']
        
        # Calculate the midpoint between eyes
        eye_midpoint_x = (left_center[0] + right_center[0]) / 2
        eye_midpoint_y = (left_center[1] + right_center[1]) / 2
        
        # Normalize to screen coordinates (-1 to 1)
        # This is a simplified mapping that will be improved with calibration
        gaze_x = (eye_midpoint_x - 0.5) * 2  # Convert from 0-1 to -1-1
        gaze_y = (eye_midpoint_y - 0.5) * 2  # Convert from 0-1 to -1-1
        
        # Clamp values to [-1, 1]
        gaze_x = max(-1.0, min(1.0, gaze_x))
        gaze_y = max(-1.0, min(1.0, gaze_y))
        
        return (gaze_x, gaze_y)
    
    def close(self):
        """Clean up resources."""
        if hasattr(self.landmarker, 'close'):
            self.landmarker.close()
