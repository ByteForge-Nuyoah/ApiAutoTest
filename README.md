# API 自动化测试框架

## 一、框架介绍
本框架是基于 Python + Pytest + Allure + Loguru 实现的接口自动化测试框架，支持 YAML/Excel 用例管理、多环境切换、多项目复用、以及丰富的通知机制。

## 二、核心功能

*   **配置分离与安全管理**
    *   使用 `.env` 文件统一管理账号、密码、密钥等敏感信息
    *   支持多项目/多环境配置 (`config/*.yaml`)，通过 `${VAR}` 动态引用环境变量
*   **多源用例生成与隔离**
    *   支持同时从 YAML 和 Excel 生成测试用例
    *   生成隔离: YAML 用例生成至 `testcases/test_auto_case/yaml_case/`，Excel 用例生成至 `testcases/test_auto_case/excel_case/`
    *   文件命名规范：Excel 用例生成文件名格式为 `test_excel_<文件名>.py`
*   **多项目与多环境支持**
    *   通过 `-env <project_name>` 参数一键切换项目/环境配置
*   **其他特性**
    *   Session 会话自动关联
    *   动态参数提取与依赖注入 (JSONPath/Regex)
    *   Allure 定制化报告
    *   Loguru 优雅日志
    *   多渠道通知 (邮件/钉钉/企业微信)
    *   Docker 容器化支持
    *   GitHub Actions CI 集成

## 三、项目结构

```text
ApiAutotest/
├── .github/                 # GitHub Actions CI 配置
│   └── workflows/
│       └── ci.yaml          # CI/CD 流水线配置
├── config/                  # 配置文件目录
│   ├── settings.py          # 全局配置文件
│   ├── test.yaml            # 测试环境配置
│   └── prod.yaml            # 生产/正式环境配置
├── core/                    # 核心逻辑目录
│   ├── assertion_utils/     # 断言工具
│   ├── case_generate_utils/ # 用例自动生成工具
│   ├── data_utils/          # 数据处理工具
│   ├── report_utils/        # 报告生成与发送工具
│   └── requests_utils/      # 请求封装工具
├── files/                   # 测试数据文件 (上传下载等)
├── interfaces/              # 接口定义目录 (YAML/Excel 用例源文件)
│   └── projects/            # 按项目分类的接口定义
├── lib/                     # 第三方库或工具 (如 Allure 命令行工具)
├── outputs/                 # 输出产物目录
│   ├── logs/                # 运行日志
│   └── report/              # 测试报告
├── testcases/               # 测试用例目录
│   ├── test_auto_case/      # 自动生成的测试用例
│   │   ├── excel_case/      # Excel 生成的用例
│   │   └── yaml_case/       # YAML 生成的用例
│   └── test_manual_case/    # 手动编写的测试用例
├── utils/                   # 通用工具类
├── .dockerignore            # Docker 构建忽略文件
├── .env                     # 环境变量配置文件 (敏感信息)
├── .env.example             # 环境变量示例文件
├── .gitignore               # Git 忽略文件配置
├── conftest.py              # Pytest 全局配置钩子
├── Dockerfile               # Docker 镜像构建文件
├── pytest.ini               # Pytest 配置文件
├── requirements.txt         # 项目依赖文件
└── run.py                   # 项目启动入口
```

## 四、快速开始

### 1. 安装依赖（推荐使用虚拟环境）
macOS 环境的系统 Python 受外部管理，建议使用虚拟环境隔离依赖：
```bash
# 创建并启用虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境 (.env)
复制模板文件并配置您的敏感信息：
```bash
cp .env.example .env
```
在 `.env` 中填入真实的数据库密码、API Key 等信息：
```properties
# .env 示例
TEST_DB_HOST=127.0.0.1
TEST_DB_PWD=secret_password
DEMO_HOST=https://demo.api.com
```

### 3. 配置项目 (config/*.yaml / *.yml)
在 `config/` 目录下创建项目配置文件（如 `prod.yaml` 或 `test.yaml`），支持引用 `.env` 变量：
```yaml
# config/prod.yaml
host: ${PROD_HOST}
username: "admin"
db_info:
  db_host: ${PROD_DB_HOST}
```

### 4. 运行测试
```bash
# 运行默认测试环境（已激活虚拟环境）
python3 run.py

