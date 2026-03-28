# -*- coding: utf-8 -*-
# @Author  : 会飞的🐟
# @File    : assert_control.py
# @Desc: 断言控制模块，封装了断言逻辑的处理和执行

import types
import allure
from loguru import logger
from requests import Response
from core.models import AssertMethod
from core.assertion_utils import assert_function
from utils.database_utils.mysql_handle import MysqlServer
from core.data_utils.extract_data_handle import json_extractor, re_extract

class AssertUtils:
    """
    单次断言工具类
    负责解析单个断言配置，获取实际值与预期值，并调用对应的断言函数进行验证。
    """
    def __init__(self, assert_data, response: Response = None, db_info: dict = None):
        """
        初始化断言工具
        
        Args:
            assert_data (dict): 单个断言的配置数据。
                                示例: {'assert_type': 'equals', 'expect_value': 200, 'type_jsonpath': '$.code'}
            response (Response, optional): 接口响应对象，用于响应断言。
            db_info (dict, optional): 数据库配置信息，用于数据库断言。
        """
        self.assert_data = assert_data
        self.response = response
        if assert_data and db_info:
            self.db_connect = MysqlServer(**db_info)

    @property
    def get_message(self):
        """
        获取断言失败时的自定义描述信息。
        如果未配置 message 字段，则返回空字符串。
        """
        return self.assert_data.get("message", "")

    @property
    def get_assert_type(self):
        """
        获取断言类型（如 equals, contains 等）。
        会检查 assert_type 是否在 core.models.AssertMethod 枚举中定义。
        
        Returns:
            str: 断言类型的名称。
            
        Raises:
            AssertionError: 如果断言数据中缺少 assert_type 字段。
        """
        assert 'assert_type' in self.assert_data.keys(), (
                " 断言数据: '%s' 中缺少 `assert_type` 属性 " % self.assert_data
        )

        # 获取断言类型对应的枚举值名称
        name = AssertMethod(self.assert_data.get("assert_type")).name
        return name

    @property
    def get_sql_result(self):
        """
        执行SQL查询并获取结果（用于数据库断言）。
        
        Returns:
            list/dict: 数据库查询结果。
            
        Raises:
            ValueError: 如果缺少 sql 配置。
        """
        if "sql" not in self.assert_data.keys() or self.assert_data["sql"] is None:
            logger.error(f"断言数据: {self.assert_data} 缺少 'sql' 属性或 'sql' 为空")
            raise ValueError("断言数据: {self.assert_data} 缺少 'sql' 属性或 'sql' 为空")
        return self.db_connect.query_all(sql=self.assert_data["sql"])

    def get_actual_value_by_response(self):
        """
        从接口响应中获取实际值。
        优先级：JSONPath > 正则表达式 > 响应文本。
        
        Returns:
            Any: 从响应中提取的实际值。
        """
        # 1. 尝试使用 JSONPath 提取
        if "type_jsonpath" in self.assert_data and self.assert_data["type_jsonpath"]:
            return json_extractor(obj=self.response.json(), expr=self.assert_data["type_jsonpath"])
        
        # 2. 尝试使用正则表达式提取
        if "type_re" in self.assert_data and self.assert_data["type_re"]:
            return re_extract(obj=self.response.text, expr=self.assert_data["type_re"])
        
        # 3. 默认返回响应文本
        else:
            return self.response.text

    def get_actual_value_by_sql(self):
        """
        从数据库查询结果中获取实际值。
        
        Returns:
            Any: 从SQL结果中提取的实际值。
        """
        # 1. 尝试使用 JSONPath 从 SQL 结果中提取
        if "type_jsonpath" in self.assert_data and self.assert_data["type_jsonpath"]:
            return json_extractor(obj=self.get_sql_result, expr=self.assert_data["type_jsonpath"])
        
        # 2. 尝试使用正则表达式从 SQL 结果中提取
        elif "type_re" in self.assert_data and self.assert_data["type_re"]:
            return re_extract(obj=str(self.get_sql_result), expr=self.assert_data["type_re"])
        
        # 3. 默认返回整个 SQL 结果
        else:
            return self.get_sql_result

    @property
    def get_expect_value(self):
        """
        获取预期结果。
        
        Raises:
            AssertionError: 如果断言数据中缺少 expect_value 字段。
        """
        assert 'expect_value' in self.assert_data.keys(), (
            f"断言数据: {self.assert_data} 中缺少 `expect_value` 属性 "
        )
        return self.assert_data.get("expect_value")

    @property
    def assert_function_mapping(self):
        """
        动态获取断言函数映射表。
        扫描 core.assertion_utils.assert_function 模块中的所有函数。
        
        Returns:
            dict: {函数名: 函数对象} 的映射字典。
        """
        module_functions = {}
        # 遍历 assert_function 模块中的所有属性
        for name, item in vars(assert_function).items():
            if isinstance(item, types.FunctionType):
                module_functions[name] = item
        return module_functions

    def assert_handle(self):
        """
        执行单个断言的核心逻辑。
        1. 获取实际值（来自SQL或Response）。
        2. 获取预期值。
        3. 获取断言类型和描述。
        4. 调用对应的断言函数进行验证。
        5. 在 Allure 报告中记录步骤。
        """
        # 1. 获取实际值
        if "sql" in self.assert_data.keys():
            actual_value = self.get_actual_value_by_sql()
        else:
            actual_value = self.get_actual_value_by_response()

        # 2. 获取预期值及其他元数据
        expect_value = self.get_expect_value
        message = str(self.get_message)
        assert_type = self.get_assert_type
        
        logger.trace(f"\nmessage: {message}\n"
                     f"assert_type: {assert_type}\n"
                     f"expect_value: {expect_value}\n"
                     f"actual_value: {actual_value}\n")
                     
        # 构造默认的断言描述信息
        message = message or (f"断言 --> "
                              f"预期结果：{type(expect_value)} || {expect_value}"
                              f"实际结果：{type(actual_value)} || {actual_value}")
                              
        # 3. 执行断言并记录 Allure
        with allure.step(message):
            # 动态调用对应的断言函数
            if assert_type in self.assert_function_mapping:
                self.assert_function_mapping[assert_type](
                    expect_value=expect_value, 
                    actual_value=actual_value,
                    message=message
                )
            else:
                logger.error(f"不支持的断言类型: {assert_type}")
                raise ValueError(f"不支持的断言类型: {assert_type}")


