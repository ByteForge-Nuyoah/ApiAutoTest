# -*- coding: utf-8 -*-
# @Author  : 会飞的🐟
# @File    : data_handle.py
# @Desc: 数据处理模块
import re
import uuid
import copy
import json
import random
from string import Template
from core.data_utils.data_tools import *
from requests.cookies import RequestsCookieJar
from requests.utils import dict_from_cookiejar
from utils.data_utils.fake_data import FakerData
from core.data_utils.eval_data_handle import eval_data

class DataHandle:
    def __init__(self):
        # 实例化FakerData类，避免反复实例，提高性能。
        self.FakerDataClass = FakerData()
        # 获取FakerData类所有自定义方法
        self.method_list = [method for method in dir(FakerData) if
                            callable(getattr(FakerData, method)) and not method.startswith("__")]

    def process_cookie_jar(self, _data):
        """
        将任意数据里的RequestsCookieJar，转成dict，再转换成JSON 格式的字符串（序列化）
        :param _data: 待处理的数据
        """
        if isinstance(_data, dict):
            for key, value in _data.items():
                _data[key] = self.process_cookie_jar(value)
        elif isinstance(_data, list):
            for i, item in enumerate(_data):
                _data[i] = self.process_cookie_jar(item)
        elif isinstance(_data, RequestsCookieJar):
            data = json.dumps(dict_from_cookiejar(_data))
        return _data

    def replace_and_store_placeholders(self, pattern, text, result_as_dict=True):
        """
        提取字符串中符合正则表达式的元素，同时用一个唯一的uuid来替换原有字符串
        例如：
        原字符串：user_id: ${user_id}, user_name: ${user_name}
        替换后的原字符串：user_id: e1c6fc74-2f21-49a9-8d0c-de16650c6364, user_name: 50c74155-5cb5-4809-bc5d-277addf8c3e7
        暂存的需要被处理的关键字或函数：
            {'e1c6fc74-2f21-49a9-8d0c-de16650c6364': {0: '${user_id}', 1: 'user_id'}, '50c74155-5cb5-4809-bc5d-277addf8c3e7': {0: '${user_name}', 1: 'user_name'}}
        """
        placeholders = {}

        def replace(match):
            placeholder = str(uuid.uuid4())  # 使用uuid生成唯一的占位符
            placeholders[placeholder] = {0: f'${match.group(1)}', 1: match.group(1)}  # 将提取到的字符串存储到字典中
            return placeholder

        # 使用正则表达式进行字符串匹配和替换，同时指定替换次数为 1
        replaced_text = re.sub(pattern, replace, text, count=1)
        while replaced_text != text:
            text = replaced_text
            replaced_text = re.sub(pattern, replace, text, count=1)

        if result_as_dict:
            return replaced_text, placeholders
        else:
            # 构造结果字符串
            result = '{\n'
            for key, value in placeholders.items():
                result += f"    '{key}': {{0: \"{value[0]}\", 1: \"{value[1]}\"}},\n"
            result += '}'
            return replaced_text, result

    def data_handle(self, obj, source=None):
        obj = copy.deepcopy(eval_data(obj))
        return self.data_handle_(obj, source)

    def data_handle_(self, obj, source=None):
        """
        递归处理字典、列表中的字符串，将${}占位符替换成source中的值
        """
        func = {}
        keys = {}

        source = {} if not source or not isinstance(source, dict) else source
        logger.trace(f"source={source}")

        # 处理一下source，检测到里面存在RequestsCookieJar，转成dict，再转换成JSON 格式的字符串（序列化）。
        # 避免传递过来一个RequestsCookieJar，替换后变成了'RequestsCookieJar'，导致cookies无法使用的问题
        source = self.process_cookie_jar(_data=source)

        # 如果进来的是字符串，先将各种类型的表达式处理完
        if isinstance(obj, str):
            # 先把python表达式找出来存着，这里会漏掉一些诸如1+1的表达式
            pattern = r"\${([^}]+\))}"  # 匹配以 "${" 开头、以 ")}" 结尾的字符串，并在括号内提取内容，括号内不能包含"}"字符
            obj, func = self.replace_and_store_placeholders(pattern, obj)

            # 模板替换
            should_eval = 0
            if obj.startswith("${") and obj.endswith("}"):
                if source.get(obj[2:-1]) and not isinstance(source[obj[2:-1]], str):
                    should_eval = 1
            obj = Template(obj).safe_substitute(source)
            if should_eval == 1:
                obj = eval_data(obj)

            if not isinstance(obj, str):
                return self.data_handle(obj)

            # 再找一遍剩余的${}跟第一步的结果合并，提取漏掉的诸如1+1的表达式(在此认为关键字无法替换的都是表达式，最后表达式也无法处理的情况就报错或者原样返回)
            pattern = r'\$\{([^}]+)\}'  # 定义匹配以"${"开头，"}"结尾的字符串的正则表达式
            obj, func_temp = self.replace_and_store_placeholders(pattern, obj)
            func.update(func_temp)
            # 进行函数调用替换
            obj = self.invoke_funcs(obj, func)
            if not isinstance(obj, str):
                return self.data_handle(obj)
            # 直接返回最后的结果
            return obj
        elif isinstance(obj, list):
            for index, item in enumerate(obj):
                obj[index] = self.data_handle(item, source)
            return obj
        elif isinstance(obj, dict):
            for key, value in obj.items():
                obj[key] = self.data_handle(value, source)
            return obj
        else:
            return obj

    def invoke_funcs(self, obj, funcs):
        """
        调用方法，并将方法返回的结果替换到obj中去
        """
        for key, funcs in funcs.items():  # 遍历方法字典调用并替换
            func = funcs[1]
            # logger.trace("invoke func : ", func)
            try:
                if "." in func:
                    if func.startswith("faker."):
                        # 英文的faker数据：self.faker = Faker()
                        faker = self.FakerDataClass.faker
                        obj = self.deal_func_res(obj, key, eval(func))
                    elif func.startswith("fk_zh."):
                        # 中文的faker数据： self.fk_zh = Faker(locale='zh_CN')
                        fk_zh = self.FakerDataClass.fk_zh
                        obj = self.deal_func_res(obj, key, eval(func))
                    else:
                        obj = self.deal_func_res(obj, key, eval(func))
                else:
                    func_parts = func.split('(')
                    func_name = func_parts[0]
                    func_args_str = ''.join(func_parts[1:])[:-1]
                    if func_name in self.method_list:  # 证明是FakerData类方法
                        method = getattr(self.FakerDataClass, func_name)
                        res = eval(f"method({func_args_str})")  # 尝试直接调用
                        obj = self.deal_func_res(obj, key, res)
                    else:  # 不是FakerData类方法，但有可能是 1+1 这样的
                        obj = self.deal_func_res(obj, key, eval(func))
            except Exception as e:
                logger.warning("Warn: --------函数：%s 无法调用成功, 请检查是否存在该函数-------" % func)
                obj = obj.replace(key, funcs[0])

        return obj

    def deal_func_res(self, obj, key, res):
        obj = obj.replace(key, str(res))
        try:
            if not isinstance(res, str):
                obj = eval(obj)
        except Exception as e:
            msg = (f"\nobj --> {obj}\n"
                   f"函数返回值 --> {res}\n"
                   f"函数返回值类型 --> {type(res)}\n")
            logger.warning(
                f"\nWarn: --------处理函数方法后，尝试eval({obj})失败，可能原始的字符串并不是python表达式-------{msg}")
        return obj