# 或未激活时使用虚拟环境中的解释器
./venv/bin/python3 run.py
```

## 五、运行参数与方式

本项目统一通过 `run.py` 入口文件执行测试，支持多种参数组合以满足不同场景需求。

### 1. 命令行参数说明
| 参数 | 缩写 | 默认值 | 说明 | 示例 |
| :--- | :--- | :--- | :--- | :--- |
| `--env` | `-env` | `test` | 指定运行环境，对应 `config/{env}.yaml` 配置文件 | `python3 run.py -env live` |
| `--m` | `-m` | `None` | 运行指定标记 (Marker) 的用例 | `python3 run.py -m smoke` |
| `--report` | `-report` | `yes` | 是否生成 Allure HTML 报告 (yes/no) | `python3 run.py -report no` |
| `--cron` | `-cron` | `False` | 是否开启定时任务模式 | `python3 run.py -cron` |
| `--project` | `-project` | `None` | 指定运行的项目名称，多个项目用逗号分隔 | `python3 run.py -project workspace` |

### 2. 常见运行场景

**场景一：切换测试环境**
```bash
# 运行 live 环境 (加载 config/live.yaml)
python3 run.py -env live
```

**场景二：只运行冒烟测试用例**
```bash
# 仅运行被标记为 smoke 的用例
python3 run.py -m smoke

# 运行 login 标记的用例
python3 run.py -m login

# 运行 auto 标记的用例
python3 run.py -m auto

# 运行 excel_case 标记的用例
python3 run.py -m excel_case
```

**场景三：CI/CD 流水线集成**
```bash
# 在流水线中通常不需要本地生成 HTML 报告
python3 run.py -env test -report no
```

**场景四：开启定时任务**
```bash
# 启动定时任务调度器（按配置文件中的时间运行）
python3 run.py -cron

# 后台运行（推荐用于服务器）
nohup python3 run.py -cron > outputs/logs/schedule.log 2>&1 &

# 使用 screen 后台运行
screen -dmS autotest python3 run.py -cron
```

**定时任务配置**（`config/settings.py`）：
```python
SCHEDULE_CONFIG = {
    "enabled": True,       # 是否启用定时任务
    "run_time": "22:00",   # 每天运行时间（24小时制）
    "env": "test",         # 运行环境
    "report": "yes",       # 是否生成报告
    "markers": None,       # 运行指定标记的用例（None 表示运行全部）
}
```

### 3. Pytest 与 Allure 参数说明

**用例创建原则：**
- 测试文件名必须以 `test` 开头
- 测试函数必须以 `test` 开头

**Pytest 相关参数**（可在 `pytest.ini` 中配置）：

| 参数 | 说明 |
|------|------|
| `--reruns` | 失败重跑次数 |
| `--reruns-delay` | 失败重跑间隔时间 |
| `--count` | 重复执行次数 |
| `-v` | 显示错误位置以及错误的详细信息 |
| `-s` | 等价于 `pytest --capture=no`，可以捕获 print 函数的输出 |
| `-q` | 简化输出信息 |
| `-m` | 运行指定标签的测试用例 |
| `-x` | 一旦错误，则停止运行 |
| `--cache-clear` | 清除 pytest 的缓存 |
| `--maxfail` | 设置最大失败次数，超出阈值则停止执行 |

**Allure 相关参数：**

| 参数 | 说明 |
|------|------|
| `--alluredir` | 指定存储测试结果的路径 |
| `--clean-alluredir` | 清除之前的测试结果 |
| `--allure-no-capture` | 禁用自动捕获 stdout/stderr/log 到报告（推荐开启，报告更简洁） |

## 六、用例编写指南

### 1. 目录结构
```text
interfaces/
  ├── project_a/         # 项目 A 的接口定义
  │     ├── test_login.yaml
  │     └── test_pay.xlsx
  └── project_b/         # 项目 B 的接口定义
        └── test_order.yaml
```

### 2. YAML 用例示例
文件名必须以 `test_` 开头（如 `test_demo.yaml`）。

```yaml
case_common:
  allure_epic: 电商平台          # Allure 报告的一级目录
  allure_feature: 用户管理模块    # Allure 报告的二级目录
  allure_story: 用户登录与验证    # Allure 报告的三级目录
  case_markers: ['smoke', 'p0'] # Pytest 标记

