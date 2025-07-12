#!/usr/bin/env python3
"""
Linux V4L2视频设备控制实现
真正的V4L2 API支持
"""

import os
import glob
import fcntl
import struct
import ctypes
from typing import List, Dict, Optional, Tuple
from video_device_controller import DeviceInfo, VideoFormat, ControlInfo

# V4L2常量定义
VIDIOC_QUERYCAP = 0x80685600
VIDIOC_ENUM_FMT = 0xC0405602
VIDIOC_ENUM_FRAMESIZES = 0xC02C561A
VIDIOC_ENUM_FRAMEINTERVALS = 0xC034561B
VIDIOC_QUERYCTRL = 0xC0445624
VIDIOC_G_CTRL = 0xC008561B
VIDIOC_S_CTRL = 0xC008561C

# V4L2结构体大小
V4L2_CAP_STRUCT_SIZE = 104
V4L2_FMTDESC_STRUCT_SIZE = 64
V4L2_FRMSIZEENUM_STRUCT_SIZE = 44
V4L2_FRMIVALENUM_STRUCT_SIZE = 52
V4L2_QUERYCTRL_STRUCT_SIZE = 68
V4L2_CONTROL_STRUCT_SIZE = 8

# V4L2像素格式
V4L2_PIX_FMT_YUYV = 0x56595559
V4L2_PIX_FMT_MJPEG = 0x47504A4D
V4L2_PIX_FMT_RGB24 = 0x33424752
V4L2_PIX_FMT_BGR24 = 0x33524742

# V4L2控制类型
V4L2_CTRL_TYPE_INTEGER = 1
V4L2_CTRL_TYPE_BOOLEAN = 2
V4L2_CTRL_TYPE_MENU = 3

# V4L2控制ID
V4L2_CID_BASE = 0x00980900
V4L2_CID_BRIGHTNESS = V4L2_CID_BASE + 0
V4L2_CID_CONTRAST = V4L2_CID_BASE + 1
V4L2_CID_SATURATION = V4L2_CID_BASE + 2
V4L2_CID_HUE = V4L2_CID_BASE + 3
V4L2_CID_AUDIO_VOLUME = V4L2_CID_BASE + 5
V4L2_CID_AUDIO_BALANCE = V4L2_CID_BASE + 6
V4L2_CID_AUDIO_BASS = V4L2_CID_BASE + 7
V4L2_CID_AUDIO_TREBLE = V4L2_CID_BASE + 8
V4L2_CID_AUDIO_MUTE = V4L2_CID_BASE + 9
V4L2_CID_AUTO_WHITE_BALANCE = V4L2_CID_BASE + 12
V4L2_CID_DO_WHITE_BALANCE = V4L2_CID_BASE + 13
V4L2_CID_RED_BALANCE = V4L2_CID_BASE + 14
V4L2_CID_BLUE_BALANCE = V4L2_CID_BASE + 15
V4L2_CID_GAMMA = V4L2_CID_BASE + 16
V4L2_CID_WHITENESS = V4L2_CID_BASE + 17
V4L2_CID_EXPOSURE = V4L2_CID_BASE + 18
V4L2_CID_AUTOGAIN = V4L2_CID_BASE + 19
V4L2_CID_GAIN = V4L2_CID_BASE + 20
V4L2_CID_HFLIP = V4L2_CID_BASE + 21
V4L2_CID_VFLIP = V4L2_CID_BASE + 22

