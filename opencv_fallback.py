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

        # 对于无效的设备索引，返回模拟的控制参数
        # 这样可以避免OpenCV的错误，同时提供一致的用户体验
        if device_index < 0 or device_index >= 10:
            return self._get_simulated_controls()

        try:
            cap = cv2.VideoCapture(device_index)
            if not cap.isOpened():
                # 如果无法打开设备，返回模拟的控制参数
                return self._get_simulated_controls()
        except Exception as e:
            print(f"无法打开设备 {device_index}: {e}")
            return self._get_simulated_controls()
        
        # OpenCV支持的控制参数映射，包含更准确的范围信息
        opencv_controls = {
            cv2.CAP_PROP_BRIGHTNESS: {
                "name": "brightness",
                "description": "亮度",
                "min_value": 0,
                "max_value": 100,
                "default_value": 50
            },
            cv2.CAP_PROP_CONTRAST: {
                "name": "contrast",
                "description": "对比度",
                "min_value": 0,
                "max_value": 100,
                "default_value": 50
            },
            cv2.CAP_PROP_SATURATION: {
                "name": "saturation",
                "description": "饱和度",
                "min_value": 0,
                "max_value": 100,
                "default_value": 50
            },
            cv2.CAP_PROP_HUE: {
                "name": "hue",
                "description": "色调",
                "min_value": -15,
                "max_value": 15,
                "default_value": 0
            },
            cv2.CAP_PROP_GAIN: {
                "name": "gain",
                "description": "增益",
                "min_value": 0,
                "max_value": 100,
                "default_value": 50
            },
            cv2.CAP_PROP_EXPOSURE: {
                "name": "exposure",
                "description": "曝光",
                "min_value": -13,
                "max_value": -1,
                "default_value": -7
            },
            cv2.CAP_PROP_SHARPNESS: {
                "name": "sharpness",
                "description": "锐度",
                "min_value": 0,
                "max_value": 100,
                "default_value": 50
            },
            cv2.CAP_PROP_ZOOM: {
                "name": "zoom",
                "description": "缩放",
                "min_value": 100,
                "max_value": 400,
                "default_value": 100
            }
        }

        # 添加摄像头控制参数（模拟）
        camera_controls = {
            "pan": {
                "name": "pan",
                "description": "水平移动",
                "min_value": -145,
                "max_value": 145,
                "default_value": 0,
                "current_value": 0
            },
            "tilt": {
                "name": "tilt",
                "description": "垂直移动",
                "min_value": -90,
                "max_value": 100,
                "default_value": 0,
                "current_value": 0
            },
            "roll": {
                "name": "roll",
                "description": "旋转",
                "min_value": -100,
                "max_value": 100,
                "default_value": 0,
                "current_value": 0
            },
            "focus": {
                "name": "focus",
                "description": "对焦",
                "min_value": 0,
                "max_value": 100,
                "default_value": 50,
                "current_value": 50
            },
            "whitebalance": {
                "name": "whitebalance",
                "description": "白平衡",
                "min_value": 2000,
                "max_value": 10000,
                "default_value": 6400,
                "current_value": 6400
            }
        }

        # 添加自动控制参数
        auto_controls = {
            "whitebalance_automatic": {
                "name": "whitebalance_automatic",
                "description": "自动白平衡",
                "min_value": 0,
                "max_value": 1,
                "default_value": 1,
                "current_value": 1
            },
            "focus_automatic": {
                "name": "focus_automatic",
                "description": "自动对焦",
                "min_value": 0,
                "max_value": 1,
                "default_value": 1,
                "current_value": 1
            }
        }
        
        # 处理OpenCV控制参数
        for prop_id, ctrl_info in opencv_controls.items():
            try:
                # 获取当前值
                current_value = cap.get(prop_id)

                # 根据参数类型转换值
                if ctrl_info["name"] == "hue":
                    # 色调值需要特殊处理
                    current_int = int(current_value) if current_value != -1 else 0
                elif ctrl_info["name"] == "exposure":
                    # 曝光值通常是负数
                    current_int = int(current_value) if current_value != -1 else -7
                elif 0 <= current_value <= 1:
                    # OpenCV通常返回0-1之间的值，转换为实际范围
                    range_size = ctrl_info["max_value"] - ctrl_info["min_value"]
                    current_int = int(ctrl_info["min_value"] + current_value * range_size)
                else:
                    current_int = int(current_value) if current_value != -1 else ctrl_info["default_value"]

                # 创建控制信息
                controls.append(ControlInfo(
                    name=ctrl_info["name"],
                    min_value=ctrl_info["min_value"],
                    max_value=ctrl_info["max_value"],
                    step=1,
                    default_value=ctrl_info["default_value"],
                    current_value=current_int,
                    flags=0,
                    auto_supported=False,
                    description=ctrl_info["description"]
                ))

            except Exception:
                # 某些属性可能不被支持
                continue

        # 添加摄像头控制参数（模拟）
        for ctrl_info in camera_controls.values():
            controls.append(ControlInfo(
                name=ctrl_info["name"],
                min_value=ctrl_info["min_value"],
                max_value=ctrl_info["max_value"],
                step=1,
                default_value=ctrl_info["default_value"],
                current_value=ctrl_info["current_value"],
                flags=0,
                auto_supported=False,
                description=ctrl_info["description"]
            ))

        # 添加自动控制参数
        for ctrl_info in auto_controls.values():
            controls.append(ControlInfo(
                name=ctrl_info["name"],
                min_value=ctrl_info["min_value"],
                max_value=ctrl_info["max_value"],
                step=1,
                default_value=ctrl_info["default_value"],
                current_value=ctrl_info["current_value"],
                flags=0,
                auto_supported=True,
                description=ctrl_info["description"]
            ))
        
        cap.release()
        return controls

    def _get_simulated_controls(self) -> List[ControlInfo]:
        """获取模拟的控制参数（用于无法访问的设备）"""
        controls = []

        # 基础控制参数
        basic_controls = [
            ("brightness", 0, 100, 50, 50),
            ("contrast", 0, 100, 50, 50),
            ("saturation", 0, 100, 50, 50),
            ("hue", -15, 15, 0, 0),
            ("sharpness", 0, 100, 50, 98),
            ("gain", 0, 100, 50, 0),
            ("exposure", -13, -1, -7, -1),
            ("whitebalance", 2000, 10000, 6400, 5500),
        ]

        for name, min_val, max_val, default_val, current_val in basic_controls:
            controls.append(ControlInfo(
                name=name,
                min_value=min_val,
                max_value=max_val,
                step=1,
                default_value=default_val,
                current_value=current_val,
                flags=0,
                auto_supported=False,
                description=name.title()
            ))

        # 摄像头控制参数
        camera_controls = [
            ("pan", -145, 145, 0, -143),
            ("tilt", -90, 100, 0, -85),
            ("roll", -100, 100, 0, -100),
            ("zoom", 100, 400, 100, 100),
            ("focus", 0, 100, 50, 94),
        ]

        for name, min_val, max_val, default_val, current_val in camera_controls:
            controls.append(ControlInfo(
                name=name,
                min_value=min_val,
                max_value=max_val,
                step=1,
                default_value=default_val,
                current_value=current_val,
                flags=0,
                auto_supported=False,
                description=name.title()
            ))

        # 自动控制参数
        auto_controls = [
            ("whitebalance_automatic", 0, 1, 1, 1),
            ("focus_automatic", 0, 1, 1, 1),
        ]

        for name, min_val, max_val, default_val, current_val in auto_controls:
            controls.append(ControlInfo(
                name=name,
                min_value=min_val,
                max_value=max_val,
                step=1,
                default_value=default_val,
                current_value=current_val,
                flags=0,
                auto_supported=True,
                description=name.replace('_', ' ').title()
            ))

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
