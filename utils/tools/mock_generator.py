# -*- coding: utf-8 -*-
# @Author  : 会飞的🐟
# @File    : mock_generator.py
# @Desc: 基于 OpenAPI/Swagger 文档自动生成 Mock 数据

import os
import json
import time
import random
import string
import re
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from loguru import logger
from jsonpath import jsonpath
from faker import Faker


class MockDataGenerator:
    """
    Mock 数据生成器
    根据 OpenAPI Schema 自动生成模拟数据
    """
    
    def __init__(self, locale: str = "zh_CN"):
        """
        初始化数据生成器
        :param locale: 语言环境
        """
        self.faker = Faker(locale)
        self._type_generators = {
            "string": self._generate_string,
            "integer": self._generate_integer,
            "number": self._generate_number,
            "boolean": self._generate_boolean,
            "array": self._generate_array,
            "object": self._generate_object,
        }
    
    def generate_from_schema(self, schema: Dict, context: Dict = None) -> Any:
        """
        根据 Schema 生成数据
        :param schema: OpenAPI Schema
        :param context: 上下文信息
        :return: 生成的数据
        """
        if not schema:
            return None
        
        schema_type = schema.get("type", "object")
        generator = self._type_generators.get(schema_type)
        
        if generator:
            return generator(schema, context or {})
        
        return None
    
    def _generate_string(self, schema: Dict, context: Dict) -> str:
        """
        生成字符串类型数据
        """
        format_type = schema.get("format", "")
        pattern = schema.get("pattern")
        enum = schema.get("enum")
        min_length = schema.get("minLength", 1)
        max_length = schema.get("maxLength", 50)
        example = schema.get("example")
        field_name = context.get("field_name", "").lower()
        
        # 如果有枚举值，随机选择一个
        if enum:
            return random.choice(enum)
        
        # 如果有示例值，直接返回
        if example is not None:
            return str(example)
        
        # 根据字段名推断数据类型
        if field_name:
            if "email" in field_name:
                return self.faker.email()
            elif "phone" in field_name or "mobile" in field_name:
                return self.faker.phone_number()
            elif "name" in field_name:
                if "user" in field_name or "nick" in field_name:
                    return self.faker.name()
                elif "first" in field_name:
                    return self.faker.first_name()
                elif "last" in field_name:
                    return self.faker.last_name()
            elif "address" in field_name:
                return self.faker.address()
            elif "city" in field_name:
                return self.faker.city()
            elif "country" in field_name:
                return self.faker.country()
            elif "company" in field_name:
                return self.faker.company()
            elif "url" in field_name or "link" in field_name:
                return self.faker.url()
            elif "image" in field_name or "avatar" in field_name or "photo" in field_name:
                return self.faker.image_url()
            elif "date" in field_name:
                if "time" in field_name:
                    return self.faker.date_time().strftime("%Y-%m-%d %H:%M:%S")
                return self.faker.date()
            elif "time" in field_name:
                return self.faker.time()
            elif "password" in field_name or "pwd" in field_name:
                return "Test@123456"
            elif "token" in field_name:
                return f"mock_token_{self._random_string(16)}"
            elif "id" in field_name:
                return str(random.randint(1, 10000))
            elif "openid" in field_name or "openid" in field_name:
                return f"mock_openid_{self._random_string(20)}"
            elif "code" in field_name:
                return str(random.randint(100000, 999999))
        
        # 根据 format 类型生成
        if format_type == "date-time":
            return self.faker.date_time().isoformat()
        elif format_type == "date":
            return self.faker.date()
        elif format_type == "time":
            return self.faker.time()
        elif format_type == "email":
            return self.faker.email()
        elif format_type == "uri" or format_type == "url":
            return self.faker.url()
        elif format_type == "uuid":
            return self.faker.uuid4()
        elif format_type == "phone":
            return self.faker.phone_number()
        elif format_type == "ipv4":
            return self.faker.ipv4()
        elif format_type == "ipv6":
            return self.faker.ipv6()
        
        # 如果有正则表达式，尝试生成匹配的数据
        if pattern:
            try:
                return self._generate_from_pattern(pattern, min_length, max_length)
            except Exception:
                pass
        
        # 默认生成随机字符串
        return self._random_string(random.randint(min_length, max_length))
    
    def _generate_integer(self, schema: Dict, context: Dict) -> int:
        """
        生成整数类型数据
        """
        example = schema.get("example")
        if example is not None:
            return int(example)
        
        minimum = schema.get("minimum", 0)
        maximum = schema.get("maximum", 1000)
        exclusive_minimum = schema.get("exclusiveMinimum", False)
        exclusive_maximum = schema.get("exclusiveMaximum", False)
        
        min_val = minimum + 1 if exclusive_minimum else minimum
        max_val = maximum - 1 if exclusive_maximum else maximum
        
        field_name = context.get("field_name", "").lower()
        
        # 根据字段名推断数据
        if field_name:
            if "id" in field_name:
                return random.randint(1, 10000)
            elif "count" in field_name or "total" in field_name or "num" in field_name:
                return random.randint(0, 100)
            elif "age" in field_name:
                return random.randint(18, 65)
            elif "status" in field_name:
                return random.choice([0, 1, 2])
            elif "code" in field_name:
                return random.randint(200, 500)
        
        return random.randint(min_val, max_val)
    
    def _generate_number(self, schema: Dict, context: Dict) -> float:
        """
        生成数字类型数据
        """
        example = schema.get("example")
        if example is not None:
            return float(example)
        
        minimum = schema.get("minimum", 0.0)
        maximum = schema.get("maximum", 1000.0)
        
        field_name = context.get("field_name", "").lower()
        
        if field_name:
            if "price" in field_name or "amount" in field_name or "money" in field_name:
                return round(random.uniform(0.01, 10000.0), 2)
            elif "rate" in field_name or "ratio" in field_name or "percent" in field_name:
                return round(random.uniform(0.0, 1.0), 4)
            elif "lat" in field_name or "latitude" in field_name:
                return round(random.uniform(-90.0, 90.0), 6)
            elif "lng" in field_name or "longitude" in field_name:
                return round(random.uniform(-180.0, 180.0), 6)
        
        return round(random.uniform(minimum, maximum), 2)
    
    def _generate_boolean(self, schema: Dict, context: Dict) -> bool:
        """
        生成布尔类型数据
        """
        example = schema.get("example")
        if example is not None:
            return bool(example)
        
        return random.choice([True, False])
    
    def _generate_array(self, schema: Dict, context: Dict) -> List:
        """
        生成数组类型数据
        """
        items_schema = schema.get("items", {})
        min_items = schema.get("minItems", 1)
        max_items = schema.get("maxItems", 5)
        
        count = random.randint(min_items, max_items)
        
        result = []
        for _ in range(count):
            item = self.generate_from_schema(items_schema, context)
            result.append(item)
        
        return result
    
    def _generate_object(self, schema: Dict, context: Dict) -> Dict:
        """
        生成对象类型数据
        """
        properties = schema.get("properties", {})
        required = schema.get("required", [])
        
        result = {}
        for prop_name, prop_schema in properties.items():
            # 跳过非必填字段（50%概率）
            if prop_name not in required and random.random() < 0.5:
                continue
            
            prop_context = {**context, "field_name": prop_name}
            result[prop_name] = self.generate_from_schema(prop_schema, prop_context)
        
        return result
    
    def _random_string(self, length: int) -> str:
        """
        生成随机字符串
        """
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))
    
    def _generate_from_pattern(self, pattern: str, min_length: int, max_length: int) -> str:
        """
        根据正则表达式生成字符串
        """
        # 简化处理：生成符合长度的随机字符串
        length = random.randint(min_length, max_length)
        return self._random_string(length)