case_info:
  # 场景一：登录并提取 Token
  - id: login_01
    title: 用户登录
    url: /api/user/login
    method: POST
    headers:
      Content-Type: application/json
    payload:
      username: ${username}      # 引用全局变量/环境变量
      password: ${password}
    # 数据提取：从响应中提取数据供后续使用
    extract:
      token: $.data.token        # 使用 JSONPath 提取 token
      user_id: $.data.id         # 提取用户 ID
    # 响应断言
    assert_response:
      status_code: 200           # 校验 HTTP 状态码
      assert_msg:
        type_jsonpath: "$.msg"   # 校验响应体字段
        expect_value: "login success"
        assert_type: "=="        # 断言类型：==, !=, in, not_in 等

  # 场景二：查询用户信息（依赖登录 Token）
  - id: get_user_info_01
    title: 查询用户信息
    url: /api/user/info
    method: GET
    headers:
      Authorization: Bearer ${token}  # 使用上一步提取的 token
    # 用例依赖：确保前置条件满足
    case_dependence:
      setup:
        interface: login_01      # 依赖登录接口
    # 响应断言
    assert_response:
      status_code: 200
      assert_code:
        type_jsonpath: "$.code"
        expect_value: 0
        assert_type: "=="
    # 数据库断言
    assert_sql:
      - sql: "SELECT username FROM users WHERE id='${user_id}'"
        expect_value: "test_user"
        assert_type: "=="
```

### 3. 自动生成说明
*   运行 `run.py` 时，框架会自动扫描 `interfaces/` 下的文件
*   YAML 文件生成的测试代码存放于：`testcases/test_auto_case/yaml_case/`
*   Excel 文件生成的测试代码存放于：`testcases/test_auto_case/excel_case/`
*   Excel 文件生成的文件名格式：`test_excel_<原文件名>.py`（如 `test_crm.xlsx` → `test_excel_crm.py`）

## 七、数据清理机制

数据清理机制用于保证测试环境隔离，避免测试数据污染。

### 1. 配置说明

在 `config/settings.py` 中配置数据清理：

```python
DATA_CLEANUP_CONFIG = {
    "enabled": True,  # 是否启用数据清理
    "databases": {
        "default": {
            "host": "localhost",
            "port": 3306,
            "user": "root",
            "password": "password",
            "database": "test_db",
            "ssh": False,  # 是否通过 SSH 隧道连接
            "ssh_config": {
                "ssh_host": "ssh.example.com",
                "ssh_port": 22,
                "ssh_user": "ssh_user",
                "ssh_pwd": "ssh_password",
            }
        }
    },
    "cleanup_on_failure": True,  # 失败时是否清理
    "cleanup_on_success": True,  # 成功时是否清理
}
```

### 2. 命令行参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--cleanup` | `auto` | 清理模式：`auto`（自动）、`manual`（手动）、`skip`（跳过） |

```bash
# 自动清理（默认）
python3 run.py --cleanup auto

# 手动清理（需在用例中手动调用）
python3 run.py --cleanup manual

# 跳过清理
python3 run.py --cleanup skip
```

### 3. 使用方式

**方式一：使用 fixture 自动清理**

```python
def test_create_order(data_cleanup):
    """
    使用 data_cleanup fixture 自动注册清理任务
    测试结束后自动执行清理
    """
    # 注册清理任务
    data_cleanup.register_cleanup(
        test_id="test_create_order",
        cleanup_sql="DELETE FROM orders WHERE order_no='TEST001'",
        db_name="default"
    )
    
    # 执行测试...
```

**方式二：使用数据库快照**

```python
def test_update_user(db_snapshot):
    """
    使用 db_snapshot fixture 创建快照
    测试结束后自动恢复数据
    """
    # 创建快照
    original_data = db_snapshot(
        db_name="default",
        table="users",
        condition="id=1"
    )
    
    # 执行测试（修改数据）...
    # 测试结束后自动恢复快照
```

**方式三：手动数据准备与清理**

```python
def test_with_manual_cleanup(cleanup_manager):
    """
    手动控制数据准备和清理
    """
    # 准备测试数据
    test_data = [
        {"id": 1, "name": "test_user1"},
        {"id": 2, "name": "test_user2"}
    ]
    cleanup_manager.insert_test_data(
        db_name="default",
        table="test_users",
        data=test_data
    )
    
    try:
        # 执行测试...
        pass
    finally:
        # 清理测试数据
        cleanup_manager.delete_by_condition(
            db_name="default",
            table="test_users",
            condition="id IN (1, 2)"
        )
```

### 4. 清理策略对比

| 策略 | 适用场景 | 优点 | 缺点 |
|------|----------|------|------|
| 注册清理 | 需要精确控制清理时机 | 灵活、可控 | 需要手动注册 |
| 快照恢复 | 需要保持数据原状 | 自动恢复、安全 | 大数据量时较慢 |
| 手动控制 | 复杂测试场景 | 完全可控 | 代码量较多 |

### 5. 最佳实践

1. **测试数据隔离**：每个测试用例使用唯一标识（如时间戳）创建数据
2. **清理优先级**：优先使用快照恢复，其次使用注册清理
3. **条件删除**：使用精确条件删除，避免误删其他数据
4. **事务回滚**：对于支持事务的数据库，可考虑使用事务回滚

