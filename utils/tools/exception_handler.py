# -*- coding: utf-8 -*-
# @Author  : 会飞的🐟
# @File    : exception_handler.py
# @Desc: 统一异常处理模块

import json
import traceback
from typing import Optional, Dict, Any
from datetime import datetime
from loguru import logger
from enum import Enum


class ExceptionLevel(Enum):
    """
    异常级别
    """
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ExceptionCategory(Enum):
    """
    异常分类
    """
    ASSERTION = "assertion"
    REQUEST = "request"
    DATA = "data"
    CONFIG = "config"
    NETWORK = "network"
    TIMEOUT = "timeout"
    DATABASE = "database"
    UNKNOWN = "unknown"


class AutomationException(Exception):
    """
    自动化测试基础异常类
    """
    
    def __init__(
        self,
        message: str,
        category: ExceptionCategory = ExceptionCategory.UNKNOWN,
        level: ExceptionLevel = ExceptionLevel.MEDIUM,
        details: Optional[Dict[str, Any]] = None,
        original_exception: Optional[Exception] = None
    ):
        self.message = message
        self.category = category
        self.level = level
        self.details = details or {}
        self.original_exception = original_exception
        self.timestamp = datetime.now()
        self.traceback_str = traceback.format_exc() if original_exception else ""
        
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典格式
        :return: 异常信息字典
        """
        return {
            "message": self.message,
            "category": self.category.value,
            "level": self.level.value,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
            "traceback": self.traceback_str,
            "original_exception": str(self.original_exception) if self.original_exception else None
        }
    
    def __str__(self) -> str:
        return f"[{self.category.value.upper()}] {self.message}"


class AssertionException(AutomationException):
    """
    断言异常
    """
    
    def __init__(
        self,
        message: str,
        expected: Any = None,
        actual: Any = None,
        assert_type: str = None,
        details: Optional[Dict[str, Any]] = None
    ):
        _details = details or {}
        if expected is not None:
            _details["expected"] = expected
        if actual is not None:
            _details["actual"] = actual
        if assert_type:
            _details["assert_type"] = assert_type
        
        super().__init__(
            message=message,
            category=ExceptionCategory.ASSERTION,
            level=ExceptionLevel.HIGH,
            details=_details
        )


class RequestException(AutomationException):
    """
    请求异常
    """
    
    def __init__(
        self,
        message: str,
        url: str = None,
        method: str = None,
        status_code: int = None,
        response: Any = None,
        details: Optional[Dict[str, Any]] = None
    ):
        _details = details or {}
        if url:
            _details["url"] = url
        if method:
            _details["method"] = method
        if status_code:
            _details["status_code"] = status_code
        if response:
            _details["response"] = str(response)[:500]
        
        super().__init__(
            message=message,
            category=ExceptionCategory.REQUEST,
            level=ExceptionLevel.HIGH,
            details=_details
        )


class DataException(AutomationException):
    """
    数据异常
    """
    
    def __init__(
        self,
        message: str,
        data_path: str = None,
        data_type: str = None,
        details: Optional[Dict[str, Any]] = None
    ):
        _details = details or {}
        if data_path:
            _details["data_path"] = data_path
        if data_type:
            _details["data_type"] = data_type
        
        super().__init__(
            message=message,
            category=ExceptionCategory.DATA,
            level=ExceptionLevel.MEDIUM,
            details=_details
        )


class ConfigException(AutomationException):
    """
    配置异常
    """
    
    def __init__(
        self,
        message: str,
        config_key: str = None,
        config_file: str = None,
        details: Optional[Dict[str, Any]] = None
    ):
        _details = details or {}
        if config_key:
            _details["config_key"] = config_key
        if config_file:
            _details["config_file"] = config_file
        
        super().__init__(
            message=message,
            category=ExceptionCategory.CONFIG,
            level=ExceptionLevel.CRITICAL,
            details=_details
        )


class NetworkException(AutomationException):
    """
    网络异常
    """
    
    def __init__(
        self,
        message: str,
        url: str = None,
        retry_count: int = 0,
        details: Optional[Dict[str, Any]] = None
    ):
        _details = details or {}
        if url:
            _details["url"] = url
        if retry_count:
            _details["retry_count"] = retry_count
        
        super().__init__(
            message=message,
            category=ExceptionCategory.NETWORK,
            level=ExceptionLevel.HIGH,
            details=_details
        )


class TimeoutException(AutomationException):
    """
    超时异常
    """
    
    def __init__(
        self,
        message: str,
        timeout: float = None,
        operation: str = None,
        details: Optional[Dict[str, Any]] = None
    ):
        _details = details or {}
        if timeout:
            _details["timeout"] = timeout
        if operation:
            _details["operation"] = operation
        
        super().__init__(
            message=message,
            category=ExceptionCategory.TIMEOUT,
            level=ExceptionLevel.MEDIUM,
            details=_details
        )


class DatabaseException(AutomationException):
    """
    数据库异常
    """
    
    def __init__(
        self,
        message: str,
        sql: str = None,
        db_name: str = None,
        details: Optional[Dict[str, Any]] = None
    ):
        _details = details or {}
        if sql:
            _details["sql"] = sql
        if db_name:
            _details["db_name"] = db_name
        
        super().__init__(
            message=message,
            category=ExceptionCategory.DATABASE,
            level=ExceptionLevel.HIGH,
            details=_details
        )


def handle_exception(
    exception: Exception,
    context: Optional[Dict[str, Any]] = None,
    raise_exception: bool = False
) -> Dict[str, Any]:
    """
    统一异常处理函数
    :param exception: 异常对象
    :param context: 上下文信息
    :param raise_exception: 是否重新抛出异常
    :return: 异常信息字典
    """
    if isinstance(exception, AutomationException):
        error_info = exception.to_dict()
    else:
        error_info = {
            "message": str(exception),
            "category": ExceptionCategory.UNKNOWN.value,
            "level": ExceptionLevel.MEDIUM.value,
            "details": {},
            "timestamp": datetime.now().isoformat(),
            "traceback": traceback.format_exc(),
            "original_exception": str(exception)
        }
    
    if context:
        error_info["context"] = context
    
    logger.error(
        f"\n{'='*60}\n"
        f"异常类型: {error_info['category'].upper()}\n"
        f"异常级别: {error_info['level'].upper()}\n"
        f"异常信息: {error_info['message']}\n"
        f"异常时间: {error_info['timestamp']}\n"
        f"详细信息: {json.dumps(error_info.get('details', {}), ensure_ascii=False, indent=2)}\n"
        f"堆栈跟踪:\n{error_info['traceback']}\n"
        f"{'='*60}"
    )
    
    if raise_exception:
        if isinstance(exception, AutomationException):
            raise exception
        else:
            raise AutomationException(
                message=str(exception),
                original_exception=exception
            )
    
    return error_info


def safe_execute(
    func,
    *args,
    default=None,
    context: Optional[Dict[str, Any]] = None,
    raise_exception: bool = False,
    **kwargs
) -> Any:
    """
    安全执行函数，捕获异常并记录
    :param func: 要执行的函数
    :param args: 位置参数
    :param default: 发生异常时的默认返回值
    :param context: 上下文信息
    :param raise_exception: 是否重新抛出异常
    :param kwargs: 关键字参数
    :return: 函数执行结果或默认值
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        handle_exception(e, context=context, raise_exception=raise_exception)
        return default
