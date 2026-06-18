# -*- coding: utf-8 -*-
# @Author  : 会飞的🐟
# @File    : files_handle.py
# @Desc: 文件处理模块
import os
import csv
import yaml
import json
import zipfile
import shutil
import base64
import re
from loguru import logger
from typing import Dict, Text, List




# --------------- YAML文件处理 -------------------------------------#
def load_yaml_file(yaml_file: Text) -> Dict:
    """load yaml file and check file content format"""
    with open(yaml_file, mode="r", encoding="utf-8") as stream:
        content = stream.read()
        
        # 替换环境变量 ${VAR}
        pattern = re.compile(r'\$\{(\w+)\}')
        def replace(match):
            env_var = match.group(1)
            return os.getenv(env_var, match.group(0))
            
        updated_content = pattern.sub(replace, content)
        
        try:
            yaml_content = yaml.load(updated_content, Loader=yaml.FullLoader)
        except yaml.YAMLError as ex:
            err_msg = f"YAMLError:\nfile: {yaml_file}\nerror: {ex}"
            logger.error(err_msg)
            raise yaml.YAMLError(err_msg) from ex

        return yaml_content


def write(yaml_file, data, mode="a") -> None:
    """
    往yaml文件中写入数据，默认是追加写入
    :param yaml_file: 要写入的文件路径
    :param data: 要写入的数据
    :param mode: 写入模式
    :return:
    """
    try:
        with open(yaml_file, mode=mode, encoding="utf-8") as f:
            yaml.dump(data, f)
    except yaml.YAMLError as e:
        logger.error(f"Error while writing to YAML file ({yaml_file}): {e}")
        raise e


# --------------- JSON文件处理 -------------------------------------#
def load_json_file(json_file: Text) -> Dict:
    """load json file and check file content format"""
    with open(json_file, mode="rb") as data_file:
        try:
            json_content = json.load(data_file)
        except json.JSONDecodeError as ex:
            err_msg = f"JSONDecodeError:\nfile: {json_file}\nerror: {ex}"
            logger.error(err_msg)
            raise json.JSONDecodeError(err_msg, ex.doc, ex.pos) from ex

        return json_content


