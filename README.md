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

## 十二、复杂场景测试示例

本章节展示框架支持的各种复杂测试场景，帮助您应对实际业务中的多样化测试需求。

### 1. 多步骤业务流程测试

模拟完整的业务流程，通过用例依赖实现多步骤串联。

**场景：电商订单完整流程（登录 → 添加购物车 → 创建订单 → 支付 → 查询订单状态）**

```yaml
case_common:
  allure_epic: 电商平台
  allure_feature: 订单模块
  allure_story: 订单完整流程
  case_markers: ['order', 'p0', 'workflow']

case_info:
  # 步骤1：用户登录，提取token和用户ID
  - id: workflow_login_01
    title: 用户登录获取凭证
    url: /api/user/login
    method: POST
    headers:
      Content-Type: application/json
    request_type: json
    payload:
      username: ${username}
      password: ${password}
    extract:
      response:
        type_jsonpath:
          token: $.data.token
          user_id: $.data.user.id
          cart_session: $.data.cart_session_id
    assert_response:
      status_code: 200
      assert_code:
        type_jsonpath: "$.code"
        expect_value: 0
        assert_type: "=="

  # 步骤2：添加商品到购物车（依赖登录）
  - id: workflow_add_cart_01
    title: 添加商品到购物车
    url: /api/cart/add
    method: POST
    headers:
      Content-Type: application/json
      Authorization: Bearer ${token}
    request_type: json
    payload:
      user_id: ${user_id}
      product_id: 10001
      quantity: 2
      cart_session: ${cart_session}
    case_dependence:
      setup:
        interface: workflow_login_01
    extract:
      response:
        type_jsonpath:
          cart_item_id: $.data.item_id
          total_price: $.data.total_price
    assert_response:
      status_code: 200
      assert_quantity:
        type_jsonpath: "$.data.quantity"
        expect_value: 2
        assert_type: "=="

  # 步骤3：创建订单（依赖添加购物车）
  - id: workflow_create_order_01
    title: 创建订单
    url: /api/order/create
    method: POST
    headers:
      Authorization: Bearer ${token}
    request_type: json
    payload:
      user_id: ${user_id}
      cart_item_ids: ["${cart_item_id}"]
      address_id: 1
      payment_method: alipay
    case_dependence:
      setup:
        interface: [workflow_login_01, workflow_add_cart_01]
    extract:
      response:
        type_jsonpath:
          order_id: $.data.order_id
          order_no: $.data.order_no
          pay_amount: $.data.pay_amount
    assert_response:
      status_code: 200
      assert_status:
        type_jsonpath: "$.data.status"
        expect_value: "pending_payment"
        assert_type: "=="

  # 步骤4：模拟支付（依赖创建订单）
  - id: workflow_pay_order_01
    title: 订单支付
    url: /api/order/pay
    method: POST
    headers:
      Authorization: Bearer ${token}
    request_type: json
    payload:
      order_id: ${order_id}
      order_no: ${order_no}
      pay_amount: ${pay_amount}
      payment_method: alipay
      transaction_id: "ALI_${generate_time('%Y%m%d%H%M%S')}_${generate_random_int(1000,9999)}"
    case_dependence:
      setup:
        interface: workflow_create_order_01
    extract:
      response:
        type_jsonpath:
          payment_id: $.data.payment_id
          paid_time: $.data.paid_time
    assert_response:
      status_code: 200
      assert_pay_status:
        type_jsonpath: "$.data.pay_status"
        expect_value: "success"
        assert_type: "=="

  # 步骤5：查询订单状态验证（依赖支付）
  - id: workflow_query_order_01
    title: 查询订单状态
    url: /api/order/detail
    method: GET
    headers:
      Authorization: Bearer ${token}
    request_type: params
    payload:
      order_id: ${order_id}
    case_dependence:
      setup:
        interface: workflow_pay_order_01
    assert_response:
      status_code: 200
      assert_order_status:
        type_jsonpath: "$.data.status"
        expect_value: "paid"
        assert_type: "=="
      assert_paid_time:
        type_jsonpath: "$.data.paid_time"
        expect_value: "${paid_time}"
        assert_type: "=="
    # 数据库断言：验证订单状态已更新
    assert_sql:
      - sql: "SELECT status FROM orders WHERE order_id='${order_id}'"
        expect_value: "paid"
        assert_type: "=="
```

