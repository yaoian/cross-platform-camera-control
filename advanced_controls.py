#!/usr/bin/env python3
"""
高级摄像头控制功能
包括自动模式切换、高级摄像头功能等
"""

from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from video_device_controller import VideoDeviceController, ControlInfo
import time


@dataclass
class AdvancedControlInfo:
    """高级控制参数信息"""
    name: str
    display_name: str
    description: str
    control_type: str  # 'range', 'boolean', 'menu', 'action'
    min_value: Optional[int] = None
    max_value: Optional[int] = None
    step: int = 1
    default_value: Optional[int] = None
    current_value: Optional[int] = None
    auto_supported: bool = False
    auto_enabled: bool = False
    menu_items: Optional[List[str]] = None
    dependencies: Optional[List[str]] = None  # 依赖的其他控制参数


class AdvancedControlManager:
    """高级控制管理器"""
    
    def __init__(self, controller: VideoDeviceController):
        """初始化高级控制管理器"""
        self.controller = controller
        self.control_profiles = {}
        self.auto_controls = {}
        
        # 定义高级控制映射
        self.advanced_controls = {
            # 基础控制
            'brightness': AdvancedControlInfo(
                name='brightness',
                display_name='亮度',
                description='调整图像亮度',
                control_type='range',
                auto_supported=True
            ),
            'contrast': AdvancedControlInfo(
                name='contrast',
                display_name='对比度',
                description='调整图像对比度',
                control_type='range',
                auto_supported=True
            ),
            'saturation': AdvancedControlInfo(
                name='saturation',
                display_name='饱和度',
                description='调整颜色饱和度',
                control_type='range',
                auto_supported=True
            ),
            'hue': AdvancedControlInfo(
                name='hue',
                display_name='色调',
                description='调整颜色色调',
                control_type='range'
            ),
            
            # 曝光控制
            'exposure': AdvancedControlInfo(
                name='exposure',
                display_name='曝光',
                description='调整曝光时间',
                control_type='range',
                auto_supported=True
            ),
            'exposure_auto': AdvancedControlInfo(
                name='exposure_auto',
                display_name='自动曝光',
                description='启用/禁用自动曝光',
                control_type='boolean',
                dependencies=['exposure']
            ),
            'gain': AdvancedControlInfo(
                name='gain',
                display_name='增益',
                description='调整传感器增益',
                control_type='range',
                auto_supported=True
            ),
            
            # 对焦控制
            'focus': AdvancedControlInfo(
                name='focus',
                display_name='对焦',
                description='调整镜头对焦位置',
                control_type='range',
                auto_supported=True
            ),
            'focus_auto': AdvancedControlInfo(
                name='focus_auto',
                display_name='自动对焦',
                description='启用/禁用自动对焦',
                control_type='boolean',
                dependencies=['focus']
            ),
            'focus_continuous': AdvancedControlInfo(
                name='focus_continuous',
                display_name='连续对焦',
                description='启用连续自动对焦',
                control_type='boolean',
                dependencies=['focus_auto']
            ),
            
            # 白平衡控制
            'white_balance': AdvancedControlInfo(
                name='white_balance',
                display_name='白平衡',
                description='调整白平衡',
                control_type='menu',
                menu_items=['自动', '白炽灯', '荧光灯', '日光', '阴天', '手动'],
                auto_supported=True
            ),
            'white_balance_temperature': AdvancedControlInfo(
                name='white_balance_temperature',
                display_name='色温',
                description='手动设置色温',
                control_type='range',
                min_value=2000,
                max_value=10000,
                dependencies=['white_balance']
            ),
            
            # 缩放和移动控制
            'zoom': AdvancedControlInfo(
                name='zoom',
                display_name='缩放',
                description='数字缩放',
                control_type='range',
                min_value=100,
                max_value=1000,
                default_value=100
            ),
            'pan': AdvancedControlInfo(
                name='pan',
                display_name='水平移动',
                description='水平方向移动',
                control_type='range'
            ),
            'tilt': AdvancedControlInfo(
                name='tilt',
                display_name='垂直移动',
                description='垂直方向移动',
                control_type='range'
            ),
            
            # 图像增强
            'sharpness': AdvancedControlInfo(
                name='sharpness',
                display_name='锐度',
                description='调整图像锐度',
                control_type='range'
            ),
            'gamma': AdvancedControlInfo(
                name='gamma',
                display_name='伽马',
                description='调整伽马值',
                control_type='range'
            ),
            'backlight_compensation': AdvancedControlInfo(
                name='backlight_compensation',
                display_name='背光补偿',
                description='背光补偿',
                control_type='boolean'
            ),
            
            # 降噪和稳定
            'noise_reduction': AdvancedControlInfo(
                name='noise_reduction',
                display_name='降噪',
                description='图像降噪',
                control_type='range'
            ),
            'image_stabilization': AdvancedControlInfo(
                name='image_stabilization',
                display_name='图像稳定',
                description='启用图像稳定',
                control_type='boolean'
            ),
        }
    
    def get_available_controls(self, device_index: int) -> List[AdvancedControlInfo]:
        """获取设备可用的高级控制参数"""
        available_controls = []
        
        # 获取基础控制参数
        basic_controls = self.controller.get_controls(device_index)
        basic_control_names = {ctrl.name for ctrl in basic_controls}
        
        # 映射到高级控制
        for name, advanced_ctrl in self.advanced_controls.items():
            if name in basic_control_names:
                # 从基础控制获取实际值
                basic_ctrl = next(ctrl for ctrl in basic_controls if ctrl.name == name)
                
                # 更新高级控制信息
                advanced_ctrl.min_value = basic_ctrl.min_value
                advanced_ctrl.max_value = basic_ctrl.max_value
                advanced_ctrl.step = basic_ctrl.step
                advanced_ctrl.default_value = basic_ctrl.default_value
                advanced_ctrl.current_value = basic_ctrl.current_value
                
                available_controls.append(advanced_ctrl)
        
        return available_controls
    
    def set_control_with_validation(self, device_index: int, control_name: str, value: Any) -> bool:
        """设置控制参数并进行验证"""
        if control_name not in self.advanced_controls:
            return False
        
        advanced_ctrl = self.advanced_controls[control_name]
        
        # 验证值的有效性
        if not self._validate_control_value(advanced_ctrl, value):
            return False
        
        # 检查依赖关系
        if not self._check_dependencies(device_index, advanced_ctrl):
            return False
        
        # 设置控制参数
        if advanced_ctrl.control_type == 'boolean':
            int_value = 1 if value else 0
        elif advanced_ctrl.control_type == 'menu':
            int_value = value if isinstance(value, int) else 0
        else:
            int_value = int(value)
        
        return self.controller.set_control(device_index, control_name, int_value)
    
    def enable_auto_mode(self, device_index: int, control_name: str) -> bool:
        """启用自动模式"""
        if control_name not in self.advanced_controls:
            return False
        
        advanced_ctrl = self.advanced_controls[control_name]
        if not advanced_ctrl.auto_supported:
            return False
        
        # 设置自动模式
        auto_control_name = f"{control_name}_automatic"
        success = self.controller.set_control(device_index, auto_control_name, 1)
        
        if success:
            self.auto_controls[control_name] = True
        
        return success
    
    def disable_auto_mode(self, device_index: int, control_name: str) -> bool:
        """禁用自动模式"""
        if control_name not in self.advanced_controls:
            return False
        
        # 设置手动模式
        auto_control_name = f"{control_name}_automatic"
        success = self.controller.set_control(device_index, auto_control_name, 0)
        
        if success:
            self.auto_controls[control_name] = False
        
        return success
    
    def create_control_profile(self, name: str, device_index: int) -> bool:
        """创建控制参数配置文件"""
        try:
            controls = self.get_available_controls(device_index)
            profile = {}
            
            for ctrl in controls:
                profile[ctrl.name] = {
                    'value': ctrl.current_value,
                    'auto_enabled': self.auto_controls.get(ctrl.name, False)
                }
            
            self.control_profiles[name] = profile
            return True
            
        except Exception as e:
            print(f"创建配置文件失败: {e}")
            return False
    
    def apply_control_profile(self, name: str, device_index: int) -> bool:
        """应用控制参数配置文件"""
        if name not in self.control_profiles:
            return False
        
        try:
            profile = self.control_profiles[name]
            
            for control_name, settings in profile.items():
                # 设置自动模式
                if settings.get('auto_enabled', False):
                    self.enable_auto_mode(device_index, control_name)
                else:
                    self.disable_auto_mode(device_index, control_name)
                    # 设置具体值
                    self.set_control_with_validation(device_index, control_name, settings['value'])
            
            return True
            
        except Exception as e:
            print(f"应用配置文件失败: {e}")
            return False
    
    def auto_adjust_exposure(self, device_index: int) -> bool:
        """自动调整曝光"""
        try:
            # 启用自动曝光
            if self.enable_auto_mode(device_index, 'exposure'):
                time.sleep(2)  # 等待自动调整
                return True
            return False
        except Exception as e:
            print(f"自动调整曝光失败: {e}")
            return False
    
    def auto_adjust_white_balance(self, device_index: int) -> bool:
        """自动调整白平衡"""
        try:
            # 启用自动白平衡
            if self.enable_auto_mode(device_index, 'white_balance'):
                time.sleep(2)  # 等待自动调整
                return True
            return False
        except Exception as e:
            print(f"自动调整白平衡失败: {e}")
            return False
    
    def _validate_control_value(self, control: AdvancedControlInfo, value: Any) -> bool:
        """验证控制参数值"""
        if control.control_type == 'range':
            if not isinstance(value, (int, float)):
                return False
            if control.min_value is not None and value < control.min_value:
                return False
            if control.max_value is not None and value > control.max_value:
                return False
        elif control.control_type == 'boolean':
            if not isinstance(value, (bool, int)):
                return False
        elif control.control_type == 'menu':
            if control.menu_items and isinstance(value, int):
                if not (0 <= value < len(control.menu_items)):
                    return False
        
        return True
    
    def _check_dependencies(self, device_index: int, control: AdvancedControlInfo) -> bool:
        """检查控制参数依赖关系"""
        if not control.dependencies:
            return True
        
        # 检查依赖的控制参数是否可用
        available_controls = self.get_available_controls(device_index)
        available_names = {ctrl.name for ctrl in available_controls}
        
        for dep in control.dependencies:
            if dep not in available_names:
                return False
        
        return True
