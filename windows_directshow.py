#!/usr/bin/env python3
"""
Windows DirectShow视频设备控制实现
基于原C++代码的Python移植版本
"""

import win32com.client
import pythoncom
from win32com.client import constants
import win32api
import struct
import ctypes
from ctypes import wintypes
from typing import List, Dict, Optional, Tuple
from video_device_controller import DeviceInfo, VideoFormat, ControlInfo

# DirectShow常量定义
CLSID_SystemDeviceEnum = "{62BE5D10-60EB-11d0-BD3B-00A0C911CE86}"
CLSID_VideoInputDeviceCategory = "{860BB310-5D01-11d0-BD3B-00A0C911CE86}"
CLSID_CaptureGraphBuilder2 = "{BF87B6E1-8C27-11d0-B3F0-00AA003761C5}"

IID_IBaseFilter = "{56A86895-0AD4-11CE-B03A-0020AF0BA770}"
IID_IAMStreamConfig = "{C6E13340-30AC-11d0-A18C-00A0C9118956}"
IID_IAMVideoProcAmp = "{C6E13360-30AC-11d0-A18C-00A0C9118956}"
IID_IAMCameraControl = "{C6E13370-30AC-11d0-A18C-00A0C9118956}"
IID_IPropertyBag = "{55272A00-42CB-11CE-8135-00AA004BB851}"

# 媒体类型常量
MEDIATYPE_Video = "{73646976-0000-0010-8000-00AA00389B71}"
FORMAT_VideoInfo = "{05589F80-C356-11CE-BF01-00AA0055595A}"

# VideoProcAmp属性
VideoProcAmp_Brightness = 0
VideoProcAmp_Contrast = 1
VideoProcAmp_Hue = 2
VideoProcAmp_Saturation = 3
VideoProcAmp_Sharpness = 4
VideoProcAmp_Gamma = 5
VideoProcAmp_ColorEnable = 6
VideoProcAmp_WhiteBalance = 7
VideoProcAmp_BacklightCompensation = 8
VideoProcAmp_Gain = 9

# CameraControl属性
CameraControl_Pan = 0
CameraControl_Tilt = 1
CameraControl_Roll = 2
CameraControl_Zoom = 3
CameraControl_Exposure = 4
CameraControl_Iris = 5
CameraControl_Focus = 6

