# -*- coding: utf-8 -*-
# @Author  : 会飞的🐟
# @File    : settings.py
# @Desc:  配置文件

import os
from dotenv import load_dotenv

# 加载环境变量，默认加载 .env 文件
load_dotenv()

# 定义一个全局变量，用于存储运行过程中相关数据
GLOBAL_VARS = {}
# 定义一个变量。存储自定义的标记markers
CUSTOM_MARKERS = []
REPORT = {
    "报告标题": "API 自动化测试报告",
    "项目名称": "统一工作台",
    "tester": "会飞的🐟",
    "department": "成都后台研发",
    "env": "test"
}
# ------------------------------------ pytest相关配置 ----------------------------------------------------#
# 失败重跑次数
RERUN = 0
# 失败重跑间隔时间
RERUN_DELAY = 5
# 当达到最大失败数，停止执行
MAX_FAIL = "100"

# ------------------------------------ 配置信息 ----------------------------------------------------#
# 1 代表 yaml文件，2 代表 excel文件，3 代表同时支持yaml和excel，其他数值将不自动生成用例
CASE_FILE_TYPE = 1
# 0表示默认不发送任何通知， 1 代表钉钉通知，2 代表企业微信通知， 3 代表邮件通知， 4 代表所有途径都发送通知
SEND_RESULT_TYPE = 0
# 指定日志收集级别
LOG_LEVEL = "DEBUG"  # 可选值：TRACE DEBUG INFO SUCCESS WARNING ERROR  CRITICAL
LOG_LEVEL_STD = "DEBUG"
"""
支持的日志级别：
    TRACE: 最低级别的日志级别，用于详细追踪程序的执行。
    DEBUG: 用于调试和开发过程中打印详细的调试信息。
    INFO: 提供程序执行过程中的关键信息。
    SUCCESS: 用于标记成功或重要的里程碑事件。
    WARNING: 表示潜在的问题或不符合预期的情况，但不会导致程序失败。
    ERROR: 表示错误和异常情况，但程序仍然可以继续运行。
    CRITICAL: 表示严重的错误和异常情况，可能导致程序崩溃或无法正常运行。
"""

# ------------------------------------ 定时任务配置 ----------------------------------------------------#
SCHEDULE_CONFIG = {
    "enabled": True,
    "run_time": "22:00",
    "env": "test",
    "report": "yes",
    "markers": None,
}

# ------------------------------------ 数据清理配置 ----------------------------------------------------#
DATA_CLEANUP_CONFIG = {
    "enabled": False,
    "databases": {
        "default": {
            "host": os.getenv("DB_HOST", "localhost"),
            "port": int(os.getenv("DB_PORT", 53306)),
            "user": os.getenv("DB_USER"),
            "password": os.getenv("DB_PASSWORD"),
            "database": os.getenv("DB_NAME"),
            "ssh": False,
            "ssh_config": {
                "ssh_host": os.getenv("SSH_HOST"),
                "ssh_port": int(os.getenv("SSH_PORT", 22)),
                "ssh_user": os.getenv("SSH_USER"),
                "ssh_pwd": os.getenv("SSH_PASSWORD"),
            }
        }
    },
    "cleanup_on_failure": True,
    "cleanup_on_success": True,
}

# ------------------------------------ Mock 服务配置 ----------------------------------------------------#
MOCK_CONFIG = {
    "enabled": True,
    "mode": "disabled",
    "recordings_dir": os.path.join(os.path.dirname(os.path.dirname(__file__)), "outputs", "mock_recordings"),
    "auto_save": True,
    "default_delay": 0.0,
}

# ------------------------------------ 多项目配置 ----------------------------------------------------#
PROJECT_CONFIG = {
    "enabled": True,
    "default_project": None,
    "projects": {
        "default": {
            "name": "统一工作台",
            "markers": None,
        }
    },
}

# ------------------------------------ 邮件配置信息 ----------------------------------------------------#
# 发送邮件的相关配置信息
email = {
    "user": os.getenv("EMAIL_USER"),
    "password": os.getenv("EMAIL_PASSWORD"),
    "host": os.getenv("EMAIL_HOST"),
    "to": os.getenv("EMAIL_TO_LIST", "").split(",") if os.getenv("EMAIL_TO_LIST") else []
}

# ------------------------------------ 邮件通知内容 ----------------------------------------------------#
email_subject = f"UI自动化报告"
email_content = """
           各位同事, 大家好:
           自动化用例于 <strong>${start_time} </strong> 开始运行，运行时长：<strong>${run_time} s</strong>， 目前已执行完成。
           ---------------------------------------------------------------------------------------------------------------
           测试人：<strong> ${tester} </strong> 
           所属部门：<strong> ${department} </strong>
           项目环境：<strong> ${env} </strong>
           ---------------------------------------------------------------------------------------------------------------
           执行结果如下:
           &nbsp;&nbsp;用例运行总数:<strong> ${total} 个</strong>
           &nbsp;&nbsp;通过用例个数（passed）: <strong><font color="green" >${passed} 个</font></strong>
           &nbsp;&nbsp;失败用例个数（failed）: <strong><font color="red" >${failed} 个</font></strong>
           &nbsp;&nbsp;异常用例个数（error）: <strong><font color="orange" >${broken} 个</font></strong>
           &nbsp;&nbsp;跳过用例个数（skipped）: <strong><font color="grey" >${skipped} 个</font></strong>
           &nbsp;&nbsp;失败重试用例个数 * 次数之和（rerun）: <strong>${rerun} 个</strong>
           &nbsp;&nbsp;成  功   率:<strong> <font color="green" >${pass_rate} %</font></strong>
           附件为具体的测试报告，详细情况可下载附件查看， 非相关负责人员可忽略此消息。谢谢。
       """
