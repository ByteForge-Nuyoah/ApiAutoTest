# -*- coding: utf-8 -*-
# @Author  : 会飞的🐟
# @File    : global_vars.py
# @Desc: 全局变量管理器，支持线程安全、测试隔离

import threading
import copy
from typing import Any, Dict, Optional
from loguru import logger


class GlobalVarsManager:
    """
    全局变量管理器

    特性：
    1. 线程安全：使用线程锁保护数据
    2. 测试隔离：支持保存/恢复快照，防止测试间污染
    3. 只读配置：区分配置数据和运行时数据
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """单例模式，确保全局唯一实例"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """初始化全局变量管理器"""
        if self._initialized:
            return

        self._data_lock = threading.Lock()
        # 配置数据（只读，从环境配置加载）
        self._config_data: Dict[str, Any] = {}
        # 运行时数据（可变，测试过程中动态更新）
        self._runtime_data: Dict[str, Any] = {}
        # 快照栈，用于测试隔离
        self._snapshot_stack: list = []
        # 初始化标记
        self._initialized = True
        logger.debug("GlobalVarsManager 初始化完成")

    def init_config(self, config: Dict[str, Any]) -> None:
        """
        初始化配置数据（只读）

        Args:
            config: 配置字典，通常从环境配置文件加载
        """
        with self._data_lock:
            self._config_data = copy.deepcopy(config)
            logger.debug(f"初始化配置数据: {list(config.keys())}")

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取变量值（优先从运行时数据获取，其次从配置数据获取）

        Args:
            key: 变量名
            default: 默认值

        Returns:
            变量值
        """
        with self._data_lock:
            # 优先从运行时数据获取
            if key in self._runtime_data:
                return copy.deepcopy(self._runtime_data[key])
            # 其次从配置数据获取
            if key in self._config_data:
                return copy.deepcopy(self._config_data[key])
            return default

    def set(self, key: str, value: Any) -> None:
        """
        设置运行时变量

        Args:
            key: 变量名
            value: 变量值
        """
        with self._data_lock:
            self._runtime_data[key] = copy.deepcopy(value)
            logger.trace(f"设置运行时变量: {key}={type(value).__name__}")

    def update(self, data: Dict[str, Any]) -> None:
        """
        批量更新运行时变量

        Args:
            data: 变量字典
        """
        if not data:
            return
        with self._data_lock:
            self._runtime_data.update(copy.deepcopy(data))
            logger.trace(f"批量更新运行时变量: {list(data.keys())}")

    def delete(self, key: str) -> bool:
        """
        删除运行时变量

        Args:
            key: 变量名

        Returns:
            是否删除成功
        """
        with self._data_lock:
            if key in self._runtime_data:
                del self._runtime_data[key]
                return True
            return False

    def clear_runtime(self) -> None:
        """
        清空所有运行时变量（保留配置数据）
        """
        with self._data_lock:
            self._runtime_data.clear()
            logger.debug("已清空所有运行时变量")

    def save_snapshot(self) -> int:
        """
        保存当前运行时数据快照

        Returns:
            快照ID（在栈中的位置）
        """
        with self._data_lock:
            snapshot = copy.deepcopy(self._runtime_data)
            self._snapshot_stack.append(snapshot)
            snapshot_id = len(self._snapshot_stack) - 1
            logger.trace(f"保存快照 #{snapshot_id}, 变量数: {len(snapshot)}")
            return snapshot_id

    def restore_snapshot(self, snapshot_id: Optional[int] = None) -> bool:
        """
        恢复到指定快照

        Args:
            snapshot_id: 快照ID，如果为None则恢复到最近的快照

        Returns:
            是否恢复成功
        """
        with self._data_lock:
            if not self._snapshot_stack:
                logger.warning("快照栈为空，无法恢复")
                return False

            if snapshot_id is not None:
                if snapshot_id < 0 or snapshot_id >= len(self._snapshot_stack):
                    logger.error(f"无效的快照ID: {snapshot_id}")
                    return False
                # 弹出到指定快照
                while len(self._snapshot_stack) > snapshot_id + 1:
                    self._snapshot_stack.pop()
                snapshot = self._snapshot_stack.pop()
            else:
                snapshot = self._snapshot_stack.pop()

            self._runtime_data = copy.deepcopy(snapshot)
            logger.trace(f"恢复快照, 变量数: {len(self._runtime_data)}")
            return True

    def get_all(self) -> Dict[str, Any]:
        """
        获取所有变量（配置 + 运行时）

        Returns:
            变量字典的深拷贝
        """
        with self._data_lock:
            result = copy.deepcopy(self._config_data)
            result.update(copy.deepcopy(self._runtime_data))
            return result

    def get_runtime_data(self) -> Dict[str, Any]:
        """
        获取运行时变量

        Returns:
            运行时变量字典的深拷贝
        """
        with self._data_lock:
            return copy.deepcopy(self._runtime_data)

    def get_config_data(self) -> Dict[str, Any]:
        """
        获取配置数据

        Returns:
            配置数据字典的深拷贝
        """
        with self._data_lock:
            return copy.deepcopy(self._config_data)

    def __contains__(self, key: str) -> bool:
        """支持 `key in manager` 语法"""
        with self._data_lock:
            return key in self._runtime_data or key in self._config_data

    def __getitem__(self, key: str) -> Any:
        """支持 `manager[key]` 语法"""
        value = self.get(key)
        if value is None and key not in self._runtime_data and key not in self._config_data:
            raise KeyError(key)
        return value

    def __setitem__(self, key: str, value: Any) -> None:
        """支持 `manager[key] = value` 语法"""
        self.set(key, value)

    def __repr__(self) -> str:
        """字符串表示"""
        with self._data_lock:
            return (f"GlobalVarsManager(config_keys={list(self._config_data.keys())}, "
                    f"runtime_keys={list(self._runtime_data.keys())})")


# 全局单例实例
_global_vars_manager: Optional[GlobalVarsManager] = None
_global_lock = threading.Lock()


def get_global_vars() -> GlobalVarsManager:
    """
    获取全局变量管理器单例

    Returns:
        GlobalVarsManager 实例
    """
    global _global_vars_manager
    if _global_vars_manager is None:
        with _global_lock:
            if _global_vars_manager is None:
                _global_vars_manager = GlobalVarsManager()
    return _global_vars_manager


def reset_global_vars() -> None:
    """
    重置全局变量管理器（主要用于测试）
    """
    global _global_vars_manager
    with _global_lock:
        if _global_vars_manager is not None:
            _global_vars_manager.clear_runtime()
        _global_vars_manager = None
    logger.debug("全局变量管理器已重置")
