import pytest
import numpy as np
import cv2
from unittest.mock import Mock, patch
from src.eye_tracker.detector import EyeDetector
from src.utils.config import Config

class TestEyeDetector:
    
    @pytest.fixture
    def mock_config(self):
        """Create a mock config for testing."""
        config = Config()
        config.model_path = "models/face_landmarker.task"
        return config
    
    @pytest.fixture
    def sample_image(self):
        """Create a sample image for testing."""
        # Create a simple 640x480 RGB image
        return np.zeros((480, 640, 3), dtype=np.uint8)
    
    def test_eye_detector_initialization(self, mock_config):
        """Test that EyeDetector can be initialized properly."""
        detector = EyeDetector(mock_config)
        assert detector.config == mock_config
        assert detector.landmarker is not None
    
    def test_eye_detector_process_image_no_face(self, mock_config, sample_image):
        """Test processing image with no face detected."""
        detector = EyeDetector(mock_config)
        result = detector.process_image(sample_image)
        
        assert result is not None
        assert 'left_eye' in result
        assert 'right_eye' in result
        assert 'face_detected' in result
        assert result['face_detected'] is False
    
    def test_eye_detector_extract_eye_landmarks(self, mock_config):
        """Test eye landmark extraction from face landmarks."""
        detector = EyeDetector(mock_config)
        
        # Mock face landmarks with basic eye coordinates
        mock_landmarks = Mock()
        mock_landmarks.landmark = [Mock() for _ in range(468)]  # MediaPipe has 468 face landmarks
        
        # Set some eye landmark coordinates
        for i in range(468):
            mock_landmarks.landmark[i].x = 0.5
            mock_landmarks.landmark[i].y = 0.5
            mock_landmarks.landmark[i].z = 0.0
        
        left_eye, right_eye = detector._extract_eye_landmarks(mock_landmarks)
        
        assert 'center' in left_eye
        assert 'center' in right_eye
        assert len(left_eye['landmarks']) > 0
        assert len(right_eye['landmarks']) > 0
    
    def test_eye_detector_calculate_gaze_direction(self, mock_config):
        """Test gaze direction calculation."""
        detector = EyeDetector(mock_config)
        
        # Mock eye data
        left_eye = {
            'center': (0.4, 0.3),
            'landmarks': [(0.4, 0.3) for _ in range(6)]
        }
        right_eye = {
            'center': (0.6, 0.3),
            'landmarks': [(0.6, 0.3) for _ in range(6)]
        }
        
        gaze_x, gaze_y = detector._calculate_gaze_direction(left_eye, right_eye)
        
        assert isinstance(gaze_x, float)
        assert isinstance(gaze_y, float)
        assert -1.0 <= gaze_x <= 1.0
        assert -1.0 <= gaze_y <= 1.0