# ------------------------------------ 钉钉相关配置 ----------------------------------------------------#
ding_talk = {
    "webhook_url": os.getenv("DINGTALK_WEBHOOK"),
    "secret": os.getenv("DINGTALK_SECRET"),
}

# ------------------------------------ 钉钉通知内容 ----------------------------------------------------#
ding_talk_title = f"UI自动化报告"
ding_talk_content = """
           各位同事, 大家好:
           ### 自动化用例于 ${start_time} 开始运行，运行时长：${run_time} s， 目前已执行完成。
            ---------------------------------------------------------------------------------------------------------------
           #### 测试人： ${tester}
           #### 所属部门： ${department}
           #### 项目环境： ${env} 
           ---------------------------------------------------------------------------------------------------------------
           #### 执行结果如下:
           - 用例运行总数: ${total} 个
           - 通过用例个数（passed）: ${passed} 个
           - 失败用例个数（failed）: ${failed} 个
           - 异常用例个数（error）: ${broken} 个
           - 跳过用例个数（skipped）: ${skipped} 个
           - 失败重试用例个数 * 次数之和（rerun）: ${rerun} 个
           - 成  功   率: ${pass_rate} %
           附件为具体的测试报告，详细情况可下载附件查看， 非相关负责人员可忽略此消息。谢谢。
       """
# ------------------------------------ 企业微信相关配置 ----------------------------------------------------#
wechat = {
    "webhook_url": os.getenv("WECHAT_WEBHOOK"),
}
# ------------------------------------ 企业微信通知内容 ----------------------------------------------------#
wechat_content = """
           各位同事, 大家好:
           ### 自动化用例于 ${start_time} 开始运行，运行时长：${run_time} s， 目前已执行完成。
           --------------------------------
           #### 测试人： ${tester}
           #### 所属部门： ${department}
           #### 项目环境： ${env} 
           --------------------------------
           #### 执行结果如下:
           - 用例运行总数: ${total} 个
           - 通过用例个数（passed）:<font color=\"info\"> ${passed} 个</font>
           - 失败用例个数（failed）: <font color=\"warning\"> ${failed}  个</font>
           - 异常用例个数（error）: <font color=\"warning\"> ${broken} 个</font>
           - 跳过用例个数（skipped）: <font color=\"comment\"> ${skipped} 个</font>
           - 失败重试用例个数 * 次数之和（rerun）: <font color=\"comment\"> ${rerun} 个</font>
           - 成  功   率: <font color=\"info\"> ${pass_rate} % </font>
           附件为具体的测试报告，详细情况可下载附件查看， 非相关负责人员可忽略此消息。谢谢。
       """

# ------------------------------------ 项目路径 ----------------------------------------------------#
# 项目根目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# 通用模块目录
UTILS_DIR = os.path.join(BASE_DIR, "utils")
# 配置文件目录
ENV_DIR = os.path.join(BASE_DIR, "config")
# 接口数据模块目录
INTERFACE_DIR = os.path.join(BASE_DIR, "interfaces")
# 项目测试数据模块目录
PROJECT_DIR = os.path.join(INTERFACE_DIR, "projects")
# 测试文件模块目录
FILES_DIR = os.path.join(BASE_DIR, "files")
# 第三方库目录
LIB_DIR = os.path.join(BASE_DIR, "lib")
# 日志/报告保存目录
OUT_DIR = os.path.join(BASE_DIR, "outputs")
if not os.path.exists(OUT_DIR):
    os.mkdir(OUT_DIR)
# 报告保存目录
REPORT_DIR = os.path.join(OUT_DIR, "report")
if not os.path.exists(REPORT_DIR):
    os.mkdir(REPORT_DIR)
# 报日志保存目录
LOG_DIR = os.path.join(OUT_DIR, "log")
if not os.path.exists(LOG_DIR):
    os.mkdir(LOG_DIR)
# 测试用例模块
CASE_DIR = os.path.join(BASE_DIR, "testcases")
# 手动生成测试用例模块
MANUAL_CASE_DIR = os.path.join(CASE_DIR, "test_manual_case")
if not os.path.exists(MANUAL_CASE_DIR):
    os.mkdir(MANUAL_CASE_DIR)
# 自动生成测试用例模块
AUTO_CASE_DIR = os.path.join(CASE_DIR, "test_auto_case")
# YAML用例生成目录
AUTO_CASE_YAML_DIR = os.path.join(AUTO_CASE_DIR, "yaml_case")
# Excel用例生成目录
AUTO_CASE_EXCEL_DIR = os.path.join(AUTO_CASE_DIR, "excel_case")
# Allure报告，测试结果集目录
ALLURE_RESULTS_DIR = os.path.join(REPORT_DIR, "allure_results")
# Allure报告，HTML测试报告目录
ALLURE_HTML_DIR = os.path.join(REPORT_DIR, "allure_html")
# Allure报告，配置文件目录
ALLURE_CONFIG_DIR = os.path.join(LIB_DIR, "allure_config")