class OpenApiMockGenerator:
    """
    基于 OpenAPI 文档生成 Mock 配置
    """
    
    def __init__(self, output_dir: str = None):
        """
        初始化
        :param output_dir: Mock 配置输出目录
        """
        self.data_generator = MockDataGenerator()
        self.output_dir = output_dir or os.path.join(os.path.dirname(__file__), "mock_configs")
    
    def generate_from_openapi(self, openapi_path: str, project_name: str = None) -> Dict[str, Any]:
        """
        从 OpenAPI 文档生成 Mock 配置
        :param openapi_path: OpenAPI 文档路径
        :param project_name: 项目名称
        :return: 生成的 Mock 配置
        """
        # 读取 OpenAPI 文档
        with open(openapi_path, "r", encoding="utf-8") as f:
            openapi_doc = json.load(f)
        
        # 解析接口
        paths = openapi_doc.get("paths", {})
        components = openapi_doc.get("components", {})
        
        mock_rules = {}
        
        for path, methods in paths.items():
            for method, operation in methods.items():
                if method.lower() not in ["get", "post", "put", "delete", "patch"]:
                    continue
                
                # 生成规则名称
                operation_id = operation.get("operationId", f"{method}_{path}".replace("/", "_"))
                rule_name = f"{project_name}_{operation_id}" if project_name else operation_id
                
                # 解析响应 Schema
                response_schema = self._extract_response_schema(operation, components)
                
                if response_schema:
                    # 生成 Mock 数据
                    mock_data = self.data_generator.generate_from_schema(response_schema)
                    
                    # 构建响应
                    mock_response = {
                        "status_code": 200,
                        "headers": {
                            "Content-Type": "application/json;charset=utf-8",
                            "X-Request-Id": f"mock-{int(time.time() * 1000)}"
                        },
                        "body": {
                            "code": 200,
                            "message": "success",
                            "data": mock_data,
                            "timestamp": int(time.time() * 1000)
                        }
                    }
                    
                    mock_rules[rule_name] = {
                        "url_pattern": re.escape(path),
                        "method": method.upper(),
                        "response": mock_response,
                        "description": operation.get("summary", ""),
                        "tags": operation.get("tags", [])
                    }
        
        return mock_rules
    
    def _extract_response_schema(self, operation: Dict, components: Dict) -> Optional[Dict]:
        """
        提取响应 Schema
        """
        responses = operation.get("responses", {})
        
        # 查找 200 响应
        success_response = responses.get("200") or responses.get("default")
        if not success_response:
            return None
        
        content = success_response.get("content", {})
        json_content = content.get("application/json", {})
        schema = json_content.get("schema", {})
        
        if not schema:
            return None
        
        # 解析 $ref
        if "$ref" in schema:
            schema = self._resolve_ref(schema["$ref"], components)
        
        # 解析嵌套的 $ref
        schema = self._resolve_all_refs(schema, components)
        
        return schema
    
    def _resolve_ref(self, ref: str, components: Dict) -> Dict:
        """
        解析 $ref 引用
        """
        if not ref.startswith("#/"):
            return {}
        
        parts = ref[2:].split("/")
        result = components
        
        for part in parts[1:]:  # 跳过 "components"
            if part in result:
                result = result[part]
            else:
                return {}
        
        return result
    
    def _resolve_all_refs(self, schema: Dict, components: Dict) -> Dict:
        """
        递归解析所有 $ref
        """
        if not isinstance(schema, dict):
            return schema
        
        if "$ref" in schema:
            resolved = self._resolve_ref(schema["$ref"], components)
            return self._resolve_all_refs(resolved, components)
        
        for key, value in schema.items():
            if isinstance(value, dict):
                schema[key] = self._resolve_all_refs(value, components)
            elif isinstance(value, list):
                schema[key] = [
                    self._resolve_all_refs(item, components) if isinstance(item, dict) else item
                    for item in value
                ]
        
        return schema
    
    def generate_mock_config_file(self, mock_rules: Dict, project_name: str) -> str:
        """
        生成 Mock 配置文件
        :param mock_rules: Mock 规则
        :param project_name: 项目名称
        :return: 配置文件路径
        """
        # 确保输出目录存在
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 生成配置文件内容
        config_content = self._generate_config_content(mock_rules, project_name)
        
        # 写入文件
        config_file = os.path.join(self.output_dir, f"{project_name}_mock_config.py")
        with open(config_file, "w", encoding="utf-8") as f:
            f.write(config_content)
        
        logger.info(f"生成 Mock 配置文件: {config_file}")
        return config_file
    
    def _generate_config_content(self, mock_rules: Dict, project_name: str) -> str:
        """
        生成配置文件内容
        """
        lines = [
            "# -*- coding: utf-8 -*-",
            f'# @Author  : Mock Generator',
            f'# @File    : {project_name}_mock_config.py',
            f'# @Desc: {project_name} 项目 Mock 配置（自动生成）',
            "",
            "import time",
            "import re",
            "from utils.tools.mock_service import MockRule, MockResponse",
            "",
            "",
            f"def get_{project_name}_mock_rules():",
            '    """',
            f"    获取 {project_name} 项目的 Mock 规则",
            "    :return: Mock 规则列表",
            '    """',
            "    rules = []",
            "",
        ]
        
        for rule_name, rule_config in mock_rules.items():
            response = rule_config["response"]
            body = response.get("body", {})
            
            lines.extend([
                f"    # {rule_config.get('description', rule_name)}",
                f"    {rule_name}_rule = MockRule(",
                f'        name="{rule_name}",',
                f'        url_pattern=r"{rule_config["url_pattern"]}",',
                f'        method="{rule_config["method"]}",',
                f"        response_builder=build_{rule_name}_response,",
                f"        delay=0.1,",
                f"        priority=10",
                f"    )",
                f"    rules.append({rule_name}_rule)",
                "",
            ])
        
        lines.extend([
            "    return rules",
            "",
            "",
        ])
        
        # 生成响应构建函数
        for rule_name, rule_config in mock_rules.items():
            response = rule_config["response"]
            body = response.get("body", {})
            
            lines.extend([
                f"def build_{rule_name}_response(url: str, method: str, **kwargs) -> MockResponse:",
                '    """',
                f"    构建 {rule_config.get('description', rule_name)} Mock 响应",
                "    :param url: 请求 URL",
                "    :param method: 请求方法",
                "    :param kwargs: 其他参数",
                "    :return: Mock 响应对象",
                '    """',
                f"    response_data = {json.dumps(body, ensure_ascii=False, indent=8)}",
                "",
                "    return MockResponse(",
                f"        status_code={response.get('status_code', 200)},",
                f"        headers={response.get('headers', {})},",
                "        body=response_data,",
                "        elapsed=0.15",
                "    )",
                "",
                "",
            ])
        
        return "\n".join(lines)


