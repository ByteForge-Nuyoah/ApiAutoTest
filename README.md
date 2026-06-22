# API 自动化测试框架

## 一、框架介绍

本框架是基于 Python + Pytest + Allure + Loguru 实现的接口自动化测试框架，支持 YAML/Excel/gRPC 用例管理、多环境切换、多项目复用、以及丰富的通知机制。

## 二、核心功能

*   **配置分离与安全管理**
    *   使用 `.env` 文件统一管理账号、密码、密钥等敏感信息
    *   支持多项目/多环境配置 (`config/*.yaml`)，通过 `${VAR}` 动态引用环境变量
*   **多源用例生成与隔离**
    *   支持同时从 YAML、Excel、gRPC Proto 生成测试用例
    *   生成隔离: YAML 用例生成至 `testcases/test_auto_case/yaml_case/`，Excel 用例生成至 `testcases/test_auto_case/excel_case/`
    *   文件命名规范：Excel 用例生成文件名格式为 `test_excel_<文件名>.py`
    *   gRPC 用例自动转换为 HTTP RESTful API 格式
*   **多项目与多环境支持**
    *   通过 `-env <project_name>` 参数一键切换项目/环境配置
*   **其他特性**
    *   Session 会话自动关联
    *   动态参数提取与依赖注入 (JSONPath/Regex)
    *   数据库断言与数据清理
    *   Mock 服务支持（录制、回放、Stub）
    *   失败快照自动捕获
    *   Allure 定制化报告
    *   Loguru 优雅日志（统一日志级别）
    *   多渠道通知 (邮件/钉钉/企业微信)
    *   Docker 容器化支持
    *   GitHub Actions CI 集成
    *   完整的类型标注支持

## 三、项目结构

```text
ApiAutotest/
├── .github/                 # GitHub Actions CI 配置
│   └── workflows/
│       ├── ci.yaml          # CI/CD 流水线配置
│       └── dependency-check.yaml  # 依赖安全检查
├── config/                  # 配置文件目录
│   ├── settings.py          # 全局配置文件
│   ├── test.yaml            # 测试环境配置
│   └── prod.yaml            # 生产/正式环境配置
├── core/                    # 核心逻辑目录
│   ├── assertion_utils/     # 断言工具
│   ├── case_generate_utils/ # 用例自动生成工具
│   ├── data_utils/          # 数据处理工具
│   ├── report_utils/        # 报告生成与发送工具
│   ├── requests_utils/      # 请求封装工具
│   └── models.py            # 数据模型定义
├── files/                   # 测试数据文件 (上传下载等)
├── interfaces/              # 接口定义目录 (YAML/Excel/Proto 用例源文件)
│   └── projects/            # 按项目分类的接口定义
├── lib/                     # 第三方库或工具 (如 Allure 命令行工具)
├── outputs/                 # 输出产物目录
│   ├── logs/                # 运行日志
│   ├── report/              # 测试报告
│   ├── 、     # Mock 录制文件
│   └── download_files/      # 文件下载目录
├── testcases/               # 测试用例目录
│   ├── test_auto_case/      # 自动生成的测试用例
│   │   ├── excel_case/      # Excel 生成的用例
│   │   └── yaml_case/       # YAML 生成的用例
│   └── test_manual_case/    # 手动编写的测试用例
├── utils/                   # 通用工具类
│   ├── yaml_case_maker/     # 用例生成工具
│   │   ├── grpc_for_yaml.py      # gRPC 转 YAML 工具
│   │   ├── openapi_for_yaml.py   # OpenAPI 转 YAML 工具
│   │   ├── postman_for_yaml.py   # Postman 转 YAML 工具
│   │   └── swagger_for_yaml.py   # Swagger 转 YAML 工具
│   ├── database_utils/      # 数据库工具
│   ├── files_utils/         # 文件处理工具
│   ├── logger_utils/        # 日志工具
│   └── tools/               # 其他工具
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
TEST_DB_PORT=3306
TEST_DB_USER=root
TEST_DB_PWD=secret_password
TEST_DB_DATABASE=test_db

PROD_HOST=https://prod.api.com
PROD_DB_HOST=prod.db.com
PROD_DB_PWD=prod_secret_password

# 邮件通知配置
EMAIL_USER=your_email@example.com
EMAIL_PASSWORD=your_email_password
EMAIL_HOST=smtp.example.com
EMAIL_TO_LIST=user1@example.com,user2@example.com

# 钉钉/企业微信通知配置
DINGTALK_WEBHOOK=https://oapi.dingtalk.com/robot/send?access_token=xxx
DINGTALK_SECRET=SECxxx
WECHAT_WEBHOOK=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx
```

### 3. 配置项目 (config/*.yaml / *.yml)

