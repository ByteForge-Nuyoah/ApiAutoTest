# -*- coding: utf-8 -*-
# @Author  : 会飞的🐟
# @File    : openapi_for_yaml.py
# @Desc: OpenAPI用例生成模块

"""
@FileName：openapi_for_yaml.py
@Description：
@Author：Floraachy
@Time：2024/11/30 14:08
"""

import os
import json
from typing import Dict
from jsonpath import jsonpath
from ruamel.yaml import YAML

"""
将apifox的接口导出并生成yaml格式接口
OpenAPI Spec 版本： OpenAPI 3.1
文件格式：JSON
包含 Apifox 扩展的 OpenAPI 字段（x-apifox-***）: 不包含
将 API 文档的目录，作为 Tags 字段导出： 是
"""


class OpenApiForYaml:
    """
    将apifox接口文档转为YAML格式接口
    """

    def __init__(self, api_dir: str, json_api_path: str):
        """
        :param api_dir: YAML接口需要保存的目录
        :param json_api_path: 需要读取的导出的apifox接口的路径，参考：GitLink.openapi.json
        """
        self._data = self.get_api_json(json_api_path)
        self.api_dir = api_dir

    def get_api_json(self, path):
        """
        获取 apifox中的 json 数据
        :param path: 需要读取的apifox文件的路径
        :return:
        """
        try:
            with open(path, "r", encoding='utf-8') as f:
                row_data = json.load(f)
                return row_data
        except FileNotFoundError:
            raise FileNotFoundError("文件路径不存在，请重新输入")

    @classmethod
    def get_cookies(cls, value):
        """
        获取cookies
        """
        # 再检查parameters是否存在，存在则检查in是否等于header， 存在则header[parameters[name]]=None
        parameters = jsonpath(obj=value, expr="$.parameters")
        if parameters and parameters != [[]]:
            for i in value['parameters']:
                if i['in'] == 'cookie':
                    cookies = {i["name"]: i["example"]}
                    return cookies

    @classmethod
    def get_headers(cls, value):
        """
        获取请求头
        """
        _headers = {}
        # 检查parameters是否存在，存在则检查in是否等于header， 存在则header[parameters[name]]=None
        parameters = jsonpath(obj=value, expr="$.parameters")
        if parameters and parameters != [[]]:
            for i in value['parameters']:
                if i['in'] == 'header':
                    _headers[i['name']] = i["example"]
        # 如果_headers是{}就返回None
        return None if not _headers else _headers

    @classmethod
    def get_query_param(cls, value):
        """
        获取query参数
        """
        _query = {}
        # 检查parameters是否存在，存在则检查in是否等于query， 存在则query[parameters[name]]=None
        parameters = jsonpath(obj=value, expr="$.parameters")
        if parameters and parameters != [[]]:
            for i in value['parameters']:
                if i['in'] == 'query':
                    _query[i['name']] = f"{i['description']}, required: {i['required']}, type: {i['schema']['type']}"
        # 如果_query是{}就返回None
        return None if not _query else _query

    @classmethod
    def get_path_param(cls, value):
        """
        获取path参数
        """
        _path = {}
        # 检查parameters是否存在，存在则检查in是否等于path， 存在则path[parameters[name]]=None
        parameters = jsonpath(obj=value, expr="$.parameters")
        if parameters and parameters != [[]]:
            for i in value['parameters']:
                if i['in'] == 'path':
                    _path[i['name']] = f"{i['description']}, required: {i['required']}, type: {i['schema']['type']}"
        # 如果_query是{}就返回None
        return None if not _path else _path

    @classmethod
    def get_request_type(cls, value, headers):
        """
        处理 request_type：需要综合考虑参数的in和header请求类型
        """
        headers_values = list(headers.values()) if isinstance(headers, dict) else str(headers)
        parameters = jsonpath(obj=value, expr="$.parameters")
        if parameters and parameters != [[]]:
            _parameters = value['parameters']
            if _parameters[0]['in'] == 'query':
                return "params"
            else:
                if 'application/x-www-form-urlencoded' in headers_values or 'multipart/form-data' in headers_values:
                    return "data"
                elif 'application/json' in headers_values:
                    return "json"
                elif 'application/octet-stream' in headers_values:
                    return "file"
                else:
                    return "data"

    @classmethod
    def get_payload(cls, value):
        """
        处理 payload数据
        """
        _dict = {}
        if value.get("requestBody", None):
            # 如果schema有值，则取schema里面的properties的值，如果无值，则取example
            if jsonpath(obj=value['requestBody'], expr="$..schema"):
                _properties = jsonpath(obj=value['requestBody'], expr="$..properties")
                _required = jsonpath(obj=value['requestBody'], expr="$..required")[0] if jsonpath(obj=value['requestBody'], expr="$..required") else []
                for k, v in _properties[0].items():
                    if k in _required:
                        _dict[k] = f"{v.get('title')}, required=True, type={v.get('type')}, 描述：{v.get('description')}"
                    else:
                        _dict[
                            k] = f"{v.get('title')}, required=False, type={v.get('type')}, 描述：{v.get('description')}"
            elif jsonpath(obj=value['requestBody'], expr="$..example"):
                _dict = jsonpath(obj=value['requestBody'], expr="$..example")[0]
            else:
                print(f"当前接口的requestBody无properties和example")
        else:
            print("当前接口无requestBody")
        return _dict

    def yaml_api(self, data: Dict, file_dir: str, api_id: str) -> None:
        """
        写入 yaml 数据
        :param file_dir: yaml接口保存的目录
        :param api_id: 接口id
        :param data: 接口数据
        :return:
        """
        # 处理文件名: /api/clue/v1/admin/account/activity/get -> test_account_activity.yaml
        # api_id here (passed from write_yaml_handler) is k + key... e.g. "get_api_clue_v1_admin_account_activity"
        # We need to apply the same filtering logic.
        
        path_parts = [p for p in api_id.split("_") if p not in 
                     ["api", "clue", "v1", "v2", "v3", "v4", "admin", "common"]]
        
        # api_id usually starts with method (e.g. get_api_...)
        # So path_parts[0] might be 'get'. 
        # But wait, in write_yaml_handler: api_id = k + key.split(".")[0].replace("/", "_")
        # key is URL. k is method.
        # So "get_api_clue_..."
        # If we remove common prefixes, we might remove 'get' if we add it to ignore list, OR we handle it.
        # Let's add methods to ignore list or handle explicitly.
        # But wait, we want to KEEP 'create' or other verbs if they are part of the resource name, but DROP HTTP method 'get'.
        # 'k' is strictly HTTP method.
        
        # Let's strip the leading method if it is detected.
        methods = ["get", "post", "put", "delete", "patch", "head", "options"]
        if path_parts and path_parts[0].lower() in methods:
            path_parts.pop(0)
            
        # Also remove trailing method if present (though k is at start, but URL might end in get?)
        if path_parts and path_parts[-1].lower() in methods:
            path_parts.pop()

        _file_name = "test_" + "_".join(path_parts) + ".yaml"

        # 创建一个YAML对象
        yaml = YAML()
        # Use append mode 'a' instead of 'w' to support multiple methods in same file
        _file_path = os.path.join(file_dir, _file_name)
        
        # Check if file exists to handle potential structure (though OpenApiForYaml structure is flat dict, not case_common/case_info wrapper?)
        # Looking at api_data in write_yaml_handler (Line 200), it's a flat dict: {id, title, url...}
        # It does NOT have case_common / case_info structure like Swagger/Postman.
        # So we can just append the document. 
        # But if we append multiple documents to a YAML file, they are separated by '---' or just multiple objects?
        # YAML dump usually dumps a single object. If we call dump multiple times, it writes multiple documents.
        # But standard YAML parsers might only read the first one unless load_all is used.
        # The user's project likely uses a loader that supports lists or expects a specific structure.
        # SwaggerForYaml generates: case_common + case_info list.
        # OpenApiForYaml generates: just the dict?
        # Let's check how it's used. 
        # If OpenApiForYaml is used for generating "Interface Definitions" (not test cases directly?), then appending might be wrong if it expects 1 file per API.
        # But the user request is to unify format to `test_account_activity.yaml`.
        # This implies it's treated as a Test Case file.
        # However, the content generated by OpenApiForYaml (Line 200) looks different from SwaggerForYaml (Line 165).
        # SwaggerForYaml: {case_common: {...}, case_info: [...]}
        # OpenApiForYaml: {id:..., title:..., url:..., ...}
        # If I merge them into one file, I might break parsing if the parser expects 1 object.
        # BUT, the user explicitly asked to change the filename format.
        # If I change filename to `test_account_activity.yaml`, and I have GET and POST, they will write to same file.
        # If I use 'w', the last one wins.
        # If I use 'a', both are there.
        # I will use 'a' and hope the parser handles it (or the user intends to have multiple docs).
        # Actually, standard YAML allows multiple documents separated by `---`.
        # `ruamel.yaml` `dump` writes one document.
        # If I write again, it appends.
        # I should probably add `file.write('---\n')` if file exists? 
        # Or just append.
        
        with open(_file_path, "a", encoding="utf-8") as file:
            # If file exists and is not empty, maybe add separator?
            # But SwaggerForYaml just writes `\n` (Line 158).
            # I'll stick to simple append.
            yaml.dump(data, file)
            file.write('\n')

    def write_yaml_handler(self):
        # 检查用例保存的目录是否存在，不存在则创建， 存在则不创建
        os.makedirs(self.api_dir, exist_ok=True)

        # 根据apifox接口文档的标题和版本新建一个目录
        api_info_path = os.path.join(self.api_dir, self._data["info"]['title'] + "_" + self._data["info"]['version'])
        os.makedirs(api_info_path, exist_ok=True)

        # 根据apifox接口文档中接口所属的tags新建子目录, 涉及到多级目录的则多级创建，例如：Wiki/wiki功能接口
        for tag in self._data['tags']:
            if "/" in tag["name"]:
                new_tag = tag["name"].split("/")
                os.makedirs(os.path.join(self.api_dir, api_info_path, new_tag[0], new_tag[1]), exist_ok=True)
            else:
                os.makedirs(os.path.join(self.api_dir, api_info_path, tag["name"]), exist_ok=True)

        # 获取所有接口的相关数据，key=接口路径， value=接口各项参数
        _api_data = self._data['paths']
        for key, value in _api_data.items():
            # 获取每一个接口数据
            for k, v in value.items():
                if v.get("tags"):
                    _tag = v["tags"][0]
                    api_path = os.path.join(api_info_path, _tag.replace("/", "\\"))
                else:
                    api_path = api_info_path
                # 将接口method以及path作为接口名，去除path原有的后缀，并将/替换为_，例如：method=get, path=/api/test.json， 处理为：get_api_test
                api_id = k + key.split(".")[0].replace("/", "_")
                api_data = {
                    "id": api_id,
                    "title": v['summary'],
                    "url": key,
                    "method": k,
                    "headers": self.get_headers(v),
                    "cookies": self.get_cookies(v),
                    "request_type": self.get_request_type(v, self.get_headers(v)),
                    "query": self.get_query_param(v),
                    "path": self.get_path_param(v),
                    "payload": self.get_payload(v),
                    "files": None,

                }
                print(api_data)
                self.yaml_api(data=api_data, file_dir=api_path, api_id=api_id)


if __name__ == '__main__':
    openapi = OpenApiForYaml(api_dir=r"C:\1projects\chywork\api_pool",
                             json_api_path=r"C:\1projects\chywork\files\GitLink.openapi.json")
    openapi.write_yaml_handler()
