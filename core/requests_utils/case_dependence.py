# -*- coding: utf-8 -*-
# @Author  : 会飞的🐟
# @File    : case_dependence.py
# @Desc: 用例依赖处理模块

import allure
from typing import Dict, List, Union, Any, Optional
from loguru import logger
from config.settings import INTERFACE_DIR
from core.data_utils.data_handle import data_handle
from core.report_utils.allure_handle import allure_step
from utils.database_utils.mysql_handle import MysqlServer
from core.requests_utils.request_control import RequestControl
from core.data_utils.extract_data_handle import json_extractor, re_extract

class CaseDependenceHandler:
    """
    处理用例依赖，支持接口依赖，环境变量依赖，数据库查询依赖。关键字：variables, interface, database,
    先处理环境变量依赖，再处理接口依赖，最后处理数据库查询依赖
    """

    def __init__(self, source: Dict[str, Any]) -> None:
        self.source = source

    def handle_variables(self, variables: Dict[str, Any]) -> None:
        """
        处理环境变量依赖

        Args:
            variables (dict): 环境变量字典，例如: {"key": "value", "key2": "${var}"}
                              支持引用已有的全局变量。
        """
        for key, value in variables.items():
            new_value = data_handle(value, self.source)
            allure_step(f"依赖环境变量 --> {key}={new_value}")
            logger.trace(f"依赖环境变量 --> {key}={new_value}")
            self.source.update({key: new_value})

    def handle_interfaces(self, interfaces: Union[str, List[str]]) -> None:
        """
        处理接口依赖

        Args:
            interfaces (str or list): 依赖的接口ID或接口ID列表。
                                      例如: "login_01" 或 ["login_01", "init_data_01"]
                                      依赖接口执行后提取的变量将更新到当前全局变量池中。
        """
        request_control = RequestControl()
        for interface in (interfaces if isinstance(interfaces, list) else [interfaces]):
            api_data = request_control.get_api_data(api_file_path=INTERFACE_DIR, key=interface)
            with allure.step(f"依赖接口：{api_data['title']}({interface})"):
                result = request_control.api_request_flow(request_data=api_data, global_var=self.source)
                self.source.update(result)

    def handle_database_dependence(self, database_dependence: Union[Dict[str, Any], List[Dict[str, Any]]], db_info: Dict[str, Any]) -> None:
        """
        处理数据库依赖

        Args:
            database_dependence (dict or list): 数据库依赖配置。
                格式示例:
                {
                    "sql": "SELECT * FROM users WHERE id=1",
                    "type_jsonpath": {"username": "$.username"}
                }
            db_info (dict): 数据库连接配置信息。
        """
        if not db_info:
            logger.warning("数据库配置信息为空，请正确更新数据库信息以连接数据库")
            return
        mysql = MysqlServer(**db_info)
        for db_item in (database_dependence if isinstance(database_dependence, list) else [database_dependence]):
            if db_item.get("sql"):
                sql = db_item["sql"]
                sql_result = mysql.query_all(sql)
                allure_step(f"依赖的数据库sql:{sql}, 查询结果：{sql_result}")
                logger.trace(f"依赖的数据库sql:{sql}, 查询结果：{sql_result}")
                db_item.pop("sql")

                for extraction_type, extractions in db_item.items():
                    if extraction_type.lower() == "type_jsonpath":
                        for key, path in extractions.items():
                            res = json_extractor(sql_result, path)
                            self.source.update({key: res})
                            allure_step(f"通过jsonpath方式从数据库提取参数：{key}:{res}")
                            logger.trace(f"通过jsonpath方式从数据库提取参数：{key}:{res}")
                    elif extraction_type.lower() == "type_re":
                        for key, pattern in extractions.items():
                            res = re_extract(str(sql_result), pattern)
                            self.source.update({key: res})
                            allure_step(f"通过正则表达式从数据库提取参数：{key}:{res}")
                            logger.trace(f"通过正则表达式从数据库提取参数：{key}:{res}")
                    else:
                        logger.error(f"提取方式： {extraction_type} 错误，仅支持type_jsonpath、type_re两种")
            else:
                logger.warning("数据库依赖参数必须传入sql")

    def case_dependence_handle(self, case_dependence: Dict[str, Any], db_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        处理用例依赖，支持接口依赖，环境变量依赖，SQL依赖。关键字：variables, interface, database,
        先处理环境变量依赖，再处理接口依赖，最后处理SQL依赖
        """
        if not case_dependence:
            logger.trace("跳过用例依赖处理")
            allure_step("跳过用例依赖处理")
            return self.source

        if case_dependence.get("variables"):
            if isinstance(case_dependence["variables"], dict):
                self.handle_variables(case_dependence["variables"])
            else:
                logger.warning("依赖环境变量格式错误，跳过依赖环境变量处理~ --> variables仅支持dict格式")

        if case_dependence.get("interface"):
            interfaces = case_dependence["interface"]
            if isinstance(interfaces, (str, list)):
                self.handle_interfaces(interfaces)
            else:
                logger.warning("依赖接口格式错误，跳过依赖接口处理~ --> interface 仅支持str和list格式")
        if case_dependence.get("database"):
            if db_info:
                database_dependence = case_dependence["database"]
                if isinstance(database_dependence, (dict, list)):
                    self.handle_database_dependence(database_dependence, db_info)
                else:
                    logger.warning("依赖数据库格式错误，跳过依赖数据库处理~ --> database 仅支持dict和list格式")
            else:
                logger.warning("数据库依赖参数未传入db_info，跳过依赖数据库处理~")
        else:
            logger.trace("不存在关键字database，跳过依赖数据库处理~")
        return self.source
