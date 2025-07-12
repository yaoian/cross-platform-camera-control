#!/usr/bin/env python3
"""
错误处理和日志记录模块
提供统一的错误处理、异常恢复和日志记录功能
"""

import logging
import traceback
import functools
import time
from typing import Any, Callable, Optional, Dict, List
from dataclasses import dataclass
from enum import Enum


class ErrorLevel(Enum):
    """错误级别"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ErrorCode(Enum):
    """错误代码"""
    # 设备相关错误
    DEVICE_NOT_FOUND = "DEVICE_NOT_FOUND"
    DEVICE_BUSY = "DEVICE_BUSY"
    DEVICE_PERMISSION_DENIED = "DEVICE_PERMISSION_DENIED"
    DEVICE_DISCONNECTED = "DEVICE_DISCONNECTED"
    
    # 控制参数错误
    CONTROL_NOT_SUPPORTED = "CONTROL_NOT_SUPPORTED"
    CONTROL_VALUE_OUT_OF_RANGE = "CONTROL_VALUE_OUT_OF_RANGE"
    CONTROL_READ_ONLY = "CONTROL_READ_ONLY"
    
    # 格式相关错误
    FORMAT_NOT_SUPPORTED = "FORMAT_NOT_SUPPORTED"
    RESOLUTION_NOT_SUPPORTED = "RESOLUTION_NOT_SUPPORTED"
    
    # 系统错误
    PLATFORM_NOT_SUPPORTED = "PLATFORM_NOT_SUPPORTED"
    DEPENDENCY_MISSING = "DEPENDENCY_MISSING"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    
    # 网络和IO错误
    IO_ERROR = "IO_ERROR"
    TIMEOUT = "TIMEOUT"
    
    # 未知错误
    UNKNOWN_ERROR = "UNKNOWN_ERROR"


@dataclass
class ErrorInfo:
    """错误信息"""
    code: ErrorCode
    message: str
    details: Optional[str] = None
    timestamp: Optional[float] = None
    context: Optional[Dict[str, Any]] = None
    recoverable: bool = True
    suggested_action: Optional[str] = None


class VideoControlError(Exception):
    """视频控制异常基类"""
    
    def __init__(self, error_info: ErrorInfo):
        self.error_info = error_info
        super().__init__(error_info.message)


class DeviceError(VideoControlError):
    """设备相关错误"""
    pass


class ControlError(VideoControlError):
    """控制参数相关错误"""
    pass


class FormatError(VideoControlError):
    """格式相关错误"""
    pass


class SystemError(VideoControlError):
    """系统相关错误"""
    pass


class ErrorHandler:
    """错误处理器"""
    
    def __init__(self, log_file: Optional[str] = None, log_level: str = "INFO"):
        """初始化错误处理器"""
        self.error_history: List[ErrorInfo] = []
        self.recovery_strategies: Dict[ErrorCode, Callable] = {}
        self.error_callbacks: List[Callable[[ErrorInfo], None]] = []
        
        # 设置日志
        self.logger = logging.getLogger("video_control")
        self.logger.setLevel(getattr(logging, log_level.upper()))
        
        # 创建格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # 文件处理器
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
        
        # 注册默认恢复策略
        self._register_default_recovery_strategies()
    
    def handle_error(self, error_code: ErrorCode, message: str, 
                    details: Optional[str] = None, context: Optional[Dict[str, Any]] = None,
                    recoverable: bool = True, suggested_action: Optional[str] = None) -> ErrorInfo:
        """处理错误"""
        error_info = ErrorInfo(
            code=error_code,
            message=message,
            details=details,
            timestamp=time.time(),
            context=context or {},
            recoverable=recoverable,
            suggested_action=suggested_action
        )
        
        # 记录错误
        self._log_error(error_info)
        
        # 添加到历史记录
        self.error_history.append(error_info)
        
        # 限制历史记录大小
        if len(self.error_history) > 1000:
            self.error_history = self.error_history[-500:]
        
        # 调用错误回调
        for callback in self.error_callbacks:
            try:
                callback(error_info)
            except Exception as e:
                self.logger.error(f"错误回调执行失败: {e}")
        
        # 尝试恢复
        if recoverable and error_code in self.recovery_strategies:
            try:
                self.recovery_strategies[error_code](error_info)
            except Exception as e:
                self.logger.error(f"错误恢复失败: {e}")
        
        return error_info
    
    def register_recovery_strategy(self, error_code: ErrorCode, strategy: Callable[[ErrorInfo], None]):
        """注册错误恢复策略"""
        self.recovery_strategies[error_code] = strategy
    
    def add_error_callback(self, callback: Callable[[ErrorInfo], None]):
        """添加错误回调"""
        self.error_callbacks.append(callback)
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """获取错误统计信息"""
        if not self.error_history:
            return {"total_errors": 0}
        
        # 按错误代码统计
        error_counts = {}
        recent_errors = []
        current_time = time.time()
        
        for error in self.error_history:
            # 统计错误类型
            code_str = error.code.value
            error_counts[code_str] = error_counts.get(code_str, 0) + 1
            
            # 最近1小时的错误
            if error.timestamp and (current_time - error.timestamp) < 3600:
                recent_errors.append(error)
        
        return {
            "total_errors": len(self.error_history),
            "error_counts": error_counts,
            "recent_errors_count": len(recent_errors),
            "most_common_error": max(error_counts.items(), key=lambda x: x[1])[0] if error_counts else None
        }
    
    def clear_error_history(self):
        """清除错误历史"""
        self.error_history.clear()
    
    def _log_error(self, error_info: ErrorInfo):
        """记录错误到日志"""
        log_message = f"[{error_info.code.value}] {error_info.message}"
        
        if error_info.details:
            log_message += f" - {error_info.details}"
        
        if error_info.context:
            log_message += f" - Context: {error_info.context}"
        
        if error_info.suggested_action:
            log_message += f" - Suggested: {error_info.suggested_action}"
        
        # 根据错误代码选择日志级别
        if error_info.code in [ErrorCode.DEVICE_NOT_FOUND, ErrorCode.DEVICE_DISCONNECTED]:
            self.logger.warning(log_message)
        elif error_info.code in [ErrorCode.PLATFORM_NOT_SUPPORTED, ErrorCode.DEPENDENCY_MISSING]:
            self.logger.error(log_message)
        elif error_info.code == ErrorCode.UNKNOWN_ERROR:
            self.logger.critical(log_message)
        else:
            self.logger.info(log_message)
    
    def _register_default_recovery_strategies(self):
        """注册默认恢复策略"""
        
        def retry_device_access(error_info: ErrorInfo):
            """重试设备访问"""
            self.logger.info("尝试重新访问设备...")
            time.sleep(1)  # 等待1秒后重试
        
        def suggest_permission_fix(error_info: ErrorInfo):
            """建议权限修复"""
            self.logger.info("建议检查设备权限或以管理员身份运行")
        
        def suggest_dependency_install(error_info: ErrorInfo):
            """建议安装依赖"""
            self.logger.info("建议安装缺失的依赖包")
        
        # 注册恢复策略
        self.register_recovery_strategy(ErrorCode.DEVICE_BUSY, retry_device_access)
        self.register_recovery_strategy(ErrorCode.DEVICE_DISCONNECTED, retry_device_access)
        self.register_recovery_strategy(ErrorCode.PERMISSION_DENIED, suggest_permission_fix)
        self.register_recovery_strategy(ErrorCode.DEPENDENCY_MISSING, suggest_dependency_install)


# 全局错误处理器实例
global_error_handler = ErrorHandler()


def error_handler(error_code: ErrorCode = ErrorCode.UNKNOWN_ERROR, 
                 recoverable: bool = True,
                 reraise: bool = False):
    """错误处理装饰器"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except VideoControlError as e:
                # 已经是我们的错误类型，直接处理
                global_error_handler.handle_error(
                    e.error_info.code,
                    e.error_info.message,
                    e.error_info.details,
                    e.error_info.context,
                    e.error_info.recoverable,
                    e.error_info.suggested_action
                )
                if reraise:
                    raise
                return None
            except Exception as e:
                # 其他异常，包装为我们的错误类型
                error_info = global_error_handler.handle_error(
                    error_code,
                    str(e),
                    traceback.format_exc(),
                    {"function": func.__name__, "args": str(args)[:100]},
                    recoverable,
                    "请检查输入参数和系统状态"
                )
                if reraise:
                    raise VideoControlError(error_info) from e
                return None
        return wrapper
    return decorator


