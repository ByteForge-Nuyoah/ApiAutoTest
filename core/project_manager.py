# -*- coding: utf-8 -*-
# @Author  : 会飞的🐟
# @File    : project_manager.py
# @Desc: 多项目管理模块

import os
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from loguru import logger
from dataclasses import dataclass, field, asdict
from enum import Enum


class ProjectStatus(Enum):
    """
    项目状态
    """
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


@dataclass
class ProjectConfig:
    """
    项目配置
    """
    name: str
    description: str = ""
    status: ProjectStatus = ProjectStatus.ACTIVE
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    case_file_type: int = 1
    env: str = "test"
    markers: List[str] = field(default_factory=list)
    report_config: Dict[str, Any] = field(default_factory=dict)
    custom_config: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典
        :return: 字典
        """
        data = asdict(self)
        data["status"] = self.status.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProjectConfig":
        """
        从字典创建
        :param data: 字典数据
        :return: ProjectConfig 实例
        """
        if "status" in data and isinstance(data["status"], str):
            data["status"] = ProjectStatus(data["status"])
        return cls(**data)


class ProjectManager:
    """
    项目管理器
    管理多个测试项目的配置和用例
    """
    
    def __init__(self, projects_dir: str, config_file: str = None):
        """
        初始化项目管理器
        :param projects_dir: 项目目录
        :param config_file: 配置文件路径
        """
        self._projects_dir = projects_dir
        self._config_file = config_file or os.path.join(projects_dir, "projects_config.json")
        self._projects: Dict[str, ProjectConfig] = {}
        self._load_config()
    
    def _load_config(self) -> None:
        """
        加载配置文件
        """
        if os.path.exists(self._config_file):
            try:
                with open(self._config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for name, config in data.get("projects", {}).items():
                        self._projects[name] = ProjectConfig.from_dict(config)
                logger.info(f"加载项目配置: {self._config_file}")
            except Exception as e:
                logger.error(f"加载项目配置失败: {e}")
    
    def _save_config(self) -> None:
        """
        保存配置文件
        """
        try:
            os.makedirs(os.path.dirname(self._config_file), exist_ok=True)
            data = {
                "projects": {name: config.to_dict() for name, config in self._projects.items()},
                "updated_at": datetime.now().isoformat()
            }
            with open(self._config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.debug(f"保存项目配置: {self._config_file}")
        except Exception as e:
            logger.error(f"保存项目配置失败: {e}")
    
    def create_project(
        self,
        name: str,
        description: str = "",
        case_file_type: int = 1,
        env: str = "test",
        markers: List[str] = None,
        **kwargs
    ) -> ProjectConfig:
        """
        创建项目
        :param name: 项目名称
        :param description: 项目描述
        :param case_file_type: 用例文件类型
        :param env: 默认环境
        :param markers: 标记列表
        :param kwargs: 其他配置
        :return: 项目配置
        """
        if name in self._projects:
            raise ValueError(f"项目已存在: {name}")
        
        project_dir = self.get_project_dir(name)
        if os.path.exists(project_dir):
            logger.warning(f"项目目录已存在: {project_dir}")
        
        config = ProjectConfig(
            name=name,
            description=description,
            case_file_type=case_file_type,
            env=env,
            markers=markers or [],
            **kwargs
        )
        
        self._projects[name] = config
        self._save_config()
        
        os.makedirs(project_dir, exist_ok=True)
        logger.info(f"创建项目: {name}")
        
        return config
    
    def get_project(self, name: str) -> Optional[ProjectConfig]:
        """
        获取项目配置
        :param name: 项目名称
        :return: 项目配置
        """
        return self._projects.get(name)
    
    def update_project(self, name: str, **kwargs) -> ProjectConfig:
        """
        更新项目配置
        :param name: 项目名称
        :param kwargs: 更新的配置
        :return: 更新后的配置
        """
        if name not in self._projects:
            raise ValueError(f"项目不存在: {name}")
        
        config = self._projects[name]
        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)
        
        config.updated_at = datetime.now().isoformat()
        self._save_config()
        
        logger.info(f"更新项目配置: {name}")
        return config
    
    def delete_project(self, name: str) -> bool:
        """
        删除项目
        :param name: 项目名称
        :return: 是否成功
        """
        if name not in self._projects:
            return False
        
        del self._projects[name]
        self._save_config()
        
        logger.info(f"删除项目: {name}")
        return True
    
    def list_projects(self, status: ProjectStatus = None) -> List[ProjectConfig]:
        """
        列出所有项目
        :param status: 过滤状态
        :return: 项目列表
        """
        projects = list(self._projects.values())
        if status:
            projects = [p for p in projects if p.status == status]
        return projects
    
    def list_project_names(self, status: ProjectStatus = None) -> List[str]:
        """
        列出所有项目名称
        :param status: 过滤状态
        :return: 项目名称列表
        """
        projects = self.list_projects(status)
        return [p.name for p in projects]
    
    def get_project_dir(self, name: str) -> str:
        """
        获取项目目录
        :param name: 项目名称
        :return: 项目目录路径
        """
        return os.path.join(self._projects_dir, name)
    
    def get_project_case_dir(self, name: str) -> str:
        """
        获取项目用例目录
        :param name: 项目名称
        :return: 用例目录路径
        """
        return os.path.join(self.get_project_dir(name), "cases")
    
    def scan_projects(self) -> List[str]:
        """
        扫描项目目录，发现新项目
        :return: 新发现的项目列表
        """
        if not os.path.exists(self._projects_dir):
            return []
        
        discovered = []
        for item in os.listdir(self._projects_dir):
            item_path = os.path.join(self._projects_dir, item)
            if os.path.isdir(item_path) and item not in self._projects:
                if item not in [".", "..", "__pycache__"]:
                    self.create_project(
                        name=item,
                        description=f"自动发现的项目: {item}"
                    )
                    discovered.append(item)
        
        if discovered:
            logger.info(f"发现新项目: {discovered}")
        
        return discovered
    
    def get_project_stats(self, name: str) -> Dict[str, Any]:
        """
        获取项目统计信息
        :param name: 项目名称
        :return: 统计信息
        """
        config = self.get_project(name)
        if not config:
            return {}
        
        project_dir = self.get_project_dir(name)
        stats = {
            "name": name,
            "status": config.status.value,
            "case_count": 0,
            "yaml_files": 0,
            "excel_files": 0,
            "last_updated": config.updated_at
        }
        
        if os.path.exists(project_dir):
            for root, dirs, files in os.walk(project_dir):
                for file in files:
                    if file.startswith("test_"):
                        if file.endswith((".yaml", ".yml")):
                            stats["yaml_files"] += 1
                        elif file.endswith((".xlsx", ".xls")):
                            stats["excel_files"] += 1
        
        stats["case_count"] = stats["yaml_files"] + stats["excel_files"]
        
        return stats


_project_manager: Optional[ProjectManager] = None


def get_project_manager(projects_dir: str = None, config_file: str = None) -> ProjectManager:
    """
    获取项目管理器单例
    :param projects_dir: 项目目录
    :param config_file: 配置文件路径
    :return: ProjectManager 实例
    """
    global _project_manager
    if _project_manager is None:
        if projects_dir is None:
            from config.settings import PROJECT_DIR
            projects_dir = PROJECT_DIR
        _project_manager = ProjectManager(projects_dir, config_file)
    return _project_manager
