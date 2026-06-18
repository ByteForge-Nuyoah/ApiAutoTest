# -*- coding: utf-8 -*-
# @Author  : 会飞的🐟
# @File    : extract_data_handle.py
# @Desc: 数据提取处理模块，支持 JSONPath、正则表达式和 Response 对象属性提取

import re
from typing import Any, Union
from loguru import logger
from jsonpath import jsonpath
from requests import Response, cookies, utils

def json_extractor(obj: Union[dict, list], expr: str = '.') -> Any:
    """
    使用 JSONPath 从目标对象中提取数据。
    
    Args:
        obj (dict/list): 待提取的 JSON/字典/列表数据。
        expr (str): JSONPath 表达式。
                    示例: 
                    - '.' : 提取整个对象
                    - '$.data' : 提取 data 字段
                    - '$..id' : 递归提取所有 id 字段
    
    Returns:
        Any: 提取到的结果。
             - 如果提取到单个值，直接返回该值。
             - 如果提取到多个值，返回列表。
             - 如果未提取到，返回 None。
             - 如果发生异常，返回异常对象。
    """
    try:
        # jsonpath 返回 False 表示未找到，返回列表表示找到（即使只有一个元素）
        jp_res = jsonpath(obj, expr)
        
        if jp_res is False:
            logger.warning(f"Jsonpath提取失败！\n提取对象：{obj}\n提取表达式：{expr}")
            return None

        # 如果结果列表长度为1，直接返回元素本身；否则返回列表
        result = jp_res[0] if len(jp_res) == 1 else jp_res
        
        logger.trace(f"\n提取对象：{obj}\n"
                     f"提取表达式： {expr} \n"
                     f"提取值类型： {type(result)}\n"
                     f"提取结果：{result}\n")
        return result
    except Exception as e:
        logger.warning(f"\n提取对象：{obj}\n"
                     f"提取表达式： {expr}\n"
                     f"错误信息：{e}\n")
        return e


def re_extract(obj: str, expr: str = '.'):
    """
    使用正则表达式从字符串中提取数据。
    
    Args:
        obj (str): 待提取的目标字符串。
        expr (str): 正则表达式。
                    注意：建议使用分组 () 来精确提取需要的部分。
    
    Returns:
        str/list/None: 提取结果。
                       - 匹配到一个结果时，返回字符串。
                       - 匹配到多个结果时，返回列表。
                       - 未匹配到或异常时，返回 None 或 异常对象。
    """
    try:
        # 执行正则查找
        matches = re.findall(expr, obj)
        
        if not matches:
            logger.trace(f"正则未匹配到数据: expr={expr}, obj={obj[:100]}...")
            return None

        # 如果提取后的数据长度为1，则取第一个元素（返回str），否则返回列表
        result = matches[0] if len(matches) == 1 else matches
        
        logger.trace(f"\n提取对象：{obj}\n"
                     f"提取表达式： {expr}\n"
                     f"提取值类型： {type(result)}\n"
                     f"提取结果：{result}\n")
        return result
    except Exception as e:
        logger.trace(f"\n提取对象：{obj}\n"
                     f"提取表达式： {expr}\n"
                     f"错误信息：{e}\n")
        return e


def response_extract(response: Response, expr: str = '.') -> Any:
    """
    从 requests.Response 对象中提取属性值。
    使用 eval 动态执行表达式，支持提取 status_code, cookies, headers, text, json() 等。
    
    Args:
        response (Response): requests 响应对象。
        expr (str): 提取表达式字符串。
                    示例:
                    - 'response.status_code'
                    - 'response.headers["Content-Type"]'
                    - 'response.cookies'
                    - 'response.json()["code"]'
    
    Returns:
        Any: 提取到的属性值。
             - 特殊处理：如果是 CookieJar 对象，会自动转换为字典。
    """
    try:
        # ⚠️ 安全警告: eval 存在安全风险，仅在受信任的测试代码中使用
        # 这里直接执行字符串表达式来获取 response 的属性
        result = eval(expr)
        
        logger.trace(f"\n提取表达式： {expr}\n"
                     f"提取值类型： {type(result)}\n"
                     f"提取结果：{result}\n")
                     
        # 将从Response对象提取的cookiejar对象转换为dict格式， 避免后续使用cookies的时候出现类型错误
        if isinstance(result, cookies.RequestsCookieJar):
            result = utils.dict_from_cookiejar(result)
            
        return result
    except Exception as e:
        logger.trace(f"\n提取表达式： {expr}\n"
                     f"提取对象： {response}\n"
                     f"错误信息：{e}\n")
        return e


if __name__ == '__main__':
    # 测试代码
    obj = [{'id': 1, 'user_id': 102, 'action': 'autologin', 'value': '3734462a398eedd9ab7448c4e2880ddd3f9bb2cb'}]
    expre = "'user_id': (.*?),"

    res = re_extract(obj=str(obj), expr=expre)
    print(res)
