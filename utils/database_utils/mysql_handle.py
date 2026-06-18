# -*- coding: utf-8 -*-
# @Author  : 会飞的🐟
# @File    : mysql_handle.py
# @Desc: MySQL数据库操作封装（支持参数化查询，防止SQL注入）

import json
import pymysql
from typing import Union, Optional, List, Dict, Any
from loguru import logger
from datetime import datetime
from sshtunnel import SSHTunnelForwarder

class MysqlServer:
    """
    初始化数据库连接(支持通过SSH隧道的方式连接)，并指定查询的结果集以字典形式返回
    支持参数化查询，防止SQL注入攻击
    """
    def __init__(self, db_host, db_port, db_user, db_pwd, db_database, ssh=False,
                 **kwargs):
        """
        初始化方法中， 连接mysql数据库， 根据ssh参数决定是否走SSH隧道方式连接mysql数据库
        """
        logger.debug("\n======================================================\n" \
                     "-------------数据库配置信息--------------------\n"
                     f"db_host: {db_host}\n" \
                     f"db_port: {db_port}\n" \
                     f"db_user: {db_user}\n" \
                     f"db_pwd: {'******'}\n" \
                     f"db_database: {db_database}\n" \
                     f"ssh: {ssh}\n" \
                     f"kwargs: {kwargs}\n" \
                     "=====================================================")
        self.server = None
        try:
            if ssh:
                self.server = SSHTunnelForwarder(
                    ssh_address_or_host=(kwargs.get("ssh_host"), int(kwargs.get("ssh_port"))),  # ssh 目标服务器 ip 和 port
                    ssh_username=kwargs.get("ssh_user"),  # ssh 目标服务器用户名
                    ssh_password=kwargs.get("ssh_pwd"),  # ssh 目标服务器用户密码
                    remote_bind_address=(db_host, db_port),  # mysql 服务ip 和 part
                    local_bind_address=('127.0.0.1', 5143),  # ssh 目标服务器的用于连接 mysql 或 redis 的端口，该 ip 必须为 127.0.0.1
                )
                self.server.start()
                db_host = self.server.local_bind_host  # server.local_bind_host 是 参数 local_bind_address 的 ip
                db_port = self.server.local_bind_port  # server.local_bind_port 是 参数 local_bind_address 的 port
            # 建立连接
            self.conn = pymysql.connect(host=db_host,
                                        port=db_port,
                                        user=db_user,
                                        password=db_pwd,
                                        database=db_database,
                                        charset="utf8",
                                        cursorclass=pymysql.cursors.DictCursor  # 加上pymysql.cursors.DictCursor这个返回的就是字典
                                        )
            # 创建一个游标对象
            self.cursor = self.conn.cursor()
        except Exception as e:
            logger.error(f"数据库连接失败：{e}")

    def __del__(self):
        """
        在对象销毁前，断开游标，关闭数据库连接
        """
        try:
            # 关闭游标
            self.cursor.close()
            # 关闭数据库链接
            self.conn.close()
            # 如果开启了SSH隧道，则关闭
            if self.server:
                self.server.close()
        except AttributeError as error:
            logger.error("数据库连接失败，失败原因 %s", error)

    def _sanitize_identifier(self, identifier: str) -> str:
        """
        清理并验证SQL标识符（表名、字段名等）
        只允许字母、数字、下划线，防止SQL注入

        :param identifier: 要清理的标识符
        :return: 清理后的安全标识符
        :raises: ValueError 如果标识符包含非法字符
        """
        import re
        # 只允许字母、数字、下划线
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', identifier):
            raise ValueError(f"非法的SQL标识符: {identifier}")
        return identifier

    def _build_safe_where_clause(self, conditions: Dict[str, Any]) -> tuple:
        """
        构建安全的WHERE子句（参数化）

        :param conditions: 条件字典 {字段名: 值}
        :return: (where子句字符串, 参数列表)
        """
        if not conditions:
            return "", []

        where_parts = []
        params = []
        for key, value in conditions.items():
            safe_key = self._sanitize_identifier(key)
            where_parts.append(f"{safe_key} = %s")
            params.append(value)

        return " AND ".join(where_parts), params

    def query_all(self, sql: str, params: Optional[tuple] = None):
        """
        查询所有符合sql条件的数据（支持参数化查询）

        :param sql: 执行的sql（可包含%s占位符）
        :param params: 参数元组，用于参数化查询
        :return: 查询结果
        """
        try:
            self.conn.commit()
            self.cursor.execute(sql, params)
            data = self.cursor.fetchall()
            logger.debug("\n======================================================\n" \
                         "-------------数据库执行结果--------------------\n"
                         f"SQL: {sql}\n" \
                         f"Params: {params}\n" \
                         f"result: {data}\n" \
                         "=====================================================")
            return data
        except Exception as e:
            logger.error(f"{sql} --> 报错: {e}")
            raise e

    def query_one(self, sql: str, params: Optional[tuple] = None):
        """
        查询符合sql条件的数据的第一条数据（支持参数化查询）

        :param sql: 执行的sql（可包含%s占位符）
        :param params: 参数元组，用于参数化查询
        :return: 返回查询结果的第一条数据
        """
        try:
            self.conn.commit()
            self.cursor.execute(sql, params)
            data = self.cursor.fetchone()
            logger.debug("\n======================================================\n" \
                         "-------------数据库执行结果--------------------\n"
                         f"SQL: {sql}\n" \
                         f"Params: {params}\n" \
                         f"result: {data}\n" \
                         "=====================================================")
            return data
        except Exception as e:
            logger.error(f"{sql} --> 报错: {e}")
            raise e

    def insert(self, sql: str, params: Optional[tuple] = None):
        """
        插入数据（支持参数化查询）

        :param sql: 执行的sql（可包含%s占位符）
        :param params: 参数元组，用于参数化查询
        """
        try:
            self.cursor.execute(sql, params)
            # 提交  只要数据库更新就要commit
            self.conn.commit()
            logger.debug("\n======================================================\n" \
                         "-------------数据库执行结果--------------------\n"
                         f"SQL: {sql}\n" \
                         f"Params: {params}\n" \
                         "插入数据成功！\n" \
                         "=====================================================")
        except Exception as e:
            logger.error(f"{sql} --> 报错: {e}")
            raise e

    def update(self, sql: str, params: Optional[tuple] = None):
        """
        更新数据（支持参数化查询）

        :param sql: 执行的sql（可包含%s占位符）
        :param params: 参数元组，用于参数化查询
        """
        try:
            self.cursor.execute(sql, params)
            # 提交 只要数据库更新就要commit
            self.conn.commit()
            logger.debug("\n======================================================\n" \
                         "-------------数据库执行结果--------------------\n"
                         f"SQL: {sql}\n" \
                         f"Params: {params}\n" \
                         "更新数据成功！\n" \
                         "=====================================================")
        except Exception as e:
            logger.error(f"{sql} --> 报错: {e}")
            raise e

    def delete(self, sql: str, params: Optional[tuple] = None):
        """
        删除数据（支持参数化查询）

        :param sql: 执行的sql（可包含%s占位符）
        :param params: 参数元组，用于参数化查询
        """
        try:
            self.cursor.execute(sql, params)
            self.conn.commit()
            logger.debug("\n======================================================\n" \
                         "-------------数据库执行结果--------------------\n"
                         f"SQL: {sql}\n" \
                         f"Params: {params}\n" \
                         "删除数据成功！\n" \
                         "=====================================================")
        except Exception as e:
            logger.error(f"{sql} --> 报错: {e}")
            raise e

    def query(self, sql: str, one: bool = True, params: Optional[tuple] = None):
        """
        根据传值决定查询一条数据还是所有（支持参数化查询）

        :param sql: 查询的SQL语句
        :param one: 默认True. True查一条数据，否则查所有
        :param params: 参数元组，用于参数化查询
        :return:
        """
        try:
            if one:
                return self.query_one(sql, params)
            else:
                return self.query_all(sql, params)
        except Exception as e:
            logger.error(f"{sql} --> 报错: {e}")
            raise e

    def select_by_conditions(self, table: str, conditions: Dict[str, Any],
                             fields: str = "*", one: bool = False) -> Union[List[Dict], Dict]:
        """
        安全的条件查询（参数化，防SQL注入）

        :param table: 表名
        :param conditions: 查询条件字典
        :param fields: 查询字段，默认 *
        :param one: 是否只返回一条
        :return: 查询结果
        """
        safe_table = self._sanitize_identifier(table)
        where_clause, params = self._build_safe_where_clause(conditions)

        sql = f"SELECT {fields} FROM {safe_table}"
        if where_clause:
            sql += f" WHERE {where_clause}"

        if one:
            return self.query_one(sql, tuple(params) if params else None)
        else:
            return self.query_all(sql, tuple(params) if params else None)

    def safe_insert(self, table: str, data: Dict[str, Any]) -> int:
        """
        安全插入数据（参数化，防SQL注入）

        :param table: 表名
        :param data: 要插入的数据字典
        :return: 影响的行数
        """
        safe_table = self._sanitize_identifier(table)
        fields = []
        placeholders = []
        params = []

        for key, value in data.items():
            fields.append(self._sanitize_identifier(key))
            placeholders.append("%s")
            params.append(value)

        sql = f"INSERT INTO {safe_table} ({', '.join(fields)}) VALUES ({', '.join(placeholders)})"
        self.insert(sql, tuple(params))
        return self.cursor.rowcount

    def safe_update(self, table: str, data: Dict[str, Any], conditions: Dict[str, Any]) -> int:
        """
        安全更新数据（参数化，防SQL注入）

        :param table: 表名
        :param data: 要更新的数据字典
        :param conditions: 更新条件
        :return: 影响的行数
        """
        safe_table = self._sanitize_identifier(table)
        set_parts = []
        params = []

        for key, value in data.items():
            set_parts.append(f"{self._sanitize_identifier(key)} = %s")
            params.append(value)

        where_clause, where_params = self._build_safe_where_clause(conditions)
        params.extend(where_params)

        sql = f"UPDATE {safe_table} SET {', '.join(set_parts)}"
        if where_clause:
            sql += f" WHERE {where_clause}"

        self.update(sql, tuple(params))
        return self.cursor.rowcount

    def safe_delete(self, table: str, conditions: Dict[str, Any]) -> int:
        """
        安全删除数据（参数化，防SQL注入）

        :param table: 表名
        :param conditions: 删除条件
        :return: 影响的行数
        """
        safe_table = self._sanitize_identifier(table)
        where_clause, params = self._build_safe_where_clause(conditions)

        if not where_clause:
            raise ValueError("删除操作必须指定条件，防止误删全表数据")

        sql = f"DELETE FROM {safe_table} WHERE {where_clause}"
        self.delete(sql, tuple(params))
        return self.cursor.rowcount

    def verify(self, result: dict) -> Union[dict, None]:
        """验证结果能否被json.dumps序列化"""
        # 尝试变成字符串，解决datetime 无法被json 序列化问题
        try:
            json.dumps(result)
        except TypeError:  # TypeError: Object of type datetime is not JSON serializable
            for k, v in result.items():
                if isinstance(v, datetime):
                    result[k] = str(v)
        return result