### 2. 文件上传与下载测试

框架支持文件上传和下载操作，适用于报表导出、附件上传等场景。

**场景一：文件上传测试**

```yaml
case_common:
  allure_epic: 文件管理
  allure_feature: 文件操作
  allure_story: 文件上传
  case_markers: ['file', 'upload']

case_info:
  - id: file_upload_01
    title: 上传单个文件
    url: /api/file/upload
    method: POST
    headers:
      Authorization: Bearer ${token}
    request_type: file
    payload: file  # 文件字段名
    files: files/test_image.png  # 文件路径，相对于 files/ 目录
    extract:
      response:
        type_jsonpath:
          file_id: $.data.file_id
          file_url: $.data.url
    assert_response:
      status_code: 200
      assert_file_id:
        type_jsonpath: "$.data.file_id"
        expect_value: null
        assert_type: "!="

  - id: file_upload_multiple_01
    title: 批量上传多个文件（手动编写的测试用例）
    run: True
    severity: normal
```

**手动编写批量上传测试用例示例：**

```python
# testcases/test_manual_case/test_file_upload.py
import pytest
import os
from config.settings import FILES_DIR, GLOBAL_VARS
from core.requests_utils.base_request import BaseRequest

@pytest.mark.file
@pytest.mark.upload
def test_batch_upload_files():
    """
    批量上传多个文件测试
    """
    token = GLOBAL_VARS.get("token")
    upload_url = GLOBAL_VARS.get("host") + "/api/file/batch-upload"
    
    # 获取 files 目录下所有图片文件
    files_dir = FILES_DIR
    image_files = [f for f in os.listdir(files_dir) if f.endswith(('.png', '.jpg', '.jpeg'))]
    
    uploaded_ids = []
    
    for image_file in image_files[:5]:  # 上传前5个文件
        file_path = os.path.join(files_dir, image_file)
        
        req_data = {
            "url": upload_url,
            "method": "POST",
            "headers": {"Authorization": f"Bearer {token}"},
            "request_type": "file",
            "payload": "files",
            "files": file_path
        }
        
        response = BaseRequest.send_request(req_data)
        
        assert response.status_code == 200
        file_id = response.json().get("data", {}).get("file_id")
        if file_id:
            uploaded_ids.append(file_id)
    
    # 验证所有文件上传成功
    assert len(uploaded_ids) == min(5, len(image_files))
    
    # 保存上传的文件ID供后续使用
    GLOBAL_VARS["uploaded_file_ids"] = uploaded_ids
```

**场景二：文件下载/导出测试**

```yaml
case_common:
  allure_epic: 报表管理
  allure_feature: 数据导出
  allure_story: Excel导出
  case_markers: ['export', 'report']

case_info:
  - id: report_export_01
    title: 导出销售报表
    url: /api/report/export
    method: POST
    headers:
      Authorization: Bearer ${token}
      Content-Type: application/json
    request_type: export  # 使用 export 类型自动下载文件
    payload:
      report_type: sales
      date_range:
        start_date: "${generate_time('%Y-%m-%d', days=-30)}"
        end_date: "${generate_time('%Y-%m-%d')}"
      format: excel
    case_dependence:
      setup:
        interface: workflow_login_01
    assert_response:
      status_code: 200
      # 文件下载后自动保存到 outputs/download_files/ 目录
```

### 3. 数据库断言与数据清理

测试数据库操作后验证数据正确性，并在测试完成后自动清理测试数据。

**场景：创建用户并验证数据库记录**

