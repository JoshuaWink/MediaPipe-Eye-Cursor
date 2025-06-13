#!/usr/bin/env python3
"""
ModuLink-based MediaPipe Eye Cursor Implementation

This module demonstrates how to properly structure the eye tracking application
using ModuLink principles of function composition and context flow.
"""

import cv2
import numpy as np
from typing import Dict, Any
from modulink import Ctx, chain, create_context, create_cli_context
from src.eye_tracker.detector import EyeDetector
from src.utils.config import Config

# ==================== LINKS (Pure Functions) ====================

async def initialize_config_link(ctx: Ctx) -> Ctx:
    """Initialize configuration from context or defaults."""
    try:
        config_path = ctx.get('config_path', 'config.json')
        config = Config.load(config_path)
        
        # Override with context values if provided
        if ctx.get('camera_index') is not None:
            config.camera_index = ctx['camera_index']
        if ctx.get('model_path'):
            config.model_path = ctx['model_path']
        if ctx.get('confidence_threshold') is not None:
            config.confidence_threshold = ctx['confidence_threshold']
            
        return {**ctx, 'config': config, 'status': 'config_loaded'}
    except Exception as e:
        return {**ctx, 'error': e, 'status': 'config_failed'}

async def initialize_detector_link(ctx: Ctx) -> Ctx:
    """Initialize the eye detector with the loaded configuration."""
    try:
        config = ctx.get('config')
        if not config:
            raise ValueError("Configuration not found in context")
            
        detector = EyeDetector(config)
        return {**ctx, 'detector': detector, 'status': 'detector_ready'}
    except Exception as e:
        return {**ctx, 'error': e, 'status': 'detector_failed'}

async def initialize_camera_link(ctx: Ctx) -> Ctx:
    """Initialize camera capture."""
    try:
        config = ctx.get('config')
        if not config:
            raise ValueError("Configuration not found in context")
            
        cap = cv2.VideoCapture(config.camera_index)
        if not cap.isOpened():
            raise RuntimeError(f"Could not open camera {config.camera_index}")
            
        # Set camera properties
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 30)
        
        return {**ctx, 'camera': cap, 'status': 'camera_ready'}
    except Exception as e:
        return {**ctx, 'error': e, 'status': 'camera_failed'}

async def capture_frame_link(ctx: Ctx) -> Ctx:
    """Capture a single frame from the camera."""
    try:
        camera = ctx.get('camera')
        if not camera:
            raise ValueError("Camera not found in context")
            
        ret, frame = camera.read()
        if not ret:
            raise RuntimeError("Failed to capture frame from camera")
            
        return {**ctx, 'frame': frame, 'frame_captured': True}
    except Exception as e:
        return {**ctx, 'error': e, 'frame_captured': False}

async def detect_eyes_link(ctx: Ctx) -> Ctx:
    """Process frame and detect eyes/gaze direction."""
    try:
        detector = ctx.get('detector')
        frame = ctx.get('frame')
        
        if not detector:
            raise ValueError("Detector not found in context")
        if frame is None:
            raise ValueError("Frame not found in context")
            
        # Process the frame
        detection_result = detector.process_image(frame)
        
        return {
            **ctx, 
            'detection_result': detection_result,
            'face_detected': detection_result['face_detected'],
            'gaze_direction': detection_result['gaze_direction'],
            'left_eye': detection_result['left_eye'],
            'right_eye': detection_result['right_eye']
        }
    except Exception as e:
        return {**ctx, 'error': e}

async def format_output_link(ctx: Ctx) -> Ctx:
    """Format detection results for display."""
    try:
        face_detected = ctx.get('face_detected', False)
        gaze_direction = ctx.get('gaze_direction', (0.0, 0.0))
        left_eye = ctx.get('left_eye')
        right_eye = ctx.get('right_eye')
        frame_count = ctx.get('frame_count', 0)
        
        lines = []
        lines.append(f"Face detected: {face_detected}")
        
        if face_detected:
            gaze_x, gaze_y = gaze_direction
            lines.append(f"Gaze direction: ({gaze_x:.2f}, {gaze_y:.2f})")
            
            if left_eye:
                left_center = left_eye['center']
                lines.append(f"Left eye center: ({left_center[0]:.2f}, {left_center[1]:.2f})")
            
            if right_eye:
                right_center = right_eye['center']
                lines.append(f"Right eye center: ({right_center[0]:.2f}, {right_center[1]:.2f})")
        else:
            lines.append("No face detected")
        
        formatted_output = f"Frame {frame_count:04d}: " + " | ".join(lines)
        
        return {**ctx, 'formatted_output': formatted_output}
    except Exception as e:
        return {**ctx, 'error': e}

async def display_output_link(ctx: Ctx) -> Ctx:
    """Display the formatted output to console."""
    try:
        formatted_output = ctx.get('formatted_output')
        if formatted_output:
            # Clear line and print new output
            print('\r' + ' ' * 100, end='')
            print(f'\r{formatted_output}', end='', flush=True)
            
        return {**ctx, 'displayed': True}
    except Exception as e:
        return {**ctx, 'error': e}

async def update_frame_count_link(ctx: Ctx) -> Ctx:
    """Increment frame counter."""
    frame_count = ctx.get('frame_count', 0) + 1
    return {**ctx, 'frame_count': frame_count}