## 八、异常处理增强

异常处理机制用于快速定位测试失败原因，提供详细的错误上下文。

### 1. 异常分类

框架提供统一的异常分类体系：

| 异常类型 | 分类 | 说明 |
|----------|------|------|
| `AssertionException` | assertion | 断言失败 |
| `RequestException` | request | 请求异常 |
| `DataException` | data | 数据异常 |
| `ConfigException` | config | 配置异常 |
| `NetworkException` | network | 网络异常 |
| `TimeoutException` | timeout | 超时异常 |
| `DatabaseException` | database | 数据库异常 |

### 2. 失败快照

测试失败时自动捕获快照，保存到 `outputs/report/failure_snapshots/` 目录：

```bash
# 启用失败快照（默认）
python3 run.py --snapshot on

# 禁用失败快照
python3 run.py --snapshot off
```

### 3. 快照内容

失败快照包含以下信息：

| 字段 | 说明 |
|------|------|
| `test_id` | 测试用例ID |
| `test_name` | 测试用例名称 |
| `timestamp` | 失败时间 |
| `failure_info` | 异常信息 |
| `request_info` | 请求信息 |
| `response_info` | 响应信息 |
| `context_vars` | 上下文变量 |
| `stack_trace` | 堆栈跟踪 |
| `logs` | 日志记录 |

### 4. 使用方式

**方式一：自动捕获**

测试失败时自动捕获快照，无需额外配置。

**方式二：手动追踪**

```python
def test_api_with_tracking(failure_tracker):
    """
    使用 failure_tracker 手动记录失败信息
    """
    # 添加日志
    failure_tracker["add_log"]("开始执行测试")
    
    # 设置上下文
    failure_tracker["set_context"]("user_id", "12345")
    
    try:
        # 执行测试...
        pass
    except Exception as e:
        # 获取追踪信息
        info = failure_tracker["get_info"]()
        print(f"追踪信息: {info}")
        raise
```

**方式三：统一异常处理**

```python
from utils.tools.exception_handler import (
    AssertionException,
    RequestException,
    handle_exception,
    safe_execute
)

# 抛出自定义异常
raise AssertionException(
    message="断言失败：状态码不匹配",
    expected=200,
    actual=404,
    assert_type="=="
)

# 统一异常处理
try:
    # 可能出错的代码
    pass
except Exception as e:
    handle_exception(e, context={"test_id": "test_001"})

# 安全执行函数
result = safe_execute(
    risky_function,
    arg1, arg2,
    default=None,
    context={"operation": "api_call"}
)
```

### 5. 最佳实践

1. **使用自定义异常**：根据场景选择合适的异常类型
2. **记录上下文**：失败时记录关键变量，便于排查
3. **查看快照**：失败后查看快照文件，快速定位问题
4. **统一处理**：使用 `handle_exception` 统一处理异常

## 九、Mock 接口数据服务

Mock 服务用于模拟接口响应，支持多种模式，便于测试开发和调试。

### 1. Mock 模式

| 模式 | 说明 |
|------|------|
| `disabled` | 禁用 Mock（默认） |
| `stub` | Stub 模式，只返回 Mock 数据 |
| `record` | 记录模式，记录真实响应 |
| `replay` | 回放模式，返回记录的响应 |
| `mixed` | 混合模式，未匹配时请求真实接口 |

### 2. 启用 Mock

**方式一：命令行参数**

```bash
# Stub 模式
python3 run.py --mock stub

# Record 模式
python3 run.py --mock record

# Replay 模式
python3 run.py --mock replay

# Mixed 模式
python3 run.py --mock mixed
```

**方式二：配置文件**

```python
# config/settings.py
MOCK_CONFIG = {
    "enabled": True,
    "mode": "stub",
    "recordings_dir": "outputs/mock_recordings",
    "auto_save": True,
    "default_delay": 0.0,
}
```

### 3. 使用方式

**方式一：使用 fixture 动态添加规则**

```python
def test_with_mock(mock_rule):
    """
    使用 mock_rule fixture 动态添加 Mock 规则
    """
    # 添加 Mock 规则
    mock_rule(
        name="login_api",
        url_pattern=r"/api/login",
        response={"code": 0, "data": {"token": "mock_token"}},
        method="POST"
    )
    
    # 执行测试，请求会被 Mock 拦截
    # ...
```

**方式二：使用装饰器**

```python
from utils.tools.mock_service import mock_response

@mock_response(
    url_pattern=r"/api/user",
    response={"code": 0, "data": {"name": "test"}}
)
def test_user_api():
    """
    使用装饰器添加 Mock 规则
    """
    # ...
```

