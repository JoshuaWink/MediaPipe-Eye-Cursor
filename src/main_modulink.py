#!/usr/bin/env python3
"""
Pure ModuLink MediaPipe Eye Cursor - Main Entry Point

This is the complete ModuLink migration using comprehensive context wrappers
to convert all existing components to ModuLink Ctx-compliant functions
without modifying the original code.
"""

import asyncio
import sys
import argparse
from modulink import Ctx, chain, create_cli_context
from src.utils.ctx_wrapper import ctx_wrap, CtxWrapper
from src.utils.context_logger import init_context_logger, get_context_logger
from src.utils.logging_middleware import create_logged_chain

# ==================== WRAPPED COMPONENTS ====================
# Using comprehensive wrapper to convert existing code to ModuLink

# Configuration Management
@ctx_wrap(input_keys=['config_path'], output_key='config')
def load_configuration(config_path='config.json'):
    """Load configuration using existing Config class."""
    from src.utils.config import Config
    return Config.load(config_path)

# Eye Tracker Initialization  
@ctx_wrap(input_keys=['config'], output_key='detector')
def initialize_eye_detector(config):
    """Initialize MediaPipe eye detector using existing EyeDetector class."""
    from src.eye_tracker.detector import EyeDetector
    return EyeDetector(config)

# Camera Management
@ctx_wrap(input_keys=['config'], output_key='camera')
def initialize_camera(config):
    """Initialize camera using existing camera logic."""
    import cv2
    cap = cv2.VideoCapture(config.camera_index)
    if not cap.isOpened():
        raise RuntimeError(f"Could not open camera {config.camera_index}")
    
    # Set camera properties
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)
    
    return cap

# Frame Capture
@ctx_wrap(input_keys=['camera'], output_key='frame')
def capture_frame(camera):
    """Capture frame from camera."""
    ret, frame = camera.read()
    if not ret:
        raise RuntimeError("Failed to capture frame from camera")
    return frame

# Eye Detection Processing
@ctx_wrap(input_keys=['detector', 'frame'], output_key='detection_result')
def process_eye_detection(detector, frame):
    """Process frame for eye detection using existing detector."""
    return detector.process_image(frame)

# Frame Counter
@ctx_wrap(input_keys=['frame_count'], output_key='frame_count')
def increment_frame_count(frame_count=0):
    """Increment frame counter."""
    return frame_count + 1

# Output Formatting
@ctx_wrap(input_keys=['face_detected', 'gaze_direction', 'left_eye', 'right_eye', 'frame_count'], output_key='formatted_output')
def format_detection_output(face_detected=False, gaze_direction=(0.0, 0.0), left_eye=None, right_eye=None, frame_count=0):
    """Format detection results for display."""
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
    
    return f"Frame {frame_count:04d}: " + " | ".join(lines)

# Display Output
@ctx_wrap(input_keys=['formatted_output'], output_key='displayed')
def display_output(formatted_output):
    """Display output to console."""
    print('\r' + ' ' * 100, end='')
    print(f'\r{formatted_output}', end='', flush=True)
    return True

# Resource Cleanup
@ctx_wrap(input_keys=['camera', 'detector'], output_key='cleanup_complete')
def cleanup_resources(camera=None, detector=None):
    """Clean up camera and detector resources."""
    if camera:
        camera.release()
    if detector:
        detector.close()
    return True

# Context Enrichment Functions
async def enrich_context_with_metadata(ctx: Ctx) -> Ctx:
    """Enrich context with additional metadata."""
    return {
        **ctx,
        'app_version': '2.0.0-modulink',
        'execution_mode': 'pure_modulink',
        'wrapper_enabled': True
    }

async def extract_detection_fields(ctx: Ctx) -> Ctx:
    """Extract detection fields into top-level context."""
    detection_result = ctx.get('detection_result', {})
    return {
        **ctx,
        'face_detected': detection_result.get('face_detected', False),
        'gaze_direction': detection_result.get('gaze_direction', (0.0, 0.0)),
        'left_eye': detection_result.get('left_eye'),
        'right_eye': detection_result.get('right_eye')
    }

# ==================== MODULINK CHAINS ====================

# System initialization chain
system_initialization_chain = create_logged_chain(
    chain(
        enrich_context_with_metadata,
        load_configuration,
        initialize_eye_detector,
        initialize_camera
    ),
    "system_initialization"
)

