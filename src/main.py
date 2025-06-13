#!/usr/bin/env python3
"""
MediaPipe Eye Cursor - Main Entry Point

A real-time eye tracking application using MediaPipe for gaze estimation.
"""

import sys
import argparse
from src.utils.config import Config
from src.ui.cli_interface import CLIInterface

def create_parser():
    """Create command line argument parser."""
    parser = argparse.ArgumentParser(
        description="MediaPipe Eye Cursor - Real-time eye tracking and gaze estimation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m src.main track                    # Start eye tracking
  python -m src.main calibrate               # Run calibration (coming soon)
  python -m src.main --camera 1 track        # Use camera index 1
  python -m src.main --config my_config.json track  # Use custom config
        """
    )
    
    parser.add_argument(
        'command',
        choices=['track', 'calibrate', 'help'],
        help='Command to execute'
    )
    
    parser.add_argument(
        '--camera',
        type=int,
        default=0,
        help='Camera index to use (default: 0)'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        default='config.json',
        help='Configuration file path (default: config.json)'
    )
    
    parser.add_argument(
        '--model',
        type=str,
        help='Path to MediaPipe face landmarker model'
    )
    
    parser.add_argument(
        '--confidence',
        type=float,
        default=0.5,
        help='Face detection confidence threshold (default: 0.5)'
    )
    
    return parser

def main():
    """Main application entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    # Load or create configuration
    config = Config.load(args.config)
    
    # Override config with command line arguments
    if args.camera != 0:
        config.camera_index = args.camera
    
    if args.model:
        config.model_path = args.model
    
    if args.confidence != 0.5:
        config.confidence_threshold = args.confidence
    
    # Save updated configuration
    config.save(args.config)
    
    # Initialize CLI interface
    cli = CLIInterface(config)
    
    try:
        if args.command == 'track':
            print("MediaPipe Eye Cursor - Starting eye tracking...")
            print(f"Using camera: {config.camera_index}")
            print(f"Model: {config.model_path}")
            print(f"Confidence threshold: {config.confidence_threshold}")
            print("-" * 50)
            
            success = cli.start_tracking()
            if not success:
                print("Failed to start eye tracking")
                sys.exit(1)
                
        elif args.command == 'calibrate':
            print("Starting calibration mode...")
            cli.run_calibration_mode()
            
        elif args.command == 'help':
            cli.show_help()
            
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    
    print("Application finished")

if __name__ == '__main__':
    main()
