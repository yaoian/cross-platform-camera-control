# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-01-11

### Added
- Initial release of cross-platform video device control tool
- Abstract base class `VideoDeviceController` for platform-specific implementations
- Windows implementation using DirectShow API with OpenCV fallback
- Linux implementation framework (V4L2 support planned)
- macOS implementation framework (AVFoundation support planned)
- Command-line interface compatible with v4l2-ctl
- Device enumeration functionality
- Video format query support
- Control parameter viewing and setting
- OpenCV-based fallback implementation for all platforms
- Comprehensive documentation and setup files

### Features
- **Cross-platform support**: Windows, Linux, macOS
- **Device enumeration**: List all available video devices
- **Format query**: Display supported video formats, resolutions, frame rates
- **Parameter control**: View and set device control parameters
- **v4l2-ctl compatibility**: Command-line interface matches v4l2-ctl syntax
- **Multiple backends**: Platform-specific APIs with OpenCV fallback

### Technical Details
- Python 3.7+ support
- Modular architecture with platform-specific implementations
- Windows: DirectShow COM interfaces + WMI device enumeration
- OpenCV integration for cross-platform compatibility
- Comprehensive error handling and fallback mechanisms

### Command-line Interface
- `--list-devices`: List all video devices
- `--list-formats-ext`: Show supported video formats
- `-L, --list-ctrls-menus`: Display control parameters
- `-c, --set-ctrl`: Set control parameters
- `-d, --device`: Specify device
- `-h, --help`: Show help information

### Dependencies
- `opencv-python>=4.5.0` (all platforms)
- `pywin32>=227` (Windows)
- `v4l2-python>=0.2.0` (Linux, planned)
- `pyobjc>=8.0` (macOS, planned)

### Known Limitations
- DirectShow implementation is basic (advanced features in development)
- Linux V4L2 implementation not yet complete
- macOS AVFoundation implementation not yet complete
- Some advanced control parameters may not be available

### Tested Platforms
- Windows 11 with MinGW
- Python 3.11
- USB webcam devices

## [Unreleased]

### Planned
- Complete DirectShow implementation for Windows
- Full V4L2 implementation for Linux
- AVFoundation implementation for macOS
- Advanced control parameter support
- Unit tests and CI/CD pipeline
- Performance optimizations
- Additional video format support
- Device hotplug detection
- Configuration file support
