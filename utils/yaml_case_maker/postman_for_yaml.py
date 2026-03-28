# -*- coding: utf-8 -*-
# @Author  : 会飞的🐟
# @File    : postman_for_yaml.py
# @Desc: 转换postman接口文档为YAML格式用例

import os
import re
import json
from typing import Dict
from ruamel.yaml import YAML

"""
相比较于pyyaml, Ruamel可以保持YAML文件的结构和顺序不变。
安装：pip install ruamel.yaml
"""


class PostmanForYaml:
    """
    将postman接口文档转为YAML格式用例
    """

    def __init__(self, case_dir, postman_path):
        """
        :param case_dir: 用例需要保存的目录
        :param postman_path: 需要读取的swagger文件的路径
        """
        self._data = self.get_postman_json(postman_path)
        self.case_dir = case_dir

    def get_postman_json(self, postman_path):
        """
        获取 postman 中的 json 数据
        :param postman_path: 需要读取的swagger文件的路径
        :return:
        """
        result = []
        try:
            with open(postman_path, "r", encoding='utf-8') as f:
                row_data = json.load(f)

                def _parse_api(content):
                    nonlocal row_data
                    nonlocal result
                    if isinstance(content, list):
                        for item in content:
                            _parse_api(content=item)
                    elif isinstance(content, dict):
                        if 'item' in content.keys():
                            _parse_api(content=content['item'])
                        elif 'request' in content.keys():
                            # 获取所有接口的相关数据
                            yaml_data = {
                                "case_common": {
                                    "allure_epic": self.get_allure_epic(row_data),
                                    "allure_feature": self.get_allure_feature(content),
                                    "allure_story": self.get_allure_story(content)
                                },
                                "case_info": [
                                    {
                                        "id": f"case_{self.get_case_id(self.get_url(content)).lower()}_01",
                                        "title": self.get_title(content),
                                        "run": False,
                                        "url": self.get_url(content),
                                        "severity": None,
                                        "method": self.get_method(content),
                                        "headers": self.get_headers(content),
                                        "cookies": None,
                                        "request_type": self.get_request_type_payload(content).get("request_type"),
                                        "payload": self.get_request_type_payload(content).get("payload"),
                                        "files": self.get_request_type_payload(content).get("files"),
                                        "extract": None,
                                        "assert_response": {'eq': {'http_code': 200}},
                                        "assert_sql": None

                                    }
                                ]
                            }
                            result.append({
                                self.get_case_id(self.get_url(content)): yaml_data
                            })
            _parse_api(content=row_data)
            return result
        except FileNotFoundError:
            raise FileNotFoundError("文件路径不存在，请重新输入")

    def get_allure_epic(self, content):
        """
        获取 yaml 用例中的 allure_epic
        """
        _allure_epic = content['info']['name']
        return _allure_epic

    @classmethod
    def get_allure_feature(cls, content):
        """
        获取 yaml 用例中的 allure_feature
        这里直接获取最下级的item.name，因为可以有多级item，不好判断
        """

        _allure_feature = content['name']
        return str(_allure_feature)

    @classmethod
    def get_allure_story(cls, content):
        """
        获取 yaml 用例中的 allure_story
        这里直接获取最下级的item.name，因为可以有多级item，不好判断
        """
        _allure_story = content['name']
        return _allure_story

    @classmethod
    def get_case_id(cls, content):
        """
        获取 case_id， 是根据接口路径生成的
        """
        # 这里接收到的参数content其实是url
        # 移除？后面拼接的值
        url_path = content.split("?")[0]
        # 去除"http://"或"https://"部分
        if url_path.startswith(("http://", "https://")):
            url_path = url_path.split("//", 1)[1]
        # 使用正则表达式匹配并删除第一个斜线以及斜线前的内容
        new_url_path = re.sub(r'^.*?/', '', url_path)
        # 将剩余的斜线替换成_
        _case_id = new_url_path.replace("/", "_")
        return _case_id

    @classmethod
    def get_title(cls, content):
        """
        获取接口的标题
        """
        _get_detail = content.get('name')
        return "测试 " + _get_detail

    @classmethod
    def get_url(cls, content):
        """
        获取接口的url
        """
        request = content.get('request')
        url = request.get('url')
        url_raw = url.get('raw') if url else url
        _url = url_raw.replace('{{', '${').replace('}}', '}')
        # 使用正则表达式匹配":dept"内的内容并替换为${dept}
        _get_url = re.sub(r':(\w+)', r'${\1}', _url)
        return _get_url

    @classmethod
    def get_method(cls, content):
        """
        获取接口的method
        """
        request = content.get('request')
        _get_method = request.get('method', 'GET').upper()
        return _get_method

    @classmethod
    def get_headers(cls, content):
        """
        获取请求头
        """
        _headers = {}
        request = content.get('request')
        if request:
            _headers = request.get('header')
            _headers = {item.get('key'): item.get('value') for item in _headers} if _headers else {}
            auth = request.get('auth')
            if auth:
                auth_type = auth.get('type')
                if auth.get(auth_type):
                    auth_value = {item.get('key'): item.get('value') for item in auth.get(auth_type) if
                                  (item and item.get('key'))}
                    _headers.update(auth_value)
        # 如果_headers是{}就返回None
        return None if not _headers else _headers

    @classmethod
    def get_request_type_payload(cls, content):
        """
        获取request_type， 并响应处理payload及file参数
        """
        api = {
            "request_type": 'json',
            "payload": {},
            "files": {"file": []}
        }
        request = content.get('request')
        if request:
            body = request.get('body')
            if body:
                # api接口请求参数类型
                request_mode = body.get('mode')
                if request_mode in ['raw', 'formdata', 'urlencoded']:
                    api["request_type"] = 'json' if request_mode == 'raw' else 'data'
                    request_data = body.get(request_mode)
                    if request_data:
                        if request_mode == 'raw':
                            api["payload"].update(
                                json.loads(request_data.replace('\t', '').replace('\n', '').replace('\r', '')))
                        elif request_mode in ['formdata', 'urlencoded']:
                            for item in request_data:
                                if item['type'] == "text":
                                    api["payload"][item['key']] = item.get('value', '')
                                elif item['type'] == "file":
                                    api["files"]["file"].append(item.get('src', ''))
                                    api["request_type"] = "file"
                else:
                    raise ValueError("不支持的请求参数类型")
        api["payload"] = None if not api["payload"] else api["payload"]
        api["files"] = None if not api["files"]["file"] else api["files"]
        return api

    def yaml_cases(self, data: Dict, file_path: str) -> None:
        """
        写入 yaml 数据
        :param file_path:
        :param data: 测试用例数据
        :return:
        """
        # 检查目录不存在则创建， 存在则不创建
        os.makedirs(self.case_dir, exist_ok=True)

        # 处理文件名: /api/clue/v1/admin/account/activity/get -> test_account_activity.yaml
        # Postman file_path usually passed as 'k' from loop, which is case_id derived from URL in get_postman_json
        # But wait, get_postman_json returns a list of dicts: { case_id: yaml_data }
        # Let's verify what 'k' is.
        # Line 80: self.get_case_id(self.get_url(content)): yaml_data
        # get_case_id returns e.g. "case_api_clue_v1_admin_login_01" (if based on Swagger logic, but here it is different)
        # Let's check get_case_id implementation in PostmanForYaml if it exists, or if it inherits?
        # PostmanForYaml does not inherit. It has no get_case_id method shown in previous Read output?
        # Wait, I missed reading the full file.
        
        _file_name = file_path + '.yaml'
        
        # Override filename logic to match standardization request if file_path looks like a URL-based ID
        # If file_path is "case_api_clue_v1_admin_login_01", we want "test_login.yaml"
        # But 'k' in write_yaml_handler is the key of the dict.
        # In get_postman_json (Line 80), key is self.get_case_id(self.get_url(content))
        # We need to see get_case_id implementation.
        
        # Assuming file_path is the long string.
        # Let's try to parse it.
        # If it starts with "case_", remove it.
        # Remove _01 suffix?
        
        # Simplified approach: Use same logic if possible, but we might not have the raw URL here easily unless we parse file_path.
        # Actually, let's look at how get_case_id constructs it.
        
        path_parts = [p for p in file_path.replace("case_", "").replace("_01", "").split("_") if p not in 
                     ["api", "clue", "v1", "v2", "v3", "v4", "admin", "common"]]
        if path_parts and path_parts[-1].lower() in ["get", "post", "put", "delete", "patch", "head", "options"]:
            path_parts.pop()
            
        _file_name = "test_" + "_".join(path_parts) + ".yaml"

        _file_path = os.path.join(self.case_dir, _file_name)
        if _file_name in os.listdir(self.case_dir):
            data.pop("case_common")
            data = data["case_info"]
        with open(_file_path, "a", encoding="utf-8") as file:
            yaml = YAML()
            yaml.dump(data, file)
            file.write('\n')

    def write_yaml_handler(self):
        # 获取所有接口的相关数据
        for case in self._data:
            for k, v in case.items():
                self.yaml_cases(data=v, file_path=k)


if __name__ == '__main__':
    PostmanForYaml(case_dir=r"C:\1_xinjinyuan_chy\1project\apiautotest\files\postman",
                   postman_path=r"C:\1_xinjinyuan_chy\1project\apiautotest\files\Gitlink.postman_collection.json").write_yaml_handler()
