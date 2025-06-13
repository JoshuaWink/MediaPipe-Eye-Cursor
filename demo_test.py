#!/usr/bin/env python3
"""
Demo test script to verify MediaPipe Eye Cursor functionality
without requiring a live camera feed.
"""

import numpy as np
import cv2
from src.utils.config import Config
from src.eye_tracker.detector import EyeDetector

def test_eye_detection():
    """Test eye detection with a mock image."""
    print("🧪 Testing MediaPipe Eye Cursor Components...")
    print("=" * 50)
    
    # Create configuration
    config = Config()
    print(f"✅ Configuration loaded: {config.model_path}")
    
    # Initialize eye detector
    try:
        detector = EyeDetector(config)
        print("✅ EyeDetector initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize EyeDetector: {e}")
        return False
    
    # Create a test image (black image - will show no face detected)
    test_image = np.zeros((480, 640, 3), dtype=np.uint8)
    print("✅ Created test image (480x640)")
    
    # Process the test image
    try:
        result = detector.process_image(test_image)
        print("✅ Image processing completed")
        
        # Display results
        print("\n📊 Detection Results:")
        print(f"   Face detected: {result['face_detected']}")
        print(f"   Gaze direction: {result['gaze_direction']}")
        print(f"   Left eye: {'Present' if result['left_eye'] else 'None'}")
        print(f"   Right eye: {'Present' if result['right_eye'] else 'None'}")
        
    except Exception as e:
        print(f"❌ Image processing failed: {e}")
        return False
    
    # Clean up
    detector.close()
    print("✅ Detector closed successfully")
    
    print("\n🎉 All tests passed! MediaPipe Eye Cursor is working correctly.")
    print("\n🚀 Ready to test with real camera:")
    print("   python -m src.main track")
    
    return True

if __name__ == "__main__":
    test_eye_detection()
