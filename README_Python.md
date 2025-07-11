# 跨平台视频设备控制工具 (Python版本)

这是一个跨平台的视频设备控制工具，模仿Linux `v4l2-ctl` 的功能，支持Windows、Linux、macOS平台。

## 项目背景

原项目 `v4w2-ctl` 是一个Windows专用的C++工具，使用DirectShow API模仿Linux的v4l2-ctl功能。本Python版本扩展了这个概念，提供真正的跨平台支持。

## 功能特性

- ✅ **跨平台支持**: Windows、Linux、macOS
- ✅ **设备枚举**: 列出所有可用的视频设备
- ✅ **格式查询**: 显示设备支持的视频格式、分辨率、帧率
- ✅ **参数控制**: 查看和设置设备控制参数（亮度、对比度等）
- ✅ **命令行兼容**: 与v4l2-ctl命令行参数兼容

## 技术实现

### 架构设计
```
VideoDeviceController (抽象基类)
├── WindowsVideoController (Windows实现)
│   ├── DirectShow API (主要实现)
│   └── OpenCV (备用方案)
├── LinuxVideoController (Linux实现)
│   └── V4L2 API
└── MacOSVideoController (macOS实现)
    └── AVFoundation API
```

### 平台特定实现

**Windows平台:**
- 主要使用DirectShow COM接口
- OpenCV作为备用方案
- 支持WMI设备查询

**Linux平台:**
- 使用V4L2 ioctl调用
- 直接访问/dev/video*设备文件
- 完整的v4l2功能支持

**macOS平台:**
- 使用AVFoundation框架
- 通过pyobjc调用Objective-C API

## 安装依赖

### Windows
```bash
pip install pywin32 opencv-python
```

### Linux
```bash
pip install v4l2-python opencv-python
# 或者
sudo apt-get install python3-v4l2
```

### macOS
```bash
pip install pyobjc opencv-python
```

## 使用方法

### 基本命令

```bash
# 显示帮助
python v4l2_ctl_cross.py -h

# 列出所有视频设备
python v4l2_ctl_cross.py --list-devices

# 显示设备支持的格式
python v4l2_ctl_cross.py -d /dev/video0 --list-formats-ext

# 显示设备控制参数
python v4l2_ctl_cross.py -d /dev/video0 -L

# 设置控制参数
python v4l2_ctl_cross.py -d /dev/video0 -c brightness=50
python v4l2_ctl_cross.py -d /dev/video0 -c brightness=50,contrast=75
```

### 示例输出

**设备列表:**
```
USB Camera: (USB\VID_1BCF&PID_2C9A&MI_00\6&33F8E1A6&0&0000):
        /dev/video0
```

**支持的格式:**
```
设备 /dev/video0 支持的格式:
    [MJPG] 640x480 @ 30.00fps
    [MJPG] 1280x720 @ 30.00fps
    [MJPG] 1920x1080 @ 30.00fps
```

**控制参数:**
```
User Controls

brightness: 50 (范围: 0-100) - 亮度
contrast: 50 (范围: 0-100) - 对比度
saturation: 50 (范围: 0-100) - 饱和度
```

## 文件结构

```
├── video_device_controller.py  # 抽象基类和接口定义
├── windows_directshow.py       # Windows DirectShow实现
├── opencv_fallback.py          # OpenCV备用实现
├── v4l2_ctl_cross.py          # 命令行接口
├── README_Python.md           # 项目说明
└── requirements.txt           # 依赖列表
```

## 开发状态

### 已完成功能
- [x] 项目架构设计
- [x] Windows平台基础实现
- [x] OpenCV备用方案
- [x] 命令行接口
- [x] 设备枚举功能
- [x] 基础格式查询
- [x] 基础参数控制

### 待完成功能
- [ ] 完整的DirectShow实现
- [ ] Linux V4L2实现
- [ ] macOS AVFoundation实现
- [ ] 高级参数控制
- [ ] 错误处理优化
- [ ] 单元测试
- [ ] 性能优化

## 与原C++项目对比

| 功能 | C++ v4w2-ctl | Python版本 |
|------|--------------|------------|
| 平台支持 | Windows only | Windows/Linux/macOS |
| 设备枚举 | ✅ | ✅ |
| 格式查询 | ✅ | ✅ (基础) |
| 参数控制 | ✅ | ✅ (基础) |
| DirectShow | ✅ 完整 | 🔄 开发中 |
| V4L2支持 | ❌ | 🔄 计划中 |
| 安装简便性 | 需编译 | pip安装 |

## 编译测试

### 原C++项目编译
```bash
# 使用MinGW编译
g++ -o v4w2-ctl-test.exe v4w2-ctl.cpp ClsDirectShow.cpp -lole32 -loleaut32 -lstrmiids

# 测试运行
.\v4w2-ctl-test.exe -h
.\v4w2-ctl-test.exe --list-devices
```

### Python版本测试
```bash
# 测试设备枚举
python v4l2_ctl_cross.py --list-devices

# 测试格式查询
python v4l2_ctl_cross.py -d /dev/video0 --list-formats-ext

# 测试参数控制
python v4l2_ctl_cross.py -d /dev/video0 -L
```

## 贡献指南

1. Fork项目
2. 创建功能分支
3. 提交更改
4. 发起Pull Request

## 许可证

MIT License - 与原项目保持一致

## 致谢

- 原项目作者 hry2566
- OpenCV社区
- Python社区的各种库维护者
