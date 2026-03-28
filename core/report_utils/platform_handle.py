# -*- coding: utf-8 -*-
# @Author  : 会飞的🐟
# @File    : platform_handle.py
# @Desc: 平台相关处理模块

import os.path
import platform
import subprocess
from config.settings import LIB_DIR


class PlatformHandle:
    """跨平台的支持allure, webdriver"""

    @property
    def allure(self):
        # 过滤掉 allure_config 目录，只查找 allure 安装包目录
        allure_dirs = [i for i in os.listdir(LIB_DIR) if i.startswith("allure") and i != "allure_config"]
        if not allure_dirs:
            raise FileNotFoundError(f"在 {LIB_DIR} 下未找到 allure 安装目录")
            
        allure_bin = os.path.join(LIB_DIR, allure_dirs[0], "bin")
        if platform.system() == "Windows":
            allure_path = os.path.join(allure_bin, "allure.bat")
        else:
            allure_path = os.path.join(allure_bin, "allure")
            # os.popen(f"chmod +x {allure_path}").read()
            cmd = f"chmod +x {allure_path}"
            try:
                # subprocess.run 会等待命令执行完成
                result = subprocess.run(
                    cmd.split(),  # 将字符串命令拆分为列表
                    shell=False,  # 不允许字符串命令
                    stdout=subprocess.PIPE,  # 捕获标准输出
                    stderr=subprocess.PIPE,  # 捕获错误输出
                    text=True  # 输出为字符串（而不是字节）
                )
                # print(f"执行命令[chmod +x {allure_path}]：{result.stdout}")  # 正常日志
                if result.stderr:
                    print(f"⚠️ 执行命令[chmod +x {allure_path}]时有警告/错误：{result.stderr}")
            except subprocess.CalledProcessError as e:
                print(f"❌ 执行命令[chmod +x {allure_path}] 失败！")
                print("命令:", e.cmd)
                print("返回码:", e.returncode)
                print("错误输出:", e.stderr)
                raise  # 把异常抛出去，外层能感知失败
        return allure_path


if __name__ == '__main__':
    res = PlatformHandle().allure
    print(res)
