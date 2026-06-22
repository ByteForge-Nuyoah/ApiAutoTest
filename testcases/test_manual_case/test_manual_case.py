# -*- coding: utf-8 -*-
# @Author  : 会飞的🐟
# @File    : test_manual_case.py
# @Desc: 手写测试用例示例（数据驱动）

import pytest
import allure
import time
from loguru import logger
from core.requests_utils.request_control import RequestControl
from core.requests_utils.case_dependence import CaseDependenceHandler
from core.case_generate_utils.case_data_analysis import CaseDataCheck
from config.settings import GLOBAL_VARS
from utils.files_utils.files_handle import load_yaml_file
import os

# 用例数据源文件路径
CASE_SOURCE_FILE = "interfaces/projects/workspace/test_login.yaml"

def _load_cases_from_yaml():
    """
    从YAML文件动态加载用例数据
    """
    if not os.path.exists(CASE_SOURCE_FILE):
        logger.error(f"用例源文件不存在: {CASE_SOURCE_FILE}")
        return []

    yaml_data = load_yaml_file(CASE_SOURCE_FILE)
    
    # 使用 CaseDataCheck 进行数据校验和处理
    case_checker = CaseDataCheck()
    cases = case_checker.case_process(yaml_data)

    return cases

# 动态加载用例数据
cases = _load_cases_from_yaml()

# 依赖处理器
dependence_handler = CaseDependenceHandler(GLOBAL_VARS)


@allure.epic("workspace")
@allure.feature("用户登录模块")
@allure.story("登录接口-手写用例")
@pytest.mark.manual
@pytest.mark.workspace
@pytest.mark.parametrize("case", cases, ids=lambda x: x["title"])
def test_yaml_login_manual(case):
    """手写登录测试用例"""
    case_id = case.get("id", "unknown")
    case_title = case.get("title", "unknown")

    with allure.step(f"执行用例: {case_id} - {case_title}"):
        try:
            start_time = time.time()
            logger.info(f"开始执行用例: {case_id} || {case_title}")

            with allure.step("前置依赖处理"):
                if case.get("case_dependence") and case["case_dependence"].get("setup"):
                    dependence_results = dependence_handler.case_dependence_handle(
                        case_dependence=case["case_dependence"]["setup"],
                        db_info=GLOBAL_VARS.get("db_info"))
                    if dependence_results:
                        GLOBAL_VARS.update(dependence_results)

            with allure.step("发送请求并验证"):
                db_info = GLOBAL_VARS.get("db_info")
                if db_info:
                    res = RequestControl().api_request_flow(
                        request_data=case,
                        global_var=GLOBAL_VARS,
                        db_info=db_info
                    )
                else:
                    res = RequestControl().api_request_flow(
                        request_data=case,
                        global_var=GLOBAL_VARS
                    )

                if res:
                    GLOBAL_VARS.update(res)

            with allure.step("后置依赖处理"):
                if case.get("case_dependence") and case["case_dependence"].get("teardown"):
                    dependence_results = dependence_handler.case_dependence_handle(
                        case_dependence=case["case_dependence"]["teardown"],
                        db_info=GLOBAL_VARS.get("db_info"))
                    if dependence_results:
                        GLOBAL_VARS.update(dependence_results)

            elapsed_time = time.time() - start_time
            logger.info(f"用例执行完成: {case_id} || 耗时: {elapsed_time:.2f}s")
            allure.attach(
                f"执行时间: {elapsed_time:.2f}秒",
                name="执行耗时",
                attachment_type=allure.attachment_type.TEXT
            )

        except Exception as e:
            logger.error(f"用例执行失败: {case_id} || 错误: {str(e)}")
            raise
