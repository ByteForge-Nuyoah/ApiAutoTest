# -*- coding: utf-8 -*-
# @Author  : 会飞的🐟
# @File    : mock_service.py
# @Desc: Mock 接口数据服务模块

import json
import time
import hashlib
import re
from typing import Optional, Dict, Any, List, Callable, Union
from datetime import datetime
from loguru import logger
from functools import wraps
from enum import Enum


class MockMode(Enum):
    """
    Mock 模式
    """
    DISABLED = "disabled"
    STUB = "stub"
    RECORD = "record"
    REPLAY = "replay"
    MIXED = "mixed"


class MockResponse:
    """
    Mock 响应对象
    模拟 requests.Response 对象
    """
    
    def __init__(
        self,
        status_code: int = 200,
        headers: Dict = None,
        body: Any = None,
        elapsed: float = 0.0
    ):
        """
        初始化 Mock 响应
        :param status_code: 状态码
        :param headers: 响应头
        :param body: 响应体
        :param elapsed: 耗时（秒）
        """
        self.status_code = status_code
        self.headers = headers or {"Content-Type": "application/json"}
        self._body = body
        self.elapsed_seconds = elapsed
    
    @property
    def text(self) -> str:
        """
        获取文本响应
        :return: 响应文本
        """
        if isinstance(self._body, (dict, list)):
            return json.dumps(self._body, ensure_ascii=False)
        return str(self._body) if self._body else ""
    
    @property
    def content(self) -> bytes:
        """
        获取字节响应
        :return: 响应字节
        """
        return self.text.encode('utf-8')
    
    def json(self) -> Any:
        """
        获取 JSON 响应
        :return: JSON 对象
        """
        if isinstance(self._body, (dict, list)):
            return self._body
        try:
            return json.loads(self.text)
        except json.JSONDecodeError:
            return None
    
    @property
    def elapsed(self):
        """
        获取耗时对象
        :return: 耗时
        """
        class Elapsed:
            def __init__(self, seconds):
                self._seconds = seconds
            
            @property
            def total_seconds(self):
                return self._seconds
            
            def __str__(self):
                return f"{self._seconds}s"
        
        return Elapsed(self.elapsed_seconds)
    
    def raise_for_status(self):
        """
        检查状态码
        :raises: HTTPError 如果状态码表示错误
        """
        if 400 <= self.status_code < 600:
            from requests import HTTPError
            raise HTTPError(f"{self.status_code} Error")
    
    def __repr__(self) -> str:
        return f"<MockResponse [{self.status_code}]>"


class MockRule:
    """
    Mock 规则
    定义如何匹配请求和返回响应
    """
    
    def __init__(
        self,
        name: str,
        url_pattern: str = None,
        method: str = None,
        request_matcher: Callable = None,
        response_builder: Union[Callable, Dict, Any] = None,
        delay: float = 0.0,
        priority: int = 0
    ):
        """
        初始化 Mock 规则
        :param name: 规则名称
        :param url_pattern: URL 匹配模式（支持正则）
        :param method: 请求方法
        :param request_matcher: 自定义请求匹配函数
        :param response_builder: 响应构建器（函数或静态值）
        :param delay: 延迟时间（秒）
        :param priority: 优先级（越大越优先）
        """
        self.name = name
        self.url_pattern = url_pattern
        self.method = method.upper() if method else None
        self.request_matcher = request_matcher
        self.response_builder = response_builder
        self.delay = delay
        self.priority = priority
        self.hit_count = 0
    
    def match(self, url: str, method: str, **kwargs) -> bool:
        """
        检查请求是否匹配规则
        :param url: 请求 URL
        :param method: 请求方法
        :param kwargs: 其他请求参数
        :return: 是否匹配
        """
        if self.method and self.method != method.upper():
            return False
        
        if self.url_pattern:
            if not re.search(self.url_pattern, url):
                return False
        
        if self.request_matcher:
            try:
                return self.request_matcher(url=url, method=method, **kwargs)
            except Exception as e:
                logger.error(f"Mock 规则匹配函数执行错误: {e}")
                return False
        
        return True
    
    def build_response(self, **kwargs) -> MockResponse:
        """
        构建 Mock 响应
        :param kwargs: 请求参数
        :return: Mock 响应对象
        """
        if self.delay > 0:
            time.sleep(self.delay)
        
        self.hit_count += 1
        
        if callable(self.response_builder):
            try:
                result = self.response_builder(**kwargs)
                if isinstance(result, MockResponse):
                    return result
                elif isinstance(result, dict):
                    return MockResponse(**result)
                else:
                    return MockResponse(body=result)
            except Exception as e:
                logger.error(f"Mock 响应构建函数执行错误: {e}")
                return MockResponse(status_code=500, body={"error": str(e)})
        
        if isinstance(self.response_builder, dict):
            return MockResponse(**self.response_builder)
        
        return MockResponse(body=self.response_builder)


