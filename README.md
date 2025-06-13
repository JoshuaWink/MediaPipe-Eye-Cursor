# MediaPipe Eye Cursor

A real-time eye tracking application using MediaPipe for gaze estimation and mouse control.

## Features

- Real-time eye detection using MediaPipe Face Landmarker
- Gaze direction calculation
- Command-line interface for testing and debugging
- Modular architecture following TDD principles
- Configurable camera settings and model parameters

## Requirements

- Python 3.12
- Camera (webcam or external)
- macOS/Linux/Windows

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd MediaPipe-Eye-Cursor
```

2. Create and activate virtual environment:
```bash
python3.12 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Basic Eye Tracking

Start eye tracking with default camera:
```bash
python -m src.main track
```

Use a specific camera:
```bash
python -m src.main --camera 1 track
```

### Configuration

Create a custom configuration:
```bash
python -m src.main --config my_config.json --confidence 0.7 track
```

### Help

Show help information:
```bash
python -m src.main help
```

## Project Structure

```
MediaPipe-Eye-Cursor/
├── src/
│   ├── eye_tracker/
│   │   ├── __init__.py
│   │   └── detector.py          # MediaPipe eye detection
│   ├── ui/
│   │   ├── __init__.py
│   │   └── cli_interface.py     # Command line interface
│   ├── utils/
│   │   ├── __init__.py
│   │   └── config.py            # Configuration management
│   └── main.py                  # Main entry point
├── tests/
│   ├── eye_tracker/
│   ├── ui/
│   └── utils/
├── models/
│   └── face_landmarker.task     # MediaPipe model
├── requirements.txt
└── README.md
```

## Development

### Running Tests

Run all tests:
```bash
python -m pytest tests/ -v
```

Run specific test module:
```bash
python -m pytest tests/eye_tracker/test_detector.py -v
```

### Test-Driven Development

This project follows TDD principles:
1. Write tests first
2. Implement minimal code to pass tests
3. Refactor and improve
4. Repeat

### Adding New Features

1. Create a new branch: `git checkout -b feature/new-feature`
2. Write tests for the new feature
3. Implement the feature
4. Ensure all tests pass
5. Commit and push changes

## Current Status

✅ **Phase 1: Core Eye Tracking (Completed)**
- MediaPipe integration
- Eye detection and basic gaze estimation
- Command-line interface
- Test coverage

🚧 **Phase 2: Calibration System (In Progress)**
- 5-point calibration (4 corners + center)
- Screen coordinate mapping
- Calibration data persistence

⏳ **Phase 3: Mouse Control (Planned)**
- Real-time cursor movement
- Click detection
- Smoothing and filtering

## Configuration Options

The application uses a JSON configuration file with the following options:

```json
{
  "camera_index": 0,
  "calibration_points": 5,
  "model_path": "models/face_landmarker.task",
  "confidence_threshold": 0.5,
  "tracking_confidence": 0.5,
  "presence_threshold": 0.5
}
```

## Troubleshooting

### Camera Issues

If the camera fails to initialize:
1. Check camera permissions
2. Try a different camera index: `--camera 1`
3. Ensure no other application is using the camera

### Model Issues

If the MediaPipe model fails to load:
1. Check that `models/face_landmarker.task` exists
2. Re-download the model if necessary
3. Verify the model path in configuration

### Performance Issues

For better performance:
1. Ensure good lighting conditions
2. Position camera at eye level
3. Reduce camera resolution if needed

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes following TDD principles
4. Ensure all tests pass
5. Submit a pull request

## License

[License information to be added]

## Acknowledgments

- MediaPipe team for the excellent face landmarker model
- OpenCV team for computer vision utilities