在 `config/` 目录下创建项目配置文件（如 `prod.yaml` 或 `test.yaml`），支持引用 `.env` 变量：

```yaml
# config/prod.yaml 示例
host: ${PROD_HOST}
username: "admin"
password: "${PROD_PASSWORD}"

# 数据库配置
db_info:
  db_host: ${PROD_DB_HOST}
  db_port: ${PROD_DB_PORT}
  db_user: ${PROD_DB_USER}
  db_pwd: ${PROD_DB_PWD}
  db_database: ${PROD_DB_DATABASE}
```

### 4. 编写 YAML 用例

在 `interfaces/projects/` 下创建 YAML 用例文件：

```yaml
# interfaces/projects/workspace/test_login.yaml
case_common:
  allure_epic: workspace
  allure_feature: 用户登录模块
  allure_story: 登录接口
  case_markers:
    - workspace
    - smoke
    - login

case_info:
  - id: login_01
    title: 用户登录
    run: True
    severity: normal
    url: /api/crm/v4/user/login
    method: POST
    headers:
      Content-Type: application/json;charset=utf-8;
    cookies:
    request_type: json
    payload:
      username: admin
      password: '"123123"'
      appPlatform: work-space
      appVersion: 1.0.1
    files:
    wait_seconds: 2
    case_dependence:
    assert_response:
      status_code: 200
      assert_token_exist:
        message: 断言响应中data.token字段存在
        expect_value: "admin"
        assert_type: "=="
        type_jsonpath: "$.data.user.username"
    assert_sql:
    extract:
      response:
        type_jsonpath:
          token: $.data.token
          openid: $.data.user.openid
```

### 5. 运行测试

```bash
# 运行所有测试（不生成报告）
python run.py -env test -report no

# 运行指定标记的测试
python run.py -env test -m "smoke"

# 运行指定项目的测试
python run.py -env test -project workspace

# 生成 Allure HTML 报告
python run.py -env test -report yes

# 开启定时任务
python run.py -cron
```

### 6. 查看测试报告

测试完成后，报告会生成在 `outputs/report/allure_html/` 目录：

```bash
# 打开报告
open outputs/report/allure_html/index.html

# 或使用 Allure 命令行工具
allure serve outputs/report/allure_results
```

## 五、用例编写规范

### 1. YAML 用例结构说明

#### 1.1 公共配置字段（case_common）

```yaml
case_common:
  allure_epic: workspace              # @allure.epic() 装饰器内容
  allure_feature: 用户登录模块          # @allure.feature() 装饰器内容
  allure_story: 登录接口               # @allure.story() 装饰器内容
  case_markers:                        # 测试方法标记
    - workspace                        # 字符串格式：添加 @pytest.mark.workspace
    - smoke                            # 多个标记用列表形式
    - {'skip': '跳过执行该用例'}        # 字典格式：跳过用例并说明原因
```

**case_markers 说明：**
- 支持自定义标记
- 支持 pytest 内置标记：skip, usefixtures
- 格式：列表嵌套字符串或字典
- 示例：`['marker1', 'marker2', {'skip': '跳过原因'}]`

#### 1.2 公共依赖配置（common_dependence）

作用范围：**class** 级别，应用于整个测试类

```yaml
common_dependence:
  setup:                               # 前置依赖（测试类执行前）
    interface: login_01                # 接口依赖
    database:                          # 数据库依赖
      sql: "SELECT * FROM users"
      type_jsonpath:
        user_id: "$[0].user_id"
    env_vars:                          # 环境变量依赖
      timestamp: "${generate_time()}"
  teardown:                            # 后置依赖（测试类执行后）
    interface: logout_01
    database:
      sql: "DELETE FROM test_data"
    env_vars:
      status: "completed"
```

#### 1.3 用例信息字段（case_info）

具体测试用例数据，以**列表**形式管理：

```yaml
case_info:
  -
    id: login_01                       # 用例ID，全局唯一，用于接口依赖
    title: 用户登录                     # 用例标题
    severity: normal                   # 用例优先级
    run: True                          # 是否执行（True/False，空则True）
    url: /api/login                    # 请求路径（资源路径或全路径）
    method: POST                       # 请求方式：GET/POST/PUT/DELETE/PATCH等
    headers:                           # 请求头（注意：cookies值需为字符串）
      Content-Type: application/json
    cookies:                           # 请求cookies（DICT或CookieJar对象）
    request_type: json                 # 请求数据类型：params/json/file/data
    payload:                           # 请求参数
      username: admin
      password: "123456"
    files: upload/test.png             # 上传文件相对路径（自动拼接files目录）
    wait_seconds: 2                    # 请求后等待时间（秒）
    case_dependence:                   # 用例依赖（function级别）
      setup:
        interface: init_01
      teardown:
        env_vars:
          status: done
    assert_response:                   # 响应断言
      status_code: 200
    assert_sql:                        # 数据库断言
    extract:                           # 后置参数提取
      response:
        type_jsonpath:
          token: $.data.token
```