**方式三：直接使用 Mock 服务**

```python
from utils.tools.mock_service import get_mock_service
from utils.tools.mock_templates import MockTemplates

def test_direct_mock():
    """
    直接使用 Mock 服务
    """
    mock_service = get_mock_service()
    
    # 添加 Mock 规则
    mock_service.add_stub(
        name="get_user",
        url_pattern=r"/api/user/\d+",
        response=MockTemplates.user(user_id=1),
        method="GET"
    )
    
    # 执行测试...
```

### 4. Mock 数据模板

框架提供常用的 Mock 数据模板：

| 模板 | 说明 |
|------|------|
| `user` | 用户数据 |
| `users` | 用户列表 |
| `product` | 商品数据 |
| `products` | 商品列表 |
| `order` | 订单数据 |
| `orders` | 订单列表 |
| `article` | 文章数据 |
| `token` | Token 数据 |
| `success` | 成功响应 |
| `error` | 错误响应 |
| `login_success` | 登录成功响应 |
| `api_response` | 标准 API 响应 |

**使用示例：**

```python
from utils.tools.mock_templates import MockTemplates, create_mock_data

# 方式一：直接使用模板类
user = MockTemplates.user(user_id=1)
users = MockTemplates.users(count=10)
login = MockTemplates.login_success()

# 方式二：使用工厂函数
user = create_mock_data("user", user_id=1)
products = create_mock_data("products", count=5)

# 方式三：生成分页数据
items = MockTemplates.users(50)
paged = MockTemplates.pagination(items, page=1, page_size=10)
```

### 5. Mock 配置自动生成

框架支持从 YAML 用例或 OpenAPI 文档自动生成 Mock 配置。

**命令行工具：**

```bash
# 从 YAML 用例目录生成 Mock 配置
python3 utils/tools/generate_mock.py yaml --dir interfaces/projects/workspace --project workspace

# 从单个 YAML 文件生成 Mock 配置
python3 utils/tools/generate_mock.py yaml --file interfaces/projects/workspace/test_login.yaml --project workspace

# 从 OpenAPI 文档生成 Mock 配置
python3 utils/tools/generate_mock.py openapi --file api.json --project myproject
```

**参数说明：**

| 参数 | 说明 |
|------|------|
| `--file, -f` | 文件路径（YAML 用例或 OpenAPI 文档） |
| `--dir, -d` | YAML 用例目录 |
| `--project, -p` | 项目名称 |
| `--output, -o` | 输出目录（默认为项目目录） |

**生成的配置文件：**

```python
# interfaces/projects/workspace/workspace_mock_config.py
from utils.tools.mock_service import MockRule, MockResponse

def get_workspace_mock_rules():
    """获取 workspace 项目的 Mock 规则"""
    rules = []
    
    # 账号密码登录
    workspace_login_01_rule = MockRule(
        name="workspace_login_01",
        url_pattern=r"/api/crm/v4/user/login",
        method="POST",
        response_builder=build_workspace_login_01_response,
        delay=0.1,
        priority=10
    )
    rules.append(workspace_login_01_rule)
    
    return rules

def build_workspace_login_01_response(url: str, method: str, **kwargs) -> MockResponse:
    """构建 账号密码登录 Mock 响应"""
    response_data = {
        "code": 200,
        "message": "success",
        "data": {
            "token": "mock_token_xxx",
            "openid": "mock_openid_xxx"
        }
    }
    return MockResponse(
        status_code=200,
        headers={'Content-Type': 'application/json;charset=utf-8'},
        body=response_data,
        elapsed=0.15
    )
```

**使用生成的 Mock 配置：**

```python
# conftest.py 或测试文件中
from interfaces.projects.workspace.workspace_mock_config import get_workspace_mock_rules

def pytest_configure(config):
    """注册 Mock 规则"""
    mock_service = get_mock_service()
    for rule in get_workspace_mock_rules():
        mock_service.add_rule(rule)
```

### 6. 高级用法

**自定义响应构建器：**

```python
from utils.tools.mock_service import MockRule, get_mock_service

def custom_response(url, method, **kwargs):
    """自定义响应构建函数"""
    payload = kwargs.get("payload", {})
    return {
        "status_code": 200,
        "body": {
            "code": 0,
            "message": "success",
            "data": {"id": payload.get("user_id", 1)}
        }
    }

mock_service = get_mock_service()
rule = MockRule(
    name="custom_rule",
    url_pattern=r"/api/custom",
    response_builder=custom_response
)
mock_service.add_rule(rule)
```

