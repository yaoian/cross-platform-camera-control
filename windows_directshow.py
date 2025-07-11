#!/usr/bin/env python3
"""
Windows DirectShow视频设备控制实现
基于原C++代码的Python移植版本
"""

import win32com.client
import pythoncom
from win32com.client import constants
import win32api
from typing import List, Dict, Optional, Tuple
from video_device_controller import DeviceInfo, VideoFormat, ControlInfo


class WindowsDirectShowController:
    """Windows DirectShow控制器"""
    
    def __init__(self):
        """初始化DirectShow"""
        try:
            pythoncom.CoInitialize()
            self.com_initialized = True
        except Exception as e:
            print(f"COM初始化失败: {e}")
            self.com_initialized = False
    
    def __del__(self):
        """清理COM资源"""
        if hasattr(self, 'com_initialized') and self.com_initialized:
            try:
                pythoncom.CoUninitialize()
            except:
                pass
    
    def list_devices(self) -> List[DeviceInfo]:
        """枚举视频设备"""
        devices = []

        try:
            # 使用WMI查询视频设备（更简单的方法）
            wmi = win32com.client.GetObject("winmgmts:")
            video_devices = wmi.InstancesOf("Win32_PnPEntity")

            index = 0
            for device in video_devices:
                if device.Name and ("camera" in device.Name.lower() or
                                   "webcam" in device.Name.lower() or
                                   "video" in device.Name.lower()):
                    devices.append(DeviceInfo(
                        index=index,
                        name=device.Name,
                        path=device.DeviceID if device.DeviceID else f"\\\\?\\video{index}",
                        description=f"/dev/video{index}"
                    ))
                    index += 1

        except Exception as e:
            print(f"枚举设备失败: {e}")

            # 备用方法：使用OpenCV检测
            try:
                import cv2
                for i in range(5):  # 检测前5个设备
                    cap = cv2.VideoCapture(i)
                    if cap.isOpened():
                        devices.append(DeviceInfo(
                            index=i,
                            name=f"Video Device {i}",
                            path=f"\\\\?\\video{i}",
                            description=f"/dev/video{i}"
                        ))
                        cap.release()
            except ImportError:
                print("无法导入OpenCV，请安装: pip install opencv-python")

        return devices
    
    def get_video_formats(self, device_index: int) -> List[VideoFormat]:
        """获取设备支持的视频格式"""
        formats = []
        
        try:
            # 获取设备
            device_filter = self._get_device_filter(device_index)
            if not device_filter:
                return formats
            
            # 创建捕获图构建器
            capture_builder = win32com.client.Dispatch("CaptureGraphBuilder2")
            
            # 查找流配置接口
            stream_config = capture_builder.FindInterface(
                None,  # PIN_CATEGORY_CAPTURE
                None,
                device_filter,
                "{C6E13340-30AC-11d0-A18C-00A0C9118956}"  # IID_IAMStreamConfig
            )
            
            if not stream_config:
                return formats
            
            # 获取格式数量和大小
            count, size = stream_config.GetNumberOfCapabilities()
            
            for i in range(count):
                try:
                    # 获取流格式
                    media_type, capabilities = stream_config.GetStreamCaps(i)
                    
                    if media_type and hasattr(media_type, 'formattype'):
                        # 解析视频格式信息
                        format_info = self._parse_video_format(media_type)
                        if format_info:
                            formats.append(format_info)
                
                except Exception as e:
                    print(f"获取格式 {i} 时出错: {e}")
                    continue
        
        except Exception as e:
            print(f"获取视频格式失败: {e}")
        
        return formats
    
    def get_device_controls(self, device_index: int) -> List[ControlInfo]:
        """获取设备控制参数"""
        controls = []
        
        try:
            device_filter = self._get_device_filter(device_index)
            if not device_filter:
                return controls
            
            # 获取视频处理放大器接口
            try:
                video_proc_amp = device_filter.QueryInterface(
                    "{C6E13360-30AC-11d0-A18C-00A0C9118956}"  # IID_IAMVideoProcAmp
                )
                controls.extend(self._get_video_proc_controls(video_proc_amp))
            except:
                pass
            
            # 获取摄像头控制接口
            try:
                camera_control = device_filter.QueryInterface(
                    "{C6E13370-30AC-11d0-A18C-00A0C9118956}"  # IID_IAMCameraControl
                )
                controls.extend(self._get_camera_controls(camera_control))
            except:
                pass
        
        except Exception as e:
            print(f"获取设备控制参数失败: {e}")
        
        return controls
    
    def set_device_control(self, device_index: int, control_name: str, value: int) -> bool:
        """设置设备控制参数"""
        try:
            device_filter = self._get_device_filter(device_index)
            if not device_filter:
                return False
            
            # 尝试设置视频处理参数
            if self._set_video_proc_control(device_filter, control_name, value):
                return True
            
            # 尝试设置摄像头控制参数
            if self._set_camera_control(device_filter, control_name, value):
                return True
        
        except Exception as e:
            print(f"设置控制参数失败: {e}")
        
        return False
    
    def _get_device_filter(self, device_index: int):
        """获取指定索引的设备过滤器"""
        try:
            device_enum = win32com.client.Dispatch("SystemDeviceEnum")
            video_enum = device_enum.CreateClassEnumerator(
                "{860BB310-5D01-11d0-BD3B-00A0C911CE86}"
            )
            
            if not video_enum:
                return None
            
            # 跳到指定设备
            for i in range(device_index + 1):
                moniker = video_enum.Next(1)
                if not moniker:
                    return None
                
                if i == device_index:
                    # 绑定到设备过滤器
                    return moniker[0].BindToObject(
                        None, None, "{56A86895-0AD4-11CE-B03A-0020AF0BA770}"  # IID_IBaseFilter
                    )
        
        except Exception as e:
            print(f"获取设备过滤器失败: {e}")
        
        return None
    
    def _parse_video_format(self, media_type) -> Optional[VideoFormat]:
        """解析视频格式信息"""
        try:
            # 这里需要解析DirectShow的媒体类型
            # 由于COM接口的复杂性，这里提供简化实现
            return VideoFormat(
                width=640,  # 默认值，实际需要从media_type解析
                height=480,
                fps=30.0,
                pixel_format="UNKNOWN",
                description="DirectShow Format"
            )
        except:
            return None
    
    def _get_video_proc_controls(self, video_proc_amp) -> List[ControlInfo]:
        """获取视频处理控制参数"""
        controls = []
        
        # DirectShow视频处理参数映射
        proc_controls = {
            0: "brightness",
            1: "contrast", 
            2: "hue",
            3: "saturation",
            4: "sharpness",
            5: "gamma",
            6: "colorEnable",
            7: "whiteBalance",
            8: "backlight_compensation",
            9: "gain"
        }
        
        for proc_id, name in proc_controls.items():
            try:
                # 获取参数范围
                min_val, max_val, step, default, flags = video_proc_amp.GetRange(proc_id)
                
                # 获取当前值
                current_val, current_flags = video_proc_amp.Get(proc_id)
                
                controls.append(ControlInfo(
                    name=name,
                    min_value=min_val,
                    max_value=max_val,
                    step=step,
                    default_value=default,
                    current_value=current_val,
                    flags=current_flags,
                    auto_supported=(flags & 0x0001) != 0  # VideoProcAmp_Flags_Auto
                ))
            
            except:
                continue
        
        return controls
    
    def _get_camera_controls(self, camera_control) -> List[ControlInfo]:
        """获取摄像头控制参数"""
        controls = []
        
        # DirectShow摄像头控制参数映射
        camera_controls = {
            0: "pan",
            1: "tilt",
            2: "roll", 
            3: "zoom",
            4: "exposure",
            5: "iris",
            6: "focus"
        }
        
        for ctrl_id, name in camera_controls.items():
            try:
                # 获取参数范围
                min_val, max_val, step, default, flags = camera_control.GetRange(ctrl_id)
                
                # 获取当前值
                current_val, current_flags = camera_control.Get(ctrl_id)
                
                controls.append(ControlInfo(
                    name=name,
                    min_value=min_val,
                    max_value=max_val,
                    step=step,
                    default_value=default,
                    current_value=current_val,
                    flags=current_flags,
                    auto_supported=(flags & 0x0001) != 0
                ))
            
            except:
                continue
        
        return controls
    
    def _set_video_proc_control(self, device_filter, control_name: str, value: int) -> bool:
        """设置视频处理控制参数"""
        # TODO: 实现视频处理参数设置
        return False
    
    def _set_camera_control(self, device_filter, control_name: str, value: int) -> bool:
        """设置摄像头控制参数"""
        # TODO: 实现摄像头控制参数设置
        return False