**字段详细说明：**

| 字段 | 必填 | 类型 | 说明 |
|------|------|------|------|
| `id` | 是 | str | 用例唯一标识，用于依赖调用 |
| `title` | 是 | str | 用例标题 |
| `severity` | 否 | str | 优先级：BLOCKER/CRITICAL/NORMAL/MINOR/TRIVIAL，默认NORMAL |
| `run` | 否 | bool | 是否执行，空或True执行，False不执行 |
| `url` | 是 | str | 请求路径（资源路径或完整URL） |
| `method` | 是 | str | 请求方式：GET/POST/PUT/PATCH/DELETE/HEAD/OPTION |
| `headers` | 是 | dict | 请求头，cookies值需为字符串类型 |
| `cookies` | 否 | dict/CookieJar | 请求cookies |
| `request_type` | 是 | str | 请求类型：params/json/file/data/export/none |
| `payload` | 否 | dict | 请求参数 |
| `files` | 否 | str | 上传文件相对路径（自动拼接files目录） |
| `wait_seconds` | 否 | int | 请求后等待秒数 |
| `case_dependence` | 否 | dict | 用例依赖（function级别） |
| `assert_response` | 是 | dict | 响应断言 |
| `assert_sql` | 否 | dict | 数据库断言 |
| `extract` | 否 | dict | 参数提取 |

**URL 处理说明：**
- 请求路径 = 基准路径（host）+ 资源路径（url）
- 通常填写资源路径即可，执行时会自动拼接
- 支持填写完整 URL，但建议使用资源路径保持统一

#### 1.4 用例依赖配置（case_dependence）

作用范围：**function** 级别，应用于单个测试方法

```yaml
case_dependence:
  setup:                               # 前置依赖（测试方法执行前）
    interface: login_01                # 接口依赖（str或list）
    database:                          # 数据库依赖
      sql: "SELECT * FROM users WHERE id=1"
      type_jsonpath:
        user_id: "$[0].user_id"
    env_vars:                          # 环境变量依赖
      timestamp: "${generate_time()}"
  teardown:                            # 后置依赖（测试方法执行后）
    interface:
      - cleanup_01
      - logout_01
    database:
      sql: "DELETE FROM test_data WHERE user_id=${user_id}"
    env_vars:
      test_status: "completed"
```

### 2. 断言方式说明

框架支持以下断言类型：

| 断言类型 | 枚举值 | 说明 | 示例 |
|---------|-------|------|------|
| `==` | equals | 相等断言 | 预期 == 实际 |
| `!=` | not_equals | 不相等断言 | 预期 != 实际 |
| `lt` | less_than | 小于断言 | 预期 < 实际 |
| `le` | less_than_or_equals | 小于等于断言 | 预期 ≤ 实际 |
| `gt` | greater_than | 大于断言 | 预期 > 实际 |
| `ge` | greater_than_or_equals | 大于等于断言 | 预期 ≥ 实际 |
| `str_eq` | string_equals | 字符串相等断言 | 字符串比较 |
| `len_eq` | length_equals | 长度相等断言 | len(预期) == len(实际) |
| `len_gt` | length_greater_than | 长度大于断言 | 预期 > len(实际) |
| `len_ge` | length_greater_than_or_equals | 长度大于等于断言 | 预期 ≥ len(实际) |
| `len_lt` | length_less_than | 长度小于断言 | 预期 < len(实际) |
| `len_le` | length_less_than_or_equals | 长度小于等于断言 | 预期 ≤ len(实际) |
| `contains` | contains | 包含断言 | 预期 in 实际 |
| `contained_by` | contained_by | 被包含断言 | 实际 in 预期 |
| `startswith` | startswith | 开头匹配断言 | 实际.startswith(预期) |
| `endswith` | endswith | 结尾匹配断言 | 实际.endswith(预期) |

**注意：**
- 断言时左侧是预期结果，右侧是实际结果
- 例如 `assert_type: lt` 表示：预期结果 < 实际结果

### 3. 响应断言说明

#### 3.1 断言状态码

```yaml
assert_response:
  status_code: 200                     # 直接断言HTTP状态码
```

#### 3.2 响应数据断言

```yaml
assert_response:
  assert_token_exist:                  # 断言标识（自定义，无实际意义）
    message: 断言响应中token字段存在      # 断言描述信息（可选）
    expect_value: "admin"              # 预期结果
    assert_type: ==                    # 断言类型
    type_jsonpath: $.data.user.username  # JSONPath提取实际结果
```

