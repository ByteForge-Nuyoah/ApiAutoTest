# -*- coding: utf-8 -*-
# @Author  : 会飞的🐟
# @File    : failure_snapshot.py
# @Desc: 失败快照模块 - 测试失败时自动捕获关键信息

import os
import json
import traceback
from typing import Optional, Dict, Any
from datetime import datetime
from loguru import logger


class FailureSnapshot:
    """失败快照类 - 记录测试失败时的关键信息"""

    def __init__(self, test_id: str, test_name: str):
        self.test_id = test_id
        self.test_name = test_name
        self.timestamp = datetime.now()
        self.exception: Optional[Exception] = None
        self.request_info: Dict[str, Any] = {}
        self.response_info: Dict[str, Any] = {}
        self.stack_trace: str = ""

    def set_failure(self, exception: Exception) -> None:
        """设置失败信息"""
        self.exception = exception
        self.stack_trace = "".join(traceback.format_exception(
            type(exception), exception, exception.__traceback__
        ))

    def set_request(self, url: str, method: str, **kwargs) -> None:
        """设置请求信息"""
        self.request_info = {
            "url": url,
            "method": method,
            **{k: self._truncate(v) for k, v in kwargs.items() if v is not None}
        }

    def set_response(self, status_code: int, **kwargs) -> None:
        """设置响应信息"""
        self.response_info = {
            "status_code": status_code,
            **{k: self._truncate(v) for k, v in kwargs.items() if v is not None}
        }

    def _truncate(self, data: Any, max_length: int = 500) -> Any:
        """截断过长的数据"""
        if data is None:
            return None
        if isinstance(data, str):
            return data[:max_length] + "..." if len(data) > max_length else data
        if isinstance(data, (dict, list)):
            serialized = json.dumps(data, ensure_ascii=False, default=str)
            if len(serialized) > max_length:
                return serialized[:max_length] + "...[truncated]"
        return data

    def to_dict(self, save_stack_trace: bool = True) -> Dict[str, Any]:
        """转换为字典（简化版）"""
        result = {
            "test_id": self.test_id,
            "test_name": self.test_name,
            "timestamp": self.timestamp.isoformat(),
            "exception": {
                "type": type(self.exception).__name__ if self.exception else "Unknown",
                "message": str(self.exception) if self.exception else ""
            },
            "request": self.request_info,
            "response": self.response_info
        }
        if save_stack_trace and self.stack_trace:
            result["stack_trace"] = self.stack_trace
        return result

    def save_to_file(self, output_dir: str) -> Optional[str]:
        """保存快照到文件"""
        try:
            os.makedirs(output_dir, exist_ok=True)
            filename = f"failure_{self.test_id.replace('::', '_')}_{self.timestamp.strftime('%Y%m%d_%H%M%S')}.json"
            filepath = os.path.join(output_dir, filename)

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)

            logger.info(f"失败快照已保存: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"保存快照失败: {e}")
            return None

    def attach_to_allure(self) -> None:
        """附加到 Allure 报告"""
        try:
            import allure
            snapshot_data = self.to_dict(save_stack_trace=False)

            # 添加摘要步骤
            with allure.step(f"❌ 失败详情: {self.test_name}"):
                # 请求信息
                if self.request_info:
                    allure.attach(
                        json.dumps(self.request_info, ensure_ascii=False, indent=2),
                        name="📤 请求信息",
                        attachment_type=allure.attachment_type.JSON
                    )

                # 响应信息
                if self.response_info:
                    allure.attach(
                        json.dumps(self.response_info, ensure_ascii=False, indent=2),
                        name="📥 响应信息",
                        attachment_type=allure.attachment_type.JSON
                    )

                # 异常信息
                if self.exception:
                    allure.attach(
                        f"{type(self.exception).__name__}: {str(self.exception)}",
                        name="❌ 异常信息",
                        attachment_type=allure.attachment_type.TEXT
                    )

                # 完整快照
                allure.attach(
                    json.dumps(snapshot_data, ensure_ascii=False, indent=2),
                    name="🔍 完整快照",
                    attachment_type=allure.attachment_type.JSON
                )
        except Exception as e:
            logger.error(f"附加快照到 Allure 失败: {e}")


# 全局快照管理
_snapshots: Dict[str, FailureSnapshot] = {}


def capture_failure(
    test_id: str,
    test_name: str,
    exception: Exception,
    request_info: Dict[str, Any] = None,
    response_info: Dict[str, Any] = None
) -> FailureSnapshot:
    """
    捕获失败快照（简化版）
    :param test_id: 测试用例ID
    :param test_name: 测试用例名称
    :param exception: 异常对象
    :param request_info: 请求信息
    :param response_info: 响应信息
    :return: 快照对象
    """
    snapshot = FailureSnapshot(test_id, test_name)
    snapshot.set_failure(exception)

    if request_info:
        snapshot.set_request(**request_info)

    if response_info:
        snapshot.set_response(**response_info)

    _snapshots[test_id] = snapshot
    return snapshot


def get_snapshot(test_id: str) -> Optional[FailureSnapshot]:
    """获取快照"""
    return _snapshots.get(test_id)


def get_all_snapshots() -> Dict[str, FailureSnapshot]:
    """获取所有快照"""
    return _snapshots


def clear_snapshots() -> None:
    """清空所有快照"""
    _snapshots.clear()