# Single frame processing chain
frame_processing_chain = create_logged_chain(
    chain(
        increment_frame_count,
        capture_frame,
        process_eye_detection,
        extract_detection_fields,
        format_detection_output,
        display_output
    ),
    "frame_processing"
)

# System cleanup chain
system_cleanup_chain = create_logged_chain(
    chain(cleanup_resources),
    "system_cleanup"
)

# ==================== APPLICATION LOGIC ====================

async def run_eye_tracking_modulink(
    camera_index: int = 0,
    config_path: str = 'config.json',
    max_frames: int = 1000,
    log_level: str = 'DEBUG'
) -> Ctx:
    """
    Run eye tracking using pure ModuLink chains with comprehensive logging.
    
    This is the main application that demonstrates complete ModuLink migration
    without modifying any of the original code - everything is wrapped.
    """
    
    # Initialize comprehensive logging
    logger = init_context_logger("logs", log_level)
    print(f"📝 ModuLink logging initialized: {logger.log_file}")
    
    # Create initial context
    initial_ctx = create_cli_context(
        command="eye_tracking_modulink",
        args=[f"--camera={camera_index}", f"--config={config_path}", f"--max-frames={max_frames}"],
        camera_index=camera_index,
        config_path=config_path,
        max_frames=max_frames,
        frame_count=0
    )
    
    print("🔗 Pure ModuLink Eye Tracking Starting...")
    print("=" * 60)
    print(f"📊 Configuration: camera={camera_index}, config={config_path}, max_frames={max_frames}")
    print(f"🔍 Introspection: Full metadata capture enabled")
    print("-" * 60)
    
    try:
        # Phase 1: System Initialization
        print("📋 Phase 1: System initialization...")
        ctx = await system_initialization_chain(initial_ctx)
        
        if ctx.get('error'):
            print(f"❌ System initialization failed: {ctx['error']}")
            return ctx
            
        print("✅ System initialized successfully")
        print(f"🎯 Detected components: {[k for k in ctx.keys() if k in ['config', 'detector', 'camera']]}")
        
        # Phase 2: Real-time Processing Loop
        print("🎥 Phase 2: Starting real-time eye tracking...")
        print("💡 Press Ctrl+C to stop gracefully")
        print("-" * 60)
        
        while ctx.get('frame_count', 0) < max_frames and not ctx.get('error'):
            ctx = await frame_processing_chain(ctx)
            
            if ctx.get('error'):
                print(f"\n❌ Frame processing error: {ctx['error']}")
                break
                
            # Control frame rate
            await asyncio.sleep(0.033)  # ~30 FPS
            
    except KeyboardInterrupt:
        print(f"\n🛑 Graceful shutdown requested...")
        ctx = {**ctx, 'interrupted': True, 'shutdown_reason': 'user_interrupt'}
        
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        ctx = {**ctx, 'error': e, 'shutdown_reason': 'unexpected_error'}
        
    finally:
        # Phase 3: Cleanup
        print(f"\n🧹 Phase 3: Resource cleanup...")
        cleanup_ctx = await system_cleanup_chain(ctx)
        
        # Final statistics
        final_frame_count = cleanup_ctx.get('frame_count', 0)
        print(f"📊 Final Statistics:")
        print(f"   Frames processed: {final_frame_count}")
        print(f"   Execution mode: {cleanup_ctx.get('execution_mode', 'unknown')}")
        print(f"   Introspection data: {'Available' if '_introspection' in cleanup_ctx else 'Not available'}")
        
        # Log summary
        log_summary = logger.get_log_summary()
        print(f"   Log entries: {log_summary['total_links_executed']}")
        print(f"   Log file: {log_summary['log_file']}")
        
        print("✅ ModuLink eye tracking completed")
        
        return cleanup_ctx

