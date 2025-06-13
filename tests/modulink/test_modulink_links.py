import pytest
import numpy as np
from unittest.mock import Mock, AsyncMock
from modulink import Ctx, create_context
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

from src.modulink_eye_tracker import (
    initialize_config_link,
    initialize_detector_link,
    capture_frame_link,
    detect_eyes_link,
    format_output_link,
    display_output_link,
    update_frame_count_link,
    cleanup_resources_link
)

class TestModuLinkLinks:
    """Test individual ModuLink links - demonstrates how easy testing becomes."""
    
    @pytest.mark.asyncio
    async def test_initialize_config_link_default(self):
        """Test config initialization with default values."""
        ctx = create_context(trigger="test")
        result = await initialize_config_link(ctx)
        
        assert 'config' in result
        assert result['status'] == 'config_loaded'
        assert result['config'].camera_index == 0
        assert 'models/face_landmarker.task' in result['config'].model_path
    
    @pytest.mark.asyncio
    async def test_initialize_config_link_with_overrides(self):
        """Test config initialization with context overrides."""
        ctx = create_context(
            trigger="test",
            camera_index=1,
            confidence_threshold=0.8
        )
        result = await initialize_config_link(ctx)
        
        assert result['config'].camera_index == 1
        assert result['config'].confidence_threshold == 0.8
    
    @pytest.mark.asyncio
    async def test_initialize_detector_link_success(self):
        """Test detector initialization success case."""
        # Create mock config
        mock_config = Mock()
        mock_config.model_path = "models/face_landmarker.task"
        mock_config.confidence_threshold = 0.5
        mock_config.tracking_confidence = 0.5
        mock_config.presence_threshold = 0.5
        
        ctx = create_context(trigger="test", config=mock_config)
        
        # This will actually initialize the detector, so we need the model file
        result = await initialize_detector_link(ctx)
        
        assert 'detector' in result
        assert result['status'] == 'detector_ready'
        assert 'error' not in result
    
    @pytest.mark.asyncio
    async def test_initialize_detector_link_no_config(self):
        """Test detector initialization failure when no config."""
        ctx = create_context(trigger="test")
        result = await initialize_detector_link(ctx)
        
        assert 'error' in result
        assert result['status'] == 'detector_failed'
        assert 'Configuration not found' in str(result['error'])
    
    @pytest.mark.asyncio
    async def test_capture_frame_link_success(self):
        """Test successful frame capture."""
        # Mock camera
        mock_camera = Mock()
        mock_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        mock_camera.read.return_value = (True, mock_frame)
        
        ctx = create_context(trigger="test", camera=mock_camera)
        result = await capture_frame_link(ctx)
        
        assert 'frame' in result
        assert result['frame_captured'] is True
        assert result['frame'].shape == (480, 640, 3)
        mock_camera.read.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_capture_frame_link_failure(self):
        """Test frame capture failure."""
        # Mock camera that fails to read
        mock_camera = Mock()
        mock_camera.read.return_value = (False, None)
        
        ctx = create_context(trigger="test", camera=mock_camera)
        result = await capture_frame_link(ctx)
        
        assert 'error' in result
        assert result['frame_captured'] is False
    
    @pytest.mark.asyncio
    async def test_detect_eyes_link_with_mock_detector(self):
        """Test eye detection with mocked detector."""
        # Mock detector
        mock_detector = Mock()
        mock_detection_result = {
            'face_detected': True,
            'gaze_direction': (0.5, -0.3),
            'left_eye': {'center': (0.4, 0.3)},
            'right_eye': {'center': (0.6, 0.3)}
        }
        mock_detector.process_image.return_value = mock_detection_result
        
        # Mock frame
        mock_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        ctx = create_context(
            trigger="test",
            detector=mock_detector,
            frame=mock_frame
        )
        
        result = await detect_eyes_link(ctx)
        
        assert result['face_detected'] is True
        assert result['gaze_direction'] == (0.5, -0.3)
        assert result['left_eye']['center'] == (0.4, 0.3)
        assert result['right_eye']['center'] == (0.6, 0.3)
        mock_detector.process_image.assert_called_once_with(mock_frame)
    
    @pytest.mark.asyncio
    async def test_detect_eyes_link_no_detector(self):
        """Test eye detection when detector is missing."""
        ctx = create_context(
            trigger="test",
            frame=np.zeros((480, 640, 3), dtype=np.uint8)
        )
        result = await detect_eyes_link(ctx)
        
        assert 'error' in result
        assert 'Detector not found' in str(result['error'])
    
    @pytest.mark.asyncio
    async def test_format_output_link_with_face(self):
        """Test output formatting when face is detected."""
        ctx = create_context(
            trigger="test",
            face_detected=True,
            gaze_direction=(0.75, -0.25),
            left_eye={'center': (0.4, 0.3)},
            right_eye={'center': (0.6, 0.3)},
            frame_count=42
        )
        
        result = await format_output_link(ctx)
        
        formatted = result['formatted_output']
        assert 'Frame 0042:' in formatted
        assert 'Face detected: True' in formatted
        assert 'Gaze direction: (0.75, -0.25)' in formatted
        assert 'Left eye center: (0.40, 0.30)' in formatted
        assert 'Right eye center: (0.60, 0.30)' in formatted
    
    @pytest.mark.asyncio
    async def test_format_output_link_no_face(self):
        """Test output formatting when no face is detected."""
        ctx = create_context(
            trigger="test",
            face_detected=False,
            gaze_direction=(0.0, 0.0),
            left_eye=None,
            right_eye=None,
            frame_count=1
        )
        
        result = await format_output_link(ctx)
        
        formatted = result['formatted_output']
        assert 'Frame 0001:' in formatted
        assert 'Face detected: False' in formatted
        assert 'No face detected' in formatted
    
    @pytest.mark.asyncio
    async def test_update_frame_count_link(self):
        """Test frame count incrementing."""
        # Test starting from 0
        ctx = create_context(trigger="test")
        result = await update_frame_count_link(ctx)
        assert result['frame_count'] == 1
        
        # Test incrementing existing count
        ctx = create_context(trigger="test", frame_count=42)
        result = await update_frame_count_link(ctx)
        assert result['frame_count'] == 43
    
    @pytest.mark.asyncio
    async def test_cleanup_resources_link(self):
        """Test resource cleanup."""
        # Mock camera and detector
        mock_camera = Mock()
        mock_detector = Mock()
        
        ctx = create_context(
            trigger="test",
            camera=mock_camera,
            detector=mock_detector
        )
        
        result = await cleanup_resources_link(ctx)
        
        assert result['cleanup_complete'] is True
        assert result['status'] == 'cleaned_up'
        mock_camera.release.assert_called_once()
        mock_detector.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cleanup_resources_link_no_resources(self):
        """Test cleanup when no resources present."""
        ctx = create_context(trigger="test")
        result = await cleanup_resources_link(ctx)
        
        assert result['cleanup_complete'] is True
        assert result['status'] == 'cleaned_up'

