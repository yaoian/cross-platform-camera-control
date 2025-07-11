#!/usr/bin/env python3
"""
基于OpenCV的跨平台视频设备控制实现
作为DirectShow实现的备用方案
"""

import cv2
import platform
from typing import List, Dict, Optional, Tuple
from video_device_controller import DeviceInfo, VideoFormat, ControlInfo


class OpenCVVideoController:
    """基于OpenCV的视频设备控制器"""
    
    def __init__(self):
        """初始化OpenCV控制器"""
        self.opencv_available = True
        try:
            # 测试OpenCV是否可用
            cv2.VideoCapture(0)
        except Exception as e:
            print(f"OpenCV初始化失败: {e}")
            self.opencv_available = False
    
    def list_devices(self) -> List[DeviceInfo]:
        """枚举视频设备"""
        devices = []
        
        if not self.opencv_available:
            return devices
        
        # 尝试打开前10个设备索引
        for i in range(10):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                # 获取设备信息
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                fps = cap.get(cv2.CAP_PROP_FPS)
                
                device_name = f"Video Device {i}"
                
                # 在Windows上尝试获取更详细的信息
                if platform.system() == "Windows":
                    try:
                        backend_name = cap.getBackendName()
                        device_name = f"Video Device {i} ({backend_name})"
                    except:
                        pass
                
                devices.append(DeviceInfo(
                    index=i,
                    name=device_name,
                    path=f"/dev/video{i}",
                    description=f"Resolution: {width}x{height}, FPS: {fps:.1f}"
                ))
                
                cap.release()
        
        return devices
    
    def get_video_formats(self, device_index: int) -> List[VideoFormat]:
        """获取设备支持的视频格式"""
        formats = []
        
        if not self.opencv_available:
            return formats
        
        cap = cv2.VideoCapture(device_index)
        if not cap.isOpened():
            return formats
        
        # 常见分辨率列表
        common_resolutions = [
            (160, 120),   # QQVGA
            (320, 240),   # QVGA
            (640, 480),   # VGA
            (800, 600),   # SVGA
            (1024, 768),  # XGA
            (1280, 720),  # HD 720p
            (1280, 1024), # SXGA
            (1600, 1200), # UXGA
            (1920, 1080), # Full HD 1080p
            (2560, 1440), # QHD
            (3840, 2160), # 4K UHD
        ]
        
        for width, height in common_resolutions:
            # 尝试设置分辨率
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            
            # 检查实际设置的分辨率
            actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            if actual_width == width and actual_height == height:
                # 获取帧率
                fps = cap.get(cv2.CAP_PROP_FPS)
                if fps <= 0:
                    fps = 30.0  # 默认帧率
                
                # 尝试获取像素格式
                fourcc = int(cap.get(cv2.CAP_PROP_FOURCC))
                pixel_format = self._fourcc_to_string(fourcc) if fourcc > 0 else "UNKNOWN"
                
                formats.append(VideoFormat(
                    width=width,
                    height=height,
                    fps=fps,
                    pixel_format=pixel_format,
                    description=f"{width}x{height} @ {fps:.1f}fps"
                ))
        
        cap.release()
        return formats
    
    def get_device_controls(self, device_index: int) -> List[ControlInfo]:
        """获取设备控制参数"""
        controls = []
        
        if not self.opencv_available:
            return controls
        
        cap = cv2.VideoCapture(device_index)
        if not cap.isOpened():
            return controls
        
        # OpenCV支持的控制参数映射
        opencv_controls = {
            cv2.CAP_PROP_BRIGHTNESS: ("brightness", "亮度"),
            cv2.CAP_PROP_CONTRAST: ("contrast", "对比度"),
            cv2.CAP_PROP_SATURATION: ("saturation", "饱和度"),
            cv2.CAP_PROP_HUE: ("hue", "色调"),
            cv2.CAP_PROP_GAIN: ("gain", "增益"),
            cv2.CAP_PROP_EXPOSURE: ("exposure", "曝光"),
            cv2.CAP_PROP_WHITE_BALANCE_BLUE_U: ("white_balance_u", "白平衡U"),
            cv2.CAP_PROP_WHITE_BALANCE_RED_V: ("white_balance_v", "白平衡V"),
            cv2.CAP_PROP_GAMMA: ("gamma", "伽马值"),
            cv2.CAP_PROP_SHARPNESS: ("sharpness", "锐度"),
            cv2.CAP_PROP_BACKLIGHT: ("backlight", "背光补偿"),
        }
        
        for prop_id, (name, description) in opencv_controls.items():
            try:
                # 获取当前值
                current_value = cap.get(prop_id)
                
                # OpenCV通常返回0-1之间的值，转换为0-100
                if 0 <= current_value <= 1:
                    current_int = int(current_value * 100)
                else:
                    current_int = int(current_value)
                
                # 创建控制信息（OpenCV不提供范围信息，使用默认值）
                controls.append(ControlInfo(
                    name=name,
                    min_value=0,
                    max_value=100,
                    step=1,
                    default_value=50,
                    current_value=current_int,
                    flags=0,
                    auto_supported=False,
                    description=description
                ))
            
            except Exception:
                # 某些属性可能不被支持
                continue
        
        cap.release()
        return controls
    
    def set_device_control(self, device_index: int, control_name: str, value: int) -> bool:
        """设置设备控制参数"""
        if not self.opencv_available:
            return False
        
        cap = cv2.VideoCapture(device_index)
        if not cap.isOpened():
            return False
        
        # 控制参数名称到OpenCV属性的映射
        control_mapping = {
            "brightness": cv2.CAP_PROP_BRIGHTNESS,
            "contrast": cv2.CAP_PROP_CONTRAST,
            "saturation": cv2.CAP_PROP_SATURATION,
            "hue": cv2.CAP_PROP_HUE,
            "gain": cv2.CAP_PROP_GAIN,
            "exposure": cv2.CAP_PROP_EXPOSURE,
            "white_balance_u": cv2.CAP_PROP_WHITE_BALANCE_BLUE_U,
            "white_balance_v": cv2.CAP_PROP_WHITE_BALANCE_RED_V,
            "gamma": cv2.CAP_PROP_GAMMA,
            "sharpness": cv2.CAP_PROP_SHARPNESS,
            "backlight": cv2.CAP_PROP_BACKLIGHT,
        }
        
        prop_id = control_mapping.get(control_name.lower())
        if prop_id is None:
            cap.release()
            return False
        
        try:
            # 将0-100的值转换为0-1（如果需要）
            if value <= 100:
                normalized_value = value / 100.0
            else:
                normalized_value = value
            
            # 设置属性
            success = cap.set(prop_id, normalized_value)
            cap.release()
            return success
        
        except Exception as e:
            print(f"设置控制参数失败: {e}")
            cap.release()
            return False
    
    def _fourcc_to_string(self, fourcc: int) -> str:
        """将FOURCC代码转换为字符串"""
        try:
            return "".join([chr((fourcc >> 8 * i) & 0xFF) for i in range(4)])
        except:
            return f"0x{fourcc:08X}"


# 测试函数
if __name__ == "__main__":
    controller = OpenCVVideoController()
    
    print("=== 设备列表 ===")
    devices = controller.list_devices()
    for device in devices:
        print(f"{device.index}: {device.name}")
        print(f"    路径: {device.path}")
        print(f"    描述: {device.description}")
        print()
    
    if devices:
        device_index = 0
        print(f"=== 设备 {device_index} 支持的格式 ===")
        formats = controller.get_video_formats(device_index)
        for fmt in formats:
            print(f"[{fmt.pixel_format}] {fmt.width}x{fmt.height} @ {fmt.fps:.1f}fps")
        
        print(f"\n=== 设备 {device_index} 控制参数 ===")
        controls = controller.get_device_controls(device_index)
        for ctrl in controls:
            print(f"{ctrl.name}: {ctrl.current_value} "
                  f"(范围: {ctrl.min_value}-{ctrl.max_value}) - {ctrl.description}")