class MockService:
    """
    Mock 服务
    管理 Mock 规则和请求拦截
    """
    
    def __init__(self, mode: MockMode = MockMode.DISABLED):
        """
        初始化 Mock 服务
        :param mode: Mock 模式
        """
        self._mode = mode
        self._rules: List[MockRule] = []
        self._recordings: Dict[str, Any] = {}
        self._enabled = mode != MockMode.DISABLED
    
    @property
    def mode(self) -> MockMode:
        """
        获取当前模式
        :return: Mock 模式
        """
        return self._mode
    
    @mode.setter
    def mode(self, value: MockMode):
        """
        设置模式
        :param value: Mock 模式
        """
        self._mode = value
        self._enabled = value != MockMode.DISABLED
    
    @property
    def enabled(self) -> bool:
        """
        是否启用
        :return: 是否启用
        """
        return self._enabled
    
    def enable(self) -> None:
        """
        启用 Mock 服务
        """
        self._enabled = True
        logger.info("Mock 服务已启用")
    
    def disable(self) -> None:
        """
        禁用 Mock 服务
        """
        self._enabled = False
        logger.info("Mock 服务已禁用")
    
    def add_rule(self, rule: MockRule) -> None:
        """
        添加 Mock 规则
        :param rule: Mock 规则
        """
        self._rules.append(rule)
        self._rules.sort(key=lambda r: r.priority, reverse=True)
        logger.debug(f"添加 Mock 规则: {rule.name}")
    
    def add_stub(
        self,
        name: str,
        url_pattern: str,
        response: Any,
        method: str = None,
        status_code: int = 200,
        delay: float = 0.0,
        priority: int = 0
    ) -> MockRule:
        """
        快捷添加 Stub 规则
        :param name: 规则名称
        :param url_pattern: URL 匹配模式
        :param response: 响应内容
        :param method: 请求方法
        :param status_code: 状态码
        :param delay: 延迟时间
        :param priority: 优先级
        :return: Mock 规则
        """
        rule = MockRule(
            name=name,
            url_pattern=url_pattern,
            method=method,
            response_builder={"status_code": status_code, "body": response},
            delay=delay,
            priority=priority
        )
        self.add_rule(rule)
        return rule
    
    def remove_rule(self, name: str) -> bool:
        """
        移除 Mock 规则
        :param name: 规则名称
        :return: 是否移除成功
        """
        for i, rule in enumerate(self._rules):
            if rule.name == name:
                self._rules.pop(i)
                logger.debug(f"移除 Mock 规则: {name}")
                return True
        return False
    
    def clear_rules(self) -> None:
        """
        清空所有规则
        """
        self._rules.clear()
        logger.debug("已清空所有 Mock 规则")
    
    def mock_request(
        self,
        url: str,
        method: str = "GET",
        **kwargs
    ) -> Optional[MockResponse]:
        """
        处理 Mock 请求
        :param url: 请求 URL
        :param method: 请求方法
        :param kwargs: 其他请求参数
        :return: Mock 响应（如果匹配）
        """
        if not self._enabled:
            return None
        
        for rule in self._rules:
            if rule.match(url, method, **kwargs):
                logger.info(f"Mock 命中规则: {rule.name} -> {method} {url}")
                return rule.build_response(url=url, method=method, **kwargs)
        
        if self._mode == MockMode.STUB:
            logger.warning(f"Mock 未命中规则: {method} {url}")
            return MockResponse(
                status_code=404,
                body={"error": "No mock rule matched", "url": url}
            )
        
        return None
    
    def record_response(self, url: str, method: str, response: Any) -> None:
        """
        记录响应（用于 Replay 模式）
        :param url: 请求 URL
        :param method: 请求方法
        :param response: 响应对象
        """
        if self._mode not in [MockMode.RECORD, MockMode.MIXED]:
            return
        
        key = self._generate_key(url, method)
        self._recordings[key] = {
            "url": url,
            "method": method,
            "status_code": getattr(response, 'status_code', 200),
            "body": response.json() if hasattr(response, 'json') else str(response),
            "timestamp": datetime.now().isoformat()
        }
        logger.debug(f"记录响应: {method} {url}")
    
    def get_recorded_response(self, url: str, method: str) -> Optional[MockResponse]:
        """
        获取记录的响应（用于 Replay 模式）
        :param url: 请求 URL
        :param method: 请求方法
        :return: Mock 响应
        """
        if self._mode not in [MockMode.REPLAY, MockMode.MIXED]:
            return None
        
        key = self._generate_key(url, method)
        recorded = self._recordings.get(key)
        
        if recorded:
            logger.info(f"Replay 命中记录: {method} {url}")
            return MockResponse(
                status_code=recorded["status_code"],
                body=recorded["body"]
            )
        
        return None
    
    def _generate_key(self, url: str, method: str) -> str:
        """
        生成缓存键
        :param url: 请求 URL
        :param method: 请求方法
        :return: 缓存键
        """
        return hashlib.md5(f"{method}:{url}".encode()).hexdigest()
    
    def load_recordings(self, file_path: str) -> None:
        """
        从文件加载记录
        :param file_path: 文件路径
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self._recordings = data
            logger.info(f"加载 Mock 记录: {file_path}, 共 {len(data)} 条")
        except Exception as e:
            logger.error(f"加载 Mock 记录失败: {e}")
    
    def save_recordings(self, file_path: str) -> None:
        """
        保存记录到文件
        :param file_path: 文件路径
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self._recordings, f, ensure_ascii=False, indent=2)
            logger.info(f"保存 Mock 记录: {file_path}, 共 {len(self._recordings)} 条")
        except Exception as e:
            logger.error(f"保存 Mock 记录失败: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息
        :return: 统计信息
        """
        return {
            "mode": self._mode.value,
            "enabled": self._enabled,
            "rules_count": len(self._rules),
            "recordings_count": len(self._recordings),
            "rules": [
                {"name": r.name, "hit_count": r.hit_count}
                for r in self._rules
            ]
        }


_mock_service: Optional[MockService] = None


def get_mock_service(mode: MockMode = MockMode.DISABLED) -> MockService:
    """
    获取 Mock 服务单例
    :param mode: Mock 模式
    :return: MockService 实例
    """
    global _mock_service
    if _mock_service is None:
        _mock_service = MockService(mode)
    return _mock_service


def mock_response(
    url_pattern: str,
    response: Any,
    method: str = None,
    status_code: int = 200,
    delay: float = 0.0
):
    """
    Mock 响应装饰器
    :param url_pattern: URL 匹配模式
    :param response: 响应内容
    :param method: 请求方法
    :param status_code: 状态码
    :param delay: 延迟时间
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            mock_service = get_mock_service()
            mock_service.add_stub(
                name=f"decorator_{func.__name__}",
                url_pattern=url_pattern,
                response=response,
                method=method,
                status_code=status_code,
                delay=delay
            )
            return func(*args, **kwargs)
        return wrapper
    return decorator