```yaml
case_common:
  allure_epic: 用户管理
  allure_feature: 用户 CRUD
  allure_story: 用户创建与验证
  case_markers: ['user', 'database', 'cleanup']

case_info:
  - id: db_user_create_01
    title: 创建用户并验证数据库
    url: /api/user/create
    method: POST
    headers:
      Authorization: Bearer ${token}
      Content-Type: application/json
    request_type: json
    payload:
      username: "test_${generate_name(lan='zh')}"
      email: "${generate_email(lan='zh')}"
      phone: "${generate_phone(lan='zh')}"
      department: "${generate_company_name(lan='zh')}"
      # 使用时间戳确保唯一性
      create_time: "${generate_time('%Y-%m-%d %H:%M:%S')}"
    case_dependence:
      setup:
        interface: workflow_login_01
    extract:
      response:
        type_jsonpath:
          new_user_id: $.data.user_id
          new_username: $.data.username
    assert_response:
      status_code: 200
      assert_code:
        type_jsonpath: "$.code"
        expect_value: 0
        assert_type: "=="
    # 数据库断言：验证用户数据已正确写入
    assert_sql:
      - sql: "SELECT username, email FROM users WHERE user_id='${new_user_id}'"
        expect_value:
          username: "${new_username}"
          email: "${generate_email(lan='zh')}"
        assert_type: "=="
      # 验证用户状态为激活状态
      - sql: "SELECT status FROM users WHERE user_id='${new_user_id}'"
        expect_value: "active"
        assert_type: "=="

  - id: db_user_update_01
    title: 更新用户信息并验证数据库
    url: /api/user/update
    method: PUT
    headers:
      Authorization: Bearer ${token}
    request_type: json
    payload:
      user_id: ${new_user_id}
      department: "研发部"
      role: "engineer"
    case_dependence:
      setup:
        interface: db_user_create_01
    assert_sql:
      - sql: "SELECT department, role FROM users WHERE user_id='${new_user_id}'"
        expect_value:
          department: "研发部"
          role: "engineer"
        assert_type: "=="
```

**数据清理配置（settings.py）：**

```python
DATA_CLEANUP_CONFIG = {
    "enabled": True,
    "databases": {
        "default": {
            "host": "${DB_HOST}",
            "port": 3306,
            "user": "root",
            "password": "${DB_PWD}",
            "database": "test_db",
            "ssh": False
        }
    },
    "cleanup_on_failure": True,
    "cleanup_on_success": True
}
```

**手动数据清理示例（Python测试用例）：**

```python
# testcases/test_manual_case/test_user_cleanup.py
import pytest
from utils.database_utils.mysql_handle import MysqlServer
from config.settings import GLOBAL_VARS

@pytest.mark.user
@pytest.mark.cleanup
def test_user_with_cleanup(data_cleanup):
    """
    创建测试用户，测试完成后自动清理
    """
    # 注册清理任务
    test_username = f"cleanup_test_{int(time.time())}"
    
    # 创建用户（API调用）
    # ...
    
    # 注册清理SQL
    data_cleanup.register_cleanup(
        test_id="test_user_cleanup",
        cleanup_sql=f"DELETE FROM users WHERE username='{test_username}'",
        db_name="default"
    )
    
    # 执行测试验证...
    # 测试结束后自动执行清理SQL
```

### 4. 动态参数生成（Faker 数据）

框架集成 Faker 库，支持生成随机测试数据，适用于参数化测试和数据驱动测试。

**可用的 Faker 方法：**

| 方法 | 说明 | 示例 |
|------|------|------|
| `generate_name(lan='zh')` | 生成姓名 | `${generate_name(lan='zh')}` → 张三 |
| `generate_email(lan='zh')` | 生成邮箱 | `${generate_email()}` → test@example.com |
| `generate_phone(lan='zh')` | 生成手机号 | `${generate_phone(lan='zh')}` → 13812345678 |
| `generate_id_number(lan='zh')` | 生成身份证号 | `${generate_id_number(lan='zh')}` |
| `generate_company_name(lan='zh')` | 生成公司名 | `${generate_company_name(lan='zh')}` → 阿里巴巴 |
| `generate_address(lan='zh')` | 生成地址 | `${generate_address(lan='zh')}` |
| `generate_city(lan='zh')` | 生成城市 | `${generate_city(lan='zh')}` → 北京市 |
| `generate_random_int(min, max)` | 生成随机整数 | `${generate_random_int(1, 100)}` |
| `generate_time(fmt, days)` | 生成时间 | `${generate_time('%Y-%m-%d', days=7)}` |
| `generate_identifier(char_len)` | 生成标识符 | `${generate_identifier(8)}` |

**场景：使用 Faker 生成完整用户注册信息**

