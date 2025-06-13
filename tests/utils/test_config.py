import pytest
import os
import json
from src.utils.config import Config


class TestConfig:
    def test_config_initialization(self):
        """Test that Config can be initialized with default values."""
        config = Config()
        assert config.camera_index == 0
        assert config.model_path is not None
        assert config.calibration_points == 5
    
    def test_config_save_and_load(self, tmp_path):
        """Test saving and loading configuration."""
        config = Config()
        config.camera_index = 1
        config.calibration_points = 9
        
        config_file = tmp_path / "test_config.json"
        config.save(str(config_file))
        
        # Load configuration
        loaded_config = Config.load(str(config_file))
        assert loaded_config.camera_index == 1
        assert loaded_config.calibration_points == 9
    
    def test_config_load_nonexistent_file(self):
        """Test loading from non-existent file returns default config."""
        config = Config.load("nonexistent.json")
        assert config.camera_index == 0
        assert config.calibration_points == 5
    
    def test_config_model_path_validation(self):
        """Test that model path is properly set."""
        config = Config()
        assert config.model_path.endswith(".task")
        assert "face_landmarker" in config.model_path