**请求匹配器：**

```python
def request_matcher(url, method, payload=None, **kwargs):
    """自定义请求匹配函数"""
    if method != "POST":
        return False
    if payload and payload.get("type") == "special":
        return True
    return False

rule = MockRule(
    name="conditional_mock",
    request_matcher=request_matcher,
    response_builder={"status_code": 200, "body": {"matched": True}}
)
```

### 7. 最佳实践

1. **开发阶段使用 Stub 模式**：快速开发，不依赖真实接口
2. **调试阶段使用 Record 模式**：记录真实响应，便于分析
3. **离线测试使用 Replay 模式**：回放记录的响应，无需网络
4. **使用数据模板**：快速生成测试数据
5. **规则命名清晰**：便于管理和调试
6. **自动生成 Mock 配置**：从 YAML 用例自动生成，减少手动编写
7. **Mock 数据与断言一致**：生成的 Mock 数据应与用例断言的预期值一致

## 十、多项目支持

框架支持多项目并行管理，不同项目的测试用例存放在独立目录中。

### 1. 项目目录结构

```
interfaces/
├── projects/                    # 项目目录
│   ├── workspace/              # 项目1：workspace
│   │   ├── test_login.yaml
│   │   ├── test_crm.xlsx
│   │   └── init_data.yaml
│   ├── crm/                    # 项目2：crm
│   │   ├── test_user.yaml
│   │   └── test_order.xlsx
│   └── erp/                    # 项目3：erp
│       └── test_api.yaml
└── test_common.yaml            # 公共用例（可选）
```

### 2. 运行方式

**运行所有项目：**

```bash
# 自动扫描 projects 目录下所有项目
python3 run.py -env test
```

**运行指定项目：**

```bash
# 运行单个项目
python3 run.py -env test -project workspace

# 运行多个项目（逗号分隔）
python3 run.py -env test -project workspace,crm
```

### 3. 生成的用例结构

不同项目的测试用例会生成到独立目录：

```
testcases/
└── test_auto_case/
    ├── yaml_case/
    │   ├── workspace/          # workspace 项目的 YAML 用例
    │   │   └── test_yaml_login.py
    │   ├── crm/                # crm 项目的 YAML 用例
    │   │   └── test_yaml_user.py
    │   └── erp/                # erp 项目的 YAML 用例
    │       └── test_yaml_api.py
    └── excel_case/
        ├── workspace/          # workspace 项目的 Excel 用例
        │   └── test_excel_crm.py
        └── crm/                # crm 项目的 Excel 用例
            └── test_excel_order.py
```

### 4. 项目配置

可在 `config/settings.py` 中配置项目信息：

```python
PROJECT_CONFIG = {
    "enabled": True,
    "default_project": None,
    "projects": {
        "workspace": {
            "description": "统一工作台项目",
            "env": "test"
        },
        "crm": {
            "description": "客户管理系统",
            "env": "test"
        }
    }
}
```

### 5. 项目管理 API

```python
from core.project_manager import get_project_manager

# 获取项目管理器
manager = get_project_manager()

# 创建项目
manager.create_project(
    name="new_project",
    description="新项目描述"
)

# 列出所有项目
projects = manager.list_projects()

# 获取项目统计
stats = manager.get_project_stats("workspace")
```

### 6. 最佳实践

1. **项目隔离**：每个项目使用独立目录，避免用例冲突
2. **命名规范**：项目目录名使用小写字母和下划线
3. **公共用例**：公共用例可放在 `interfaces/` 根目录
4. **环境配置**：每个项目可配置独立的测试环境

## 十一、Excel 模板与示例

### 1. 字段规范（列名）
| 字段 | 说明 |
|------|------|
| id | 用例唯一标识，必须以非空字符串填写 |
| title | 用例标题（展示与报告） |
| severity | 用例等级：NORMAL/TRIVIAL/MINOR/CRITICAL/BLOCKER |
| url | 接口路径，如 /api/crm/v4/user/login |
| run | 是否执行，True/False（为 False 时将被跳过） |
| method | 请求方法：GET/POST/PUT/DELETE 等 |
| headers | 请求头，建议 JSON 字符串或字典字面量 |
| cookies | Cookie 配置（可空） |
| request_type | 请求体类型：JSON/FORM/FILE 等 |
| payload | 请求体，支持字典或 JSON 字符串 |
| files | 文件上传（可空） |
| wait_seconds | 请求前等待时间（秒）（可空） |
| validate | 断言规则 |
| extract | 参数提取，如 `{'token': '$.data.token'}` |
| case_dependence | 用例依赖，包含 setup/teardown（可空） |
| markers | 用例标记，如 `login`、`smoke` |