**断言参数说明：**

| 字段 | 必填 | 说明 |
|------|------|------|
| `message` | 否 | 断言描述信息 |
| `expect_value` | 是 | 预期结果 |
| `assert_type` | 是 | 断言类型 |
| `type_jsonpath` | 否 | JSONPath表达式从response.json()提取 |
| `type_re` | 否 | 正则表达式从response.text提取 |

**提取方式说明：**
- `type_jsonpath`：从响应JSON中提取，与`type_re`任选其一
- `type_re`：从响应文本中提取，与`type_jsonpath`任选其一
- 不填写提取方式：默认使用response.text作为实际结果

#### 3.3 响应断言示例

```yaml
# 示例1：JSONPath提取断言
assert_response:
  check_user_id:
    message: 验证用户ID正确
    expect_value: "12345"
    assert_type: ==
    type_jsonpath: $.data.user_id

# 示例2：正则表达式提取断言
assert_response:
  check_token_format:
    message: 验证token格式正确
    expect_value: "eyJ"
    assert_type: startswith
    type_re: '"token":"(.*?)"

# 示例3：包含断言
assert_response:
  check_message:
    message: 验证响应消息包含"成功"
    expect_value: "成功"
    assert_type: contains
    type_jsonpath: $.message
```

### 4. 数据库断言说明

#### 4.1 数据库断言参数

```yaml
assert_sql:
  check_user_record:                   # 断言标识（自定义）
    message: 断言数据库中存在用户记录    # 断言描述（可选）
    sql: "SELECT * FROM users WHERE username='admin'"  # SQL查询语句
    expect_value: 1                    # 预期结果
    assert_type: len_eq                # 断言类型
    type_jsonpath: "$[0].user_id"      # JSONPath从查询结果提取（可选）
```

**断言参数说明：**

| 字段 | 必填 | 说明 |
|------|------|------|
| `message` | 否 | 断言描述信息 |
| `sql` | 是 | SQL查询语句 |
| `expect_value` | 是 | 集预期结果 |
| `assert_type` | 是 | 断言类型 |
| `type_jsonpath` | 否 | JSONPath从查询结果提取 |
| `type_re` | 否 | 正则表达式从查询结果提取 |

**数据库查询说明：**
- 使用查询所有（query_all）方法，返回list格式
- 如果多条符合条件，返回所有数据
- 不填写提取方式：默认使用整个查询结果作为实际结果

#### 4.2 数据库断言示例

```yaml
# 示例1：验证查询结果数量
assert_sql:
  check_user_count:
    message: 断言数据库中用户记录数为1
    sql: "SELECT * FROM users WHERE user_id=${user_id}"
    expect_value: 1
    assert_type: len_eq

# 示例2：验证字段值（JSONPath提取）
assert_sql:
  check_user_status:
    message: 断言用户状态为active
    sql: "SELECT status FROM users WHERE user_id=${user_id}"
    expect_value: "active"
    assert_type: ==
    type_jsonpath: "$[0].status"

# 示例3：验证字段值（正则提取）
assert_sql:
  check_field_value:
    message: 断言字段值包含特定内容
    sql: "SELECT * FROM tokens"
    type_re: "'user_id': (.*?),"
    expect_value: ${user_id}
    assert_type: contains
```

### 5. 参数提取说明

目前支持从三种来源提取参数：
- **response**：响应数据
- **database**：数据库查询结果
- **case**：用例数据本身

支持三种提取方式：
- `type_jsonpath`：JSONPath表达式
- `type_re`：正则表达式
- `type_response`：Response对象属性

**注意事项：**
- 提取来源关键字（case/response/database）必须完全一致
- 提取方式关键字（type_jsonpath/type_re/type_response）必须完全一致
- 提取结果自动保存到全局变量GLOBAL_VARS，可在其他接口使用：`${变量名}`

#### 5.1 从响应数据提取参数

```yaml
extract:
  response:
    # JSONPath提取
    type_jsonpath:
      token: $.data.token
      user_id: $.data.user.userId
    # 正则表达式提取
    type_re:
      username: '"username":"(.*?)"
    # Response对象属性提取
    type_response:
      status_code: response.status_code
      cookies: response.cookies
```

**提取方式说明：**
- **JSONPath提取**：从response.json()提取，长度为1的列表自动取第一个元素
- **正则提取**：从response.text提取，长度为1的列表自动取第一个元素
- **Response属性提取**：获取Response对象属性值，如：
  - `response.status_code`
  - `response.cookies`
  - `response.headers`
  - `response.text`
  - `response.is_redirect`

#### 5.2 从用例数据提取参数