def generate_mock_from_yaml(yaml_path: str, project_name: str = None) -> Dict[str, Any]:
    """
    从 YAML 测试用例文件生成 Mock 配置
    :param yaml_path: YAML 文件路径
    :param project_name: 项目名称
    :return: Mock 规则
    """
    from ruamel.yaml import YAML
    
    yaml = YAML()
    with open(yaml_path, "r", encoding="utf-8") as f:
        yaml_data = yaml.load(f)
    
    if not yaml_data:
        logger.warning(f"YAML 文件为空或解析失败: {yaml_path}")
        return {}
    
    mock_rules = {}
    data_generator = MockDataGenerator()
    
    case_info_list = yaml_data.get("case_info", [])
    if not isinstance(case_info_list, list):
        case_info_list = [case_info_list] if case_info_list else []
    
    for case_info in case_info_list:
        if not case_info:
            continue
        
        case_id = case_info.get("id", "unknown")
        url = case_info.get("url", "")
        method = case_info.get("method", "GET").upper()
        title = case_info.get("title", "")
        
        if not url:
            logger.warning(f"用例 {case_id} 缺少 URL，跳过")
            continue
        
        # 生成规则名称
        rule_name = f"{project_name}_{case_id}" if project_name else case_id
        
        # 从断言中提取预期数据
        assert_response = case_info.get("assert_response", {}) or {}
        extract_data = case_info.get("extract", {}) or {}
        response_extract = extract_data.get("response", {}).get("type_jsonpath", {})
        
        # 生成基础 Mock 数据
        mock_data = {}
        
        # 从 extract 中提取字段
        if response_extract:
            for key, jsonpath_expr in response_extract.items():
                mock_data[key] = data_generator._random_string(16)
        
        # 从断言中提取字段
        for assert_key, assert_config in assert_response.items():
            if assert_key == "status_code":
                continue
            
            if isinstance(assert_config, dict):
                jsonpath_expr = assert_config.get("type_jsonpath", "")
                expect_value = assert_config.get("expect_value")
                
                # 从 jsonpath 中提取字段名
                if jsonpath_expr:
                    field_match = re.search(r'\$\.data\.?(\w*)', jsonpath_expr)
                    if field_match:
                        field_name = field_match.group(1)
                        if field_name and field_name not in mock_data:
                            if expect_value:
                                mock_data[field_name] = expect_value
                            else:
                                mock_data[field_name] = data_generator._random_string(16)
        
        # 如果没有提取到任何数据，生成默认数据
        if not mock_data:
            mock_data = {
                "id": random.randint(1, 1000),
                "message": "success"
            }
        
        # 构建响应
        mock_response = {
            "status_code": 200,
            "headers": {
                "Content-Type": "application/json;charset=utf-8"
            },
            "body": {
                "code": 200,
                "message": "success",
                "data": mock_data,
                "timestamp": int(time.time() * 1000)
            }
        }
        
        mock_rules[rule_name] = {
            "url_pattern": re.escape(url),
            "method": method,
            "response": mock_response,
            "description": title
        }
    
    return mock_rules


if __name__ == "__main__":
    # 示例：从 OpenAPI 文档生成 Mock 配置
    generator = OpenApiMockGenerator()
    
    # 示例 Schema
    schema = {
        "type": "object",
        "properties": {
            "id": {"type": "integer"},
            "username": {"type": "string"},
            "email": {"type": "string", "format": "email"},
            "phone": {"type": "string"},
            "age": {"type": "integer"},
            "created_at": {"type": "string", "format": "date-time"}
        }
    }
    
    data_gen = MockDataGenerator()
    mock_data = data_gen.generate_from_schema(schema)
    print(json.dumps(mock_data, ensure_ascii=False, indent=2))
