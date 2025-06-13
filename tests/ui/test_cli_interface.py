import pytest
from unittest.mock import Mock, patch
from src.ui.cli_interface import CLIInterface
from src.utils.config import Config

class TestCLIInterface:
    
    @pytest.fixture
    def mock_config(self):
        """Create a mock config for testing."""
        config = Config()
        config.model_path = "models/face_landmarker.task"
        return config
    
    def test_cli_initialization(self, mock_config):
        """Test that CLI can be initialized properly."""
        cli = CLIInterface(mock_config)
        assert cli.config == mock_config
        assert cli.eye_detector is not None
    
    @patch('cv2.VideoCapture')
    def test_cli_start_camera(self, mock_video_capture, mock_config):
        """Test camera initialization."""
        mock_cap = Mock()
        mock_video_capture.return_value = mock_cap
        mock_cap.isOpened.return_value = True
        
        cli = CLIInterface(mock_config)
        success = cli._initialize_camera()
        
        assert success is True
        mock_video_capture.assert_called_with(mock_config.camera_index)
    
    @patch('cv2.VideoCapture')
    def test_cli_camera_failure(self, mock_video_capture, mock_config):
        """Test camera initialization failure."""
        mock_cap = Mock()
        mock_video_capture.return_value = mock_cap
        mock_cap.isOpened.return_value = False
        
        cli = CLIInterface(mock_config)
        success = cli._initialize_camera()
        
        assert success is False
    
    def test_cli_format_gaze_output(self, mock_config):
        """Test gaze output formatting."""
        cli = CLIInterface(mock_config)
        
        gaze_data = {
            'face_detected': True,
            'gaze_direction': (0.5, -0.3),
            'left_eye': {'center': (0.4, 0.3)},
            'right_eye': {'center': (0.6, 0.3)}
        }
        
        output = cli._format_gaze_output(gaze_data)
        
        assert "Face detected: True" in output
        assert "Gaze direction: (0.50, -0.30)" in output
        assert "Left eye center: (0.40, 0.30)" in output
        assert "Right eye center: (0.60, 0.30)" in output
    
    def test_cli_format_no_face_output(self, mock_config):
        """Test output formatting when no face is detected."""
        cli = CLIInterface(mock_config)
        
        gaze_data = {
            'face_detected': False,
            'gaze_direction': (0.0, 0.0),
            'left_eye': None,
            'right_eye': None
        }
        
        output = cli._format_gaze_output(gaze_data)
        
        assert "Face detected: False" in output
        assert "No face detected" in output
