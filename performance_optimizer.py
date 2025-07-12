#!/usr/bin/env python3
"""
性能优化模块
提供缓存、异步操作、资源管理等性能优化功能
"""

import time
import threading
import functools
import weakref
from typing import Any, Callable, Dict, Optional, List, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, Future
import asyncio


@dataclass
class CacheEntry:
    """缓存条目"""
    value: Any
    timestamp: float
    access_count: int = 0
    ttl: float = 300.0  # 默认5分钟过期


class LRUCache:
    """LRU缓存实现"""
    
    def __init__(self, max_size: int = 128, default_ttl: float = 300.0):
        """初始化LRU缓存"""
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache: Dict[str, CacheEntry] = {}
        self.access_order: List[str] = []
        self.lock = threading.RLock()
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        with self.lock:
            if key not in self.cache:
                return None
            
            entry = self.cache[key]
            current_time = time.time()
            
            # 检查是否过期
            if current_time - entry.timestamp > entry.ttl:
                self._remove(key)
                return None
            
            # 更新访问信息
            entry.access_count += 1
            self._move_to_end(key)
            
            return entry.value
    
    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """设置缓存值"""
        with self.lock:
            current_time = time.time()
            ttl = ttl or self.default_ttl
            
            if key in self.cache:
                # 更新现有条目
                self.cache[key].value = value
                self.cache[key].timestamp = current_time
                self.cache[key].ttl = ttl
                self._move_to_end(key)
            else:
                # 添加新条目
                if len(self.cache) >= self.max_size:
                    self._evict_lru()
                
                self.cache[key] = CacheEntry(value, current_time, 0, ttl)
                self.access_order.append(key)
    
    def clear(self) -> None:
        """清空缓存"""
        with self.lock:
            self.cache.clear()
            self.access_order.clear()
    
    def _remove(self, key: str) -> None:
        """移除缓存条目"""
        if key in self.cache:
            del self.cache[key]
            self.access_order.remove(key)
    
    def _move_to_end(self, key: str) -> None:
        """将键移动到访问顺序末尾"""
        if key in self.access_order:
            self.access_order.remove(key)
            self.access_order.append(key)
    
    def _evict_lru(self) -> None:
        """淘汰最少使用的条目"""
        if self.access_order:
            lru_key = self.access_order[0]
            self._remove(lru_key)


