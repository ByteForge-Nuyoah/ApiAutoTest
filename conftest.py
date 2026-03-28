# -*- coding: utf-8 -*-
# @Author  : 会飞的🐟
# @File    : conftest.py
# @Desc: 全局配置文件

import time
import os
import pytest
from datetime import datetime
from loguru import logger
from config.settings import REPORT_DIR, CUSTOM_MARKERS, ENV_DIR, GLOBAL_VARS, DATA_CLEANUP_CONFIG, MOCK_CONFIG
from utils.files_utils.files_handle import load_yaml_file
from utils.database_utils.data_cleanup import get_cleanup_manager
from utils.tools.failure_snapshot import get_snapshot_manager, capture_failure
from utils.tools.exception_handler import handle_exception
from utils.tools.mock_service import get_mock_service, MockMode


def is_xdist_master(config):
    """
    判断是否是 xdist 主进程
    :param config: pytest config 对象
    :return: True 表示是主进程
    """
    has_xdist = hasattr(config, "workerinput")
    return not has_xdist


# ------------------------------------- START: pytest钩子函数处理---------------------------------------#
def pytest_addoption(parser):
    """
    注册自定义命令行参数
    """
    parser.addoption("--env", action="store", default="test", help="run env: test or live")
    parser.addoption("--cleanup", action="store", default="auto", help="cleanup mode: auto, manual, skip")
    parser.addoption("--snapshot", action="store", default="on", help="failure snapshot: on, off")
    parser.addoption("--mock", action="store", default=None, help="mock mode: disabled, stub, record, replay, mixed")


def pytest_configure(config):
    """
    1. 加载环境配置到全局变量
    2. 注册自定义标记
    3. 初始化数据清理管理器
    4. 初始化 Mock 服务
    """
    # 判断是否是主进程
    is_master = is_xdist_master(config)
    
    # 加载环境配置
    env = config.getoption("--env")
    if env:
        env_path = os.path.join(ENV_DIR, f"{env}.yml")
        if not os.path.exists(env_path):
            env_path = os.path.join(ENV_DIR, f"{env}.yaml")
        
        if os.path.exists(env_path):
            if is_master:
                logger.info(f"Loading environment config from: {env_path}")
            __env = load_yaml_file(env_path)
            GLOBAL_VARS.update(__env)
        else:
            if is_master:
                logger.warning(f"Environment config file not found: {env}")

    # 注册自定义标记
    if is_master:
        logger.debug(f"需要注册的标记：{CUSTOM_MARKERS}")
    # 对标记进行去重处理
    unique_markers = []
    for item in CUSTOM_MARKERS:
        if item not in unique_markers:
            unique_markers.append(item)
    # 注册标记
    for custom_marker in unique_markers:
        if isinstance(custom_marker, str):
            config.addinivalue_line('markers', f'{custom_marker}')
        elif isinstance(custom_marker, dict):
            for k, v in custom_marker.items():
                config.addinivalue_line('markers', f'{k}:{v}')

    # 初始化数据清理管理器
    _init_cleanup_manager(is_master)
    
    # 初始化 Mock 服务
    _init_mock_service(config, is_master)


def _init_cleanup_manager(is_master=True):
    """
    初始化数据清理管理器
    根据配置注册数据库连接
    :param is_master: 是否是主进程
    """
    if not DATA_CLEANUP_CONFIG.get("enabled", False):
        if is_master:
            logger.debug("数据清理功能未启用")
        return
    
    cleanup_manager = get_cleanup_manager()
    db_configs = DATA_CLEANUP_CONFIG.get("databases", {})
    
    for db_name, db_config in db_configs.items():
        try:
            cleanup_manager.register_db(db_name, db_config)
        except Exception as e:
            logger.error(f"数据库连接注册失败: {db_name}, 错误: {e}")


