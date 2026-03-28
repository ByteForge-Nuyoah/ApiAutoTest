# -*- coding: utf-8 -*-
# @Author  : 会飞的🐟
# @File    : failure_snapshot.py
# @Desc: 失败快照模块 - 测试失败时自动捕获上下文信息

import os
import json
import time
import traceback
from typing import Optional, Dict, Any, List
from datetime import datetime
from pathlib import Path
from loguru import logger


class FailureSnapshot:
    """
    失败快照类
    用于记录测试失败时的详细信息
    """
    
    def __init__(self, test_id: str, test_name: str):
        """
        初始化快照
        :param test_id: 测试用例ID
        :param test_name: 测试用例名称
        """
        self.test_id = test_id
        self.test_name = test_name
        self.timestamp = datetime.now()
        self.failure_info: Dict[str, Any] = {}
        self.request_info: Dict[str, Any] = {}
        self.response_info: Dict[str, Any] = {}
        self.context_vars: Dict[str, Any] = {}
        self.stack_trace: str = ""
        self.screenshot_path: Optional[str] = None
        self.logs: List[str] = []
        self.tags: List[str] = []
    
    def set_failure_info(
        self,
        exception: Exception,
        message: str = None,
        category: str = "unknown"
    ) -> None:
        """
        设置失败信息
        :param exception: 异常对象
        :param message: 自定义消息
        :param category: 异常分类
        """
        self.failure_info = {
            "exception_type": type(exception).__name__,
            "exception_message": str(exception),
            "custom_message": message,
            "category": category,
            "timestamp": self.timestamp.isoformat()
        }
        self.stack_trace = "".join(traceback.format_exception(
            type(exception), exception, exception.__traceback__
        ))
    
    def set_request_info(
        self,
        url: str,
        method: str,
        headers: Dict = None,
        params: Dict = None,
        body: Any = None,
        cookies: Dict = None
    ) -> None:
        """
        设置请求信息
        :param url: 请求URL
        :param method: 请求方法
        :param headers: 请求头
        :param params: 请求参数
        :param body: 请求体
        :param cookies: Cookies
        """
        self.request_info = {
            "url": url,
            "method": method,
            "headers": self._safe_serialize(headers),
            "params": self._safe_serialize(params),
            "body": self._safe_serialize(body),
            "cookies": self._safe_serialize(cookies)
        }
    
    def set_response_info(
        self,
        status_code: int,
        headers: Dict = None,
        body: Any = None,
        elapsed: float = None
    ) -> None:
        """
        设置响应信息
        :param status_code: 状态码
        :param headers: 响应头
        :param body: 响应体
        :param elapsed: 耗时（秒）
        """
        self.response_info = {
            "status_code": status_code,
            "headers": self._safe_serialize(headers),
            "body": self._safe_serialize(body, max_length=2000),
            "elapsed_seconds": elapsed
        }
    
    def set_context_vars(self, variables: Dict[str, Any]) -> None:
        """
        设置上下文变量
        :param variables: 变量字典
        """
        self.context_vars = self._safe_serialize(variables)
    
    def add_log(self, log_message: str) -> None:
        """
        添加日志记录
        :param log_message: 日志消息
        """
        self.logs.append(f"[{datetime.now().isoformat()}] {log_message}")
    
    def add_tag(self, tag: str) -> None:
        """
        添加标签
        :param tag: 标签
        """
        self.tags.append(tag)
    
    def _safe_serialize(self, data: Any, max_length: int = 500) -> Any:
        """
        安全序列化数据
        :param data: 原始数据
        :param max_length: 最大长度
        :return: 序列化后的数据
        """
        if data is None:
            return None
        
        try:
            if isinstance(data, (dict, list)):
                serialized = json.dumps(data, ensure_ascii=False, default=str)
                if len(serialized) > max_length:
                    return serialized[:max_length] + "...[truncated]"
                return data
            elif isinstance(data, str):
                if len(data) > max_length:
                    return data[:max_length] + "...[truncated]"
                return data
            else:
                return str(data)
        except Exception:
            return str(data)[:max_length]
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典格式
        :return: 快照信息字典
        """
        return {
            "test_id": self.test_id,
            "test_name": self.test_name,
            "timestamp": self.timestamp.isoformat(),
            "failure_info": self.failure_info,
            "request_info": self.request_info,
            "response_info": self.response_info,
            "context_vars": self.context_vars,
            "stack_trace": self.stack_trace,
            "screenshot_path": self.screenshot_path,
            "logs": self.logs,
            "tags": self.tags
        }
    
    def save_to_file(self, output_dir: str) -> str:
        """
        保存快照到文件
        :param output_dir: 输出目录
        :return: 文件路径
        """
        os.makedirs(output_dir, exist_ok=True)
        
        filename = f"failure_{self.test_id}_{self.timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
        
        logger.info(f"失败快照已保存: {filepath}")
        return filepath


class SnapshotManager:
    """
    快照管理器
    管理所有测试失败快照
    """
    
    def __init__(self, output_dir: str = None):
        """
        初始化快照管理器
        :param output_dir: 输出目录
        """
        self._snapshots: Dict[str, FailureSnapshot] = {}
        self._output_dir = output_dir or os.path.join("outputs", "failure_snapshots")
    
    def create_snapshot(self, test_id: str, test_name: str) -> FailureSnapshot:
        """
        创建快照
        :param test_id: 测试用例ID
        :param test_name: 测试用例名称
        :return: 快照对象
        """
        snapshot = FailureSnapshot(test_id, test_name)
        self._snapshots[test_id] = snapshot
        return snapshot
    
    def get_snapshot(self, test_id: str) -> Optional[FailureSnapshot]:
        """
        获取快照
        :param test_id: 测试用例ID
        :return: 快照对象
        """
        return self._snapshots.get(test_id)
    
    def save_all(self) -> List[str]:
        """
        保存所有快照
        :return: 文件路径列表
        """
        paths = []
        for snapshot in self._snapshots.values():
            try:
                path = snapshot.save_to_file(self._output_dir)
                paths.append(path)
            except Exception as e:
                logger.error(f"保存快照失败: {snapshot.test_id}, 错误: {e}")
        return paths
    
    def get_summary(self) -> Dict[str, Any]:
        """
        获取快照摘要
        :return: 摘要信息
        """
        return {
            "total_snapshots": len(self._snapshots),
            "test_ids": list(self._snapshots.keys()),
            "output_dir": self._output_dir
        }
    
    def clear(self) -> None:
        """
        清空所有快照
        """
        self._snapshots.clear()


_snapshot_manager: Optional[SnapshotManager] = None


def get_snapshot_manager(output_dir: str = None) -> SnapshotManager:
    """
    获取快照管理器单例
    :param output_dir: 输出目录
    :return: SnapshotManager 实例
    """
    global _snapshot_manager
    if _snapshot_manager is None:
        _snapshot_manager = SnapshotManager(output_dir)
    return _snapshot_manager


def capture_failure(
    test_id: str,
    test_name: str,
    exception: Exception,
    request_info: Dict[str, Any] = None,
    response_info: Dict[str, Any] = None,
    context_vars: Dict[str, Any] = None
) -> FailureSnapshot:
    """
    快捷捕获失败快照
    :param test_id: 测试用例ID
    :param test_name: 测试用例名称
    :param exception: 异常对象
    :param request_info: 请求信息
    :param response_info: 响应信息
    :param context_vars: 上下文变量
    :return: 快照对象
    """
    manager = get_snapshot_manager()
    snapshot = manager.create_snapshot(test_id, test_name)
    
    snapshot.set_failure_info(exception)
    
    if request_info:
        snapshot.set_request_info(**request_info)
    
    if response_info:
        snapshot.set_response_info(**response_info)
    
    if context_vars:
        snapshot.set_context_vars(context_vars)
    
    return snapshot