async def cleanup_resources_link(ctx: Ctx) -> Ctx:
    """Clean up camera and detector resources."""
    try:
        # Clean up camera
        camera = ctx.get('camera')
        if camera:
            camera.release()
            
        # Clean up detector
        detector = ctx.get('detector')
        if detector:
            detector.close()
            
        return {**ctx, 'cleanup_complete': True, 'status': 'cleaned_up'}
    except Exception as e:
        return {**ctx, 'error': e, 'status': 'cleanup_failed'}

# ==================== MIDDLEWARE ====================

async def error_handler_middleware(ctx: Ctx) -> Ctx:
    """Middleware to handle and log errors."""
    if ctx.get('error'):
        error = ctx['error']
        print(f"\n❌ Error: {error}")
        return {**ctx, 'should_stop': True}
    return ctx

async def logging_middleware(ctx: Ctx) -> Ctx:
    """Middleware to log context status."""
    status = ctx.get('status')
    if status:
        print(f"🔄 Status: {status}")
    return ctx

# ==================== CHAINS ====================

# Initialization chain
initialization_chain = chain(
    initialize_config_link,
    initialize_detector_link,
    initialize_camera_link
)

# Single frame processing chain
frame_processing_chain = chain(
    update_frame_count_link,
    capture_frame_link,
    detect_eyes_link,
    format_output_link,
    display_output_link
)

# Cleanup chain
cleanup_chain = chain(cleanup_resources_link)

# ==================== MAIN APPLICATION FUNCTIONS ====================

async def run_eye_tracking_modulink(
    camera_index: int = 0,
    config_path: str = 'config.json',
    max_frames: int = 1000
) -> Ctx:
    """
    Run eye tracking using ModuLink chain composition.
    
    Args:
        camera_index: Camera device index
        config_path: Path to configuration file
        max_frames: Maximum number of frames to process
        
    Returns:
        Final context with results
    """
    # Create initial context
    initial_ctx = create_cli_context(
        command="eye_tracking",
        args=[f"--camera={camera_index}", f"--config={config_path}"],
        camera_index=camera_index,
        config_path=config_path,
        max_frames=max_frames,
        frame_count=0
    )
    
    print("🧪 ModuLink Eye Tracking Starting...")
    print("=" * 60)
    
    try:
        # Step 1: Initialize everything
        print("📋 Initializing system...")
        ctx = await initialization_chain(initial_ctx)
        
        if ctx.get('error'):
            print(f"❌ Initialization failed: {ctx['error']}")
            return ctx
            
        print("✅ System initialized successfully")
        print("🎥 Starting eye tracking... Press Ctrl+C to stop")
        print("-" * 60)
        
        # Step 2: Main processing loop
        while ctx.get('frame_count', 0) < max_frames and not ctx.get('should_stop'):
            ctx = await frame_processing_chain(ctx)
            
            if ctx.get('error'):
                break
                
            # Small delay to control frame rate
            import asyncio
            await asyncio.sleep(0.033)  # ~30 FPS
            
    except KeyboardInterrupt:
        print("\n🛑 Stopping eye tracking...")
        ctx = {**ctx, 'interrupted': True}
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        ctx = {**ctx, 'error': e}
    finally:
        # Step 3: Cleanup
        print("\n🧹 Cleaning up resources...")
        cleanup_ctx = await cleanup_chain(ctx)
        print("✅ Cleanup complete")
        
        return cleanup_ctx

async def demo_modulink_chain():
    """
    Demonstrate ModuLink chain composition with a mock frame.
    """
    print("🧪 ModuLink Chain Demo (No Camera Required)")
    print("=" * 50)
    
    # Create a demo context with mock data
    demo_ctx = create_context(
        trigger="demo",
        config_path="config.json",
        camera_index=0,
        frame_count=1
    )
    
    # Add a mock frame (black image)
    demo_ctx['frame'] = np.zeros((480, 640, 3), dtype=np.uint8)
    
    try:
        # Initialize detector only (skip camera)
        print("📋 Initializing configuration and detector...")
        ctx = await chain(initialize_config_link, initialize_detector_link)(demo_ctx)
        
        if ctx.get('error'):
            print(f"❌ Initialization failed: {ctx['error']}")
            return ctx
            
        print("✅ Initialization successful")
        
        # Process the mock frame
        print("🔍 Processing mock frame...")
        processing_chain = chain(
            detect_eyes_link,
            format_output_link,
            display_output_link
        )
        
        ctx = await processing_chain(ctx)
        
        if ctx.get('error'):
            print(f"❌ Processing failed: {ctx['error']}")
        else:
            print("\n✅ Mock frame processed successfully!")
            
        # Cleanup
        print("\n🧹 Cleaning up...")
        cleanup_ctx = await cleanup_chain(ctx)
        
        return cleanup_ctx
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        return {**demo_ctx, 'error': e}

# ==================== CLI INTERFACE ====================

if __name__ == "__main__":
    import sys
    import asyncio
    
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        # Run demo without camera
        asyncio.run(demo_modulink_chain())
    else:
        # Run full eye tracking
        camera_index = int(sys.argv[1]) if len(sys.argv) > 1 else 0
        asyncio.run(run_eye_tracking_modulink(camera_index=camera_index))
