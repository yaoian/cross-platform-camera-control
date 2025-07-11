#!/usr/bin/env python3
"""
Cross-Platform Camera Control Tool - Demo Script
演示脚本展示主要功能
"""

import sys
import time
from video_device_controller import create_controller


def print_header(title):
    """打印标题"""
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)


def print_section(title):
    """打印章节标题"""
    print(f"\n📋 {title}")
    print("-" * 40)


def demo_device_enumeration():
    """演示设备枚举功能"""
    print_section("设备枚举 (Device Enumeration)")
    
    try:
        controller = create_controller()
        devices = controller.list_devices()
        
        if not devices:
            print("❌ 未找到视频设备")
            return None
        
        print(f"✅ 找到 {len(devices)} 个视频设备:")
        for device in devices:
            print(f"  📹 设备 {device.index}: {device.name}")
            print(f"     路径: {device.path}")
            if device.description:
                print(f"     描述: {device.description}")
            print()
        
        return devices[0].index if devices else None
        
    except Exception as e:
        print(f"❌ 设备枚举失败: {e}")
        return None


def demo_format_query(device_index):
    """演示格式查询功能"""
    print_section("格式查询 (Format Query)")
    
    try:
        controller = create_controller()
        formats = controller.get_formats(device_index)
        
        if not formats:
            print("❌ 无法获取设备格式信息")
            return
        
        print(f"✅ 设备 {device_index} 支持的格式:")
        for fmt in formats:
            print(f"  🎥 [{fmt.pixel_format}] {fmt.width}x{fmt.height} @ {fmt.fps:.1f}fps")
            if fmt.description:
                print(f"      {fmt.description}")
        
    except Exception as e:
        print(f"❌ 格式查询失败: {e}")


def demo_control_parameters(device_index):
    """演示控制参数功能"""
    print_section("控制参数 (Control Parameters)")
    
    try:
        controller = create_controller()
        controls = controller.get_controls(device_index)
        
        if not controls:
            print("❌ 无法获取设备控制参数")
            return
        
        print(f"✅ 设备 {device_index} 支持的控制参数:")
        for ctrl in controls:
            auto_flag = " (支持自动)" if ctrl.auto_supported else ""
            print(f"  🎛️  {ctrl.name}: {ctrl.current_value}")
            print(f"      范围: {ctrl.min_value}-{ctrl.max_value}, 步长: {ctrl.step}")
            print(f"      默认值: {ctrl.default_value}{auto_flag}")
            if ctrl.description:
                print(f"      描述: {ctrl.description}")
            print()
        
        return controls
        
    except Exception as e:
        print(f"❌ 控制参数查询失败: {e}")
        return []


def demo_parameter_setting(device_index, controls):
    """演示参数设置功能"""
    print_section("参数设置 (Parameter Setting)")
    
    if not controls:
        print("❌ 没有可用的控制参数")
        return
    
    try:
        controller = create_controller()
        
        # 尝试设置亮度
        brightness_ctrl = None
        for ctrl in controls:
            if ctrl.name.lower() == 'brightness':
                brightness_ctrl = ctrl
                break
        
        if brightness_ctrl:
            original_value = brightness_ctrl.current_value
            new_value = min(brightness_ctrl.max_value, original_value + 10)
            
            print(f"🔧 尝试设置亮度从 {original_value} 到 {new_value}")
            
            success = controller.set_control(device_index, 'brightness', new_value)
            if success:
                print("✅ 亮度设置成功")
                
                # 验证设置
                time.sleep(1)
                current_value = controller.get_control(device_index, 'brightness')
                if current_value is not None:
                    print(f"✅ 验证: 当前亮度值 = {current_value}")
                
                # 恢复原值
                controller.set_control(device_index, 'brightness', original_value)
                print(f"🔄 已恢复原始亮度值: {original_value}")
            else:
                print("❌ 亮度设置失败")
        else:
            print("⚠️  未找到亮度控制参数，尝试设置对比度")
            
            # 尝试设置对比度
            contrast_ctrl = None
            for ctrl in controls:
                if ctrl.name.lower() == 'contrast':
                    contrast_ctrl = ctrl
                    break
            
            if contrast_ctrl:
                original_value = contrast_ctrl.current_value
                new_value = min(contrast_ctrl.max_value, original_value + 5)
                
                print(f"🔧 尝试设置对比度从 {original_value} 到 {new_value}")
                success = controller.set_control(device_index, 'contrast', new_value)
                
                if success:
                    print("✅ 对比度设置成功")
                    controller.set_control(device_index, 'contrast', original_value)
                    print(f"🔄 已恢复原始对比度值: {original_value}")
                else:
                    print("❌ 对比度设置失败")
            else:
                print("⚠️  未找到可设置的控制参数")
        
    except Exception as e:
        print(f"❌ 参数设置失败: {e}")


def demo_command_line_interface():
    """演示命令行接口"""
    print_section("命令行接口 (Command Line Interface)")
    
    print("📝 v4l2-ctl兼容的命令行接口示例:")
    print()
    print("# 列出所有设备")
    print("python v4l2_ctl_cross.py --list-devices")
    print()
    print("# 显示设备格式")
    print("python v4l2_ctl_cross.py -d /dev/video0 --list-formats-ext")
    print()
    print("# 显示控制参数")
    print("python v4l2_ctl_cross.py -d /dev/video0 -L")
    print()
    print("# 设置参数")
    print("python v4l2_ctl_cross.py -d /dev/video0 -c brightness=50")
    print("python v4l2_ctl_cross.py -d /dev/video0 -c brightness=50,contrast=75")
    print()
    print("# 显示帮助")
    print("python v4l2_ctl_cross.py -h")


def main():
    """主演示函数"""
    print_header("Cross-Platform Camera Control Tool - 功能演示")
    
    print("🚀 欢迎使用跨平台摄像头控制工具!")
    print("📱 本工具支持 Windows、Linux、macOS 平台")
    print("🔧 兼容 v4l2-ctl 命令行接口")
    print("⚡ 支持多种后端: DirectShow、V4L2、AVFoundation、OpenCV")
    
    # 演示设备枚举
    device_index = demo_device_enumeration()
    
    if device_index is None:
        print("\n❌ 无法继续演示，因为没有找到可用的视频设备")
        print("💡 请确保:")
        print("   - 摄像头已连接并正常工作")
        print("   - 摄像头没有被其他应用程序占用")
        print("   - 已安装必要的依赖包")
        return
    
    # 演示格式查询
    demo_format_query(device_index)
    
    # 演示控制参数
    controls = demo_control_parameters(device_index)
    
    # 演示参数设置
    demo_parameter_setting(device_index, controls)
    
    # 演示命令行接口
    demo_command_line_interface()
    
    print_header("演示完成")
    print("🎉 感谢使用跨平台摄像头控制工具!")
    print("📚 更多信息请查看:")
    print("   - GitHub: https://github.com/yaoian/cross-platform-camera-control")
    print("   - 文档: README.md")
    print("   - 贡献指南: CONTRIBUTING.md")
    print()
    print("🐛 如果遇到问题，请在GitHub上提交Issue")
    print("💡 欢迎贡献代码和建议!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️  演示被用户中断")
    except Exception as e:
        print(f"\n❌ 演示过程中发生错误: {e}")
        print("🔍 请检查系统配置和依赖安装")
        sys.exit(1)
