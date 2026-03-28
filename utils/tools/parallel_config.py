# -*- coding: utf-8 -*-
# @Author  : 会飞的🐟
# @File    : parallel_config.py
# @Desc: 并行执行策略配置模块

import os
import multiprocessing
from typing import Optional, List
from loguru import logger
from enum import Enum


_log_printed = False


class DistributionMode(Enum):
    """
    pytest-xdist 分布模式
    """
    EACH = "each"
    LOAD = "load"
    LOADSCOPE = "loadscope"
    LOADFILE = "loadfile"
    LOADGROUP = "loadgroup"
    NO = "no"


class ParallelStrategy:
    """
    并行执行策略配置
    用于动态调整并行参数
    """
    
    def __init__(
        self,
        workers: Optional[int] = None,
        distribution: DistributionMode = DistributionMode.LOADSCOPE,
        max_workers: int = 8,
        auto_detect: bool = True
    ):
        """
        初始化并行策略
        :param workers: 工作进程数，None 表示自动检测
        :param distribution: 分布模式
        :param max_workers: 最大工作进程数
        :param auto_detect: 是否自动检测最优进程数
        """
        self._workers = workers
        self._distribution = distribution
        self._max_workers = max_workers
        self._auto_detect = auto_detect
    
    @property
    def workers(self) -> int:
        """
        获取工作进程数
        :return: 工作进程数
        """
        if self._workers is not None:
            return min(self._workers, self._max_workers)
        
        if self._auto_detect:
            return self._detect_optimal_workers()
        
        return 1
    
    @property
    def distribution(self) -> str:
        """
        获取分布模式
        :return: 分布模式字符串
        """
        return self._distribution.value
    
    def _detect_optimal_workers(self) -> int:
        """
        自动检测最优工作进程数
        基于 CPU 核心数和系统负载
        :return: 最优工作进程数
        """
        global _log_printed
        
        cpu_count = multiprocessing.cpu_count()
        
        optimal_workers = max(1, cpu_count - 1)
        
        optimal_workers = min(optimal_workers, self._max_workers)
        
        if not _log_printed:
            logger.debug(f"自动检测并行进程数: CPU核心={cpu_count}, 最优进程数={optimal_workers}")
            _log_printed = True
        
        return optimal_workers
    
    def get_pytest_args(self) -> List[str]:
        """
        生成 pytest-xdist 参数
        :return: pytest 参数列表
        """
        args = []
        
        if self.workers > 1:
            args.append(f"-n={self.workers}")
            args.append(f"--dist={self.distribution}")
        elif self.workers == 1:
            args.append("-n=1")
        else:
            args.append("-n=auto")
            args.append(f"--dist={self.distribution}")
        
        return args
    
    def set_workers(self, workers: int) -> "ParallelStrategy":
        """
        设置工作进程数
        :param workers: 工作进程数
        :return: self
        """
        self._workers = workers
        return self
    
    def set_distribution(self, mode: DistributionMode) -> "ParallelStrategy":
        """
        设置分布模式
        :param mode: 分布模式
        :return: self
        """
        self._distribution = mode
        return self
    
    def set_max_workers(self, max_workers: int) -> "ParallelStrategy":
        """
        设置最大工作进程数
        :param max_workers: 最大工作进程数
        :return: self
        """
        self._max_workers = max_workers
        return self
    
    def disable_parallel(self) -> "ParallelStrategy":
        """
        禁用并行执行
        :return: self
        """
        self._workers = 1
        self._auto_detect = False
        return self
    
    def enable_parallel(self, workers: Optional[int] = None) -> "ParallelStrategy":
        """
        启用并行执行
        :param workers: 工作进程数，None 表示自动检测
        :return: self
        """
        self._workers = workers
        self._auto_detect = workers is None
        return self
    
    def __str__(self) -> str:
        return f"ParallelStrategy(workers={self.workers}, distribution={self.distribution})"
    
    def __repr__(self) -> str:
        return self.__str__()


def get_parallel_strategy_from_config(config: dict) -> ParallelStrategy:
    """
    从配置字典创建并行策略
    :param config: 配置字典
    :return: ParallelStrategy 实例
    """
    enabled = config.get("enabled", True)
    workers = config.get("workers", "auto")
    distribution = config.get("distribution", "loadscope")
    max_workers = config.get("max_workers", 8)
    
    if not enabled:
        strategy = ParallelStrategy(workers=1, auto_detect=False)
        strategy.disable_parallel()
        return strategy
    
    if workers == "auto":
        strategy = ParallelStrategy(
            workers=None,
            distribution=DistributionMode(distribution),
            max_workers=max_workers,
            auto_detect=True
        )
    else:
        strategy = ParallelStrategy(
            workers=int(workers),
            distribution=DistributionMode(distribution),
            max_workers=max_workers,
            auto_detect=False
        )
    
    return strategy


_default_strategy: Optional[ParallelStrategy] = None


def get_default_strategy() -> ParallelStrategy:
    """
    获取默认并行策略
    :return: ParallelStrategy 实例
    """
    global _default_strategy
    if _default_strategy is None:
        _default_strategy = ParallelStrategy()
    return _default_strategy


def set_default_strategy(strategy: ParallelStrategy) -> None:
    """
    设置默认并行策略
    :param strategy: ParallelStrategy 实例
    """
    global _default_strategy
    _default_strategy = strategy