def create_error(error_code: ErrorCode, message: str, **kwargs) -> VideoControlError:
    """创建错误对象"""
    error_info = ErrorInfo(
        code=error_code,
        message=message,
        timestamp=time.time(),
        **kwargs
    )
    
    # 根据错误代码选择异常类型
    if error_code in [ErrorCode.DEVICE_NOT_FOUND, ErrorCode.DEVICE_BUSY, 
                      ErrorCode.DEVICE_PERMISSION_DENIED, ErrorCode.DEVICE_DISCONNECTED]:
        return DeviceError(error_info)
    elif error_code in [ErrorCode.CONTROL_NOT_SUPPORTED, ErrorCode.CONTROL_VALUE_OUT_OF_RANGE,
                        ErrorCode.CONTROL_READ_ONLY]:
        return ControlError(error_info)
    elif error_code in [ErrorCode.FORMAT_NOT_SUPPORTED, ErrorCode.RESOLUTION_NOT_SUPPORTED]:
        return FormatError(error_info)
    elif error_code in [ErrorCode.PLATFORM_NOT_SUPPORTED, ErrorCode.DEPENDENCY_MISSING,
                        ErrorCode.PERMISSION_DENIED]:
        return SystemError(error_info)
    else:
        return VideoControlError(error_info)