```yaml
extract:
  case:
    type_jsonpath:
      case_login: $.payload.login
    type_re:
      case_url_key: "'url': 'https?://[^/]+/api/(.*?)/login.json'"
```

**注意：**
- 如果需要提取url中的参数，实际执行时的url带有域名
- 例如：用例数据url是`/api/login.json`，执行时url是`https://example.com/api/login.json`
- 提取表达式需要对准带有域名的url

#### 5.3 从数据库提取参数

```yaml
extract:
  database:
    sql: "SELECT * FROM users WHERE username='admin'"
    type_jsonpath:
      sql_user_id: "$[0].user_id"
      sql_email: "$[0].email"
    type_re:
      sql_username: "'username': '(.*?)'"
```

**注意：**
- 必须有`sql`关键字
- 查询结果为list格式（查询所有）
- config/settings.py中的db_info必须不为空
- 不填写提取方式：默认返回整个查询结果

#### 5.4 兼容老版本写法

如果未指定提取来源，框架兼容老版本写法：

```yaml
# 老版本写法（无提取来源关键字）
extract:
  type_jsonpath:
    token: $.data.token
  type_re:
    username: '"username":"(.*?)"

# 新版本写法（推荐，明确提取来源）
extract:
  response:
    type_jsonpath:
      token: $.data.token
```

### 6. 用例依赖详细说明

#### 6.1 环境变量依赖（env_vars）

设置环境变量，支持常量、全局变量、内置函数：

```yaml
case_dependence:
  setup:
    env_vars:
      timestamp: "${generate_time('%Y%m%d%H%M%S')}"  # 使用内置函数
      random_code: "${generate_random_str(8)}"       # 使用内置函数
      user_login: flora                              # 直接赋值
  teardown:
    env_vars:
      test_status: "completed"
```

#### 6.2 接口依赖（interface）

依赖其他接口的执行结果：

```yaml
case_dependence:
  setup:
    interface: login_01               # 单个接口（字符串）
  teardown:
    interface:                        # 多个接口（列表）
      - cleanup_01
      - logout_01
```

**说明：**
- interface值指向其他用例的ID
- 支持字符串（单个）或列表（多个）
- 依赖接口执行后的extract结果自动更新到全局变量

#### 6.3 数据库依赖（database）

从数据库查询并提取参数：

```yaml
case_dependence:
  setup:
    database:
      sql: "SELECT * FROM users WHERE username='admin'"
      type_jsonpath:
        db_user_id: "$[0].user_id"
      type_re:
        db_username: "'username': '(.*?)'"
  teardown:
    database:
      -                                # 支持列表格式（多个查询）
        sql: "SELECT max_id FROM sequence"
        type_jsonpath:
          next_id: "$[0].max_id"
      -
        sql: "DELETE FROM test_data WHERE user_id=${db_user_id}"
```

**注意：**
- 必须有`sql`关键字
- config/settings.py中的db_info必须不为空
- 支持dict（单个）或list（多个）格式

### 7. 请求类型说明

| 类型 | 说明 | Content-Type | 使用场景 |
|------|------|--------------|----------|
| `params` | URL查询参数 | - | GET请求参数，拼接到URL |
| `json` | JSON格式请求体 | application/json | POST/PUT/PATCH请求 |
| `data` | 表单数据 | application/x-www-form-urlencoded | 表单提交 |
| `file` | 文件上传 | multipart/form-data | 文件上传场景 |
| `export` | 文件下载/导出 | - | 自动保存文件到outputs/download_files/ |
| `none` | 无请求参数 | - | 无参数的GET/DELETE请求 |

### 8. Excel用例特别说明

框架支持Excel多表单自动生成测试用例，每个表单作为一个测试模块。

#### 8.1 Excel表单命名规则

**示例：**
- Excel文件：`test_demo.xlsx`
- 表单1：`GitLink-登录模块`
- 表单2：`示例模块`

**生成规则：**

| 规则 | 说明 | 示例 |
|------|------|------|
| 包含"-" | 取"-"后部分首字母+文件名 | GitLink-登录模块 → test_demo_dlmk.py |
| 不包含"-" | 取表单名称首字母+文件名 | 示例模块 → test_demo_slmk.py |

**生成的测试文件：**

表单1生成的测试用例：
- 测试模块：`test_demo_dlmk.py`
- 测试类：`TestDemoDlmkAuto`
- 测试方法：`test_demo_dlmk_auto`

表单2生成的测试用例：
- 测试模块：`test_demo_slmk.py`
- 测试类：`TestDemoSlmkAuto`
- 测试方法：`test_demo_slmk_auto`

#### 8.2 Excel字段映射说明

Excel表单中的列名与YAML字段对应关系：

