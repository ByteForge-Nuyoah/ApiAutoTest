# -*- coding: utf-8 -*-
# @Author  : 会飞的🐟
# @File    : run.py
# @Desc: 测试用例执行主程序
import os
import sys
import time
import click
import shutil
import pytest
import subprocess
from pathlib import Path
from loguru import logger
from datetime import datetime
from utils.tools.schedule_task import start_schedule
from utils.logger_utils.loguru_log import capture_logs
from utils.files_utils.files_handle import load_yaml_file
from core.report_utils.send_result_handle import send_result
from core.report_utils.platform_handle import PlatformHandle
from core.report_utils.allure_handle import generate_allure_report
from core.case_generate_utils.case_fun_generate import generate_cases, generate_cases_for_projects, generate_cases_for_project
from config.settings import LOG_LEVEL, GLOBAL_VARS, REPORT, RERUN, RERUN_DELAY, MAX_FAIL, LOG_LEVEL_STD
from config.settings import BASE_DIR, REPORT_DIR, LOG_DIR, ENV_DIR, ALLURE_RESULTS_DIR, ALLURE_HTML_DIR, AUTO_CASE_DIR, \
    ALLURE_CONFIG_DIR, PROJECT_DIR

# 主函数
@click.command()
@click.option("-report", default="yes", help="是否生成allure html report，支持如下类型：yes, no")
@click.option("-env", default="test", help="输入运行环境：test 或 live")
@click.option("-m", default=None, help="选择需要运行的用例：python.ini配置的名称")
@click.option("-cron", default=False, is_flag=True, help="是否开启定时任务")
@click.option("-project", default=None, help="指定运行的项目名称，多个项目用逗号分隔，不指定则运行所有项目")
def run(env, m, report, cron, project):
    if cron:
        start_schedule()
        return

    try:
        # ------------------------ 捕获日志----------------------------
        capture_logs(level=LOG_LEVEL, level_std=LOG_LEVEL_STD, filename=os.path.join(LOG_DIR, "api.log"))
        logger.info(f"""\n\n ============接口自动化测试开始{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}=============""")
        # ------------------------ 处理一下获取到的参数----------------------------
        # # 根据指定的环境参数，将运行环境所需相关配置数据保存到GLOBAL_VARS
        env_path = os.path.join(ENV_DIR, f"{env}.yml")
        if not os.path.exists(env_path):
             env_path = os.path.join(ENV_DIR, f"{env}.yaml")
             
        if not os.path.exists(env_path):
            raise FileNotFoundError(f"Environment configuration file not found for: {env}")
            
        __env = load_yaml_file(env_path)
        GLOBAL_VARS.update(__env)
        # ------------------------ 自动生成测试用例 ------------------------
        # 删除原有的测试用例，以便生成新的测试用例
        if os.path.exists(AUTO_CASE_DIR):
            shutil.rmtree(AUTO_CASE_DIR)

        # 根据项目参数生成测试用例
        if project:
            # 指定项目运行
            project_names = [p.strip() for p in project.split(",")]
            generate_cases_for_projects(project_names)
        elif os.path.exists(PROJECT_DIR) and os.listdir(PROJECT_DIR):
            # 多项目模式：扫描项目目录
            generate_cases_for_projects()
        else:
            # 单项目模式：使用原有逻辑
            generate_cases()

        # ------------------------ 设置pytest相关参数 ------------------------
        arg_list = [f"--maxfail={MAX_FAIL}", f"--reruns={RERUN}",
                    f"--reruns-delay={RERUN_DELAY}", f'--alluredir={ALLURE_RESULTS_DIR}',
                    '--clean-alluredir', f'--env={env}']
        if m:
            arg_list.append(f"-m {m}")

        # ------------------------ pytest执行测试用例 ------------------------
        pytest.main(args=arg_list)
        # ------------------------ 生成测试报告 ------------------------
        if report == "yes":
            # 仅生成最新的报告，不保留历史记录
            _ALLURE_HTML_DIR = ALLURE_HTML_DIR
            
            # 如果目录存在，先删除，确保只保留最新的
            if os.path.exists(_ALLURE_HTML_DIR):
                shutil.rmtree(_ALLURE_HTML_DIR)

            # print("ALLURE HTML DIR: {}".format(_ALLURE_HTML_DIR))
            report_path, attachment_path = generate_allure_report(allure_results=ALLURE_RESULTS_DIR,
                                                                  allure_report=_ALLURE_HTML_DIR,
                                                                  windows_title=REPORT["项目名称"],
                                                                  report_name=REPORT["报告标题"],
                                                                  env_info={
                                                                      "运行环境": GLOBAL_VARS.get("host", None)},
                                                                  allure_config_path=ALLURE_CONFIG_DIR,
                                                                  attachment_path=os.path.join(REPORT_DIR,
                                                                                               f'allure_report.zip'))
            # -----------------拼接测试报告地址，用于流水线运行，不需要的可忽略--------------------
            sub_path = Path(_ALLURE_HTML_DIR).relative_to(Path(os.path.dirname(BASE_DIR)))
            new_sub_path = os.path.normpath(sub_path).replace('\\', '/')
            # 从系统环境变量NGINX获取其值作为nginx地址，拼接allure html报告地址并输出
            if os.environ.get("NGINX"):
                logger.debug(f"系统环境变量NGINX={os.environ.get('NGINX'):}")
                url = os.environ.get("NGINX")[0:len(os.environ.get("NGINX")) - 1] if os.environ.get("NGINX").endswith(
                    "/") else os.environ.get("NGINX")
                print(f'测试报告地址：{url}/{new_sub_path}')
            # ------------------------ 发送测试结果 ------------------------

            send_result(report_info=REPORT, report_path=report_path, attachment_path=attachment_path)

            # ------------------------ 自动打开并关闭报告 ------------------------
            logger.info("正在打开Allure报告...")
            try:
                allure_cmd = PlatformHandle().allure
                # allure open command
                cmd = [allure_cmd, "open", report_path]
                # Start the process without waiting
                proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                # Wait for 20 seconds
                time.sleep(20)
                # Terminate the process
                proc.terminate()
                # Wait for process to terminate to avoid zombie process
                proc.wait()
                logger.info("Allure报告已关闭")
            except Exception as e:
                logger.error(f"打开或关闭Allure报告时发生错误: {e}")
    except Exception as e:
        raise e


if __name__ == "__main__":
    run()