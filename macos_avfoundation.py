#!/usr/bin/env python3
"""
macOS AVFoundation视频设备控制实现
使用AVFoundation框架进行摄像头控制
"""

import platform
from typing import List, Dict, Optional, Tuple
from video_device_controller import DeviceInfo, VideoFormat, ControlInfo

# 检查是否在macOS上
if platform.system() == "Darwin":
    try:
        import objc
        from Foundation import NSObject, NSArray
        from AVFoundation import (
            AVCaptureDevice, AVCaptureDeviceTypeBuiltInWideAngleCamera,
            AVCaptureDeviceTypeExternalUnknown, AVMediaTypeVideo,
            AVCaptureSessionPresetLow, AVCaptureSessionPresetMedium,
            AVCaptureSessionPresetHigh, AVCaptureSessionPreset640x480,
            AVCaptureSessionPreset1280x720, AVCaptureSessionPreset1920x1080
        )
        AVFOUNDATION_AVAILABLE = True
    except ImportError:
        AVFOUNDATION_AVAILABLE = False
        print("AVFoundation不可用，请安装pyobjc: pip install pyobjc pyobjc-framework-AVFoundation")
else:
    AVFOUNDATION_AVAILABLE = False


class MacOSAVFoundationController:
    """macOS AVFoundation控制器"""
    
    def __init__(self):
        """初始化AVFoundation控制器"""
        if not AVFOUNDATION_AVAILABLE:
            raise ImportError("AVFoundation框架不可用")
        
        self.devices_cache = None
    
    def list_devices(self) -> List[DeviceInfo]:
        """枚举AVFoundation设备"""
        devices = []
        
        if not AVFOUNDATION_AVAILABLE:
            return devices
        
        try:
            # 获取所有视频设备
            discovery_session = AVCaptureDevice.discoverySessionWithDeviceTypes_mediaType_position_(
                [AVCaptureDeviceTypeBuiltInWideAngleCamera, AVCaptureDeviceTypeExternalUnknown],
                AVMediaTypeVideo,
                0  # AVCaptureDevicePositionUnspecified
            )
            
            av_devices = discovery_session.devices()
            
            for i, device in enumerate(av_devices):
                device_name = str(device.localizedName())
                device_id = str(device.uniqueID())
                manufacturer = str(device.manufacturer()) if hasattr(device, 'manufacturer') else "Apple"
                
                devices.append(DeviceInfo(
                    index=i,
                    name=device_name,
                    path=device_id,
                    description=f"Manufacturer: {manufacturer}"
                ))
            
            self.devices_cache = av_devices
            
        except Exception as e:
            print(f"AVFoundation设备枚举失败: {e}")
        
        return devices
    
    def get_video_formats(self, device_index: int) -> List[VideoFormat]:
        """获取设备支持的视频格式"""
        formats = []
        
        if not AVFOUNDATION_AVAILABLE:
            return formats
        
        try:
            # 确保设备缓存存在
            if self.devices_cache is None:
                self.list_devices()
            
            if not self.devices_cache or device_index >= len(self.devices_cache):
                return formats
            
            device = self.devices_cache[device_index]
            
            # 获取设备支持的格式
            supported_formats = device.formats()
            
            for fmt in supported_formats:
                # 获取媒体类型
                media_type = fmt.mediaType()
                if media_type != AVMediaTypeVideo:
                    continue
                
                # 获取格式描述
                format_description = fmt.formatDescription()
                
                # 获取分辨率
                dimensions = format_description.videoDimensions()
                width = dimensions.width
                height = dimensions.height
                
                # 获取像素格式
                pixel_format = format_description.mediaSubType()
                pixel_format_str = self._fourcc_to_string(pixel_format)
                
                # 获取支持的帧率范围
                frame_rate_ranges = fmt.videoSupportedFrameRateRanges()
                
                for rate_range in frame_rate_ranges:
                    min_fps = rate_range.minFrameRate()
                    max_fps = rate_range.maxFrameRate()
                    
                    # 添加常见帧率
                    common_fps = [15.0, 24.0, 30.0, 60.0]
                    for fps in common_fps:
                        if min_fps <= fps <= max_fps:
                            formats.append(VideoFormat(
                                width=int(width),
                                height=int(height),
                                fps=fps,
                                pixel_format=pixel_format_str,
                                description=f"{width}x{height} @ {fps:.1f}fps ({pixel_format_str})"
                            ))
            
        except Exception as e:
            print(f"获取AVFoundation格式失败: {e}")
        
        return formats
    
    def get_device_controls(self, device_index: int) -> List[ControlInfo]:
        """获取设备控制参数"""
        controls = []
        
        if not AVFOUNDATION_AVAILABLE:
            return controls
        
        try:
            # 确保设备缓存存在
            if self.devices_cache is None:
                self.list_devices()
            
            if not self.devices_cache or device_index >= len(self.devices_cache):
                return controls
            
            device = self.devices_cache[device_index]
            
            # 检查设备支持的控制功能
            control_checks = [
                ('brightness', 'isBrightnessSupported', 'brightness', 'setBrightness:'),
                ('contrast', 'isContrastSupported', 'contrast', 'setContrast:'),
                ('saturation', 'isSaturationSupported', 'saturation', 'setSaturation:'),
                ('exposure', 'isExposureModeSupported:', 'exposureDuration', 'setExposureTargetBias:completionHandler:'),
                ('focus', 'isFocusModeSupported:', 'lensPosition', 'setFocusModeLockedWithLensPosition:completionHandler:'),
                ('white_balance', 'isWhiteBalanceModeSupported:', 'deviceWhiteBalanceGains', 'setWhiteBalanceModeLockedWithDeviceWhiteBalanceGains:completionHandler:'),
                ('zoom', 'isRampingVideoZoom', 'videoZoomFactor', 'rampToVideoZoomFactor:withRate:'),
            ]
            
            for name, check_method, get_method, set_method in control_checks:
                try:
                    # 检查是否支持该控制
                    if hasattr(device, check_method):
                        if check_method.endswith(':'):
                            # 需要参数的方法，使用默认参数
                            supported = getattr(device, check_method.rstrip(':'))(0)
                        else:
                            supported = getattr(device, check_method)()
                        
                        if supported:
                            # 获取当前值
                            current_value = 0
                            if hasattr(device, get_method):
                                try:
                                    current_value = float(getattr(device, get_method)())
                                    current_value = int(current_value * 100)  # 转换为0-100范围
                                except:
                                    current_value = 50  # 默认值
                            
                            controls.append(ControlInfo(
                                name=name,
                                min_value=0,
                                max_value=100,
                                step=1,
                                default_value=50,
                                current_value=current_value,
                                flags=0,
                                auto_supported=True,
                                description=f"AVFoundation {name.title()} Control"
                            ))
                
                except Exception as e:
                    print(f"检查控制 {name} 时出错: {e}")
                    continue
            
        except Exception as e:
            print(f"获取AVFoundation控制参数失败: {e}")
        
        return controls
    
    def set_device_control(self, device_index: int, control_name: str, value: int) -> bool:
        """设置设备控制参数"""
        if not AVFOUNDATION_AVAILABLE:
            return False
        
        try:
            # 确保设备缓存存在
            if self.devices_cache is None:
                self.list_devices()
            
            if not self.devices_cache or device_index >= len(self.devices_cache):
                return False
            
            device = self.devices_cache[device_index]
            
            # 锁定设备配置
            if not device.lockForConfiguration_(None):
                return False
            
            try:
                # 将0-100的值转换为0.0-1.0
                normalized_value = value / 100.0
                
                # 根据控制名称设置相应参数
                if control_name == 'brightness' and hasattr(device, 'setBrightness:'):
                    device.setBrightness_(normalized_value)
                elif control_name == 'contrast' and hasattr(device, 'setContrast:'):
                    device.setContrast_(normalized_value)
                elif control_name == 'saturation' and hasattr(device, 'setSaturation:'):
                    device.setSaturation_(normalized_value)
                elif control_name == 'zoom' and hasattr(device, 'setVideoZoomFactor:'):
                    # 缩放因子通常是1.0-设备最大值
                    max_zoom = device.activeFormat().videoMaxZoomFactor()
                    zoom_factor = 1.0 + (normalized_value * (max_zoom - 1.0))
                    device.setVideoZoomFactor_(zoom_factor)
                else:
                    return False
                
                return True
                
            finally:
                device.unlockForConfiguration()
            
        except Exception as e:
            print(f"设置AVFoundation控制参数失败: {e}")
            return False
    
    def _fourcc_to_string(self, fourcc: int) -> str:
        """将FOURCC代码转换为字符串"""
        try:
            chars = []
            for i in range(4):
                char_code = (fourcc >> (8 * (3 - i))) & 0xFF
                if 32 <= char_code <= 126:  # 可打印ASCII字符
                    chars.append(chr(char_code))
                else:
                    chars.append('?')
            return ''.join(chars)
        except:
            return f"0x{fourcc:08X}"


# 测试函数
if __name__ == "__main__":
    if AVFOUNDATION_AVAILABLE:
        controller = MacOSAVFoundationController()
        
        print("=== macOS AVFoundation设备测试 ===")
        devices = controller.list_devices()
        for device in devices:
            print(f"设备 {device.index}: {device.name}")
            print(f"  路径: {device.path}")
            print(f"  描述: {device.description}")
            print()
        
        if devices:
            device_index = 0
            print(f"=== 设备 {device_index} 格式测试 ===")
            formats = controller.get_video_formats(device_index)
            for fmt in formats[:5]:  # 只显示前5个格式
                print(f"[{fmt.pixel_format}] {fmt.width}x{fmt.height} @ {fmt.fps:.1f}fps")
            
            print(f"\n=== 设备 {device_index} 控制参数测试 ===")
            controls = controller.get_device_controls(device_index)
            for ctrl in controls:
                print(f"{ctrl.name}: {ctrl.current_value} (范围: {ctrl.min_value}-{ctrl.max_value})")
    else:
        print("AVFoundation不可用，无法进行测试")
