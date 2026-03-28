# -*- coding: utf-8 -*-
# @Author  : 会飞的🐟
# @File    : data_tools.py
# @Desc: 数据处理工具模块

import os
import base64
import random
from loguru import logger
from config.settings import FILES_DIR
from datetime import datetime, timedelta
from utils.tools.aes_encrypt_decrypt import Encrypt
from utils.files_utils.files_handle import file_to_base64, filepath_to_base64, get_files




def zip_test_step(step_id, step_status_id=None):
    """
    处理测试用例的步骤
    """
    if step_status_id:
        return [{'id': id, 'stepStatus': execResult} for id, execResult in zip(step_id, step_status_id)]
    else:
        random_list = [0, 1, 2, 3, 4]
        return [{'id': id, 'stepStatus': random.choice(random_list)} for id in step_id]


def get_file_content(file_name):
    """
    获取文件二进制内容
    :param file_name: 文件名称
    :return:
    """
    file_path = os.path.join(FILES_DIR, file_name)
    if os.path.exists(file_path):
        # 如果文件是一个真实存在的路径，则返回文件二进制内容
        return file_to_base64(file_path=file_path)
    else:
        # 若文件不存在，则尝试以文件扩展名随机选择一个文件
        logger.warning(f"图片不存在，将获取传入文件名后缀，随机取对应类型的文件， 路径：{file_path}")
        file_extension = os.path.splitext(file_name)[1]
        files = get_files(target=FILES_DIR, end=file_extension)
        if files:
            # 返回文件二进制内容
            return file_to_base64(file_path=random.choice(files))
        else:
            logger.warning(f"找不到该文件后缀对应的同类型文件，将返回空， 传入的文件名：{file_name}")
            return None


def list_to_str(target):
    """
    将列表中的元素转换为字符串，并用逗号分隔。
    :param target: 要转换为字符串的列表。
    :return: 以逗号分隔的字符串。
    """
    if isinstance(target, list) and target:
        # 过滤掉列表中的None值
        filtered_list = [str(item) for item in target if item is not None]
        # 使用逗号连接字符串
        return ",".join(filtered_list)
    elif isinstance(target, str) and target:
        return target
    else:
        return None


def string_to_base64(input_string: str):
    """
    将字符串转换为Base64格式
    """
    base64_bytes = base64.b64encode(input_string.encode('utf-8'))
    base64_string = base64_bytes.decode('utf-8')
    return base64_string


def str_to_list(target):
    """
    将字符串转换为列表，字符串中以逗号分隔的元素将转换为列表中的元素。
    """
    if isinstance(target, str):
        return [target]
    else:
        return target


def none_to_null(target):
    """
    将'None'转成空字符串
    """
    if target == 'None':
        return ""
    else:
        return target


def get_filepath_base64(file_name):
    """
    返回文件路径的base64编码
    """
    file_path = os.path.join(FILES_DIR, file_name)
    if os.path.exists(file_path):
        # 如果文件是一个真实存在的路径，则返回base64编码内容
        return filepath_to_base64(file_path=file_path)

    else:
        logger.warning(f"找不到该文件，将返回空， 传入的文件名：{file_name}")
        return None


def get_base64_content(input_string: str):
    """
    获取base64编码内容
    """
    byte_string = input_string.encode('utf-8')
    base64_bytes = base64.b64encode(byte_string)
    base64_string = base64_bytes.decode('utf-8')
    return base64_string


def base64_decode(encoded_string):
    try:
        decoded_bytes = base64.b64decode(encoded_string)
        decoded_string = decoded_bytes.decode('utf-8')
        return decoded_string
    except Exception as e:
        return f"Error decoding: {str(e)}"


def update_wiki_sidebar(sidebar_content, new_page_name):
    """
    获取wiki sideber的base64编码内容，将新页面追加到后面，再重新编码返回
    """
    _sidebar_content = base64_decode(sidebar_content)
    new_sidebar_content = _sidebar_content + f"\n[[{new_page_name}]]"
    return string_to_base64(new_sidebar_content)


def get_current_week(start_or_end="start"):
    """
    获取当前日期，并根据参数返回本周的开始或结束日期。

    参数:
    - start_or_end: 字符串，指定返回本周的开始日期（"start"）还是结束日期（"end"）。

    返回:
    - 本周开始或结束日期的字符串表示，格式为"月日"（例如："01月01日"）。
    """
    # 获取当前日期
    today = datetime.today()
    # 计算今天是本周的第几天（0代表周一，1代表周二，以此类推）
    current_weekday = today.weekday()

    if start_or_end == "start":
        # 计算本周的周一
        res = today - timedelta(days=current_weekday)
    elif start_or_end == "end":
        # 计算本周的周日
        res = today - timedelta(days=current_weekday) + timedelta(days=6)
    else:
        # 如果参数非法，返回当前日期的周一
        logger.error(f"Invalid value for start_or_end: {start_or_end}. Defaulting to 'start'.")
        res = today - timedelta(days=current_weekday)

    return res.strftime("%m月%d日")


def split_data(target: str, split_char: str, start_index: int, end_index: int = None):
    """
    切割数据，返回指定索引范围内的切割结果
    :param target: 要切割的字符串
    :param split_char: 切割的方式
    :param start_index: 切割结果的起始索引。假如end_index为空，则返回指定索引值
    :param end_index: 切割结果的结束索引（可选，默认为 None）
    :return: 指定索引范围内的切割结果
    """
    # 参数类型检查
    if not isinstance(target, str):
        raise ValueError("target must be a string")

    if start_index and end_index:
        return target.split(split_char)[start_index:end_index]
    else:
        return target.split(split_char)[start_index]


def aes_encrypt_data(target_str: str, ace_key):
    """
    使用AES-CBC对称加密算法对密码进行加密
    """
    ace = Encrypt(key=ace_key, iv=ace_key)
    return ace.aes_encrypt(target_str)