class PerformanceOptimizer:
    """性能优化器"""
    
    def __init__(self):
        """初始化性能优化器"""
        self.device_cache = LRUCache(max_size=32, default_ttl=60.0)  # 设备信息缓存1分钟
        self.format_cache = LRUCache(max_size=64, default_ttl=300.0)  # 格式信息缓存5分钟
        self.control_cache = LRUCache(max_size=64, default_ttl=30.0)  # 控制信息缓存30秒
        
        self.thread_pool = ThreadPoolExecutor(max_workers=4)
        self.resource_refs = weakref.WeakSet()
        
        # 性能统计
        self.stats = {
            'cache_hits': 0,
            'cache_misses': 0,
            'async_operations': 0,
            'total_operations': 0
        }
    
    def cached_device_list(self, controller, force_refresh: bool = False) -> List:
        """缓存的设备列表"""
        cache_key = f"devices_{id(controller)}"
        
        if not force_refresh:
            cached_devices = self.device_cache.get(cache_key)
            if cached_devices is not None:
                self.stats['cache_hits'] += 1
                return cached_devices
        
        # 缓存未命中，获取新数据
        self.stats['cache_misses'] += 1
        devices = controller.list_devices()
        self.device_cache.set(cache_key, devices)
        
        return devices
    
    def cached_device_formats(self, controller, device_index: int, force_refresh: bool = False) -> List:
        """缓存的设备格式"""
        cache_key = f"formats_{id(controller)}_{device_index}"
        
        if not force_refresh:
            cached_formats = self.format_cache.get(cache_key)
            if cached_formats is not None:
                self.stats['cache_hits'] += 1
                return cached_formats
        
        # 缓存未命中，获取新数据
        self.stats['cache_misses'] += 1
        formats = controller.get_formats(device_index)
        self.format_cache.set(cache_key, formats)
        
        return formats
    
    def cached_device_controls(self, controller, device_index: int, force_refresh: bool = False) -> List:
        """缓存的设备控制参数"""
        cache_key = f"controls_{id(controller)}_{device_index}"
        
        if not force_refresh:
            cached_controls = self.control_cache.get(cache_key)
            if cached_controls is not None:
                self.stats['cache_hits'] += 1
                return cached_controls
        
        # 缓存未命中，获取新数据
        self.stats['cache_misses'] += 1
        controls = controller.get_controls(device_index)
        self.control_cache.set(cache_key, controls, ttl=30.0)  # 控制参数缓存时间较短
        
        return controls
    
    def async_device_enumeration(self, controller) -> Future:
        """异步设备枚举"""
        self.stats['async_operations'] += 1
        return self.thread_pool.submit(self.cached_device_list, controller)
    
    def async_format_query(self, controller, device_index: int) -> Future:
        """异步格式查询"""
        self.stats['async_operations'] += 1
        return self.thread_pool.submit(self.cached_device_formats, controller, device_index)
    
    def async_control_query(self, controller, device_index: int) -> Future:
        """异步控制参数查询"""
        self.stats['async_operations'] += 1
        return self.thread_pool.submit(self.cached_device_controls, controller, device_index)
    
    def batch_device_info(self, controller, device_indices: List[int]) -> Dict[int, Dict[str, Any]]:
        """批量获取设备信息"""
        results = {}
        futures = {}
        
        # 启动异步操作
        for device_index in device_indices:
            futures[device_index] = {
                'formats': self.async_format_query(controller, device_index),
                'controls': self.async_control_query(controller, device_index)
            }
        
        # 收集结果
        for device_index, device_futures in futures.items():
            try:
                results[device_index] = {
                    'formats': device_futures['formats'].result(timeout=5.0),
                    'controls': device_futures['controls'].result(timeout=5.0)
                }
            except Exception as e:
                results[device_index] = {
                    'formats': [],
                    'controls': [],
                    'error': str(e)
                }
        
        return results
    
    def preload_device_info(self, controller) -> None:
        """预加载设备信息"""
        try:
            # 获取设备列表
            devices = self.cached_device_list(controller)
            
            if not devices:
                return
            
            # 预加载前几个设备的信息
            device_indices = [device.index for device in devices[:3]]  # 只预加载前3个设备
            self.batch_device_info(controller, device_indices)
            
        except Exception as e:
            print(f"预加载设备信息失败: {e}")
    
    def invalidate_cache(self, controller, device_index: Optional[int] = None) -> None:
        """使缓存失效"""
        if device_index is not None:
            # 使特定设备的缓存失效
            format_key = f"formats_{id(controller)}_{device_index}"
            control_key = f"controls_{id(controller)}_{device_index}"
            
            self.format_cache._remove(format_key)
            self.control_cache._remove(control_key)
        else:
            # 使所有相关缓存失效
            device_key = f"devices_{id(controller)}"
            self.device_cache._remove(device_key)
            
            # 清空格式和控制缓存
            self.format_cache.clear()
            self.control_cache.clear()
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计"""
        total_cache_operations = self.stats['cache_hits'] + self.stats['cache_misses']
        cache_hit_rate = (self.stats['cache_hits'] / total_cache_operations * 100 
                         if total_cache_operations > 0 else 0)
        
        return {
            'cache_hit_rate': f"{cache_hit_rate:.1f}%",
            'cache_hits': self.stats['cache_hits'],
            'cache_misses': self.stats['cache_misses'],
            'async_operations': self.stats['async_operations'],
            'total_operations': self.stats['total_operations'],
            'device_cache_size': len(self.device_cache.cache),
            'format_cache_size': len(self.format_cache.cache),
            'control_cache_size': len(self.control_cache.cache)
        }
    
    def cleanup(self) -> None:
        """清理资源"""
        self.thread_pool.shutdown(wait=True)
        self.device_cache.clear()
        self.format_cache.clear()
        self.control_cache.clear()
    
    def __del__(self):
        """析构函数"""
        try:
            self.cleanup()
        except:
            pass


def performance_monitor(func: Callable) -> Callable:
    """性能监控装饰器"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            # 记录性能信息
            if hasattr(global_optimizer, 'stats'):
                global_optimizer.stats['total_operations'] += 1
            
            # 如果执行时间过长，记录警告
            if execution_time > 2.0:
                print(f"⚠️  {func.__name__} 执行时间较长: {execution_time:.2f}s")
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            print(f"❌ {func.__name__} 执行失败 ({execution_time:.2f}s): {e}")
            raise
    
    return wrapper


def cached_method(ttl: float = 300.0):
    """缓存方法装饰器"""
    def decorator(func: Callable) -> Callable:
        cache = LRUCache(max_size=64, default_ttl=ttl)
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = f"{func.__name__}_{hash(str(args) + str(sorted(kwargs.items())))}"
            
            # 尝试从缓存获取
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # 执行函数并缓存结果
            result = func(*args, **kwargs)
            cache.set(cache_key, result)
            
            return result
        
        return wrapper
    return decorator


# 全局性能优化器实例
global_optimizer = PerformanceOptimizer()


# 导出主要接口
__all__ = [
    'LRUCache', 'PerformanceOptimizer', 'global_optimizer',
    'performance_monitor', 'cached_method'
]