def get_user_friendly_message(error_code: ErrorCode) -> str:
    """获取用户友好的错误消息"""
    messages = {
        ErrorCode.DEVICE_NOT_FOUND: "未找到视频设备。请检查摄像头是否已连接。",
        ErrorCode.DEVICE_BUSY: "设备正在被其他应用程序使用。请关闭其他摄像头应用。",
        ErrorCode.DEVICE_PERMISSION_DENIED: "没有访问设备的权限。请以管理员身份运行或检查设备权限。",
        ErrorCode.DEVICE_DISCONNECTED: "设备已断开连接。请重新连接摄像头。",
        ErrorCode.CONTROL_NOT_SUPPORTED: "设备不支持此控制参数。",
        ErrorCode.CONTROL_VALUE_OUT_OF_RANGE: "控制参数值超出有效范围。",
        ErrorCode.CONTROL_READ_ONLY: "此控制参数为只读，无法修改。",
        ErrorCode.FORMAT_NOT_SUPPORTED: "设备不支持此视频格式。",
        ErrorCode.RESOLUTION_NOT_SUPPORTED: "设备不支持此分辨率。",
        ErrorCode.PLATFORM_NOT_SUPPORTED: "当前平台不受支持。",
        ErrorCode.DEPENDENCY_MISSING: "缺少必要的依赖包。请安装相关依赖。",
        ErrorCode.PERMISSION_DENIED: "权限被拒绝。请检查系统权限设置。",
        ErrorCode.IO_ERROR: "输入/输出错误。请检查设备连接。",
        ErrorCode.TIMEOUT: "操作超时。请重试或检查设备状态。",
        ErrorCode.UNKNOWN_ERROR: "发生未知错误。请查看详细日志信息。"
    }
    
    return messages.get(error_code, "发生未知错误。")


# 导出主要接口
__all__ = [
    'ErrorLevel', 'ErrorCode', 'ErrorInfo', 'VideoControlError',
    'DeviceError', 'ControlError', 'FormatError', 'SystemError',
    'ErrorHandler', 'global_error_handler', 'error_handler',
    'create_error', 'get_user_friendly_message'
]