| Excel列名 | YAML字段 | 说明 |
|-----------|---------|------|
| 用例ID | id | 用例唯一标识 |
| 用例标题 | title | 用例标题 |
| 用例优先级 | severity | BLOCKER/CRITICAL/NORMAL/MINOR/TRIVIAL |
| 请求路径 | url | 接口路径 |
| 请求方式 | method | GET/POST/PUT/DELETE等 |
| 请求头 | headers | JSON格式字符串 |
| 请求cookies | cookies | JSON格式字符串 |
| 请求数据类型 | request_type | params/json/data/file |
| 请求参数 | payload | JSON格式字符串 |
| 上传文件 | files | 文件路径 |
| 响应断言 | assert_response | JSON格式字符串 |
| 数据库断言 | assert_sql | JSON格式字符串 |
| 后置提取 | extract | JSON格式字符串 |
| 用例依赖 | case_dependence | JSON格式字符串 |
| 前置等待 | wait_seconds | 数字 |

**注意事项：**
- Excel中的JSON字段需要以字符串形式填写
- 例如headers：`{"Content-Type": "application/json"}`
- 例如payload：`{"username": "admin", "password": "123456"}`

## 六、参数提取与依赖

### 1. JSONPath 提取

```yaml
extract:
  response:
    type_jsonpath:
      token: $.data.token
      user_id: $.data.user.userId
      username: $.data.user.username
```

### 2. 正则表达式提取

```yaml
extract:
  response:
    type_re:
      order_id: 'order_id=(\d+)'
      tracking_code: 'tracking_code=([A-Z0-9]+)'
```

### 3. 用例依赖

```yaml
case_dependence:
  setup:
    # 方式1: 接口依赖
    interface: login_01
    # 方式2: 环境变量依赖
    variables:
      timestamp: "${generate_time('%Y%m%d%H%M%S')}"
      random_code: "${generate_random_str(8)}"
    # 方式3: 数据库依赖
    database:
      sql: "SELECT user_id FROM users WHERE username='admin'"
      type_jsonpath:
        user_id: "$[0].user_id"
  teardown:
    # 后置清理（可选）
    variables:
      status: "completed"
```

## 七、数据库断言

### 1. 基本数据库断言

```yaml
assert_sql:
  check_user_exists:
    message: 断言数据库：验证用户记录存在
    sql: "SELECT * FROM users WHERE username='admin'"
    expect_value: 1
    assert_type: "len_eq"
```

### 2. 数据库字段断言

```yaml
assert_sql:
  verify_user_status:
    message: 断言数据库：验证用户状态为激活
    sql: "SELECT status FROM users WHERE username='admin'"
    expect_value: "active"
    assert_type: "=="
    type_jsonpath: "$[0].status"
```

### 3. 数据库断言类型

支持的断言类型与响应断言相同，常用：
- `len_eq`: 验证查询结果数量
- `==`: 验证具体字段值
- `contains`: 验证字段包含特定值

## 八、Mock 服务

### 1. Mock 配置

```python
# config/settings.py
MOCK_CONFIG = {
    "enabled": True,
    "mode": "disabled",  # disabled, stub, record, replay, mixed
    "recordings_dir": "outputs/mock_recordings",
    "auto_save": True,
    "default_delay": 0.0,
}
```

### 2. Mock 模式说明

| 模式 | 说明 |
|------|------|
| `disabled` | 禁用 Mock，发送真实请求 |
| `stub` | 使用预定义的 Mock 响应 |
| `record` | 录制真实响应并保存 |
| `replay` | 使用录制的响应，不发送真实请求 |
| `mixed` | 混合模式：有录制就用录制，否则发送真实请求并录制 |

### 3. 运行时切换 Mock 模式

```bash
# 使用 Stub 模式
python run.py --mock stub

# 使用 Record 模式录制响应
python run.py --mock record

# 使用 Replay 模式回放录制
python run.py --mock replay
```

## 九、日志管理

### 1. 日志级别配置

```python
# config/settings.py
LOG_LEVEL = "DEBUG"      # 文件日志级别
LOG_LEVEL_STD = "DEBUG"  # 控制台日志级别
```

### 2. 支持的日志级别

| 级别 | 说明 | 使用场景 |
|------|------|----------|
| `TRACE` | 详细追踪 | 提取结果、跳过处理、调试信息 |
| `DEBUG` | 调试信息 | 请求/响应详情、数据处理 |
| `INFO` | 关键信息 | 用例执行、重要事件 |
| `SUCCESS` | 成功标记 | 测试通过、执行完成 |
| `WARNING` | 警告信息 | 格式错误、配置缺失、潜在问题 |
| `ERROR` | 错误信息 | 异常情况、断言失败 |
| `CRITICAL` | 严重错误 | 程序崩溃、致命错误 |

### 3. 日志文件位置

