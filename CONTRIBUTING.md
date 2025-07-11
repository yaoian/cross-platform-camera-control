# Contributing to Cross-Platform Camera Control

Thank you for your interest in contributing to this project! 🎉

## 🚀 Getting Started

### Prerequisites
- Python 3.7 or higher
- Git
- Platform-specific dependencies (see README.md)

### Development Setup
1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/cross-platform-camera-control.git
   cd cross-platform-camera-control
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   pip install -e .  # Install in development mode
   ```
4. Create a new branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## 🛠️ Development Guidelines

### Code Style
- Follow PEP 8 Python style guide
- Use meaningful variable and function names
- Add docstrings to all public functions and classes
- Keep functions focused and small

### Platform-Specific Development
- **Windows**: Focus on DirectShow API improvements
- **Linux**: Implement V4L2 functionality
- **macOS**: Implement AVFoundation support
- **Cross-platform**: Enhance OpenCV fallback

### Testing
- Test your changes on your target platform
- Ensure backward compatibility
- Add test cases for new features
- Test with different camera devices if possible

## 📝 Contribution Types

### 🐛 Bug Fixes
1. Create an issue describing the bug
2. Reference the issue in your PR
3. Include steps to reproduce
4. Test the fix thoroughly

### ✨ New Features
1. Discuss the feature in an issue first
2. Follow the existing architecture patterns
3. Update documentation
4. Add examples if applicable

### 📚 Documentation
- Improve README.md
- Add code comments
- Update CHANGELOG.md
- Create usage examples

### 🔧 Platform Support
Priority areas for contribution:
- Complete DirectShow implementation (Windows)
- V4L2 implementation (Linux)
- AVFoundation implementation (macOS)
- Advanced control parameters
- Device hotplug detection

## 🔄 Pull Request Process

1. **Before submitting:**
   - Ensure your code follows the style guidelines
   - Test your changes thoroughly
   - Update documentation if needed
   - Add your changes to CHANGELOG.md

2. **PR Description:**
   - Clearly describe what your PR does
   - Reference any related issues
   - Include testing information
   - Add screenshots/output if relevant

3. **Review Process:**
   - Maintainers will review your PR
   - Address any feedback promptly
   - Be patient - reviews take time

## 🏗️ Architecture Overview

```
VideoDeviceController (Abstract Base)
├── WindowsVideoController
│   ├── DirectShow API (primary)
│   └── OpenCV fallback
├── LinuxVideoController  
│   └── V4L2 API
└── MacOSVideoController
    └── AVFoundation API
```

### Key Files
- `video_device_controller.py` - Abstract base class
- `windows_directshow.py` - Windows implementation
- `opencv_fallback.py` - Cross-platform fallback
- `v4l2_ctl_cross.py` - Command-line interface

## 🧪 Testing Guidelines

### Manual Testing
```bash
# Test device enumeration
python v4l2_ctl_cross.py --list-devices

# Test format query
python v4l2_ctl_cross.py -d /dev/video0 --list-formats-ext

# Test control parameters
python v4l2_ctl_cross.py -d /dev/video0 -L

# Test parameter setting
python v4l2_ctl_cross.py -d /dev/video0 -c brightness=50
```

### Platform Testing
- Test on your target platform
- Verify cross-platform compatibility
- Test with different camera devices
- Check error handling

## 📋 Issue Guidelines

### Bug Reports
- Use the bug report template
- Include full error output
- Specify your environment details
- Provide reproduction steps

### Feature Requests
- Use the feature request template
- Explain the use case clearly
- Consider implementation complexity
- Discuss alternatives

## 🤝 Community Guidelines

- Be respectful and inclusive
- Help others learn and contribute
- Provide constructive feedback
- Follow the code of conduct

## 📞 Getting Help

- Open an issue for questions
- Check existing issues and documentation
- Be specific about your problem
- Include relevant details

## 🎯 Priority Areas

Current development priorities:
1. **Windows DirectShow** - Complete implementation
2. **Linux V4L2** - Full V4L2 support
3. **macOS AVFoundation** - Native macOS support
4. **Advanced Controls** - More camera parameters
5. **Error Handling** - Better error messages
6. **Performance** - Optimization and speed
7. **Testing** - Unit tests and CI/CD

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to make camera control better for everyone! 🚀