### 2. 断言写法规范（validate）
```json
{
  "status_code": 200,
  "assert_ret": { "type_jsonpath": "$.ret", "expect_value": 0, "assert_type": "==" },
  "assert_user": { "type_jsonpath": "$.data.user.username", "expect_value": "admin", "assert_type": "==" }
}
```

**支持的断言类型：**
`==`, `not_eq`, `gt`, `ge`, `lt`, `le`, `contains`, `str_eq`, `len_eq`, `len_gt`, `len_ge`, `len_lt`, `len_le`, `contained_by`, `startswith`, `endswith`

### 3. 依赖场景示例
```json
{
  "setup": { "interface": "login_01" },
  "teardown": null
}
```

### 4. Excel 用例依赖说明
**重要**：Excel 用例之间的依赖目前不支持，Excel 用例需要依赖 YAML 文件中的用例。

```json
// 错误示例：Excel 用例依赖另一个 Excel 用例（不支持）
{
  "setup": { "interface": "case_login_excel_01" }
}

// 正确示例：Excel 用例依赖 YAML 用例
{
  "setup": { "interface": "login_01" }
}
```

### 5. 字段映射说明
Excel 列名与内部字段的映射关系：

| Excel 列名 | 内部字段 | 说明 |
|------------|----------|------|
| `assert_response` | `validate` | 响应断言规则 |
| `extract` | `extract` | 参数提取配置 |
| `case_dependence` | `case_dependence` | 用例依赖配置 |

**注意**：`extract` 和 `assert_response` 两列不要填反：
- `extract`：填写需要从响应中提取的参数，如 `{"token": "$.data.token"}`
- `assert_response`：填写断言规则，如 `{"status_code": 200, "assert_code": {...}}`

## 十二、Docker 支持

### 1. 构建镜像
```bash
docker build -t api-autotest:latest .
```

### 2. 运行容器
```bash
# 默认运行测试环境
docker run --rm api-autotest:latest

# 运行生产环境
docker run --rm api-autotest:latest -env prod -report yes

# 挂载报告目录
docker run --rm -v $(pwd)/outputs:/app/outputs api-autotest:latest
```

### 3. Dockerfile 优化说明
Dockerfile 采用分层构建策略，优化镜像构建速度：

| 层级 | 内容 | 变化频率 | 缓存利用 |
|------|------|----------|----------|
| 1 | 基础镜像 | 极低 | ✅ |
| 2 | 系统依赖 | 低 | ✅ |
| 3 | Python 依赖 | 中 | ✅ |
| 4 | 源代码 | 高 | 按需更新 |

**构建效率：**
- 首次构建：完整安装依赖（约 2-3 分钟）
- 后续构建（仅代码变化）：跳过依赖安装（约 10-20 秒）

## 十三、CI/CD 集成

### 1. GitHub Actions
项目已配置 `.github/workflows/ci.yaml`，支持以下功能：

**触发条件：**
- Push 到 `main` / `master` 分支
- Pull Request 到 `main` / `master` 分支
- 手动触发（可选择 test/prod 环境）

**流水线特性：**
| 特性 | 说明 |
|------|------|
| 并发控制 | 同一分支同时只运行一个流水线 |
| 依赖缓存 | 缓存 Python 环境，跳过重复安装 |
| 多环境支持 | main 分支 → test 环境，master 分支 → prod 环境 |
| 测试报告 | 自动上传测试报告，保留 7-30 天 |
| 代码检查 | PR 时运行 Ruff 代码质量检查 |

**缓存策略：**
```yaml
# 缓存整个 Python 环境
path: ${{ env.pythonLocation }}
key: ${{ runner.os }}-py-${{ env.PYTHON_VERSION }}-${{ hashFiles('requirements.txt') }}
```

**条件安装：**
- 缓存命中：跳过依赖安装
- 缓存未命中：安装依赖并缓存

### 2. Secrets 配置
在 GitHub 仓库的 Settings → Secrets and variables → Actions 中配置：

| Secret 名称 | 说明 |
|-------------|------|
| `TEST_USERNAME` | 测试环境用户名 |
| `TEST_PASSWORD` | 测试环境密码 |
| `TEST_DB_HOST` | 测试环境数据库地址 |
| `TEST_DB_PWD` | 测试环境数据库密码 |
| `DINGTALK_WEBHOOK` | 钉钉机器人 Webhook |
| `EMAIL_USER` | 邮件发送账号 |
| `EMAIL_PASSWORD` | 邮件授权码 |

## 十四、常见问题与排查

