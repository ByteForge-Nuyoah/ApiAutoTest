# -*- coding: utf-8 -*-
# @Author  : 会飞的🐟
# @File    : loguru_log.py
# @Desc: loguru日志处理模块
import sys
from loguru import logger


def capture_logs(filename, level="TRACE", level_std="INFO", filter_type=None):
    """
    日志处理
    文档参考：https://zhuanlan.zhihu.com/p/429452898
       基本参数释义：
        sink：可以是一个 file 对象，例如 sys.stderr 或 open('file.log', 'w')，也可以是 str 字符串或者 pathlib.Path 对象，即文件路径，也可以是一个方法，可以自行定义输出实现，也可以是一个 logging 模块的 Handler，比如 FileHandler、StreamHandler 等，还可以是 coroutine function，即一个返回协程对象的函数等。
        level：日志输出和保存级别。
        format：日志格式模板。
        filter：一个可选的指令，用于决定每个记录的消息是否应该发送到 sink。
        colorize：格式化消息中包含的颜色标记是否应转换为用于终端着色的 ansi 代码，或以其他方式剥离。 如果没有，则根据 sink 是否为 tty（电传打字机缩写） 自动做出选择。
        serialize：在发送到 sink 之前，是否应首先将记录的消息转换为 JSON 字符串。
        backtrace：格式化的异常跟踪是否应该向上扩展，超出捕获点，以显示生成错误的完整堆栈跟踪。
        diagnose：异常跟踪是否应显示变量值以简化调试。建议在生产环境中设置 False，避免泄露敏感数据。
        enqueue：要记录的消息是否应在到达 sink 之前首先通过多进程安全队列，这在通过多个进程记录到文件时很有用，这样做的好处还在于使日志记录调用是非阻塞的。
        catch：是否应自动捕获 sink 处理日志消息时发生的错误，如果为 True，则会在 sys.stderr 上显示异常消息，但该异常不会传播到 sink，从而防止应用程序崩溃。
        kwargs：仅对配置协程或文件接收器有效的附加参数

       日志级别，从低到高：
       logger.trace()   等级5
       logger.debug()   等级10
       logger.info()   等级20
       logger.success()   等级25
       logger.warning()   等级30
       logger.error()   等级40
       logger.critical()   等级50
    :param filename: 日志文件名
    :param filter_type: 日志过滤，如：将日志级别为ERROR的单独记录到一个文件中
    :param level: 日志级别设置
    :param level_std: 控制台输出日志级别设置
    """
    if level.upper() in ["TRACE", "DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL"]:
        level = level
    else:
        logger.error(f"level={level}, 值错误\n"
                     f"level的可选值是：TRACE DEBUG INFO SUCCESS WARNING ERROR  CRITICAL\n"
                     f"将默认level=trace收集日志")
        level = "TRACE"

    logger.remove()  # 清除之前的设置
    dic = dict(sink=filename,  # 日志保存路径
               rotation='10 MB',
               retention='3 days',
               format="{time:YYYY-MM-DD HH:mm:ss} | {level} | From {module}.{function}.{line} : {message}",  # 日志输出格式
               encoding='utf-8',
               level=level,  # 日志级别设置
               enqueue=True
               )
    if filter_type:
        dic["filter"] = lambda x: filter_type in str(x['level']).upper()

    logger.add(**dic)
    # 添加控制台输出
    logger.add(sink=sys.stderr,
               level=level_std,
               format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>From {module}.{function}.{line}</cyan> : <level>{message}</level>",
               colorize=True)