# 摄像头控制ID
V4L2_CID_CAMERA_CLASS_BASE = 0x009A0900
V4L2_CID_EXPOSURE_AUTO = V4L2_CID_CAMERA_CLASS_BASE + 1
V4L2_CID_EXPOSURE_ABSOLUTE = V4L2_CID_CAMERA_CLASS_BASE + 2
V4L2_CID_FOCUS_ABSOLUTE = V4L2_CID_CAMERA_CLASS_BASE + 10
V4L2_CID_FOCUS_AUTO = V4L2_CID_CAMERA_CLASS_BASE + 12
V4L2_CID_ZOOM_ABSOLUTE = V4L2_CID_CAMERA_CLASS_BASE + 13
V4L2_CID_ZOOM_RELATIVE = V4L2_CID_CAMERA_CLASS_BASE + 14
V4L2_CID_PAN_ABSOLUTE = V4L2_CID_CAMERA_CLASS_BASE + 15
V4L2_CID_TILT_ABSOLUTE = V4L2_CID_CAMERA_CLASS_BASE + 16


class LinuxV4L2Controller:
    """Linux V4L2控制器"""
    
    def __init__(self):
        """初始化V4L2控制器"""
        self.device_files = {}  # 缓存打开的设备文件
    
    def __del__(self):
        """清理资源"""
        for fd in self.device_files.values():
            try:
                os.close(fd)
            except:
                pass
    
    def list_devices(self) -> List[DeviceInfo]:
        """枚举V4L2设备"""
        devices = []
        
        try:
            # 查找所有/dev/video*设备
            device_files = glob.glob("/dev/video*")
            device_files.sort()
            
            for i, device_path in enumerate(device_files):
                try:
                    # 尝试打开设备获取信息
                    fd = os.open(device_path, os.O_RDWR)
                    
                    # 查询设备能力
                    cap_data = self._query_capability(fd)
                    if cap_data:
                        device_name = cap_data.get('card', f'Video Device {i}')
                        driver = cap_data.get('driver', 'unknown')
                        
                        devices.append(DeviceInfo(
                            index=i,
                            name=device_name,
                            path=device_path,
                            description=f"Driver: {driver}"
                        ))
                    
                    os.close(fd)
                    
                except Exception as e:
                    # 设备可能被占用或无权限，跳过
                    continue
        
        except Exception as e:
            print(f"V4L2设备枚举失败: {e}")
        
        return devices
    
    def get_video_formats(self, device_index: int) -> List[VideoFormat]:
        """获取设备支持的视频格式"""
        formats = []
        
        try:
            device_path = f"/dev/video{device_index}"
            if not os.path.exists(device_path):
                return formats
            
            fd = os.open(device_path, os.O_RDWR)
            
            # 枚举像素格式
            fmt_index = 0
            while True:
                try:
                    fmt_data = self._enum_format(fd, fmt_index)
                    if not fmt_data:
                        break
                    
                    pixel_format = fmt_data['pixelformat']
                    description = fmt_data['description']
                    
                    # 枚举帧大小
                    frame_sizes = self._enum_frame_sizes(fd, pixel_format)
                    
                    for width, height in frame_sizes:
                        # 枚举帧率
                        frame_rates = self._enum_frame_intervals(fd, pixel_format, width, height)
                        
                        for fps in frame_rates:
                            formats.append(VideoFormat(
                                width=width,
                                height=height,
                                fps=fps,
                                pixel_format=self._fourcc_to_string(pixel_format),
                                description=f"{width}x{height} @ {fps:.1f}fps ({description})"
                            ))
                    
                    fmt_index += 1
                    
                except Exception:
                    break
            
            os.close(fd)
            
        except Exception as e:
            print(f"获取V4L2格式失败: {e}")
        
        return formats
    
    def get_device_controls(self, device_index: int) -> List[ControlInfo]:
        """获取设备控制参数"""
        controls = []
        
        try:
            device_path = f"/dev/video{device_index}"
            if not os.path.exists(device_path):
                return controls
            
            fd = os.open(device_path, os.O_RDWR)
            
            # V4L2控制ID列表
            control_ids = [
                (V4L2_CID_BRIGHTNESS, "brightness"),
                (V4L2_CID_CONTRAST, "contrast"),
                (V4L2_CID_SATURATION, "saturation"),
                (V4L2_CID_HUE, "hue"),
                (V4L2_CID_GAMMA, "gamma"),
                (V4L2_CID_GAIN, "gain"),
                (V4L2_CID_EXPOSURE, "exposure"),
                (V4L2_CID_AUTO_WHITE_BALANCE, "auto_white_balance"),
                (V4L2_CID_RED_BALANCE, "red_balance"),
                (V4L2_CID_BLUE_BALANCE, "blue_balance"),
                (V4L2_CID_FOCUS_ABSOLUTE, "focus"),
                (V4L2_CID_FOCUS_AUTO, "focus_auto"),
                (V4L2_CID_ZOOM_ABSOLUTE, "zoom"),
                (V4L2_CID_PAN_ABSOLUTE, "pan"),
                (V4L2_CID_TILT_ABSOLUTE, "tilt"),
            ]
            
            for ctrl_id, ctrl_name in control_ids:
                try:
                    ctrl_info = self._query_control(fd, ctrl_id)
                    if ctrl_info:
                        # 获取当前值
                        current_value = self._get_control(fd, ctrl_id)
                        if current_value is not None:
                            controls.append(ControlInfo(
                                name=ctrl_name,
                                min_value=ctrl_info['minimum'],
                                max_value=ctrl_info['maximum'],
                                step=ctrl_info['step'],
                                default_value=ctrl_info['default_value'],
                                current_value=current_value,
                                flags=ctrl_info['flags'],
                                auto_supported=ctrl_info['type'] == V4L2_CTRL_TYPE_BOOLEAN,
                                description=ctrl_info['name']
                            ))
                except Exception:
                    continue
            
            os.close(fd)
            
        except Exception as e:
            print(f"获取V4L2控制参数失败: {e}")
        
        return controls
    
    def set_device_control(self, device_index: int, control_name: str, value: int) -> bool:
        """设置设备控制参数"""
        try:
            device_path = f"/dev/video{device_index}"
            if not os.path.exists(device_path):
                return False
            
            fd = os.open(device_path, os.O_RDWR)
            
            # 控制参数名称映射
            control_mapping = {
                "brightness": V4L2_CID_BRIGHTNESS,
                "contrast": V4L2_CID_CONTRAST,
                "saturation": V4L2_CID_SATURATION,
                "hue": V4L2_CID_HUE,
                "gamma": V4L2_CID_GAMMA,
                "gain": V4L2_CID_GAIN,
                "exposure": V4L2_CID_EXPOSURE,
                "auto_white_balance": V4L2_CID_AUTO_WHITE_BALANCE,
                "red_balance": V4L2_CID_RED_BALANCE,
                "blue_balance": V4L2_CID_BLUE_BALANCE,
                "focus": V4L2_CID_FOCUS_ABSOLUTE,
                "focus_auto": V4L2_CID_FOCUS_AUTO,
                "zoom": V4L2_CID_ZOOM_ABSOLUTE,
                "pan": V4L2_CID_PAN_ABSOLUTE,
                "tilt": V4L2_CID_TILT_ABSOLUTE,
            }
            
            ctrl_id = control_mapping.get(control_name.lower())
            if ctrl_id is None:
                os.close(fd)
                return False
            
            # 设置控制参数
            success = self._set_control(fd, ctrl_id, value)
            os.close(fd)
            
            return success
            
        except Exception as e:
            print(f"设置V4L2控制参数失败: {e}")
            return False

    def _query_capability(self, fd: int) -> Optional[Dict]:
        """查询设备能力"""
        try:
            # v4l2_capability结构体
            cap_struct = bytearray(V4L2_CAP_STRUCT_SIZE)

            # 执行VIDIOC_QUERYCAP ioctl
            fcntl.ioctl(fd, VIDIOC_QUERYCAP, cap_struct)

            # 解析结构体
            driver = cap_struct[0:16].decode('utf-8', errors='ignore').rstrip('\x00')
            card = cap_struct[16:48].decode('utf-8', errors='ignore').rstrip('\x00')
            bus_info = cap_struct[48:80].decode('utf-8', errors='ignore').rstrip('\x00')
            version = struct.unpack('<I', cap_struct[80:84])[0]
            capabilities = struct.unpack('<I', cap_struct[84:88])[0]

            return {
                'driver': driver,
                'card': card,
                'bus_info': bus_info,
                'version': version,
                'capabilities': capabilities
            }

        except Exception as e:
            print(f"查询设备能力失败: {e}")
            return None

    def _enum_format(self, fd: int, index: int) -> Optional[Dict]:
        """枚举像素格式"""
        try:
            # v4l2_fmtdesc结构体
            fmt_struct = bytearray(V4L2_FMTDESC_STRUCT_SIZE)

            # 设置索引和类型
            struct.pack_into('<I', fmt_struct, 0, index)  # index
            struct.pack_into('<I', fmt_struct, 4, 1)      # type (V4L2_BUF_TYPE_VIDEO_CAPTURE)

            # 执行VIDIOC_ENUM_FMT ioctl
            fcntl.ioctl(fd, VIDIOC_ENUM_FMT, fmt_struct)

            # 解析结构体
            flags = struct.unpack('<I', fmt_struct[8:12])[0]
            description = fmt_struct[12:44].decode('utf-8', errors='ignore').rstrip('\x00')
            pixelformat = struct.unpack('<I', fmt_struct[44:48])[0]

            return {
                'index': index,
                'flags': flags,
                'description': description,
                'pixelformat': pixelformat
            }

        except Exception:
            return None

    def _enum_frame_sizes(self, fd: int, pixelformat: int) -> List[Tuple[int, int]]:
        """枚举帧大小"""
        frame_sizes = []

        try:
            index = 0
            while True:
                try:
                    # v4l2_frmsizeenum结构体
                    size_struct = bytearray(V4L2_FRMSIZEENUM_STRUCT_SIZE)

                    # 设置参数
                    struct.pack_into('<I', size_struct, 0, index)        # index
                    struct.pack_into('<I', size_struct, 4, pixelformat)  # pixel_format

                    # 执行VIDIOC_ENUM_FRAMESIZES ioctl
                    fcntl.ioctl(fd, VIDIOC_ENUM_FRAMESIZES, size_struct)

                    # 解析结构体
                    type_val = struct.unpack('<I', size_struct[8:12])[0]

                    if type_val == 1:  # V4L2_FRMSIZE_TYPE_DISCRETE
                        width = struct.unpack('<I', size_struct[12:16])[0]
                        height = struct.unpack('<I', size_struct[16:20])[0]
                        frame_sizes.append((width, height))
                    elif type_val == 2:  # V4L2_FRMSIZE_TYPE_STEPWISE
                        min_width = struct.unpack('<I', size_struct[12:16])[0]
                        max_width = struct.unpack('<I', size_struct[16:20])[0]
                        step_width = struct.unpack('<I', size_struct[20:24])[0]
                        min_height = struct.unpack('<I', size_struct[24:28])[0]
                        max_height = struct.unpack('<I', size_struct[28:32])[0]
                        step_height = struct.unpack('<I', size_struct[32:36])[0]

                        # 生成常见分辨率
                        common_sizes = [(640, 480), (800, 600), (1024, 768), (1280, 720), (1920, 1080)]
                        for w, h in common_sizes:
                            if (min_width <= w <= max_width and
                                min_height <= h <= max_height):
                                frame_sizes.append((w, h))

                    index += 1

                except Exception:
                    break

        except Exception:
            pass

        # 如果没有找到帧大小，返回默认值
        if not frame_sizes:
            frame_sizes = [(640, 480)]

        return frame_sizes

    def _enum_frame_intervals(self, fd: int, pixelformat: int, width: int, height: int) -> List[float]:
        """枚举帧率"""
        frame_rates = []

        try:
            index = 0
            while True:
                try:
                    # v4l2_frmivalenum结构体
                    interval_struct = bytearray(V4L2_FRMIVALENUM_STRUCT_SIZE)

                    # 设置参数
                    struct.pack_into('<I', interval_struct, 0, index)        # index
                    struct.pack_into('<I', interval_struct, 4, pixelformat)  # pixel_format
                    struct.pack_into('<I', interval_struct, 8, width)        # width
                    struct.pack_into('<I', interval_struct, 12, height)      # height

                    # 执行VIDIOC_ENUM_FRAMEINTERVALS ioctl
                    fcntl.ioctl(fd, VIDIOC_ENUM_FRAMEINTERVALS, interval_struct)

                    # 解析结构体
                    type_val = struct.unpack('<I', interval_struct[16:20])[0]

                    if type_val == 1:  # V4L2_FRMIVAL_TYPE_DISCRETE
                        numerator = struct.unpack('<I', interval_struct[20:24])[0]
                        denominator = struct.unpack('<I', interval_struct[24:28])[0]
                        if denominator > 0:
                            fps = denominator / numerator
                            frame_rates.append(fps)

                    index += 1

                except Exception:
                    break

        except Exception:
            pass

        # 如果没有找到帧率，返回默认值
        if not frame_rates:
            frame_rates = [30.0]

        return frame_rates

    def _query_control(self, fd: int, ctrl_id: int) -> Optional[Dict]:
        """查询控制参数信息"""
        try:
            # v4l2_queryctrl结构体
            ctrl_struct = bytearray(V4L2_QUERYCTRL_STRUCT_SIZE)

            # 设置控制ID
            struct.pack_into('<I', ctrl_struct, 0, ctrl_id)

            # 执行VIDIOC_QUERYCTRL ioctl
            fcntl.ioctl(fd, VIDIOC_QUERYCTRL, ctrl_struct)

            # 解析结构体
            ctrl_type = struct.unpack('<I', ctrl_struct[4:8])[0]
            name = ctrl_struct[8:40].decode('utf-8', errors='ignore').rstrip('\x00')
            minimum = struct.unpack('<i', ctrl_struct[40:44])[0]
            maximum = struct.unpack('<i', ctrl_struct[44:48])[0]
            step = struct.unpack('<i', ctrl_struct[48:52])[0]
            default_value = struct.unpack('<i', ctrl_struct[52:56])[0]
            flags = struct.unpack('<I', ctrl_struct[56:60])[0]

            return {
                'id': ctrl_id,
                'type': ctrl_type,
                'name': name,
                'minimum': minimum,
                'maximum': maximum,
                'step': step,
                'default_value': default_value,
                'flags': flags
            }

        except Exception:
            return None

    def _get_control(self, fd: int, ctrl_id: int) -> Optional[int]:
        """获取控制参数值"""
        try:
            # v4l2_control结构体
            ctrl_struct = bytearray(V4L2_CONTROL_STRUCT_SIZE)

            # 设置控制ID
            struct.pack_into('<I', ctrl_struct, 0, ctrl_id)

            # 执行VIDIOC_G_CTRL ioctl
            fcntl.ioctl(fd, VIDIOC_G_CTRL, ctrl_struct)

            # 解析值
            value = struct.unpack('<i', ctrl_struct[4:8])[0]
            return value

        except Exception:
            return None

    def _set_control(self, fd: int, ctrl_id: int, value: int) -> bool:
        """设置控制参数值"""
        try:
            # v4l2_control结构体
            ctrl_struct = bytearray(V4L2_CONTROL_STRUCT_SIZE)

            # 设置控制ID和值
            struct.pack_into('<I', ctrl_struct, 0, ctrl_id)
            struct.pack_into('<i', ctrl_struct, 4, value)

            # 执行VIDIOC_S_CTRL ioctl
            fcntl.ioctl(fd, VIDIOC_S_CTRL, ctrl_struct)

            return True

        except Exception:
            return False

    def _fourcc_to_string(self, fourcc: int) -> str:
        """将FOURCC代码转换为字符串"""
        try:
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