```yaml
case_common:
  allure_epic: 注册模块
  allure_feature: 用户注册
  allure_story: Faker数据驱动
  case_markers: ['register', 'faker', 'p1']

case_info:
  - id: faker_register_01
    title: 使用Faker数据注册用户
    url: /api/user/register
    method: POST
    headers:
      Content-Type: application/json
    request_type: json
    payload:
      # 使用Faker生成随机测试数据
      username: "user_${generate_identifier(8)}"
      password: "${generate_random_int(100000, 999999)}"
      real_name: "${generate_name(lan='zh')}"
      email: "${generate_email(lan='zh')}"
      phone: "${generate_phone(lan='zh')}"
      id_card: "${generate_id_number(lan='zh')}"
      company: "${generate_company_name(lan='zh')}"
      province: "${generate_province(lan='zh')}"
      city: "${generate_city(lan='zh')}"
      address: "${generate_address(lan='zh')}"
      # 动态时间
      register_time: "${generate_time('%Y-%m-%d %H:%M:%S')}"
      expire_time: "${generate_time('%Y-%m-%d', days=365)}"
    extract:
      response:
        type_jsonpath:
          registered_user_id: $.data.user_id
          registered_username: $.data.username
    assert_response:
      status_code: 200
      assert_code:
        type_jsonpath: "$.code"
        expect_value: 0
        assert_type: "=="
      # 验证返回的用户名与提交的一致
      assert_username:
        type_jsonpath: "$.data.username"
        expect_value: "${registered_username}"
        assert_type: "=="
```

### 5. 多重依赖与依赖链

支持多种依赖类型：接口依赖、环境变量依赖、数据库依赖。

**场景：复杂依赖链（环境变量 → 接口 → 数据库）**

```yaml
case_common:
  allure_epic: 综合测试
  allure_feature: 依赖管理
  allure_story: 多重依赖
  case_markers: ['dependence', 'complex']

case_info:
  - id: complex_dependence_01
    title: 多重依赖测试
    url: /api/order/verify
    method: POST
    headers:
      Authorization: Bearer ${token}
      Content-Type: application/json
    request_type: json
    payload:
      order_id: ${order_id}
      verify_code: ${verify_code}
      user_balance: ${user_balance}
    case_dependence:
      setup:
        # 环境变量依赖：设置初始变量
        variables:
          verify_code: "${generate_random_int(1000, 9999)}"
          request_time: "${generate_time('%Y-%m-%d %H:%M:%S')}"
        # 接口依赖：先执行登录和创建订单
        interface: [workflow_login_01, workflow_create_order_01]
        # 数据库依赖：查询用户余额
        database:
          - sql: "SELECT balance FROM user_account WHERE user_id='${user_id}'"
            type_jsonpath:
              user_balance: $.0.balance
    extract:
      response:
        type_jsonpath:
          verify_result: $.data.result
    assert_response:
      status_code: 200
      assert_result:
        type_jsonpath: "$.data.result"
        expect_value: "success"
        assert_type: "=="
```

### 6. 正则表达式提取

适用于从响应文本、Cookie值等非JSON结构中提取数据。

**场景：从响应头或HTML内容中提取数据**

```yaml
case_common:
  allure_epic: 认证模块
  allure_feature: OAuth认证
  allure_story: 正则提取
  case_markers: ['regex', 'oauth']

case_info:
  - id: regex_extract_01
    title: OAuth认证并提取授权码
    url: /api/oauth/authorize
    method: GET
    headers:
      Authorization: Bearer ${token}
    request_type: params
    payload:
      client_id: ${client_id}
      redirect_uri: ${redirect_uri}
      response_type: code
    extract:
      response:
        # JSONPath提取
        type_jsonpath:
          auth_state: $.data.state
      # 正则表达式提取（从响应文本中）
      type_re:
        # 从重定向URL中提取授权码
        auth_code: "code=(\w+)"
        # 从响应中提取session_id
        session_id: "session_id=([a-f0-9]+)"
    assert_response:
      status_code: 200

  - id: regex_cookie_01
    title: 从Cookie中提取Session ID
    url: /api/user/session
    method: POST
    headers:
      Content-Type: application/json
    request_type: json
    payload:
      username: ${username}
    extract:
      response:
        # 从Response对象提取Cookie
        type_response:
          cookies: response.cookies
        # 正则提取Cookie中的session值
        type_re:
          session_token: "session=(\w+)"
    assert_response:
      status_code: 200
```

