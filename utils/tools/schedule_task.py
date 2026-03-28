# -*- coding: utf-8 -*-
# @Author  : 会飞的🐟
# @File    : schedule_task.py
# @Desc: 定时任务调度器

import sys
import time
import schedule
import subprocess
from loguru import logger
from config.settings import SCHEDULE_CONFIG


def run_task(command_args):
    """
    执行测试任务
    :param command_args: 传递给 run.py 的参数列表
    """
    logger.info(f"开始执行定时任务，执行命令: {' '.join(command_args)}")
    try:
        cmd = [sys.executable, "run.py"] + command_args
        subprocess.run(cmd, check=True)
        logger.info("定时任务执行完成")
    except subprocess.CalledProcessError as e:
        logger.error(f"定时任务执行失败: {e}")
    except Exception as e:
        logger.error(f"定时任务执行出现异常: {e}")


def build_command_args():
    """
    根据配置构建命令行参数
    :return: 命令行参数列表
    """
    args = []
    
    if SCHEDULE_CONFIG.get("env"):
        args.extend(["-env", SCHEDULE_CONFIG["env"]])
    
    if SCHEDULE_CONFIG.get("report"):
        args.extend(["-report", SCHEDULE_CONFIG["report"]])
    
    if SCHEDULE_CONFIG.get("markers"):
        args.extend(["-m", SCHEDULE_CONFIG["markers"]])
    
    return args


def start_schedule():
    """
    开启定时任务
    从 settings.py 读取配置
    """
    if not SCHEDULE_CONFIG.get("enabled", False):
        logger.warning("定时任务未启用，请在 config/settings.py 中设置 SCHEDULE_CONFIG['enabled'] = True")
        return
    
    run_time = SCHEDULE_CONFIG.get("run_time", "22:00")
    command_args = build_command_args()
    
    logger.info(f"定时任务已启用")
    logger.info(f"运行时间: 每天 {run_time}")
    logger.info(f"运行环境: {SCHEDULE_CONFIG.get('env', 'test')}")
    logger.info(f"生成报告: {SCHEDULE_CONFIG.get('report', 'yes')}")
    if SCHEDULE_CONFIG.get("markers"):
        logger.info(f"运行标记: {SCHEDULE_CONFIG['markers']}")
    
    schedule.every().day.at(run_time).do(run_task, command_args)
    
    logger.info(f"定时任务调度器已启动，等待执行...")
    
    while True:
        try:
            schedule.run_pending()
            time.sleep(60)
        except KeyboardInterrupt:
            logger.info("收到中断信号，停止定时任务调度器")
            break
        except Exception as e:
            logger.error(f"定时任务调度器运行异常: {e}")
            time.sleep(60)


if __name__ == "__main__":
    start_schedule()
