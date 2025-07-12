#!/usr/bin/env python3
"""
跨平台视频设备控制工具
模仿v4l2-ctl功能，支持Windows、Linux、macOS
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple
import platform
import sys


@dataclass
class DeviceInfo:
    """视频设备信息"""
    index: int
    name: str
    path: str
    description: str = ""


@dataclass
class VideoFormat:
    """视频格式信息"""
    width: int
    height: int
    fps: float
    pixel_format: str
    description: str = ""


@dataclass
class ControlInfo:
    """控制参数信息"""
    name: str
    min_value: int
    max_value: int
    step: int
    default_value: int
    current_value: int
    flags: int
    auto_supported: bool = False
    description: str = ""


class VideoDeviceController(ABC):
    """视频设备控制器抽象基类"""
    
    @abstractmethod
    def list_devices(self) -> List[DeviceInfo]:
        """列出所有视频设备"""
        pass
    
    @abstractmethod
    def get_formats(self, device_index: int) -> List[VideoFormat]:
        """获取设备支持的视频格式"""
        pass
    
    @abstractmethod
    def get_controls(self, device_index: int) -> List[ControlInfo]:
        """获取设备支持的控制参数"""
        pass
    
    @abstractmethod
    def set_control(self, device_index: int, control_name: str, value: int) -> bool:
        """设置设备控制参数"""
        pass
    
    @abstractmethod
    def get_control(self, device_index: int, control_name: str) -> Optional[int]:
        """获取设备控制参数当前值"""
        pass


class WindowsVideoController(VideoDeviceController):
    """Windows平台视频设备控制器（使用DirectShow + OpenCV备用）"""

    def __init__(self):
        self.directshow = None
        self.opencv_fallback = None
        self.device_mapping = {}  # 逻辑设备到物理设备的映射

        # 尝试使用DirectShow
        try:
            from windows_directshow import WindowsDirectShowController
            self.directshow = WindowsDirectShowController()
        except Exception as e:
            print(f"DirectShow初始化失败: {e}")

        # 使用OpenCV作为备用
        try:
            from opencv_fallback import OpenCVVideoController
            self.opencv_fallback = OpenCVVideoController()
            self._build_device_mapping()
        except Exception as e:
            print(f"OpenCV备用方案初始化失败: {e}")

    def _build_device_mapping(self):
        """构建设备映射表"""
        # 简化映射，避免OpenCV初始化开销
        self.device_mapping = {0: 0, 1: 1, 2: 0}  # 简单的静态映射

    def list_devices(self) -> List[DeviceInfo]:
        """列出Windows视频设备"""
        if self.directshow:
            devices = self.directshow.list_devices()
            if devices:
                return devices

        if self.opencv_fallback:
            return self.opencv_fallback.list_devices()

        return []

    def get_formats(self, device_index: int) -> List[VideoFormat]:
        """获取Windows设备支持的格式"""
        if self.opencv_fallback:
            # OpenCV使用连续的设备索引，我们需要映射
            opencv_index = self._map_to_opencv_index(device_index)
            return self.opencv_fallback.get_video_formats(opencv_index)
        return []

    def get_controls(self, device_index: int) -> List[ControlInfo]:
        """获取Windows设备控制参数"""
        # 优先使用DirectShow获取真实参数
        if self.directshow:
            try:
                controls = self.directshow.get_device_controls(device_index)
                if controls:
                    return controls
            except Exception as e:
                print(f"DirectShow获取控制参数失败: {e}")

        # 备用方案：返回模拟的控制参数
        if self.opencv_fallback:
            return self.opencv_fallback._get_simulated_controls()
        return []

    def _map_to_opencv_index(self, device_index: int) -> int:
        """将设备索引映射到OpenCV索引"""
        # 使用预构建的映射表
        if device_index in self.device_mapping:
            return self.device_mapping[device_index]

        # 如果没有映射，返回0（第一个设备）
        return 0

    def set_control(self, device_index: int, control_name: str, value: int) -> bool:
        """设置Windows设备控制参数"""
        # 优先使用DirectShow
        if self.directshow:
            return self.directshow.set_device_control(device_index, control_name, value)

        # 备用方案
        if self.opencv_fallback:
            return self.opencv_fallback.set_device_control(device_index, control_name, value)
        return False

    def get_control(self, device_index: int, control_name: str) -> Optional[int]:
        """获取Windows设备控制参数值"""
        controls = self.get_controls(device_index)
        for ctrl in controls:
            if ctrl.name == control_name:
                return ctrl.current_value
        return None


class LinuxVideoController(VideoDeviceController):
    """Linux平台视频设备控制器（使用V4L2）"""

    def __init__(self):
        try:
            from linux_v4l2 import LinuxV4L2Controller
            self.v4l2 = LinuxV4L2Controller()
        except ImportError as e:
            print(f"V4L2实现导入失败: {e}")
            # 使用简化实现作为备用
            import fcntl
            import os
            import glob
            self.fcntl = fcntl
            self.os = os
            self.glob = glob
            self.v4l2 = None

    def list_devices(self) -> List[DeviceInfo]:
        """列出Linux视频设备"""
        if self.v4l2:
            return self.v4l2.list_devices()

        # 备用实现
        devices = []
        device_files = self.glob.glob("/dev/video*")

        for i, device_path in enumerate(sorted(device_files)):
            try:
                # 尝试打开设备获取信息
                with open(device_path, 'rb') as f:
                    devices.append(DeviceInfo(
                        index=i,
                        name=f"Video Device {i}",
                        path=device_path,
                        description="V4L2 Device"
                    ))
            except Exception:
                continue

        return devices

    def get_formats(self, device_index: int) -> List[VideoFormat]:
        """获取Linux设备支持的格式"""
        if self.v4l2:
            return self.v4l2.get_video_formats(device_index)
        return []

    def get_controls(self, device_index: int) -> List[ControlInfo]:
        """获取Linux设备控制参数"""
        if self.v4l2:
            return self.v4l2.get_device_controls(device_index)
        return []

    def set_control(self, device_index: int, control_name: str, value: int) -> bool:
        """设置Linux设备控制参数"""
        if self.v4l2:
            return self.v4l2.set_device_control(device_index, control_name, value)
        return False

    def get_control(self, device_index: int, control_name: str) -> Optional[int]:
        """获取Linux设备控制参数值"""
        controls = self.get_controls(device_index)
        for ctrl in controls:
            if ctrl.name == control_name:
                return ctrl.current_value
        return None


class MacOSVideoController(VideoDeviceController):
    """macOS平台视频设备控制器（使用AVFoundation）"""

    def __init__(self):
        self.avfoundation = None
        try:
            from macos_avfoundation import MacOSAVFoundationController
            self.avfoundation = MacOSAVFoundationController()
        except ImportError as e:
            print(f"AVFoundation实现导入失败: {e}")
            # 使用OpenCV作为备用
            try:
                from opencv_fallback import OpenCVVideoController
                self.opencv_fallback = OpenCVVideoController()
            except ImportError:
                raise ImportError("macOS平台需要安装pyobjc或opencv: pip install pyobjc pyobjc-framework-AVFoundation opencv-python")

    def list_devices(self) -> List[DeviceInfo]:
        """列出macOS视频设备"""
        if self.avfoundation:
            return self.avfoundation.list_devices()
        elif hasattr(self, 'opencv_fallback'):
            return self.opencv_fallback.list_devices()
        return []

    def get_formats(self, device_index: int) -> List[VideoFormat]:
        """获取macOS设备支持的格式"""
        if self.avfoundation:
            return self.avfoundation.get_video_formats(device_index)
        elif hasattr(self, 'opencv_fallback'):
            return self.opencv_fallback.get_video_formats(device_index)
        return []

    def get_controls(self, device_index: int) -> List[ControlInfo]:
        """获取macOS设备控制参数"""
        if self.avfoundation:
            return self.avfoundation.get_device_controls(device_index)
        elif hasattr(self, 'opencv_fallback'):
            return self.opencv_fallback.get_device_controls(device_index)
        return []

    def set_control(self, device_index: int, control_name: str, value: int) -> bool:
        """设置macOS设备控制参数"""
        if self.avfoundation:
            return self.avfoundation.set_device_control(device_index, control_name, value)
        elif hasattr(self, 'opencv_fallback'):
            return self.opencv_fallback.set_device_control(device_index, control_name, value)
        return False

    def get_control(self, device_index: int, control_name: str) -> Optional[int]:
        """获取macOS设备控制参数值"""
        controls = self.get_controls(device_index)
        for ctrl in controls:
            if ctrl.name == control_name:
                return ctrl.current_value
        return None


def create_controller() -> VideoDeviceController:
    """根据当前平台创建对应的控制器"""
    system = platform.system()
    
    if system == "Windows":
        return WindowsVideoController()
    elif system == "Linux":
        return LinuxVideoController()
    elif system == "Darwin":  # macOS
        return MacOSVideoController()
    else:
        raise NotImplementedError(f"不支持的平台: {system}")


if __name__ == "__main__":
    # 简单测试
    try:
        controller = create_controller()
        devices = controller.list_devices()
        print(f"找到 {len(devices)} 个视频设备:")
        for device in devices:
            print(f"  {device.index}: {device.name} ({device.path})")
    except Exception as e:
        print(f"错误: {e}")