async def demo_modulink_pure():
    """
    Demo pure ModuLink functionality without camera using mock data.
    """
    print("🧪 Pure ModuLink Demo (No Camera Required)")
    print("=" * 50)
    
    # Initialize logging
    logger = init_context_logger("logs", "DEBUG")
    print(f"📝 Logging: {logger.log_file}")
    
    # Create demo context with mock frame
    import numpy as np
    demo_ctx = create_cli_context(
        command="demo_pure_modulink",
        args=["--demo"],
        config_path="config.json",
        camera_index=0,
        frame_count=0
    )
    
    try:
        # Initialize system (without camera)
        print("📋 Initializing system...")
        init_chain_no_camera = create_logged_chain(
            chain(
                enrich_context_with_metadata,
                load_configuration,
                initialize_eye_detector
            ),
            "demo_initialization"
        )
        
        ctx = await init_chain_no_camera(demo_ctx)
        
        if ctx.get('error'):
            print(f"❌ Initialization failed: {ctx['error']}")
            return ctx
            
        print("✅ System initialized (camera-less mode)")
        
        # Add mock frame
        mock_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        ctx['frame'] = mock_frame
        
        # Process mock frame
        print("🔍 Processing mock frame...")
        demo_processing_chain = create_logged_chain(
            chain(
                increment_frame_count,
                process_eye_detection,
                extract_detection_fields,
                format_detection_output,
                display_output
            ),
            "demo_processing"
        )
        
        ctx = await demo_processing_chain(ctx)
        
        if ctx.get('error'):
            print(f"❌ Processing failed: {ctx['error']}")
        else:
            print(f"\n✅ Mock frame processed successfully!")
            print(f"🔍 Introspection available: {'Yes' if '_introspection' in ctx else 'No'}")
            
            # Show introspection sample
            if '_introspection' in ctx:
                introspection = ctx['_introspection']
                print(f"📊 Function executed: {introspection.get('function_metadata', {}).get('name', 'unknown')}")
                print(f"⏱️  Execution time: {introspection.get('performance_delta', {}).get('execution_time', 'unknown')} seconds")
        
        # Cleanup (detector only)
        print("\n🧹 Cleaning up...")
        cleanup_ctx = await cleanup_resources({'detector': ctx.get('detector')})
        
        return cleanup_ctx
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        return {**demo_ctx, 'error': e}

# ==================== CLI INTERFACE ====================

def create_argument_parser():
    """Create command line argument parser."""
    parser = argparse.ArgumentParser(
        description="Pure ModuLink MediaPipe Eye Cursor - Real-time eye tracking with comprehensive introspection",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m src.main_modulink track                     # Start eye tracking
  python -m src.main_modulink demo                      # Demo mode (no camera)
  python -m src.main_modulink track --camera 1          # Use camera 1
  python -m src.main_modulink track --max-frames 100    # Limit to 100 frames
        """
    )
    
    parser.add_argument(
        'command',
        choices=['track', 'demo', 'help'],
        help='Command to execute'
    )
    
    parser.add_argument(
        '--camera',
        type=int,
        default=0,
        help='Camera index (default: 0)'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        default='config.json',
        help='Configuration file path (default: config.json)'
    )
    
    parser.add_argument(
        '--max-frames',
        type=int,
        default=1000,
        help='Maximum frames to process (default: 1000)'
    )
    
    parser.add_argument(
        '--log-level',
        type=str,
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='DEBUG',
        help='Logging level (default: DEBUG)'
    )
    
    return parser

async def main():
    """Main application entry point - pure ModuLink."""
    parser = create_argument_parser()
    args = parser.parse_args()
    
    print("🔗 Pure ModuLink MediaPipe Eye Cursor")
    print("=" * 50)
    print("🧬 All functions wrapped with comprehensive introspection")
    print("📊 Full metadata capture enabled")
    print("🔍 Context flow logging active")
    print("-" * 50)
    
    try:
        if args.command == 'track':
            result = await run_eye_tracking_modulink(
                camera_index=args.camera,
                config_path=args.config,
                max_frames=args.max_frames,
                log_level=args.log_level
            )
            
            if result.get('error'):
                print(f"❌ Eye tracking failed: {result['error']}")
                sys.exit(1)
                
        elif args.command == 'demo':
            result = await demo_modulink_pure()
            
            if result.get('error'):
                print(f"❌ Demo failed: {result['error']}")
                sys.exit(1)
                
        elif args.command == 'help':
            parser.print_help()
            
    except KeyboardInterrupt:
        print("\n🛑 Application interrupted by user")
    except Exception as e:
        print(f"💥 Application error: {e}")
        sys.exit(1)
    
    print("\n🎯 Pure ModuLink application completed")

if __name__ == '__main__':
    asyncio.run(main())