class AssertHandle(AssertUtils):
    """
    批量断言处理类
    负责处理整个用例的断言配置（可能包含多个断言项）。
    """
    
    def get_assert_data_list(self):
        """
        解析断言配置，将其转换为断言数据列表。
        特殊处理 status_code 断言，直接在此处执行，不放入列表。
        
        Returns:
            list: 待执行的普通断言数据列表。
        """
        assert_list = []
        if self.assert_data and isinstance(self.assert_data, dict):
            for k, v in self.assert_data.items():
                # 特殊处理：如果键是 status_code，直接断言响应状态码
                if k.lower() == "status_code":
                    with allure.step("断言 --> 响应状态码"):
                        assert_function.equals(expect_value=v, actual_value=self.response.status_code)
                else:
                    # 其他断言加入列表后续处理
                    assert_list.append(v)
        else:
            logger.trace(f"断言数据为空或者不是字典格式，跳过断言！\n"
                         f"断言数据：{self.assert_data}")
        return assert_list

    def assert_handle(self):
        """
        遍历执行所有断言。
        """
        # 遍历所有断言项（status_code 已在 get_assert_data_list 中处理）
        for value in self.get_assert_data_list():
            # 更新当前处理的断言数据
            self.assert_data = value
            # 调用父类的单次断言逻辑
            super().assert_handle()
