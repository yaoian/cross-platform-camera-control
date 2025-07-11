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
        except Exception as e:
            print(f"OpenCV备用方案初始化失败: {e}")

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
            return self.opencv_fallback.get_video_formats(device_index)
        return []

    def get_controls(self, device_index: int) -> List[ControlInfo]:
        """获取Windows设备控制参数"""
        if self.opencv_fallback:
            return self.opencv_fallback.get_device_controls(device_index)
        return []

    def set_control(self, device_index: int, control_name: str, value: int) -> bool:
        """设置Windows设备控制参数"""
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
            import fcntl
            import os
            import glob
            self.fcntl = fcntl
            self.os = os
            self.glob = glob
        except ImportError:
            raise ImportError("Linux平台需要fcntl模块")
    
    def list_devices(self) -> List[DeviceInfo]:
        """列出Linux视频设备"""
        devices = []
        device_files = self.glob.glob("/dev/video*")
        
        for i, device_path in enumerate(sorted(device_files)):
            try:
                # 尝试打开设备获取信息
                with open(device_path, 'rb') as f:
                    # TODO: 使用V4L2 ioctl获取设备信息
                    devices.append(DeviceInfo(
                        index=i,
                        name=f"Video Device {i}",
                        path=device_path,
                        description=""
                    ))
            except Exception:
                continue
        
        return devices
    
    def get_formats(self, device_index: int) -> List[VideoFormat]:
        """获取Linux设备支持的格式"""
        # TODO: 实现V4L2格式查询
        return []
    
    def get_controls(self, device_index: int) -> List[ControlInfo]:
        """获取Linux设备控制参数"""
        # TODO: 实现V4L2控制参数查询
        return []
    
    def set_control(self, device_index: int, control_name: str, value: int) -> bool:
        """设置Linux设备控制参数"""
        # TODO: 实现V4L2控制参数设置
        return False
    
    def get_control(self, device_index: int, control_name: str) -> Optional[int]:
        """获取Linux设备控制参数值"""
        # TODO: 实现V4L2控制参数获取
        return None


class MacOSVideoController(VideoDeviceController):
    """macOS平台视频设备控制器（使用AVFoundation）"""
    
    def __init__(self):
        try:
            import objc
            self.objc = objc
            # TODO: 导入AVFoundation框架
        except ImportError:
            raise ImportError("macOS平台需要安装pyobjc: pip install pyobjc")
    
    def list_devices(self) -> List[DeviceInfo]:
        """列出macOS视频设备"""
        # TODO: 实现AVFoundation设备枚举
        return []
    
    def get_formats(self, device_index: int) -> List[VideoFormat]:
        """获取macOS设备支持的格式"""
        # TODO: 实现AVFoundation格式查询
        return []
    
    def get_controls(self, device_index: int) -> List[ControlInfo]:
        """获取macOS设备控制参数"""
        # TODO: 实现AVFoundation控制参数查询
        return []
    
    def set_control(self, device_index: int, control_name: str, value: int) -> bool:
        """设置macOS设备控制参数"""
        # TODO: 实现AVFoundation控制参数设置
        return False
    
    def get_control(self, device_index: int, control_name: str) -> Optional[int]:
        """获取macOS设备控制参数值"""
        # TODO: 实现AVFoundation控制参数获取
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