### 7. SSH 隧道数据库连接

通过 SSH 隧道连接远程数据库，适用于生产环境或安全隔离环境。

**配置示例（settings.py 或环境配置文件）：**

```yaml
# config/prod.yaml
db_info:
  db_host: 10.0.0.100  # 内网数据库IP
  db_port: 3306
  db_user: readonly
  db_pwd: ${PROD_DB_PWD}
  db_database: prod_db
  # SSH隧道配置
  ssh: true
  ssh_config:
    ssh_host: ssh.jumpserver.com  # SSH跳板机
    ssh_port: 22
    ssh_user: autotest
    ssh_pwd: ${SSH_PWD}
```

**测试用例示例：**

```yaml
case_common:
  allure_epic: 生产验证
  allure_feature: 数据验证
  allure_story: SSH隧道连接
  case_markers: ['ssh', 'prod', 'critical']

case_info:
  - id: ssh_db_verify_01
    title: 通过SSH隧道验证生产数据
    url: /api/order/query
    method: GET
    headers:
      Authorization: Bearer ${prod_token}
    request_type: params
    payload:
      order_no: "ORD202401150001"
    # 通过SSH隧道进行数据库断言
    assert_sql:
      - sql: "SELECT status, amount FROM orders WHERE order_no='ORD202401150001'"
        expect_value:
          status: "completed"
          amount: 299.00
        assert_type: "=="
```

### 8. Cookie/Session 管理

框架自动管理 Session 会话，支持 Cookie 提取和传递。

**场景：Cookie 自动传递与验证**

```yaml
case_common:
  allure_epic: 会话管理
  allure_feature: Cookie管理
  allure_story: Session持久化
  case_markers: ['cookie', 'session']

case_info:
  # 登录获取Cookie
  - id: cookie_login_01
    title: 登录并获取Cookie
    url: /api/auth/login
    method: POST
    headers:
      Content-Type: application/json
    request_type: json
    payload:
      username: ${username}
      password: ${password}
    extract:
      response:
        # 提取整个Cookie对象
        type_response:
          login_cookies: response.cookies
        # JSONPath提取token
        type_jsonpath:
          auth_token: $.data.token
    assert_response:
      status_code: 200

  # 使用Cookie访问需要认证的接口
  - id: cookie_access_01
    title: 使用Cookie访问用户信息
    url: /api/user/profile
    method: GET
    headers:
      Authorization: Bearer ${auth_token}
    # 传递上一接口的Cookie
    cookies: ${login_cookies}
    case_dependence:
      setup:
        interface: cookie_login_01
    extract:
      response:
        type_jsonpath:
          user_profile_id: $.data.profile_id
    assert_response:
      status_code: 200
      assert_username:
        type_jsonpath: "$.data.username"
        expect_value: "${username}"
        assert_type: "=="
```

### 9. 条件执行与等待策略

支持请求前等待、条件断言等策略。

**场景：轮询等待异步任务完成**

```yaml
case_common:
  allure_epic: 异步任务
  allure_feature: 任务管理
  allure_story: 轮询等待
  case_markers: ['async', 'polling']

case_info:
  - id: async_task_create_01
    title: 创建异步任务
    url: /api/task/create
    method: POST
    headers:
      Authorization: Bearer ${token}
    request_type: json
    payload:
      task_type: data_export
      params:
        dataset_id: 100
        format: csv
    extract:
      response:
        type_jsonpath:
          task_id: $.data.task_id
    assert_response:
      status_code: 200

  - id: async_task_wait_01
    title: 等待任务完成（请求前等待5秒）
    url: /api/task/status
    method: GET
    headers:
      Authorization: Bearer ${token}
    request_type: params
    payload:
      task_id: ${task_id}
    # 请求前等待时间（秒）
    wait_seconds: 5
    case_dependence:
      setup:
        interface: async_task_create_01
    extract:
      response:
        type_jsonpath:
          task_status: $.data.status
          task_result_url: $.data.result_url
    assert_response:
      status_code: 200
      # 任务状态为完成或处理中
      assert_status:
        type_jsonpath: "$.data.status"
        expect_value: ["completed", "processing"]
        assert_type: "contained_by"
```

