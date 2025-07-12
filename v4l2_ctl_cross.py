#!/usr/bin/env python3
"""
跨平台v4l2-ctl工具
支持Windows、Linux、macOS的视频设备控制
"""

import argparse
import sys
import os
from typing import Optional
from video_device_controller import create_controller, VideoDeviceController

# 抑制OpenCV错误输出
os.environ['OPENCV_LOG_LEVEL'] = 'SILENT'
try:
    import cv2
    cv2.setLogLevel(0)
except ImportError:
    pass


def parse_device_path(device_path: str) -> int:
    """解析设备路径，提取设备索引"""
    if device_path.startswith("/dev/video"):
        try:
            return int(device_path.replace("/dev/video", ""))
        except ValueError:
            return 0
    else:
        try:
            return int(device_path)
        except ValueError:
            return 0


def parse_control_setting(control_str: str) -> tuple:
    """解析控制参数设置字符串，格式：control=value"""
    if "=" not in control_str:
        raise ValueError(f"无效的控制参数格式: {control_str}")
    
    parts = control_str.split("=", 1)
    control_name = parts[0].strip()
    try:
        value = int(parts[1].strip())
        return control_name, value
    except ValueError:
        raise ValueError(f"无效的控制参数值: {parts[1]}")


def list_devices(controller: VideoDeviceController):
    """列出所有视频设备"""
    devices = controller.list_devices()
    if not devices:
        print("未找到视频设备")
        return
    
    for device in devices:
        print(f"{device.name}: ({device.path}):")
        print(f"        /dev/video{device.index}")


def list_formats(controller: VideoDeviceController, device_index: int):
    """列出设备支持的格式"""
    formats = controller.get_formats(device_index)
    if not formats:
        print(f"设备 /dev/video{device_index} 无可用格式信息")
        return
    
    print(f"设备 /dev/video{device_index} 支持的格式:")
    for fmt in formats:
        print(f"    [{fmt.pixel_format}] {fmt.width}x{fmt.height} @ {fmt.fps:.2f}fps")
        if fmt.description:
            print(f"        {fmt.description}")


def list_controls(controller: VideoDeviceController, device_index: int):
    """列出设备支持的控制参数"""
    controls = controller.get_controls(device_index)
    if not controls:
        print(f"设备 /dev/video{device_index} 无可用控制参数")
        return

    # 分组显示控制参数
    user_controls = []
    camera_controls = []

    for ctrl in controls:
        if ctrl.name in ['pan', 'tilt', 'roll', 'zoom', 'focus', 'focus_automatic']:
            camera_controls.append(ctrl)
        else:
            user_controls.append(ctrl)

    # 显示User Controls
    if user_controls:
        print("User Controls")
        print()

        for ctrl in user_controls:
            # 确定控制类型
            ctrl_type = "(bool)" if ctrl.name.endswith("_automatic") else "(int)"

            # 格式化输出，模仿原版格式
            name_padded = f"{ctrl.name:>25}"
            print(f"{name_padded} {ctrl_type}    : "
                  f"min={ctrl.min_value} max={ctrl.max_value} step={ctrl.step} "
                  f"default={ctrl.default_value} value={ctrl.current_value}")

    # 显示Camera Controls
    if camera_controls:
        print()
        print("Camera Controls")
        print()

        for ctrl in camera_controls:
            # 确定控制类型
            ctrl_type = "(bool)" if ctrl.name.endswith("_automatic") else "(int)"

            # 格式化输出，模仿原版格式
            name_padded = f"{ctrl.name:>25}"
            print(f"{name_padded} {ctrl_type}    : "
                  f"min={ctrl.min_value} max={ctrl.max_value} step={ctrl.step} "
                  f"default={ctrl.default_value} value={ctrl.current_value}")


def set_control(controller: VideoDeviceController, device_index: int, control_name: str, value: int):
    """设置设备控制参数"""
    success = controller.set_control(device_index, control_name, value)
    if success:
        print(f"成功设置 {control_name} = {value}")
    else:
        print(f"设置 {control_name} = {value} 失败")


def show_help():
    """显示帮助信息"""
    help_text = """
跨平台视频设备控制工具 (v4l2-ctl兼容版本)

General/Common options:
    -c, --set-ctrl <ctrl>=<val>[,<ctrl>=<val>...]
                     设置控制参数
    -d, --device=<dev> 
                     使用指定设备，默认为 /dev/video0
    -h, --help       显示此帮助信息
    -L, --list-ctrls-menus
                     显示所有控制参数和菜单 [VIDIOC_QUERYMENU]
    --list-devices   列出所有视频设备
    --list-formats-ext 
                     显示支持的视频格式，包括帧大小和帧率

示例:
    python v4l2_ctl_cross.py --list-devices
    python v4l2_ctl_cross.py -d /dev/video0 --list-formats-ext
    python v4l2_ctl_cross.py -d /dev/video0 -L
    python v4l2_ctl_cross.py -d /dev/video0 -c brightness=50
    """
    print(help_text)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="跨平台视频设备控制工具",
        add_help=False  # 使用自定义帮助
    )
    
    # 添加参数
    parser.add_argument("-h", "--help", action="store_true", help="显示帮助信息")
    parser.add_argument("-d", "--device", default="/dev/video0", help="指定设备")
    parser.add_argument("-c", "--set-ctrl", help="设置控制参数")
    parser.add_argument("-L", "--list-ctrls-menus", action="store_true", help="列出控制参数")
    parser.add_argument("--list-devices", action="store_true", help="列出所有设备")
    parser.add_argument("--list-formats-ext", action="store_true", help="列出支持的格式")
    
    # 解析参数
    args = parser.parse_args()
    
    # 显示帮助
    if args.help or len(sys.argv) == 1:
        show_help()
        return
    
    try:
        # 创建控制器
        controller = create_controller()
        
        # 解析设备索引
        device_index = parse_device_path(args.device)
        
        # 执行相应操作
        if args.list_devices:
            list_devices(controller)
        elif args.list_formats_ext:
            list_formats(controller, device_index)
        elif args.list_ctrls_menus:
            list_controls(controller, device_index)
        elif args.set_ctrl:
            # 解析控制参数设置
            control_settings = args.set_ctrl.split(",")
            for setting in control_settings:
                try:
                    control_name, value = parse_control_setting(setting.strip())
                    set_control(controller, device_index, control_name, value)
                except ValueError as e:
                    print(f"错误: {e}")
        else:
            print("请指定操作参数，使用 -h 查看帮助")
    
    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