# 声明data_handle方法，这样外部就可以直接import data_handle来使用了
data_handle = DataHandle().data_handle

# if __name__ == '__main__':
    # # 下面是测试代码
    # print("\n----------测试场景1: 识别${python表达式}，这里random方法是需要导入random包的---------------------\n")
    # data = "选择.gitignore: ${random.choice(['Ada', 'Actionscript', 'Ansible', 'Android', 'Agda'])}，开源许可证: ${random.choice(['0BSD', 'AAL', 'AFL-1.1', '389-exception'])}"
    # new = data_handle(data)
    # print(new, type(new),
    #       end="\n\n---------------------------------------------------------------------------------------------\n\n")
    #
    # print("-----------测试场景2：识别${python表达式}，可以在当前文件导入其他模块，一样可以识别替换---------------------")
    # # 导入其他方法，也可以直接使用
    # # from utils.time_handle import test_fun_a
    # # data = "${test_fun_a()}"
    # # new = data_handle(data)
    # # print(new, type(new))
    #
    # print("\n-----------测试场景3：识别FakerData类中的方法---------------------\n")
    # """
    # 使用FakerData类中的方法可以直接这样写：${generate_random_int()}， 也可以带上类名：${FakerData().generate_random_int()}
    # """
    # data = {
    #     "age": "${generate_random_int()}",
    #     "message": "Hello, ${FakerData().generate_female_name()}!",
    #     "nested_data": [
    #         "This is ${name}'s data.",
    #         {
    #             "message": "Age: ${generate_random_int()}",
    #             "nested_list": [
    #                 "More data: ${FakerData().generate_random_int()}",
    #             ]
    #         }
    #     ]
    # }
    # new = data_handle(data)
    # print(new, type(new), end="\n\n")
    #
    # """
    # 使用FakerData类中的方法, 支持方法传参使用，注意参数如果是str格式，建议使用单引号
    # """
    # payload = {
    #     "name": "${generate_name(lan='zh')}",
    #     "repository_name": "${generate_name('zh')}",
    #     "desc": '[[1,2,3,4],"${FakerData().generate_random_int()}"]',
    #     "pre": '[[1,2,3,4],${FakerData().generate_name()}]',
    #     "startTime": "${FakerData.generate_time('%Y-%m-%d')}",
    # }
    # new = data_handle(payload)
    # print(new, type(new), end="\n\n")
    #
    # """
    # 还可以直接使用FakerData类中的实例属性
    # """
    #
    # data = {
    #     "payload": {
    #         "en_name": "${faker.name()}",  # 这里是使用类FakerData里面的实例属性faker
    #         "zh_name": "${fk_zh.name()}",  # 这里是使用类FakerData里面的实例属性fk_zh
    #         "url": "/api/accounts/${FakerData.generate_time('%Y-%m-%d')}/login.json",
    #     }
    # }
    #
    # new = data_handle(data)
    # print(new, type(new), end="\n\n")
    #
    # """
    # FakerData类中没有封装random_name这个方法，会无法处理
    # """
    # data = '[[1,2,3,4],"${FakerData().random_name()}"]'
    # new = data_handle(data)
    # print(new, type(new),
    #       end="\n\n---------------------------------------------------------------------------------------------\n\n")
    #
    # print("\n-----------测试场景4：识别${}进行关键字替换---------------------\n")
    # user_info = {
    #     "user_id": 104,
    #     "user_name": "flora"
    # }
    # data_03 = "user_id: ${user_id}, user_name: ${user_name}"
    # new = data_handle(data_03, user_info)
    # print(new, type(new), end="\n\n")
    #
    # """
    # 识别${}进行关键字替换时会保留原值的类型。 比如eval('1,2,4')会变成元组(1,2,4)。经过本方法处理，会保留原有格式
    # """
    # data = {
    #     "winner_id": "${winner_id}",
    #     "user_id": "${user_id}",
    #     "time": "${generate_time()}",
    #     "attachment_ids": "${attachment_ids}",
    #     "assigned_id": "${assigned_id}",
    #     "cookies": "${cookies}"
    # }
    # source = {
    #     "winner_id": "1,2,4",
    #     "assigned_id": [],
    #     '报告标题': 'UI自动化测试报告', '项目名称': 'GitLink 确实开源', 'tester': '陈银花',
    #     'department': '开源中心', 'env': 'https://testforgeplus.trustie.net',
    #     'host': 'https://testforgeplus.trustie.net', 'login': 'autotest',
    #     'nickname': 'autotest', 'user_id': 106, 'super_login': 'floraachy', 'super_user_id': 103,
    #     'project_id': '59',
    #     'repo_id': '59', 'project_url': '/autotest/auotest',
    #     'attachment_ids': ['85b7f7ff-59e6-4f38-88da-29440aa4fc18', 'ba23f9b1-ad92-476d-ac4d-aba1382a9636'],
    #     'file_name': 'gitlinklogo3.jpg',
    #     'cookies': '{"_educoder_session": "d79e0e75f71cd98a9df2665d405b49e7", "autologin_trustie": "d25b412c26388182a50e8be38e4b9731c4e783ba"}',
    # }
    #
    # new = data_handle(obj=data, source=source)
    # print(new, type(new),
    #       end="\n\n---------------------------------------------------------------------------------------------\n\n")
    #
    # print("\n-----------测试场景5：识别 字符串里面是python表达式的情况---------------------\n")
    # data = [
    #     "[1,2,3,4]", "1+1", "[1, '1', [1, 2], {'name':'flora', 'age': '1'}]"
    # ]
    # new = data_handle(data)
    # print(new, type(new),
    #       end="\n\n---------------------------------------------------------------------------------------------\n\n")
    #
    # print("\n-----------测试场景5：导入的函数---------------------\n")
    # source = {
    #     "added_testcase_test_step": [
    #         {'id': 5878, 'index': 0, 'content': '科技-大学', 'expectedResult': '一直-有些', 'execResult': 0},
    #         {'id': 5879, 'index': 1, 'content': '包括-质量', 'expectedResult': '系统-发表', 'execResult': 0}],
    #     "test_ids": [1, 2, 3, 4, 5]
    # }
    # data = {
    #     "testcaseStepList": "${data_keys_to_keep(${added_testcase_test_step},'id')}"}
    #
    # new = data_handle(obj=data, source=source)
    # print(new, type(new),
    #       end="\n\n---------------------------------------------------------------------------------------------\n\n")
    #
    # data = {
    #     "test_ids": '${list_to_str(target=${test_ids})}'
    # }
    #
    # new = data_handle(obj=data, source=source)
    # print(new, type(new),
    #       end="\n\n---------------------------------------------------------------------------------------------\n\n")
