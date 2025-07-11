# Cross-Platform Video Device Control Tool

A cross-platform video device control tool compatible with v4l2-ctl, supporting Windows, Linux, and macOS.

## 🌟 Features

- ✅ **Cross-Platform Support**: Windows, Linux, macOS
- ✅ **Device Enumeration**: List all available video devices
- ✅ **Format Query**: Display supported video formats, resolutions, frame rates
- ✅ **Parameter Control**: View and set device control parameters (brightness, contrast, etc.)
- ✅ **v4l2-ctl Compatible**: Command-line interface compatible with v4l2-ctl
- ✅ **Multiple Backends**: DirectShow (Windows), V4L2 (Linux), AVFoundation (macOS), OpenCV (fallback)

## 🚀 Quick Start

### Installation

```bash
# Install from source
git clone https://github.com/yaoian/cross-platform-video-control.git
cd cross-platform-video-control
pip install -r requirements.txt

# Or install as package
pip install cross-platform-video-control
```

### Basic Usage

```bash
# Show help
python v4l2_ctl_cross.py -h

# List all video devices
python v4l2_ctl_cross.py --list-devices

# Show supported formats
python v4l2_ctl_cross.py -d /dev/video0 --list-formats-ext

# Show device controls
python v4l2_ctl_cross.py -d /dev/video0 -L

# Set control parameters
python v4l2_ctl_cross.py -d /dev/video0 -c brightness=50
python v4l2_ctl_cross.py -d /dev/video0 -c brightness=50,contrast=75
```

## 📋 Example Output

**Device List:**
```
USB Camera: (USB\VID_1BCF&PID_2C9A&MI_00\6&33F8E1A6&0&0000):
        /dev/video0
```

**Control Parameters:**
```
User Controls

brightness: 50 (range: 0-100) - Brightness
contrast: 50 (range: 0-100) - Contrast
saturation: 50 (range: 0-100) - Saturation
```

## 🏗️ Architecture

```
VideoDeviceController (Abstract Base Class)
├── WindowsVideoController (Windows Implementation)
│   ├── DirectShow API (Primary)
│   └── OpenCV (Fallback)
├── LinuxVideoController (Linux Implementation)
│   └── V4L2 API
└── MacOSVideoController (macOS Implementation)
    └── AVFoundation API
```

## 📦 Platform-Specific Dependencies

### Windows
```bash
pip install pywin32 opencv-python
```

### Linux
```bash
pip install v4l2-python opencv-python
# or
sudo apt-get install python3-v4l2
```

### macOS
```bash
pip install pyobjc opencv-python pyobjc-framework-AVFoundation
```

## 📁 Project Structure

```
├── video_device_controller.py  # Abstract base class and interfaces
├── windows_directshow.py       # Windows DirectShow implementation
├── opencv_fallback.py          # OpenCV fallback implementation
├── v4l2_ctl_cross.py          # Command-line interface
├── setup.py                   # Package configuration
├── requirements.txt           # Dependencies
└── README.md                  # Project documentation
```

## 🔧 Development Status

### ✅ Completed Features
- [x] Project architecture design
- [x] Windows platform basic implementation
- [x] OpenCV fallback solution
- [x] Command-line interface
- [x] Device enumeration
- [x] Basic format query
- [x] Basic parameter control

### 🚧 In Progress
- [ ] Complete DirectShow implementation
- [ ] Linux V4L2 implementation
- [ ] macOS AVFoundation implementation
- [ ] Advanced parameter control
- [ ] Error handling optimization
- [ ] Unit tests
- [ ] Performance optimization

## 📊 Comparison with Original C++ Project

| Feature | C++ v4w2-ctl | Python Version |
|---------|--------------|----------------|
| Platform Support | Windows only | Windows/Linux/macOS |
| Device Enumeration | ✅ | ✅ |
| Format Query | ✅ | ✅ (Basic) |
| Parameter Control | ✅ | ✅ (Basic) |
| DirectShow | ✅ Complete | 🔄 In Development |
| V4L2 Support | ❌ | 🔄 Planned |
| Installation | Requires compilation | pip install |

## 🛠️ Building Original C++ Project

```bash
# Using MinGW
g++ -o v4w2-ctl.exe v4w2-ctl.cpp ClsDirectShow.cpp -lole32 -loleaut32 -lstrmiids

# Test
./v4w2-ctl.exe -h
./v4w2-ctl.exe --list-devices
```

## 🤝 Contributing

1. Fork the project
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## 📄 License

MIT License - Same as the original project

## 🙏 Acknowledgments

- Original project author: hry2566
- OpenCV community
- Python community library maintainers

## 📞 Support

If you encounter any issues or have questions, please [open an issue](https://github.com/yaoian/cross-platform-video-control/issues) on GitHub.