**手动轮询等待示例：**

```python
# testcases/test_manual_case/test_async_polling.py
import pytest
import time
from config.settings import GLOBAL_VARS
from core.requests_utils.base_request import BaseRequest

@pytest.mark.async
def test_polling_task_completion():
    """
    轮询等待异步任务完成
    """
    task_id = GLOBAL_VARS.get("task_id")
    token = GLOBAL_VARS.get("token")
    host = GLOBAL_VARS.get("host")
    
    max_retries = 10
    retry_interval = 3  # 秒
    
    for i in range(max_retries):
        req_data = {
            "url": f"{host}/api/task/status",
            "method": "GET",
            "headers": {"Authorization": f"Bearer {token}"},
            "request_type": "params",
            "payload": {"task_id": task_id}
        }
        
        response = BaseRequest.send_request(req_data)
        status = response.json().get("data", {}).get("status")
        
        if status == "completed":
            # 任务完成，获取结果
            result_url = response.json().get("data", {}).get("result_url")
            assert result_url is not None
            GLOBAL_VARS["task_result_url"] = result_url
            return
        
        elif status == "failed":
            pytest.fail(f"Task {task_id} failed")
        
        # 筃待后继续轮询
        time.sleep(retry_interval)
    
    pytest.fail(f"Task {task_id} did not complete within {max_retries * retry_interval} seconds")
```

### 10. 批量数据验证

验证列表数据的批量断言，如分页数据、列表查询结果。

**场景：验证分页数据结构**

```yaml
case_common:
  allure_epic: 数据查询
  allure_feature: 列表接口
  allure_story: 批量验证
  case_markers: ['list', 'pagination']

case_info:
  - id: batch_list_01
    title: 获取用户列表并验证
    url: /api/user/list
    method: GET
    headers:
      Authorization: Bearer ${token}
    request_type: params
    payload:
      page: 1
      page_size: 20
      department: 研发部
    case_dependence:
      setup:
        interface: workflow_login_01
    extract:
      response:
        type_jsonpath:
          # 提取整个用户列表
          user_list: $.data.list
          total_count: $.data.total
          current_page: $.data.page
    assert_response:
      status_code: 200
      # 验证分页信息
      assert_page:
        type_jsonpath: "$.data.page"
        expect_value: 1
        assert_type: "=="
      assert_page_size:
        type_jsonpath: "$.data.page_size"
        expect_value: 20
        assert_type: "=="
      # 验证列表长度不超过page_size
      assert_list_length:
        type_jsonpath: "$.data.list"
        expect_value: 20
        assert_type: "len_le"  # 长度小于等于
      # 验证total大于0
      assert_total:
        type_jsonpath: "$.data.total"
        expect_value: 0
        assert_type: "gt"  # 大于
```

**复杂断言示例：**

```yaml
  - id: batch_verify_each_01
    title: 验证每个用户数据结构
    url: /api/user/list
    method: GET
    headers:
      Authorization: Bearer ${token}
    request_type: params
    payload:
      page: 1
      page_size: 10
    assert_response:
      status_code: 200
      # 验证第一个用户包含必要字段
      assert_first_user_id:
        type_jsonpath: "$.data.list[0].user_id"
        expect_value: null
        assert_type: "!="
      assert_first_user_name:
        type_jsonpath: "$.data.list[0].username"
        expect_value: null
        assert_type: "!="
        message: "第一个用户的username不能为空"
      # 验证列表中包含特定用户
      assert_contains_admin:
        type_jsonpath: "$.data.list[*].username"
        expect_value: "admin"
        assert_type: "contains"
```

### 11. 复合断言组合

多种断言类型组合使用，实现精细化验证。

**支持的断言类型：**

| 断言类型 | 说明 | 使用场景 |
|---------|------|---------|
| `==` | 相等断言 | 值精确匹配 |
| `!=` / `not_eq` | 不相等断言 | 值不匹配 |
| `gt` | 大于断言 | 数值比较 |
| `ge` | 大于等于断言 | 数值比较 |
| `lt` | 小于断言 | 数值比较 |
| `le` | 小于等于断言 | 数值比较 |
| `contains` | 包含断言 | 列表/字符串包含元素 |
| `contained_by` | 被包含断言 | 元素在列表中存在 |
| `startswith` | 开头匹配断言 | 字符串前缀验证 |
| `endswith` | 结尾匹配断言 | 字符串后缀验证 |
| `len_eq` | 长度相等断言 | 列表长度验证 |
| `len_gt` | 长度大于断言 | 列表长度验证 |
| `len_le` | 长度小于等于断言 | 列表长度验证 |
| `str_eq` | 字符串相等断言 | 字符串匹配 |

