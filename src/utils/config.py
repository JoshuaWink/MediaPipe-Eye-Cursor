import json
import os
from typing import Optional
import mediapipe as mp

class Config:
    """Configuration management for the eye tracking application."""
    
    def __init__(self):
        """Initialize configuration with default values."""
        self.camera_index = 0
        self.calibration_points = 5
        self.model_path = self._get_default_model_path()
        self.confidence_threshold = 0.5
        self.tracking_confidence = 0.5
        self.presence_threshold = 0.5
    
    def _get_default_model_path(self) -> str:
        """Get the default MediaPipe face landmarker model path."""
        # Use the downloaded model in the models directory
        return "models/face_landmarker.task"
    
    def save(self, filepath: str) -> None:
        """Save configuration to a JSON file."""
        config_data = {
            'camera_index': self.camera_index,
            'calibration_points': self.calibration_points,
            'model_path': self.model_path,
            'confidence_threshold': self.confidence_threshold,
            'tracking_confidence': self.tracking_confidence,
            'presence_threshold': self.presence_threshold
        }
        
        # Only create directory if filepath contains a directory
        directory = os.path.dirname(filepath)
        if directory:
            os.makedirs(directory, exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump(config_data, f, indent=2)
    
    @classmethod
    def load(cls, filepath: str) -> 'Config':
        """Load configuration from a JSON file."""
        config = cls()
        
        if not os.path.exists(filepath):
            return config
        
        try:
            with open(filepath, 'r') as f:
                config_data = json.load(f)
            
            config.camera_index = config_data.get('camera_index', config.camera_index)
            config.calibration_points = config_data.get('calibration_points', config.calibration_points)
            config.model_path = config_data.get('model_path', config.model_path)
            config.confidence_threshold = config_data.get('confidence_threshold', config.confidence_threshold)
            config.tracking_confidence = config_data.get('tracking_confidence', config.tracking_confidence)
            config.presence_threshold = config_data.get('presence_threshold', config.presence_threshold)
            
        except (json.JSONDecodeError, IOError):
            # Return default config if file is corrupted
            pass
        
        return config