def _init_mock_service(config, is_master=True):
    """
    初始化 Mock 服务
    根据命令行参数或配置设置 Mock 模式
    :param config: pytest config 对象
    :param is_master: 是否是主进程
    """
    mock_mode_str = config.getoption("--mock")
    
    if mock_mode_str is None:
        mock_mode_str = MOCK_CONFIG.get("mode", "disabled")
    
    if mock_mode_str == "disabled":
        if is_master:
            logger.debug("Mock 服务未启用")
        return
    
    try:
        mock_mode = MockMode(mock_mode_str)
    except ValueError:
        logger.error(f"无效的 Mock 模式: {mock_mode_str}")
        return
    
    mock_service = get_mock_service(mock_mode)
    mock_service.enable()
    
    if MOCK_CONFIG.get("auto_save", True):
        recordings_dir = MOCK_CONFIG.get("recordings_dir")
        if recordings_dir:
            os.makedirs(recordings_dir, exist_ok=True)
            recordings_file = os.path.join(recordings_dir, "mock_recordings.json")
            if mock_mode in [MockMode.REPLAY, MockMode.MIXED]:
                mock_service.load_recordings(recordings_file)
    
    logger.info(f"Mock 服务已启用，模式: {mock_mode.value}")


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    测试执行结果钩子
    在测试失败时自动捕获快照
    """
    outcome = yield
    report = outcome.get_result()
    
    if report.when == "call" and report.failed:
        snapshot_mode = item.config.getoption("--snapshot")
        if snapshot_mode == "on":
            _capture_failure_snapshot(item, call, report)


def _capture_failure_snapshot(item, call, report):
    """
    捕获失败快照
    :param item: 测试项
    :param call: 调用信息
    :param report: 测试报告
    """
    try:
        test_id = item.nodeid
        test_name = item.name
        
        exception = call.excinfo.value if call.excinfo else Exception("Unknown error")
        
        snapshot = capture_failure(
            test_id=test_id,
            test_name=test_name,
            exception=exception
        )
        
        if hasattr(item, 'funcargs'):
            if 'request_info' in item.funcargs:
                snapshot.set_request_info(**item.funcargs['request_info'])
            if 'response_info' in item.funcargs:
                snapshot.set_response_info(**item.funcargs['response_info'])
        
        snapshot.add_log(f"测试失败: {report.failure_message}")
        
        snapshot.save_to_file(os.path.join(REPORT_DIR, "failure_snapshots"))
        
        logger.error(
            f"\n{'='*60}\n"
            f"测试失败快照\n"
            f"测试ID: {test_id}\n"
            f"测试名称: {test_name}\n"
            f"失败原因: {str(exception)}\n"
            f"{'='*60}"
        )
    except Exception as e:
        logger.error(f"捕获失败快照时发生错误: {e}")


def pytest_sessionfinish(session, exitstatus):
    """
    测试会话结束时执行
    执行所有注册的清理任务
    保存 Mock 记录
    """
    # 只在主进程执行
    if not is_xdist_master(session.config):
        return
    
    cleanup_mode = session.config.getoption("--cleanup")
    
    if cleanup_mode == "skip":
        logger.info("跳过数据清理")
    elif cleanup_mode in ["auto", "manual"]:
        cleanup_manager = get_cleanup_manager()
        cleanup_manager.cleanup_all()
        cleanup_manager.close_all()
        logger.info("数据清理完成")
    
    snapshot_manager = get_snapshot_manager()
    if snapshot_manager._snapshots:
        snapshot_manager.save_all()
        summary = snapshot_manager.get_summary()
        logger.info(f"失败快照统计: {summary['total_snapshots']} 个")
    
    mock_service = get_mock_service()
    if mock_service.enabled and mock_service.mode in [MockMode.RECORD, MockMode.MIXED]:
        if MOCK_CONFIG.get("auto_save", True):
            recordings_dir = MOCK_CONFIG.get("recordings_dir")
            if recordings_dir:
                os.makedirs(recordings_dir, exist_ok=True)
                recordings_file = os.path.join(recordings_dir, "mock_recordings.json")
                mock_service.save_recordings(recordings_file)
                logger.info(f"Mock 记录已保存: {recordings_file}")


@pytest.fixture(scope="session")
def cleanup_manager():
    """
    数据清理管理器 fixture
    :return: DataCleanupManager 实例
    """
    return get_cleanup_manager()


@pytest.fixture(scope="session")
def mock_service():
    """
    Mock 服务 fixture
    :return: MockService 实例
    """
    return get_mock_service()


@pytest.fixture(scope="function")
def mock_rule(mock_service):
    """
    Mock 规则 fixture
    用于动态添加 Mock 规则
    :param mock_service: Mock 服务实例
    :return: 添加规则的函数
    """
    added_rules = []
    
    def add_rule(
        name: str,
        url_pattern: str,
        response: any,
        method: str = None,
        status_code: int = 200,
        delay: float = 0.0
    ):
        """
        添加 Mock 规则
        :param name: 规则名称
        :param url_pattern: URL 匹配模式
        :param response: 响应内容
        :param method: 请求方法
        :param status_code: 状态码
        :param delay: 延迟时间
        """
        rule = mock_service.add_stub(
            name=name,
            url_pattern=url_pattern,
            response=response,
            method=method,
            status_code=status_code,
            delay=delay
        )
        added_rules.append(name)
        return rule
    
    yield add_rule
    
    for rule_name in added_rules:
        mock_service.remove_rule(rule_name)


@pytest.fixture(scope="function")
def data_cleanup(request, cleanup_manager):
    """
    数据清理 fixture
    用于单个测试用例的数据准备和清理
    :param request: pytest request 对象
    :param cleanup_manager: 数据清理管理器
    :return: 数据清理管理器实例
    """
    test_id = request.node.nodeid
    
    yield cleanup_manager
    
    cleanup_mode = request.config.getoption("--cleanup")
    if cleanup_mode == "auto":
        cleanup_manager.execute_cleanup(test_id)


@pytest.fixture(scope="function")
def db_snapshot(cleanup_manager):
    """
    数据库快照 fixture
    用于创建和恢复数据库快照
    :param cleanup_manager: 数据清理管理器
    :return: 快照管理函数
    """
    snapshots = []
    
    def create_snapshot(db_name: str, table: str, condition: str = None):
        """
        创建快照
        :param db_name: 数据库名称
        :param table: 表名
        :param condition: 查询条件
        """
        data = cleanup_manager.snapshot_table(db_name, table, condition)
        snapshots.append((db_name, table))
        return data
    
    yield create_snapshot
    
    for db_name, table in snapshots:
        cleanup_manager.restore_table(db_name, table)


@pytest.fixture(scope="function")
def failure_tracker(request):
    """
    失败追踪 fixture
    用于手动记录失败信息
    :param request: pytest request 对象
    :return: 追踪函数
    """
    tracker_info = {
        "test_id": request.node.nodeid,
        "test_name": request.node.name,
        "logs": [],
        "context": {}
    }
    
    def add_log(message: str):
        """
        添加日志
        :param message: 日志消息
        """
        tracker_info["logs"].append({
            "timestamp": datetime.now().isoformat(),
            "message": message
        })
    
    def set_context(key: str, value):
        """
        设置上下文
        :param key: 键
        :param value: 值
        """
        tracker_info["context"][key] = value
    
    def get_info():
        """
        获取追踪信息
        :return: 追踪信息字典
        """
        return tracker_info
    
    yield {
        "add_log": add_log,
        "set_context": set_context,
        "get_info": get_info
    }


def pytest_terminal_summary(terminalreporter, config):
    """
    收集测试结果
    """
    # 只在主进程执行
    if not is_xdist_master(config):
        return

    _RERUN = len([i for i in terminalreporter.stats.get('rerun', []) if i.when != 'teardown'])
    try:
        # 获取pytest传参--reruns的值
        reruns_value = int(config.getoption("--reruns"))
        _RERUN = int(_RERUN / reruns_value)
    except Exception:
        reruns_value = "未配置--reruns参数"
        _RERUN = len([i for i in terminalreporter.stats.get('rerun', []) if i.when != 'teardown'])

    _PASSED = len([i for i in terminalreporter.stats.get('passed', []) if i.when != 'teardown'])
    _ERROR = len([i for i in terminalreporter.stats.get('error', []) if i.when != 'teardown'])
    _FAILED = len([i for i in terminalreporter.stats.get('failed', []) if i.when != 'teardown'])
    _SKIPPED = len([i for i in terminalreporter.stats.get('skipped', []) if i.when != 'teardown'])
    _XPASSED = len([i for i in terminalreporter.stats.get('xpassed', []) if i.when != 'teardown'])
    _XFAILED = len([i for i in terminalreporter.stats.get('xfailed', []) if i.when != 'teardown'])
    _DESELECTED = len(terminalreporter.stats.get('deselected', []))
    deselected_cases = "\n".join(list(map(str, terminalreporter.stats.get("deselected", []))))

    _TOTAL = _PASSED + _ERROR + _FAILED + _SKIPPED + _XPASSED + _XFAILED + _DESELECTED

    # 兼容处理开始时间
    _sessionstarttime = getattr(config, "_sessionstarttime", time.time())

    _DURATION = time.time() - _sessionstarttime

    session_start_time = datetime.fromtimestamp(_sessionstarttime)
    _START_TIME = f"{session_start_time.year}年{session_start_time.month}月{session_start_time.day}日 " \
                  f"{session_start_time.hour}:{session_start_time.minute}:{session_start_time.second}"

    test_info = f"各位同事, 大家好:\n" \
                f"自动化用例于 {_START_TIME}- 开始运行，运行时长：{_DURATION:.2f} s， 目前已执行完成。\n" \
                f"--------------------------------------\n" \
                f"#### 执行结果如下:\n" \
                f"- 测试用例总数: {_TOTAL} 个\n" \
                f"- 跳过用例个数（skipped+deselected）: {_SKIPPED + _DESELECTED} 个\n" \
                f"- 实际执行用例总数: {_PASSED + _FAILED + _XPASSED + _XFAILED} 个\n" \
                f"--------------------------------------------------------------\n" \
                f"- 通过用例个数（passed）: {_PASSED} 个\n" \
                f"- 失败用例个数（failed）: {_FAILED} 个\n" \
                f"- 异常用例个数（error）: {_ERROR} 个\n" \
                f"- 重跑的用例数(--reruns的值): {_RERUN} 个 ({reruns_value})\n" \
                f"--------------------------------------------------------------\n" \
                f"- 忽略(deselected)的用例:\n{deselected_cases}\n" \
                f"--------------------------------------------------------------\n"

    try:
        _RATE = (_PASSED + _XPASSED) / (_PASSED + _FAILED + _XPASSED + _XFAILED) * 100
        test_result = f"- 用例成功率: {_RATE:.2f} %\n"
        logger.success(f"{test_info}{test_result}")
    except ZeroDivisionError:
        test_result = "- 用例成功率: 0.00 %\n"
        logger.critical(f"{test_info}{test_result}")

    # 这里是方便在流水线里面发送测试结果到钉钉/企业微信的
    with open(file=os.path.join(REPORT_DIR, "test_result.txt"), mode="w", encoding="utf-8") as f:
        f.write(f"{test_info}{test_result}")

# ------------------------------------- END: pytest钩子函数处理---------------------------------------#
