# -*- coding: utf-8 -*-
# @Author  : 会飞的🐟
# @File    : data_cleanup.py
# @Desc: 数据清理模块 - 保证测试隔离（支持参数化查询，防止SQL注入）

import json
from typing import Dict, List, Optional, Any
from loguru import logger
from utils.database_utils.mysql_handle import MysqlServer


class DataCleanupManager:
    """
    数据清理管理器
    用于测试前后的数据准备和清理，保证测试环境隔离
    所有数据库操作均使用参数化查询，防止SQL注入
    """

    def __init__(self):
        self._db_connections: Dict[str, MysqlServer] = {}
        self._cleanup_registry: Dict[str, List[Dict]] = {}
        self._snapshot_data: Dict[str, Any] = {}

    def register_db(self, name: str, db_config: Dict) -> None:
        """
        注册数据库连接
        :param name: 数据库连接名称
        :param db_config: 数据库配置
        """
        try:
            self._db_connections[name] = MysqlServer(
                db_host=db_config.get("host"),
                db_port=db_config.get("port", 3306),
                db_user=db_config.get("user"),
                db_pwd=db_config.get("password"),
                db_database=db_config.get("database"),
                ssh=db_config.get("ssh", False),
                **db_config.get("ssh_config", {})
            )
            logger.info(f"数据库连接注册成功: {name}")
        except Exception as e:
            logger.error(f"数据库连接注册失败: {name}, 错误: {e}")
            raise e

    def get_db(self, name: str) -> Optional[MysqlServer]:
        """
        获取数据库连接
        :param name: 数据库连接名称
        :return: MysqlServer 实例
        """
        return self._db_connections.get(name)

    def register_cleanup(self, test_id: str, table: str, conditions: Dict[str, Any], db_name: str = "default") -> None:
        """
        注册清理任务（使用安全的参数化查询）
        :param test_id: 测试用例ID
        :param table: 表名
        :param conditions: 删除条件字典
        :param db_name: 数据库连接名称
        """
        if test_id not in self._cleanup_registry:
            self._cleanup_registry[test_id] = []

        self._cleanup_registry[test_id].append({
            "db_name": db_name,
            "table": table,
            "conditions": conditions
        })
        logger.debug(f"注册清理任务: {test_id} -> {table}")

    def execute_cleanup(self, test_id: str) -> bool:
        """
        执行指定测试用例的清理任务（使用安全的参数化删除）
        :param test_id: 测试用例ID
        :return: 是否执行成功
        """
        cleanup_tasks = self._cleanup_registry.get(test_id, [])
        if not cleanup_tasks:
            logger.debug(f"未找到清理任务: {test_id}")
            return True

        success = True
        for task in cleanup_tasks:
            db_name = task.get("db_name", "default")
            table = task.get("table")
            conditions = task.get("conditions", {})

            db = self.get_db(db_name)
            if not db:
                logger.error(f"数据库连接不存在: {db_name}")
                success = False
                continue

            try:
                # 使用安全的删除方法
                db.safe_delete(table, conditions)
                logger.info(f"清理任务执行成功: {table}")
            except Exception as e:
                logger.error(f"清理任务执行失败: {table}, 错误: {e}")
                success = False

        return success

    def cleanup_all(self) -> bool:
        """
        执行所有注册的清理任务
        :return: 是否全部执行成功
        """
        all_success = True
        for test_id in self._cleanup_registry:
            if not self.execute_cleanup(test_id):
                all_success = False

        self._cleanup_registry.clear()
        return all_success

    def snapshot_table(self, db_name: str, table: str, conditions: Dict[str, Any] = None) -> List[Dict]:
        """
        创建表数据快照（使用安全的参数化查询）
        :param db_name: 数据库连接名称
        :param table: 表名
        :param conditions: 查询条件字典（可选）
        :return: 快照数据
        """
        db = self.get_db(db_name)
        if not db:
            logger.error(f"数据库连接不存在: {db_name}")
            return []

        try:
            # 使用安全的条件查询
            data = db.select_by_conditions(table, conditions or {}, one=False)
            snapshot_key = f"{db_name}.{table}"
            self._snapshot_data[snapshot_key] = data
            logger.info(f"快照创建成功: {snapshot_key}, 记录数: {len(data)}")
            return data
        except Exception as e:
            logger.error(f"快照创建失败: {snapshot_key}, 错误: {e}")
            return []

    def restore_table(self, db_name: str, table: str, key_field: str = "id") -> bool:
        """
        从快照恢复表数据（使用安全的参数化更新）
        :param db_name: 数据库连接名称
        :param table: 表名
        :param key_field: 主键字段名
        :return: 是否恢复成功
        """
        snapshot_key = f"{db_name}.{table}"
        data = self._snapshot_data.get(snapshot_key, [])

        if not data:
            logger.warning(f"未找到快照数据: {snapshot_key}")
            return False

        db = self.get_db(db_name)
        if not db:
            logger.error(f"数据库连接不存在: {db_name}")
            return False

        try:
            for record in data:
                key_value = record.get(key_field)
                update_data = {k: v for k, v in record.items() if k != key_field}
                conditions = {key_field: key_value}

                # 使用安全的更新方法
                db.safe_update(table, update_data, conditions)

            logger.info(f"快照恢复成功: {snapshot_key}")
            return True
        except Exception as e:
            logger.error(f"快照恢复失败: {snapshot_key}, 错误: {e}")
            return False

    def delete_by_condition(self, db_name: str, table: str, conditions: Dict[str, Any]) -> bool:
        """
        按条件删除数据（使用安全的参数化删除）
        :param db_name: 数据库连接名称
        :param table: 表名
        :param conditions: 删除条件字典
        :return: 是否删除成功
        """
        db = self.get_db(db_name)
        if not db:
            logger.error(f"数据库连接不存在: {db_name}")
            return False

        try:
            db.safe_delete(table, conditions)
            logger.info(f"数据删除成功: {table}")
            return True
        except Exception as e:
            logger.error(f"数据删除失败: {table}, 错误: {e}")
            return False

    def truncate_table(self, db_name: str, table: str) -> bool:
        """
        清空表数据（慎用）
        注意：TRUNCATE操作无法参数化，但表名会进行验证
        :param db_name: 数据库连接名称
        :param table: 表名
        :return: 是否清空成功
        """
        db = self.get_db(db_name)
        if not db:
            logger.error(f"数据库连接不存在: {db_name}")
            return False

        try:
            # 使用标识符验证方法
            safe_table = db._sanitize_identifier(table)
            sql = f"TRUNCATE TABLE {safe_table}"
            db.update(sql)
            logger.warning(f"表已清空: {table}")
            return True
        except Exception as e:
            logger.error(f"表清空失败: {table}, 错误: {e}")
            return False

    def insert_test_data(self, db_name: str, table: str, data: List[Dict]) -> bool:
        """
        插入测试数据（使用安全的参数化插入）
        :param db_name: 数据库连接名称
        :param table: 表名
        :param data: 要插入的数据列表
        :return: 是否插入成功
        """
        db = self.get_db(db_name)
        if not db:
            logger.error(f"数据库连接不存在: {db_name}")
            return False

        if not data:
            logger.warning("没有数据需要插入")
            return True

        try:
            for record in data:
                # 使用安全的插入方法
                db.safe_insert(table, record)

            logger.info(f"测试数据插入成功: {table}, 记录数: {len(data)}")
            return True
        except Exception as e:
            logger.error(f"测试数据插入失败: {table}, 错误: {e}")
            return False

    def close_all(self) -> None:
        """
        关闭所有数据库连接
        """
        for name, db in self._db_connections.items():
            try:
                del db
                logger.debug(f"数据库连接已关闭: {name}")
            except Exception as e:
                logger.error(f"关闭数据库连接失败: {name}, 错误: {e}")

        self._db_connections.clear()
        self._cleanup_registry.clear()
        self._snapshot_data.clear()


_data_cleanup_manager: Optional[DataCleanupManager] = None


def get_cleanup_manager() -> DataCleanupManager:
    """
    获取数据清理管理器单例
    :return: DataCleanupManager 实例
    """
    global _data_cleanup_manager
    if _data_cleanup_manager is None:
        _data_cleanup_manager = DataCleanupManager()
    return _data_cleanup_manager
