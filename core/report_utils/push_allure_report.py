# -*- coding: utf-8 -*-
# @Author  : 会飞的🐟
# @File    : push_allure_report.py
# @Desc: 推送allure报告到gitlink仓库模块
import os
import shutil
import subprocess
from loguru import logger
from utils.files_utils.files_handle import copy_all_files

"""
subprocess.run: 用于执行系统命令。

 check=True 表示如果命令执行失败会抛出异常。

 -C 参数用于指定Git命令的工作目录。
 
"""


def push_allure_report(allure_report_dir: str, remote_url: str, username: str, password: str, branch: str = "master",
                       message: str = "update report"):
    """
    将本地生成的 Allure HTML 报告推送到指定的 GitLink 仓库。
    :param allure_report_dir : 本地生成的 Allure HTML 报告目录路径。
    :param remote_url:  远程仓库的HTTP地址， 需要带有.git， 例如：https://gitlink.org.cn/floraachy/floraachy.gitlink.net.git。
    :param branch:  远程仓库的分支。
    :param username:  登录远程仓库的用户名。
    :param password:  登录远程仓库的密码。
    :param message: 提交更改的说明信息。
    """
    if remote_url is None or username is None or password is None:
        return "remote_url/username/password error"

    repo_name = remote_url[:-4].split("/")[-1]
    repo_path = os.path.join(os.path.dirname(allure_report_dir), repo_name)
    print(f"本地仓库地址：{repo_path}")
    logger.debug(f"本地仓库地址：{repo_path}")

    try:
        # 检查目录是否存在
        if os.path.exists(repo_path):
            print(f"目录已存在，正在删除: {repo_path}")
            logger.debug(f"目录已存在，正在删除: {repo_path}")
            shutil.rmtree(repo_path)  # 删除目录及其内容

        # 重新创建目录
        os.makedirs(repo_path)
        logger.debug(f"目录已重新创建: {repo_path}")
        print(f"目录已重新创建: {repo_path}")
    except Exception as e:
        logger.error(f"操作失败: {e}")
        print(f"操作失败: {e}")

    try:
        # -------------初始化本地仓库并提交代码 -----------------
        subprocess.run(["git", "-C", repo_path, "init"], check=True)
        print("初始化本地仓库成功")
        logger.debug("初始化本地仓库成功")

        auth_remote_url = f"https://{username}:{password}@{remote_url.split("//")[-1]}"
        print(f"添加远程仓库: {auth_remote_url}")
        logger.debug(f"添加远程仓库: {auth_remote_url}")
        subprocess.run(["git", "-C", repo_path, "remote", "add", "origin", auth_remote_url], check=True)

        print("复制 Allure HTML报告所有文件到本地仓库")
        logger.debug("复制 Allure HTML报告所有文件到本地仓库")
        copy_all_files(src_dir=allure_report_dir, dst_dir=repo_path)

        print("将更改添加到暂存区")
        logger.debug("将更改添加到暂存区")
        subprocess.run(["git", "-C", repo_path, "add", "."], check=True)

        print("提交更改")
        logger.debug("提交更改")
        subprocess.run(["git", "-C", repo_path, "commit", "-m", message], check=True)

        print("强制推送代码")
        logger.debug("强制推送代码")
        subprocess.run(["git", "-C", repo_path, "push", "--force", "origin", branch], check=True)

        print("Allure 报告推送成功！")
        logger.success("Allure 报告推送成功！")
    except subprocess.CalledProcessError as e:
        print(f"Git 操作失败: {e}")
        logger.error(f"Git 操作失败: {e}")