- 文件日志：`outputs/log/api.log`
- 错误日志：`outputs/log/error.log`

## 十、通知机制

### 1. 通知类型配置

```python
# config/settings.py
SEND_RESULT_TYPE = 0  # 0:不发送, 1:钉钉, 2:企业微信, 3:邮件, 4:全部
```

### 2. 钉钉通知

```yaml
# .env
DINGTALK_WEBHOOK=https://oapi.dingtalk.com/robot/send?access_token=xxx
DINGTALK_SECRET=SECxxx
```

### 3. 企业微信通知

```yaml
# .env
WECHAT_WEBHOOK=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx
```

### 4. 邮件通知

```yaml
# .env
EMAIL_USER=your_email@example.com
EMAIL_PASSWORD=your_email_password
EMAIL_HOST=smtp.example.com
EMAIL_TO_LIST=user1@example.com,user2@example.com
```

## 十一、数据清理策略

### 1. 配置数据清理

```python
# config/settings.py
DATA_CLEANUP_CONFIG = {
    "enabled": True,
    "databases": {
        "default": {
            "host": "${DB_HOST}",
            "port": 3306,
            "user": "${DB_USER}",
            "password": "${DB_PASSWORD}",
            "database": "${DB_NAME}",
        }
    },
    "cleanup_on_failure": True,
    "cleanup_on_success": True,
}
```

### 2. 清理策略类型

| 策略 | 适用场景 | 说明 |
|------|----------|------|
| 注册清理 | 需精确控制时机 | 手动注册清理任务 |
| 快照恢复 | 保持数据原状 | 自动恢复测试数据 |
| 手动控制 | 复杂测试场景 | 完全手动管理 |

## 十二、失败快照

### 1. 启用失败快照

```bash
# 启用（默认）
python run.py --snapshot on

# 禁用
python run.py --snapshot off
```

### 2. 快照内容

失败快照保存在 `outputs/report/failure_snapshots/`，包含：
- 失败时间戳
- 用例 ID 和标题
- 异常类型和堆栈
- 全局变量状态
- 请求/响应数据

## 十三、gRPC 接口测试

### 1. Proto 文件定义

```protobuf
syntax = "proto3";
package user;

message LoginRequest {
    string username = 1;
    string password = 2;
}

message LoginResponse {
    int32 code = 1;
    string message = 2;
    string token = 3;
}

service UserService {
    rpc Login(LoginRequest) returns (LoginResponse);
}
```

### 2. 自动生成测试用例

```python
from utils.yaml_case_maker.grpc_for_yaml import GrpcForYaml

grpc_parser = GrpcForYaml(
    case_dir="./interfaces/projects/user_service",
    proto_path="./protos/user.proto"
)
grpc_parser.yaml_file_dump()
```

### 3. 生成的 YAML 用例

工具自动将 gRPC 转换为 HTTP 格式（通过 gRPC-Gateway）：

```yaml
case_info:
- id: Login_01
  title: 测试 Login
  url: /user.UserService/Login  # HTTP URL
  method: POST                   # POST 方法
  headers:
    Content-Type: application/json
  request_type: json
  payload:
    username: string_value
    password: string_value
  assert_response:
    status_code: 200
```

### 4. 配置 gRPC-Gateway

**方式一：gRPC-Gateway**

```bash
# 安装
go install github.com/grpc-ecosystem/grpc-gateway/v2/protoc-gen-grpc-gateway@latest

# 生成反向代理
protoc -I . --grpc-gateway_out ./gateway user.proto
```

**方式二：Envoy 配置**

```yaml
http_filters:
- name: envoy.filters.http.grpc_json_transcoder
  config:
    proto_descriptor: "/path/to/api.pb"
    services: ["user.UserService"]
```

### 5. 运行 gRPC 测试

```bash
# 运行 gRPC-HTTP 测试
python run.py -env test -m "grpc_http"
```

### 6. 字段类型映射

| Proto 类型 | JSON 默认值 |
|-----------|------------|
| string | "string_value" |
| int32/int64 | 0 |
| float/double | 0.0 |
| bool | false |
| repeated | [value] |
| message | {...} |

## 十四、定时任务

### 1. 配置定时任务

```python
# config/settings.py
SCHEDULE_CONFIG = {
    "enabled": True,
    "run_time": "22:00",  # 每天22点执行
    "env": "test",
    "report": "yes",
    "markers": None,
}
```

### 2. 启动定时任务

```bash
python run.py -cron
```

## 十五、Docker 容器化

### 1. 构建镜像

```bash
docker build -t api-autotest:latest .
```

### 2. 运行容器

```bash
docker run -d \
  --name api-autotest \
  -v $(pwd)/outputs:/app/outputs \
  -v $(pwd)/config:/app/config \
  -v $(pwd)/interfaces:/app/interfaces \
  api-autotest:latest \
  python run.py -env test -report yes
```