class TestModuLinkComposition:
    """Test ModuLink chain composition and context flow."""
    
    @pytest.mark.asyncio
    async def test_simple_chain_composition(self):
        """Test composing multiple links into a chain."""
        from modulink import chain
        
        # Create a simple chain with mocked components
        mock_detector = Mock()
        mock_detector.process_image.return_value = {
            'face_detected': False,
            'gaze_direction': (0.0, 0.0),
            'left_eye': None,
            'right_eye': None
        }
        
        mock_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Chain: update frame count -> detect eyes -> format output
        processing_chain = chain(
            update_frame_count_link,
            detect_eyes_link,
            format_output_link
        )
        
        ctx = create_context(
            trigger="test",
            detector=mock_detector,
            frame=mock_frame,
            frame_count=0
        )
        
        result = await processing_chain(ctx)
        
        # Verify the chain executed all links
        assert result['frame_count'] == 1
        assert result['face_detected'] is False
        assert 'formatted_output' in result
        assert 'Frame 0001:' in result['formatted_output']
    
    @pytest.mark.asyncio
    async def test_error_propagation_in_chain(self):
        """Test that errors propagate through the chain correctly."""
        from modulink import chain
        
        # Create a chain where the first link will fail
        processing_chain = chain(
            detect_eyes_link,  # This will fail due to missing detector
            format_output_link
        )
        
        ctx = create_context(
            trigger="test",
            frame=np.zeros((480, 640, 3), dtype=np.uint8)
            # Note: no detector provided, will cause error
        )
        
        result = await processing_chain(ctx)
        
        # Error should be present and subsequent links should not execute
        assert 'error' in result
        assert 'Detector not found' in str(result['error'])
        # format_output_link should not have executed due to error
        assert 'formatted_output' not in result

class TestModuLinkContextFlow:
    """Test how context flows through ModuLink chains."""
    
    @pytest.mark.asyncio
    async def test_context_immutability(self):
        """Test that links don't mutate the original context."""
        original_ctx = create_context(trigger="test", frame_count=5)
        
        # Store the original state
        original_frame_count = original_ctx['frame_count']
        
        # Run a link that modifies frame_count
        result = await update_frame_count_link(original_ctx)
        
        # Original context should be unchanged
        assert original_ctx['frame_count'] == original_frame_count
        # Result should have the updated value
        assert result['frame_count'] == original_frame_count + 1
    
    @pytest.mark.asyncio
    async def test_context_accumulation(self):
        """Test that context accumulates data as it flows through links."""
        from modulink import chain
        
        # Mock components
        mock_detector = Mock()
        mock_detector.process_image.return_value = {
            'face_detected': True,
            'gaze_direction': (0.1, 0.2),
            'left_eye': {'center': (0.3, 0.4)},
            'right_eye': {'center': (0.5, 0.6)}
        }
        
        # Create chain
        accumulation_chain = chain(
            update_frame_count_link,
            detect_eyes_link,
            format_output_link
        )
        
        initial_ctx = create_context(
            trigger="test",
            detector=mock_detector,
            frame=np.zeros((480, 640, 3), dtype=np.uint8),
            initial_value="preserved"
        )
        
        result = await accumulation_chain(initial_ctx)
        
        # Check that all data is preserved and accumulated
        assert result['trigger'] == 'test'  # Original data preserved
        assert result['initial_value'] == 'preserved'  # Custom data preserved
        assert result['frame_count'] == 1  # Added by update_frame_count_link
        assert result['face_detected'] is True  # Added by detect_eyes_link
        assert result['gaze_direction'] == (0.1, 0.2)  # Added by detect_eyes_link
        assert 'formatted_output' in result  # Added by format_output_link
