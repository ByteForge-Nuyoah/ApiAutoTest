# -*- coding: utf-8 -*-
# @Author  : 会飞的🐟
# @File    : get_results_handle.py
# @Desc: 获取allure测试报告中的测试结果模块

import os
import json
from loguru import logger
from utils.tools.time_handle import timestamp_strftime


def get_test_results_from_from_allure_report(allure_html_path):
    """
    从allure生成的html报告的summary.json中，获取测试结果及测试情况
    :param allure_html_path: allure生成的html报告的绝对路径
    """
    try:
        summary_json_path = os.path.join(allure_html_path, "widgets", "summary.json")
        with open(summary_json_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        case_count = data['statistic']
        _time = data['time']
        logger.trace(f"获取到的data是：{data}")
        logger.trace(f"获取到的_time是：{data['time']}")
        logger.trace(f"获取到的start是：{_time['start']}")
        keep_keys = {"passed", "failed", "broken", "skipped", "total"}
        test_results = {k: v for k, v in data['statistic'].items() if k in keep_keys}
        # 判断运行用例总数大于0
        if case_count["total"] > 0:
            # 计算用例成功率
            test_results["pass_rate"] = round(
                (case_count["passed"] + case_count["skipped"]) / case_count["total"] * 100, 2
            )
        else:
            # 如果未运行用例，则成功率为 0.0
            test_results["pass_rate"] = 0.0

        # 收集用例运行时长
        test_results['run_time'] = _time if test_results['total'] == 0 else round(_time['duration'] / 1000, 2)
        test_results["start_time"] = timestamp_strftime(_time["start"])
        test_results["stop_time"] = timestamp_strftime(_time["stop"])

        # 收集重试次数
        retry_trend_json_path = os.path.join(allure_html_path, "widgets", "retry-trend.json")
        with open(retry_trend_json_path, 'r', encoding='utf-8') as file:
            retry_data = json.load(file)
        test_results["rerun"] = retry_data[0]["data"]["retry"]
        # 项目环境
        env_json_path = os.path.join(allure_html_path, "widgets", "environment.json")
        with open(env_json_path, 'r', encoding='utf-8') as file:
            env_data = json.load(file)
        for data in env_data:
            test_results[data['name']] = data["values"][0]
        logger.trace(f"获取到的测试结果：{test_results}")
        return test_results
    except FileNotFoundError as e:
        logger.error(f"程序中检查到您未生成allure报告，通常可能导致的原因是allure环境未配置正确，{e}")
        raise FileNotFoundError(
            "程序中检查到您未生成allure报告，"
            "通常可能导致的原因是allure环境未配置正确，"
        ) from e