### 1. 忽略（deselected）与跳过（skipped）的区别
- **deselected**：因 `-m/-k` 等筛选条件不匹配被收集阶段排除
- **skipped**：在执行阶段被显式跳过（`run=False`）

### 2. 标记筛选建议
- 若看到大量 `deselected`，请确认所用标记与用例实际标记一致
- 可在 Excel 的 `markers` 列或 YAML 的 `case_common.case_markers` 中配置标记

### 3. Allure 报告查看
- 结果目录：`outputs/report/allure_results`
- HTML 报告：`outputs/report/allure_html`
- 命令行查看：`allure open outputs/report/allure_results`

### 4. 导入冲突（import file mismatch）
- 同名 Excel 可能生成同名 .py，导致 Pytest 发现两个模块
- 请确保同目录内文件名唯一或清理 `testcases/test_auto_case/` 后再生成

## 十五、依赖库
核心依赖如下，详细列表请见 `requirements.txt`：
*   pytest
*   allure-pytest
*   requests
*   loguru
*   pyyaml
*   openpyxl
*   python-dotenv
*   yagmail

## 十六、注意事项

### 1. 用例文件命名规范
*   必须以 `test` 开头（例如 `test_login.yaml`）
*   文件名建议使用下划线 `_` 分隔

### 2. 配置与安全
*   环境配置文件：使用 `-env abc` 运行时，必须确保 `config/abc.yaml` 存在
*   敏感信息：`.env` 文件**严禁提交到代码仓库**（`.gitignore` 已默认忽略）
*   CI/CD 环境：请在 GitHub Secrets 中配置对应变量

### 3. Excel 用例编写
*   数字字符串需保留原样时，在单元格前加单引号 `'`（如 `'13800138000`）
*   框架会自动忽略 `id` 为空的行

### 4. Allure 报告
*   本地查看报告需要使用 `allure open` 命令
*   直接浏览器打开 HTML 文件可能无法加载数据

### 5. 依赖安装
*   macOS 推荐使用虚拟环境：`python3 -m venv venv && source venv/bin/activate`

## 十七、更新日志

### v2.8 (2026-04)
*   移除多进程并行执行功能
    *   移除 `-n` 和 `-dist` 命令行参数
    *   移除 `PARALLEL_CONFIG` 配置
    *   移除 `parallel_config.py` 模块
    *   测试用例改为单线程串行执行，保证执行顺序稳定

### v2.7 (2026-03)
*   新增多项目支持
    *   支持多项目并行管理，不同项目用例存放在独立目录
    *   新增 `-project` 命令行参数，支持指定运行项目
    *   新增项目管理模块 `project_manager.py`
    *   项目用例自动生成到独立目录
    *   支持项目管理 API

### v2.6 (2026-03)
*   新增 Mock 接口数据服务
    *   支持多种 Mock 模式：stub、record、replay、mixed
    *   新增 `--mock` 命令行参数
    *   提供 `mock_service` 和 `mock_rule` fixture
    *   内置常用 Mock 数据模板
    *   支持自定义响应构建器和请求匹配器

### v2.5 (2026-03)
*   新增异常处理增强
    *   统一异常分类与处理机制
    *   测试失败自动捕获快照
    *   新增 `--snapshot` 命令行参数
    *   提供 `failure_tracker` fixture
    *   支持请求/响应信息自动记录

### v2.3 (2026-03)
*   新增数据清理机制
    *   支持数据库快照与恢复
    *   支持注册清理任务自动执行
    *   支持手动数据准备与清理
    *   新增 `--cleanup` 命令行参数
    *   提供 `data_cleanup` 和 `db_snapshot` fixture

### v2.2 (2026-03)
*   新增定时任务功能
    *   支持配置化定时任务调度
    *   可配置运行时间、环境、报告、标记等
    *   支持后台运行和 screen 方式运行

### v2.1 (2026-03)
*   优化 GitHub Actions CI 配置
    *   缓存整个 Python 环境，避免重复安装依赖
    *   条件安装：缓存命中时跳过依赖安装步骤
    *   移除 matrix 策略，改为独立 job
*   优化 Dockerfile 构建策略
    *   分层复制源代码，最大化利用 Docker 缓存
    *   源代码变化时不再重新安装依赖
*   完善 `.gitignore` 和 `.dockerignore` 配置

### v2.0 (2026-03)
*   优化 Excel 用例文件名生成格式：`test_excel_<文件名>.py`
*   新增 Docker 容器化支持
*   优化 GitHub Actions CI 配置（并发控制、代码检查）
*   改进测试用例生成逻辑，避免文件名冲突
*   增强 Allure 报告元数据提取