## 十六、CI/CD 集成

### 1. GitHub Actions 配置

```yaml
# .github/workflows/ci.yaml
name: API Automation Test

on:
  push:
    branches: [ main, dev ]
  pull_request:
    branches: [ main ]
  schedule:
    - cron: '0 2 * * *'  # 每天2点执行

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    
    - name: Run tests
      run: |
        python run.py -env test -report yes
    
    - name: Upload Allure report
      uses: actions/upload-artifact@v2
      with:
        name: allure-report
        path: outputs/report/allure_html
```

## 十七、最佳实践

### 1. 用例编写建议

1. **用例 ID 规范**：使用 `{功能}_{操作}_{序号}` 格式，如 `user_login_01`
2. **断言完整性**：每个断言都添加 `message` 描述，便于失败定位
3. **依赖顺序**：`variables` → `interface` → `database`
4. **参数提取**：优先使用 JSONPath，正则表达式用于复杂场景
5. **数据清理**：在 `assert_sql` 验证后及时注册清理任务

### 2. 测试数据管理

1. **唯一性标识**：使用时间戳或随机数确保数据唯一
2. **敏感信息**：通过 `.env` 管理，不硬编码
3. **测试隔离**：每个用例使用独立测试数据
4. **数据工厂**：使用 Faker 库生成随机测试数据

### 3. 日志使用规范

1. **TRACE**：提取结果、跳过处理
2. **DEBUG**：请求/响应详情、数据处理
3. **INFO**：用例执行、关键事件
4. **WARNING**：格式错误、配置缺失
5. **ERROR**：异常情况、断言失败
6. **CRITICAL**：致命错误

### 4. gRPC 测试建议

1. **使用 gRPC-Gateway**：保持框架统一，无需修改核心代码
2. **配置环境变量**：网关地址配置在 `config/*.yaml`
3. **JSON 格式**：便于调试和查看
4. **完整兼容**：支持所有现有断言、提取、依赖功能

### 5. 团队协作建议

1. **版本控制**：用例文件纳入 Git 管理
2. **代码审查**：重要用例变更需要 Code Review
3. **持续集成**：每次提交自动运行测试
4. **报告分享**：使用通知机制及时分享测试结果
5. **文档更新**：用例变更同步更新文档

## 十八、常见问题

### Q1: 如何切换测试环境？

```bash
# 切换到 test 环境
python run.py -env test

# 切换到 prod 环境
python run.py -env prod
```

### Q2: 如何只运行特定用例？

```bash
# 运行 smoke 标记的用例
python run.py -m "smoke"

# 运行多个标记
python run.py -m "smoke or login"
```

### Q3: 如何调试单个用例？

```bash
# 使用 pytest 直接运行
pytest testcases/test_auto_case/yaml_case/workspace/test_yaml_login.py::test_yaml_login_auto -v -s
```

### Q4: 如何处理用例依赖？

```yaml
case_dependence:
  setup:
    interface: login_01  # 先执行 login_01 提取 token
```

### Q5: 如何添加数据库断言？

```yaml
assert_sql:
  verify_data:
    sql: "SELECT * FROM table WHERE condition"
    expect_value: 1
    assert_type: "len_eq"
```

### Q6: 如何测试 gRPC 接口？

通过 gRPC-Gateway 转换为 HTTP 测试，无需修改框架代码：

```bash
# 1. 生成用例
python generate_grpc_cases.py

# 2. 运行测试
python run.py -m "grpc_http"
```

## 十九、技术支持

- **作者**：会飞的🐟
- **邮箱**：workspace@example.com
- **项目地址**：[GitHub Repository]
- **文档版本**：v2.0

## 二十、更新日志

### v2.0 (2026-06-22)

**新增功能：**
- ✨ gRPC 接口测试支持（通过 HTTP 网关转换）
- ✨ 完整的类型标注支持
- ✨ 统一的日志级别管理
- ✨ Mock 服务增强（录制、回放、混合模式）
- ✨ 失败快照自动捕获
- ✨ 数据清理策略优化
- ✨ SSH 隧道数据库连接

**优化改进：**
- 🎨 统一报告标题格式
- 🎨 日志级别规范化（TRACE/WARNING/ERROR）
- 🎨 代码可读性和可维护性提升
- 📝 README 文档完善
- 📝 gRPC 测试使用说明

**Bug 修复：**
- 🐛 修复数据库断言 db_connect 初始化问题
- 🐛 修复 CaseDependenceHandler db_info 传递问题
- 🐛 修复日志级别混乱问题

---

**注意**：本框架持续更新，如有问题或建议请联系作者或提交 Issue。