# 控制标志
VideoProcAmp_Flags_Auto = 0x0001
VideoProcAmp_Flags_Manual = 0x0002


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
            # 使用DirectShow API枚举设备
            devices = self._enumerate_directshow_devices()
            if devices:
                return devices
        except Exception as e:
            print(f"DirectShow枚举失败: {e}")

        try:
            # 备用方法：使用WMI查询视频设备
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
            print(f"WMI枚举失败: {e}")

            # 最后备用方法：使用OpenCV检测
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

    def _enumerate_directshow_devices(self) -> List[DeviceInfo]:
        """使用DirectShow API枚举设备"""
        devices = []

        # 暂时禁用DirectShow枚举，因为COM接口调用复杂
        # 后续可以通过ctypes或其他方式实现
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
            # 确保COM已初始化
            pythoncom.CoInitialize()

            # 创建设备枚举器
            device_enum = pythoncom.CoCreateInstance(
                CLSID_SystemDeviceEnum,
                None,
                pythoncom.CLSCTX_INPROC_SERVER,
                pythoncom.IID_IUnknown
            )

            # 获取视频输入设备类别枚举器
            video_enum = device_enum.CreateClassEnumerator(
                CLSID_VideoInputDeviceCategory, 0
            )

            if not video_enum:
                return None

            # 跳到指定设备
            current_index = 0
            while True:
                try:
                    moniker = video_enum.Next(1)
                    if not moniker:
                        break

                    if current_index == device_index:
                        # 绑定到设备过滤器
                        device_filter = moniker[0].BindToObject(
                            None, None, IID_IBaseFilter
                        )
                        return device_filter

                    current_index += 1

                except Exception as e:
                    print(f"处理设备 {current_index} 时出错: {e}")
                    break

        except Exception as e:
            print(f"获取设备过滤器失败: {e}")

        return None
    
    def _parse_video_format(self, media_type) -> Optional[VideoFormat]:
        """解析视频格式信息"""
        try:
            # 检查媒体类型是否为视频
            if not hasattr(media_type, 'majortype') or media_type.majortype != MEDIATYPE_Video:
                return None

            # 检查格式类型
            if not hasattr(media_type, 'formattype') or media_type.formattype != FORMAT_VideoInfo:
                return None

            # 获取格式数据
            if not hasattr(media_type, 'pbFormat') or not media_type.pbFormat:
                return None

            # 解析VIDEOINFOHEADER结构
            format_data = media_type.pbFormat

            # VIDEOINFOHEADER结构解析
            # 前64字节是RECT结构（源矩形和目标矩形）
            # 接下来8字节是时间信息
            # 然后是BITMAPINFOHEADER

            # 跳过RECT结构（32字节）和时间信息（8字节）
            bitmap_offset = 40  # VIDEOINFOHEADER中BITMAPINFOHEADER的偏移

            if len(format_data) < bitmap_offset + 40:  # BITMAPINFOHEADER最小40字节
                return None

            # 解析BITMAPINFOHEADER
            bitmap_data = format_data[bitmap_offset:]

            # BITMAPINFOHEADER结构：
            # DWORD biSize (4字节)
            # LONG biWidth (4字节)
            # LONG biHeight (4字节)
            # WORD biPlanes (2字节)
            # WORD biBitCount (2字节)
            # DWORD biCompression (4字节)
            # ...

            width = struct.unpack('<L', bitmap_data[4:8])[0]  # biWidth
            height = struct.unpack('<l', bitmap_data[8:12])[0]  # biHeight (可能为负)
            height = abs(height)  # 取绝对值
            bit_count = struct.unpack('<H', bitmap_data[14:16])[0]  # biBitCount
            compression = struct.unpack('<L', bitmap_data[16:20])[0]  # biCompression

            # 解析像素格式
            pixel_format = self._fourcc_to_string(compression)
            if pixel_format == "\x00\x00\x00\x00":
                pixel_format = f"RGB{bit_count}"

            # 计算帧率（从AvgTimePerFrame）
            fps = 30.0  # 默认帧率
            try:
                # AvgTimePerFrame在VIDEOINFOHEADER的偏移32处（8字节）
                if len(format_data) >= 40:
                    avg_time_per_frame = struct.unpack('<Q', format_data[32:40])[0]
                    if avg_time_per_frame > 0:
                        # 时间单位是100纳秒
                        fps = 10000000.0 / avg_time_per_frame
            except:
                pass

            return VideoFormat(
                width=width,
                height=height,
                fps=fps,
                pixel_format=pixel_format,
                description=f"{width}x{height} @ {fps:.1f}fps ({pixel_format})"
            )

        except Exception as e:
            print(f"解析视频格式失败: {e}")
            return None

    def _fourcc_to_string(self, fourcc: int) -> str:
        """将FOURCC代码转换为字符串"""
        try:
            # 将32位整数转换为4个字符
            chars = []
            for i in range(4):
                char_code = (fourcc >> (8 * i)) & 0xFF
                if 32 <= char_code <= 126:  # 可打印ASCII字符
                    chars.append(chr(char_code))
                else:
                    chars.append('?')
            return ''.join(chars)
        except:
            return f"0x{fourcc:08X}"
    
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
        try:
            # 获取视频处理放大器接口
            video_proc_amp = device_filter.QueryInterface(IID_IAMVideoProcAmp)

            # 控制参数名称映射
            control_mapping = {
                "brightness": VideoProcAmp_Brightness,
                "contrast": VideoProcAmp_Contrast,
                "hue": VideoProcAmp_Hue,
                "saturation": VideoProcAmp_Saturation,
                "sharpness": VideoProcAmp_Sharpness,
                "gamma": VideoProcAmp_Gamma,
                "colorEnable": VideoProcAmp_ColorEnable,
                "whiteBalance": VideoProcAmp_WhiteBalance,
                "backlight_compensation": VideoProcAmp_BacklightCompensation,
                "gain": VideoProcAmp_Gain
            }

            # 处理自动模式
            auto_mode = False
            if control_name.endswith("_automatic"):
                control_name = control_name.replace("_automatic", "")
                auto_mode = True

            prop_id = control_mapping.get(control_name.lower())
            if prop_id is None:
                return False

            # 获取当前值和标志
            current_val, current_flags = video_proc_amp.Get(prop_id)

            if auto_mode:
                # 设置自动/手动模式
                flags = VideoProcAmp_Flags_Auto if value == 1 else VideoProcAmp_Flags_Manual
                video_proc_amp.Set(prop_id, current_val, flags)
            else:
                # 设置具体数值
                video_proc_amp.Set(prop_id, value, current_flags)

            return True

        except Exception as e:
            print(f"设置视频处理参数失败: {e}")
            return False

    def _set_camera_control(self, device_filter, control_name: str, value: int) -> bool:
        """设置摄像头控制参数"""
        try:
            # 获取摄像头控制接口
            camera_control = device_filter.QueryInterface(IID_IAMCameraControl)

            # 控制参数名称映射
            control_mapping = {
                "pan": CameraControl_Pan,
                "tilt": CameraControl_Tilt,
                "roll": CameraControl_Roll,
                "zoom": CameraControl_Zoom,
                "exposure": CameraControl_Exposure,
                "iris": CameraControl_Iris,
                "focus": CameraControl_Focus
            }

            # 处理自动模式
            auto_mode = False
            if control_name.endswith("_automatic"):
                control_name = control_name.replace("_automatic", "")
                auto_mode = True

            prop_id = control_mapping.get(control_name.lower())
            if prop_id is None:
                return False

            # 获取当前值和标志
            current_val, current_flags = camera_control.Get(prop_id)

            if auto_mode:
                # 设置自动/手动模式
                flags = VideoProcAmp_Flags_Auto if value == 1 else VideoProcAmp_Flags_Manual
                camera_control.Set(prop_id, current_val, flags)
            else:
                # 设置具体数值
                camera_control.Set(prop_id, value, current_flags)

            return True

        except Exception as e:
            print(f"设置摄像头控制参数失败: {e}")
            return False
