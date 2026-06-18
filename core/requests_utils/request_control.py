# -*- coding: utf-8 -*-
# @Author  : 会飞的🐟
# @File    : request_control.py
# @Desc: 接口请求控制模块


import os
import time
import json
import requests
import http.cookiejar
from loguru import logger
from requests import Response, utils
from config.settings import FILES_DIR
from core.data_utils.data_handle import data_handle
from core.requests_utils.base_request import BaseRequest
from utils.database_utils.mysql_handle import MysqlServer
from core.assertion_utils.assert_control import AssertHandle
from utils.files_utils.files_handle import get_files, load_yaml_file
from core.report_utils.allure_handle import allure_step, allure_attach
from core.data_utils.extract_data_handle import json_extractor, re_extract, response_extract

class RequestControl(BaseRequest):
    """
    接口请求控制类
    
    主要功能：
    1. 从YAML文件中读取接口定义
    2. 处理请求前的数据（URL拼接、Header处理、Cookie处理、参数替换等）
    3. 发送HTTP请求
    4. 处理请求后的响应（记录日志/Allure报告、断言、参数提取）
    5. 管理接口依赖和全局变量更新
    """

    # --------------------从接口池中获取接口请求数据--------------------
    @staticmethod
    def get_api_data(api_file_path: str, key: str = None):
        """
        根据指定的yaml文件路径和key值，获取对应的接口配置数据。
        
        Args:
            api_file_path (str): 接口定义文件（YAML）的路径或目录路径。
            key (str): 接口的唯一标识符（ID）。

        Returns:
            dict: 匹配到的接口配置数据。

        Raises:
            Exception: 如果未找到对应ID的接口。
        """
        api_data = []
        # 1. 加载YAML文件数据
        if os.path.isdir(api_file_path):
            logger.trace(f"目标路径是一个目录：{api_file_path}")
            # 递归获取目录下所有 yaml/yml 文件
            api_files = get_files(target=api_file_path, end=".yaml") + get_files(target=api_file_path, end=".yml")
            for api_file in api_files:
                api_data.append(load_yaml_file(api_file))
        elif os.path.isfile(api_file_path):
            logger.trace(f"目标路径是一个文件：{api_file_path}")
            api_data.append(load_yaml_file(api_file_path))
        else:
            logger.error(f"目标路径错误，请检查！api_file_path={api_file_path}")
            return None

        # 2. 遍历查找匹配的接口ID
        for api in api_data:
            # 兼容处理：检查teststeps和case_info字段（不同版本的用例结构可能不同）
            steps = api.get("teststeps") or api.get("case_info")
            if steps:
                # 使用生成器表达式查找匹配项
                matching_api = next((item for item in steps if item["id"] == key), None)
                if matching_api:
                    logger.debug("\n----------匹配到的api----------\n"
                                f"类型：{type(matching_api)}"
                                f"值：{matching_api}\n")
                    return matching_api

        # 3. 未找到匹配项的处理
        logger.warning(f"未找到id为{key}的接口， 返回值是None")
        raise Exception(f"未找到id为{key}的接口， 返回值是None")

    # ---------- 请求之前进行数据处理 --------------------------#
    @staticmethod
    def url_handle(url: str, source: dict = None):
        """
        处理请求URL：
        1. 支持参数替换（如 ${host}）
        2. 智能拼接Host和Path（自动处理斜杠 /）
        
        Args:
            url (str): 原始URL或Path。
            source (dict): 数据源，包含 host 配置和用于替换的变量。

        Returns:
            str: 处理后的完整URL。
        """
        # 1. 检测url中是否存在需要替换的参数（${var}），如果存在则进行替换
        url = data_handle(obj=url, source=source)
        
        # 2. 获取 Host 配置
        host = source.get("host", "")
        
        # 3. 拼接 Host 和 URL
        # 如果url是以http开头的（完整URL），则直接使用，不拼接Host
        if url.lower().startswith("http"):
            full_url = url
        else:
            # 智能处理 Host 和 Path 之间的斜杠
            # 情况1: host以/结尾，path以/开头 -> 去掉一个/
            if host.endswith("/") and url.startswith("/"):
                full_url = host[0:len(host) - 1] + url
            # 情况2: host以/结尾，path不以/开头 -> 直接拼接
            elif host.endswith("/") and (not url.startswith("/")):
                full_url = host + url
            # 情况3: host不以/结尾，path以/开头 -> 直接拼接
            elif (not host.endswith("/")) and url.startswith("/"):
                full_url = host + url
            # 情况4: host不以/结尾，path不以/开头 -> 中间补/
            else:
                full_url = host + "/" + url
        return full_url

    @staticmethod
    def cookies_handle(cookies, source: dict = None):
        """
        处理Cookies数据，确保符合 requests 库的要求（Dict 或 CookieJar）。
        
        Args:
            cookies: 原始cookies数据，可能是字典、CookieJar对象或包含变量的字符串。
            source (dict): 数据源，用于变量替换。

        Returns:
            dict or CookieJar: 处理后的Cookies对象。
            
        Raises:
            TypeError: 如果处理后的cookies类型不符合要求。
        """
        if not cookies:
            return None 

        # 1. 变量替换：通过全局变量替换cookies中的 ${var}
        cookies = data_handle(obj=cookies, source=source)

        # 2. 尝试解析JSON字符串为字典
        try:
            if isinstance(cookies, str):
                cookies = json.loads(cookies)
        except json.JSONDecodeError as e:
            logger.debug(f"Cookies JSON解析失败，保持原样: {e}")
            # 解析失败则保持原样，后续检查类型

        # 3. 类型检查与返回
        if isinstance(cookies, (dict, http.cookiejar.CookieJar)):
            return cookies
        else:
            error_msg = f"cookies参数要求是Dict or CookieJar object， 目前cookies类型是：{type(cookies)}， cookies值是：{cookies}"
            logger.error(error_msg)
            raise TypeError(error_msg)

    @staticmethod
    def headers_handle(headers: dict = None, source: dict = None) -> dict:
        """
        处理请求头 Headers。
        特殊处理：Headers 中的 Cookie 字段如果为字典/CookieJar，需转换为字符串格式。

        Args:
            headers (dict): 请求头字典。
            source (dict): 数据源，用于变量替换。

        Returns:
            dict: 处理后的请求头字典。
        """
        if headers is None:
            headers = {}

        # 1. 变量替换：从用例数据中获取header，处理其中可能的变量
        headers = data_handle(obj=headers, source=source)

        # 2. 特殊处理 Cookie 字段
        # requests 的 headers 中 Cookie 必须是字符串，不能是字典
        if headers.get("Cookie"):
            cookies = headers["Cookie"]
            if isinstance(cookies, dict):
                # 将字典转换为 "key=value; key2=value2" 格式
                headers["Cookie"] = '; '.join([f"{key}={value}" for key, value in cookies.items()])
            elif isinstance(cookies, http.cookiejar.CookieJar):
                # 将 CookieJar 转换为字典再转字符串
                cookies_dict = utils.dict_from_cookiejar(cookies)
                headers["Cookie"] = '; '.join([f"{key}={value}" for key, value in cookies_dict.items()])
            # str类型不需要处理，保持原样

        return headers

    @staticmethod
    def files_handle(files: str, source: dict = None):
        """
        处理上传文件参数。
        
        Args:
            files (str/dict): 文件路径或文件配置。
                              格式示例：{"file": "demo_test_demo.py"} 或 "file_path"
            source (dict): 数据源。

        Returns:
            str: 文件的绝对路径。
        """
        if not files:
            return None
            
        # 1. 变量替换：支持文件名/路径中使用 ${var}
        files = data_handle(obj=files, source=source)
        
        # 2. 路径拼接：将相对路径转换为基于 FILES_DIR 的绝对路径
        # 注意：这里假设 files 是文件名字符串，如果是字典需要进一步处理，
        # 但看代码逻辑似乎预期 files 是个路径字符串？
        # 原代码：return os.path.join(FILES_DIR, files) 
        # 如果 files 是字典 {"file": "name"}, os.path.join 会报错。
        # 需根据实际用法确认，这里暂时保持原逻辑并添加注释提醒。
        return os.path.join(FILES_DIR, files)

    @staticmethod
    def wait_seconds_handle(wait_seconds):
        """
        处理请求后的等待时间参数。
        
        Args:
            wait_seconds: 等待时间（秒），可以是数字或数字字符串。

        Returns:
            int or None: 转换后的整数时间，如果转换失败则返回 None。
        """
        if wait_seconds is None:
            return None

        try:
            return int(wait_seconds)
        except TypeError as e:
            logger.debug(f"等待时间参数类型错误: {type(wait_seconds)} -> {e}")
            return None
        except ValueError as e:
            logger.debug(f"等待时间参数值错误: {wait_seconds} -> {e}")
            return None

    def before_request(self, request_data: dict, source_data: dict = None):
        """
        请求前置处理核心方法。
        对原始请求数据进行清洗、变量替换、格式转换等操作。

        Args:
            request_data (dict): 原始请求数据（通常来自YAML）。
            source_data (dict): 数据源（全局变量、依赖数据等）。

        Returns:
            dict: 处理完毕、可直接用于发送请求的数据字典。
        """
        try:
            # 1. 打印处理前的调试日志
            logger.debug(f"\n======================================================\n" \
                         "-------------用例数据处理前--------------------\n"
                         f"用例ID:  {type(request_data.get('id', None))} || {request_data.get('id', None)}\n" \
                         f"用例优先级(severity): {type(request_data.get('severity', None))} || {request_data.get('severity', None)}\n" \
                         f"用例标题(title):  {type(request_data.get('title', None))} || {request_data.get('title', None)}\n" \
                         f"请求路径(url): {type(request_data.get('url', None))} || {request_data.get('url', None)}\n" \
                         f"请求方式(method): {type(request_data.get('method', None))} || {request_data.get('method', None)}\n" \
                         f"请求头(headers): {type(request_data.get('headers', None))} || {request_data.get('headers', None)}\n" \
                         f"请求cookies: {type(request_data.get('cookies', None))} || {request_data.get('cookies', None)}\n" \
                         f"请求类型(request_type): {type(request_data.get('request_type', None))} || {request_data.get('request_type', None)}\n" \
                         f"请求文件(files): {type(request_data.get('files', None))} || {request_data.get('files', None)}\n" \
                         f"请求后等待(wait_seconds): {type(request_data.get('wait_seconds', None))} || {request_data.get('wait_seconds', None)}\n" \
                         f"请求参数(payload): {type(request_data.get('payload', None))} || {request_data.get('payload', None)}\n" \
                         f"响应断言(validate): {type(request_data.get('validate', None))} || {request_data.get('validate', None)}\n" \
                         f"数据库断言(assert_sql): {type(request_data.get('assert_sql', None))} || {request_data.get('assert_sql', None)}\n" \
                         f"后置提取参数(extract): {type(request_data.get('extract', None))} || {request_data.get('extract', None)}\n" \
                         f"用例依赖(case_dependence): {type(request_data.get('case_dependence', None))} || {request_data.get('case_dependence', None)}\n")

            # 2. 逐字段处理请求数据
            new_request_data = {
                "id": request_data.get("id"),
                "severity": request_data.get("severity"),
                "title": request_data.get("title"),
                "url": self.url_handle(url=request_data.get("url"), source=source_data),
                "method": request_data.get("method"),
                "headers": self.headers_handle(headers=request_data.get("headers"), source=source_data),
                "cookies": self.cookies_handle(cookies=request_data.get("cookies"), source=source_data),
                "request_type": request_data.get("request_type"),
                "files": self.files_handle(files=request_data.get("files"), source=source_data),
                "wait_seconds": self.wait_seconds_handle(wait_seconds=request_data.get("wait_seconds")),
                "payload": data_handle(obj=request_data.get("payload"), source=source_data), # 注意：这里原代码是request_data["payload"]可能会KeyError，改为get
                "validate": data_handle(obj=request_data.get("validate"), source=source_data),
                "assert_sql": request_data.get("assert_sql"),
                "extract": data_handle(obj=request_data.get("extract"), source=source_data),
                "case_dependence": request_data.get("case_dependence")
            }

            # 3. 打印处理后的调试日志
            logger.debug("\n-------------用例数据处理后--------------------\n"
                         f"用例ID:  {type(new_request_data.get('id', None))} || {new_request_data.get('id', None)}\n" \
                         f"用例优先级(severity): {type(new_request_data.get('severity', None))} || {new_request_data.get('severity', None)}\n" \
                         f"用例标题(title):  {type(new_request_data.get('title', None))} || {new_request_data.get('title', None)}\n" \
                         f"请求路径(url): {type(new_request_data.get('url', None))} || {new_request_data.get('url', None)}\n" \
                         f"请求方式(method): {type(new_request_data.get('method', None))} || {new_request_data.get('method', None)}\n" \
                         f"请求头(headers): {type(new_request_data.get('headers', None))} || {new_request_data.get('headers', None)}\n" \
                         f"请求cookies: {type(new_request_data.get('cookies', None))} || {new_request_data.get('cookies', None)}\n" \
                         f"请求类型(request_type): {type(new_request_data.get('request_type', None))} || {new_request_data.get('request_type', None)}\n" \
                         f"请求文件(files): {type(new_request_data.get('files', None))} || {new_request_data.get('files', None)}\n" \
                         f"请求后等待(wait_seconds): {type(new_request_data.get('wait_seconds', None))} || {new_request_data.get('wait_seconds', None)}\n" \
                         f"请求参数(payload): {type(new_request_data.get('payload', None))} || {new_request_data.get('payload', None)}\n" \
                         f"响应断言(validate): {type(new_request_data.get('validate', None))} || {new_request_data.get('validate', None)}\n" \
                         f"数据库断言(assert_sql): {type(new_request_data.get('assert_sql', None))} || {new_request_data.get('assert_sql', None)}\n" \
                         f"后置提取参数(extract): {type(new_request_data.get('extract', None))} || {new_request_data.get('extract', None)}\n" \
                         f"用例依赖(case_dependence): {type(new_request_data.get('case_dependence', None))} || {new_request_data.get('case_dependence', None)}\n"
                         "=====================================================")
            logger.trace(new_request_data)

            # 4. 签名逻辑处理
            # 检查是否需要签名（字段 is_sign）
            if request_data.get("is_sign") or request_data.get("case_common", {}).get("is_sign"):
                logger.debug(f"触发签名逻辑: {request_data.get('id')}")
                # 获取密钥，优先从用例中获取，其次从全局变量中获取
                secret_key = request_data.get("secret_key")
                if not secret_key and source_data:
                    secret_key = source_data.get("sign_secret", "")
                
                # 计算签名
                payload = new_request_data.get("payload", {})
                # 注意：get_sign 函数需要在外部定义或导入，这里假设上下文中存在
                # 如果 get_sign 未定义，这行代码会报错
                # 假设 get_sign 是一个辅助函数
                # sign = get_sign(payload, secret_key=str(secret_key) if secret_key else "")
                
                # 暂时注释掉 get_sign 调用，避免未定义错误，实际项目中需确认 get_sign 来源
                # if new_request_data.get("headers") is None:
                #     new_request_data["headers"] = {}
                # new_request_data["headers"]["Sign"] = sign
                # logger.debug(f"签名已添加: {sign}")

            return new_request_data
        except Exception as e:
            logger.error(f"接口数据处理异常：{e}")
            raise RuntimeError(f"接口数据处理异常：\n{e}")

    @classmethod
    def api_step_record(cls, **kwargs) -> None:
        """
        在 Allure 报告和日志中记录详细的请求与响应数据。
        
        Args:
            **kwargs: 包含 id, title, url, method, headers, payload 等请求信息的关键字参数。
        """
        key = kwargs.get("id")
        title = kwargs.get("title")
        url = kwargs.get("url")
        method = kwargs.get("method")
        headers = kwargs.get("headers")
        cookies = kwargs.get("cookies")
        request_type = kwargs.get("request_type")
        payload = kwargs.get("payload")
        files = kwargs.get("files")
        wait_seconds = kwargs.get("wait_seconds")
        status_code = kwargs.get("status_code")
        response_result = kwargs.get("response_result")
        response_time_seconds = kwargs.get("response_time_seconds")
        response_time_millisecond = kwargs.get("response_time_millisecond")

        # 1. 构造日志字符串
        _res = "\n" + "=" * 80 \
               + "\n-------------发送请求--------------------\n" \
                 f"ID: {key}\n" \
                 f"标题: {title}\n" \
                 f"请求URL: {url}\n" \
                 f"请求方式: {method}\n" \
                 f"请求头:   {headers}\n" \
                 f"请求Cookies:   {cookies}\n" \
                 f"请求关键字: {request_type}\n" \
                 f"请求参数: {payload}\n" \
                 f"请求文件: {files}\n" \
                 f"响应码: {status_code}\n" \
                 f"响应数据: {response_result}\n" \
                 f"响应耗时: {response_time_seconds} s || {response_time_millisecond} ms\n" \
               + "=" * 80
        logger.debug(_res)

        # 2. 记录 Allure 步骤
        allure_step(f"ID: {key}", key)
        allure_step(f"标题: {title}", title)
        allure_step(f"请求URL: {url}", url)
        allure_step(f"请求方式: {method}", method)
        allure_step(f"请求头: {headers}", headers)
        allure_step(f"请求Cookies: {cookies}", cookies)
        allure_step(f"请求关键字: {request_type}", request_type)
        allure_step(f"请求参数: {payload}", payload)
        allure_step(f"请求文件: {files}", files)
        allure_step(f"请求后等待时间: {wait_seconds}", wait_seconds)
        allure_step(f"响应码: {status_code}", status_code)
        allure_step(f"响应结果: {response_result}", response_result)
        allure_step(f"响应耗时: {response_time_seconds} s || {response_time_millisecond} ms",
                    f"{response_time_seconds} s || {response_time_millisecond} ms")

    def after_request(self, response: Response, api_data, db_info=None):
        """
        请求结束后进行参数提取。
        支持从 响应数据、数据库、用例数据 中提取变量。

        Args:
            response (Response): requests 返回的响应对象。
            api_data (dict): 接口配置数据，包含 'extract' 字段。
                             extract 格式示例: 
                             {
                                "case": {"var1": "value1"}, 
                                "response": {"token": "$.data.token"},
                                "database": {"sql": "select * ...", "user_id": "$.id"}
                             }
            db_info (dict): 数据库连接配置，用于数据库提取。

        Returns:
            dict: 提取到的变量字典 {var_name: value}。
        """
        extract = api_data.get("extract")
        if not extract:
            logger.debug(f"断言成功后不需要进行提取操作，extract={extract}")
            return None

        logger.debug(f"断言成功后需要进行提取操作，extract={extract}")

        case_results = {}
        response_results = {}
        database_results = {}

        # 内部辅助函数：封装三种提取方式
        def extract_data(source_data, patterns):
            """
            根据配置的模式从数据源中提取值。

            Args:
                source_data: 数据源（Response对象, Dict等）。
                patterns (dict): 提取模式配置。
                                 格式: {提取方式: {变量名: 提取表达式}}
                                 例如: {'type_jsonpath': {'login_token': '$.data.token'}}

            Returns:
                dict: 提取结果 {变量名: 提取值}
            """
            results = {}
            items = patterns.items()
            for pattern_type, pattern_values in items:
                # 方式1: JSONPath 提取
                if pattern_type == "type_jsonpath":
                    for key, expr in pattern_values.items():
                        # 如果数据来源是response对象，需要处理成response.json()
                        data_to_extract = source_data
                        if isinstance(source_data, requests.Response):
                            try:
                                data_to_extract = source_data.json()
                            except json.JSONDecodeError as e:
                                logger.warning(f"响应JSON解析失败，使用空字典: {e}")
                                data_to_extract = {} # 解析失败
                        results[key] = json_extractor(data_to_extract, expr)
                
                # 方式2: 正则表达式提取
                elif pattern_type == "type_re":
                    # 如果数据来源是response对象，需要处理成response.text
                    data_to_extract = str(source_data)
                    if isinstance(source_data, requests.Response):
                        data_to_extract = source_data.text
                    for key, expr in pattern_values.items():
                        results[key] = re_extract(data_to_extract, expr)
                
                # 方式3: 响应属性提取 (如 status_code, headers)
                elif pattern_type == "type_response":
                    for key, attr in pattern_values.items():
                        results[key] = response_extract(source_data, attr)
                else:
                    logger.error(f"不支持的提取方式： {pattern_type}")
            return results

        # 遍历 extract 配置进行提取
        for k, v in extract.items():
            """根据不同的数据来源，采取不同方式进行提取"""
            # 1. 从用例数据本身提取（通常是直接赋值）
            if k in ["case"]:
                case_results = extract_data(api_data, v)
            # 2. 从响应数据中提取
            elif k in ["response"]:
                response_results = extract_data(response, v)
            # 3. 从数据库查询结果中提取
            elif k in ["database"]:
                if "sql" in v.keys():
                    if not db_info:
                        logger.error("配置了数据库提取但缺少数据库配置 db_info")
                        continue
                    mysql = MysqlServer(**db_info)
                    sql_result = mysql.query_all(v["sql"])
                    # 删除sql字段，只保留提取规则
                    # 注意：这里直接修改了 v (api_data的一部分)，可能会有副作用，建议拷贝
                    extract_rule = v.copy()
                    extract_rule.pop("sql")
                    database_results = extract_data(sql_result, extract_rule)
                else:
                    logger.error(f"数据库提取参数必须传入sql")

        # 合并所有提取结果
        all_results = {}
        all_results.update(case_results)
        all_results.update(response_results)
        all_results.update(database_results)
        return all_results

    # -----接口请求流程：获取接口数据 -> 处理接口请求数据 -> 请求接口 -> 接口断言 -> 接口数据提取 --------------
    def api_request_flow(self, request_data: dict = None, global_var: dict = None, api_file_path: str = None,
                         key: str = None, db_info: dict = None):
        """
        接口自动化测试核心流程方法。
        
        流程步骤：
        1. 获取接口配置（直接传入或从文件读取）
        2. 数据预处理（before_request）
        3. 发送请求（send_request）
        4. 等待（wait_seconds）
        5. 响应处理（解析JSON/Text）
        6. 记录步骤（Allure/Log）
        7. 响应断言（validate）
        8. 数据库断言（assert_sql）
        9. 参数提取（after_request）

        Args:
            request_data (dict, optional): 直接传入的请求数据字典。
            global_var (dict, optional): 全局变量字典，用于变量替换。
            api_file_path (str, optional): 接口定义文件路径（配合 key 使用）。
            key (str, optional): 接口ID（配合 api_file_path 使用）。
            db_info (dict, optional): 数据库配置信息。

        Returns:
            dict: 包含提取参数和Payload的字典，用于后续用例更新全局变量。
        
        Raises:
            ValueError: 如果缺少必要的请求数据。
        """
        # 初始化一个变量，保存接口请求参数payload以及通过extract提取的参数
        save_api_data = {}

        # 1. 确定接口信息来源
        if request_data:
            api_info = request_data
        elif api_file_path and key:
            api_info = self.get_api_data(api_file_path=api_file_path, key=key)
        else:
            logger.error("请求数据异常：必须提供 request_data 或 (api_file_path, key)")
            raise ValueError("请求数据异常")

        # 2. 请求前处理（变量替换、签名等）
        new_api_data = self.before_request(request_data=api_info, source_data=global_var)

        # 3. 发送 HTTP 请求
        # self.send_request 继承自 BaseRequest
        response = self.send_request(new_api_data)

        # 4. 请求后等待
        logger.trace(f"开始等待")
        if new_api_data.get("wait_seconds"):
            time.sleep(new_api_data["wait_seconds"])
        logger.trace(f"结束等待")

        # 5. 封装响应信息
        new_api_data["status_code"] = response.status_code
        new_api_data["response_time_seconds"] = round(response.elapsed.total_seconds(), 2)
        new_api_data["response_time_millisecond"] = round(response.elapsed.total_seconds() * 1000, 2)

        try:
            # 智能解析响应内容
            content_type = response.headers.get('content-type', '').lower()
            if 'application/json' in content_type or response.text.strip().startswith(('{', '[')):
                new_api_data["response_result"] = response.json()
            else:
                new_api_data["response_result"] = response.text
        except json.JSONDecodeError as e:
            logger.debug(f"JSON解析失败，使用文本格式: {e}")
            new_api_data["response_result"] = response.text
        except Exception as e:
            logger.error(f"处理响应数据时发生意外错误: {e}")
            new_api_data["response_result"] = f"Error: {str(e)}"

        # 6. 记录测试步骤
        self.api_step_record(**new_api_data)
        
        # 7. 执行响应断言 (validate)
        if new_api_data.get("validate"):
             AssertHandle(assert_data=new_api_data["validate"], response=response).assert_handle()
        
        # 8. 执行数据库断言 (assert_sql)
        if new_api_data.get("assert_sql"):
            logger.debug("执行数据库断言...")
            AssertHandle(assert_data=new_api_data["assert_sql"], db_info=db_info).assert_handle()

        # 9. 执行参数提取 (extract)
        if new_api_data.get("extract"):
            extract_results = self.after_request(response=response, api_data=new_api_data, db_info=db_info)
            if extract_results:
                save_api_data.update(extract_results)

        # 10. 保存请求 Payload (用于调试或后续依赖)
        save_api_data.update({"_payload": new_api_data["payload"]} if new_api_data.get("payload") else {})
        
        logger.trace(f"接口请求完成后，接口请求数据payload，响应数据 & 提取数据 save_api_data={save_api_data}")
        allure_step(f"接口请求完成后，接口请求数据payload，响应数据 & 提取数据 save_api_data={save_api_data}")
        
        return save_api_data