**组合断言示例：**

```yaml
case_info:
  - id: combined_assert_01
    title: 组合断言验证
    url: /api/product/detail
    method: GET
    request_type: params
    payload:
      product_id: 10001
    assert_response:
      status_code: 200
      # 数值范围验证
      assert_price:
        type_jsonpath: "$.data.price"
        expect_value: 0
        assert_type: "gt"  # 价格大于0
        message: "商品价格必须大于0"
      assert_stock:
        type_jsonpath: "$.data.stock"
        expect_value: 10
        assert_type: "ge"  # 库存大于等于10
      # 字符串验证
      assert_name:
        type_jsonpath: "$.data.name"
        expect_value: ""
        assert_type: "!="
        message: "商品名称不能为空"
      assert_code:
        type_jsonpath: "$.data.product_code"
        expect_value: "PRD"
        assert_type: "startswith"  # 商品编码以PRD开头
      # 列表验证
      assert_categories:
        type_jsonpath: "$.data.categories"
        expect_value: 1
        assert_type: "len_gt"  # 分类数量大于1
      assert_has_tag:
        type_jsonpath: "$.data.tags"
        expect_value: "热销"
        assert_type: "contains"  # 标签包含"热销"
```

### 12. Python 表达式动态计算

支持在参数中使用 Python 表达式进行动态计算。

**场景：动态计算订单金额**

```yaml
case_info:
  - id: expr_calc_01
    title: 使用表达式计算金额
    url: /api/order/create
    method: POST
    request_type: json
    payload:
      # 直接使用Python表达式
      unit_price: 99.00
      quantity: 3
      # 表达式计算总价
      total_price: "${99.00 * 3}"
      # 表达式计算折扣后价格
      discounted_price: "${99.00 * 3 * 0.9}"
      # 使用变量进行计算
      final_amount: "${total_price - discounted_price}"
      # 时间戳计算
      order_timestamp: "${int(time.time())}"
      # 随机选择
      payment_method: "${random.choice(['alipay', 'wechat', 'credit_card'])}"
    assert_response:
      status_code: 200
      assert_total:
        type_jsonpath: "$.data.total_price"
        expect_value: 297.00
        assert_type: "=="
      assert_discount:
        type_jsonpath: "$.data.discounted_price"
        expect_value: 267.3
        assert_type: "=="
```

### 13. 自定义函数调用

在测试用例中调用自定义工具函数。

```yaml
case_info:
  - id: custom_func_01
    title: 调用自定义函数
    url: /api/data/process
    method: POST
    request_type: json
    payload:
      # 调用 data_tools.py 中的函数
      file_list: "${list_to_str(target=['file1', 'file2', 'file3'])}"
      # Base64编码
      encoded_content: "${get_base64_content('test content')}"
      # AES加密（需配置密钥）
      encrypted_pwd: "${aes_encrypt_data(target_str='password123', ace_key='secret_key')}"
      # 数据切割
      split_result: "${split_data(target='a,b,c,d', split_char=',', start_index=0, end_index=2)}"
    assert_response:
      status_code: 200
```

### 最佳实践总结

1. **用例依赖顺序**：`variables` → `interface` → `database`，按此顺序处理依赖
2. **数据清理时机**：在 `assert_sql` 中验证数据后，及时注册清理任务
3. **Faker 数据唯一性**：使用时间戳或随机数确保测试数据唯一性
4. **断言信息完整**：为每个断言添加 `message` 描述，便于失败定位
5. **等待策略**：异步任务使用轮询 + 超时机制，避免无限等待
6. **Session 管理**：复杂认证流程建议手动编写 Python 测试用例
7. **SSH 安全**：SSH 隧道密码通过 `.env` 管理，不要硬编码
8. **表达式谨慎**：Python 表达式只在受信任的测试代码中使用