# --------------- CSV文件处理 -------------------------------------#
def load_csv_file(csv_file: Text) -> List[Dict]:
    """load csv file and check file content format

    Args:
        csv_file (str): csv file path, csv file content is like below:

    Returns:
        list: list of parameters, each parameter is in dict format

    Examples:
        >>> cat csv_file
        username,password
        test1,111111
        test2,222222
        test3,333333

        >>> load_csv_file(csv_file)
        [
            {'username': 'test1', 'password': '111111'},
            {'username': 'test2', 'password': '222222'},
            {'username': 'test3', 'password': '333333'}
        ]

    """
    if not os.path.isabs(csv_file):
        global project_meta
        if project_meta is None:
            raise RuntimeError("load_project_meta() has not been called!")

        # make compatible with Windows/Linux
        csv_file = os.path.join(project_meta.RootDir, *csv_file.split("/"))

    if not os.path.isfile(csv_file):
        # file path not exist
        raise FileNotFoundError(f"CSV文件不存在: {csv_file}")

    csv_content_list = []

    with open(csv_file, encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            csv_content_list.append(row)

    return csv_content_list


# --------------- 其他文件处理方法 -------------------------------------#
def get_files(target, start=None, end=None):
    """
    @param: target: 目标文件绝对路径
    @param: start: 以什么开头，默认为空
    @param: end: 以什么结尾，默认为空
    获取目录下所有的文件，以列表的形式返回
    """
    if os.path.isfile(target):
        return []
    # files返回j经过处理的文件列表
    files = []
    # dirpath：表示获取的目录的路径，以string形式返回值。
    # dirnames： 包含了当前dirpath路径下所有的子目录名字（不包含目录路径），以列表形式返回值。
    # filenames：包含了当前dirpath路径下所有的非目录子文件的名字（不包含目录路径）。
    for dirpath, dirnames, filenames in os.walk(target):
        for filename in filenames:
            file_path = os.path.abspath(os.path.join(dirpath, filename))
            # 如果"start"和"end"都有值
            if start and end:
                # filename是以"start"且filename是以"end"结尾，则追加到files
                if filename.startswith(start) and filename.endswith(end):
                    files.append(file_path)
            # 或者如果"start"有值，filename是以"start"开头，则追加到files
            elif start and (not end):
                if filename.startswith(start):
                    files.append(file_path)
            # 或者如果"end"有值，且filename是以"end"结尾，则追加到files
            elif end and (not start):
                if filename.endswith(end):
                    files.append(file_path)
            else:
                files.append(file_path)
    # 判断files列表是否为空，不为空则返回files，为空则返回all_files
    return files


def get_newest_file(dir_path):
    """
    获取目录下最新的文件
    """
    if os.path.isfile(dir_path):
        return None

    # 获取目录下所有文件
    files = os.listdir(dir_path)

    # 按文件修改时间排序
    sorted_files = sorted(
        [(os.path.join(dir_path, file), os.path.getmtime(os.path.join(dir_path, file))) for file in files],
        key=lambda x: x[1],
        reverse=True
    )

    # 返回最新文件路径
    return sorted_files[0][0]


def zip_file(in_path: str, out_path: str):
    """
    压缩指定文件夹
    :param in_path: 目标文件夹路径
    :param out_path: 压缩文件保存路径+xxxx.zip
    :return: 无
    """
    # 如果传入的路径是一个目录才进行压缩操作
    if os.path.isdir(in_path):
        logger.trace(f"目标路径:{in_path} 是一个目录，开始进行压缩......")
        # 使用 with 语句确保文件句柄正确关闭
        with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for path, dirnames, filenames in os.walk(in_path):
                # 去掉目标跟路径，只对目标文件夹下边的文件及文件夹进行压缩
                fpath = path.replace(in_path, '')
                for filename in filenames:
                    zipf.write(
                        os.path.join(path, filename),
                        os.path.join(fpath, filename)
                    )
        logger.debug(f"目标路径:{in_path} 压缩完成！, 压缩文件路径：{out_path}")
    else:
        logger.error(f"目标路径:{in_path} 不是一个目录，请检查！")


def delete_dir_file(file_path):
    """
    删除指定目录下的所有文件
    :param file_path: 目标文件夹路径 (存在多级路径的暂不支持)
    """
    paths = os.listdir(file_path)
    if paths:
        logger.debug(f"目标目录: {file_path} 存在文件或目录，进行删除操作")
        for item in paths:
            path = os.path.join(file_path, item)
            # 如果目标路径是一个文件，使用os.remove删除
            if os.path.isfile(path):
                os.remove(path)
            # 如果目标路径是一个目录，使用os.rmdir删除
            if os.path.isdir(path):
                os.rmdir(path)
    else:
        logger.warning(f"目标目录: {file_path} 不存在文件或目录，不需要删除")


def copy_file(src_file_path, dest_dir_path):
    """
    复制一个文件到另一个目录
    :param: src_file_path: 源文件路径
    :param: dest_dir_path: 目标文件夹路径

    """
    # 判断源文件路径是否存在
    if not os.path.isfile(src_file_path):
        logger.error(f"源文件路径不存在：{src_file_path}")
        return "源文件路径不存在"

    # 判断目标文件夹路径是否存在，不存在则创建
    if not os.path.isdir(dest_dir_path):
        os.makedirs(dest_dir_path)

    # 复制文件
    try:
        shutil.copy(src_file_path, dest_dir_path)
        logger.debug(f"复制文件成功，源文件：{src_file_path}, 目标文件：{dest_dir_path}")
        return "复制成功"
    except Exception as e:
        logger.error(f"复制文件失败，源文件：{src_file_path}, 目标文件：{dest_dir_path}, 错误：{e}")
        return f"复制失败：{e}"


def get_file_field(file_path):
    """
    获取文件名称和二进制内容
    :param: file_path: 文件路径
    """
    # 处理文件绝对路径
    file_name = os.path.basename(file_path)
    # 获取文件二进制内容
    with open(file_path, 'rb') as f:
        file_content = f.read()
    return (file_name, file_content)


def get_relative_path(file_path, directory_path):
    """
    os.path.relpath()是Python中os.path模块提供的一个函数，用于计算两个路径之间的相对路径。
    例如：file_path=data/gitlink/project/test_login_demo.yaml， directory_path=data， 将返回/gitlink/project
    :param: file_path: 文件路径
    :param: directory_path: 相对于目录路径
    """
    # 获取file_path相对于directory_path的相对路径
    relative_path = os.path.relpath(os.path.abspath(file_path), os.path.abspath(directory_path))
    # 如果相对路径中包含文件名，则去除文件名部分并返回
    return os.path.dirname(relative_path)


def file_to_base64(file_path):
    """
    使用Python的标准库base64来读取文件内容并将其转换为base64编码
    """
    if os.path.exists(file_path):
        with open(file_path, "rb") as file:
            encoded_string = base64.b64encode(file.read())
            return encoded_string.decode('utf-8')
    else:
        logger.warning(f"{file_path} 不是一个真实有效的文件路径")


def filepath_to_base64(file_path):
    """
    使用Python的标准库base64来将文件路径并将其转换为base64编码
    """
    if os.path.exists(file_path):
        encoded_string = base64.b64encode(file_path.encode('utf-8'))
        return encoded_string.decode('utf-8')
    else:
        logger.warning(f"{file_path} 不是一个真实有效的文件路径")

def copy_all_files(src_dir, dst_dir):
    """
    将源目录中的所有文件和子目录复制到目标目录中。

    参数:
        src_dir (str): 源目录路径。
        dst_dir (str): 目标目录路径。
    """
    try:
        # 确保目标目录存在
        os.makedirs(dst_dir, exist_ok=True)

        # 遍历源目录中的所有文件和子目录
        for item in os.listdir(src_dir):
            src_item = os.path.join(src_dir, item)  # 源文件/目录的完整路径
            dst_item = os.path.join(dst_dir, item)  # 目标文件/目录的完整路径

            if os.path.isfile(src_item):
                # 如果是文件，直接复制
                shutil.copy2(src_item, dst_item)
                print(f"复制文件: {src_item} -> {dst_item}")
            elif os.path.isdir(src_item):
                # 如果是目录，递归复制
                shutil.copytree(src_item, dst_item, dirs_exist_ok=True)
                print(f"复制目录: {src_item} -> {dst_item}")
    except Exception as e:
        print(f"复制失败: {e}")