# -*- coding: utf-8 -*-
# @Author  : 会飞的🐟
# @File    : grpc_for_yaml.py
# @Desc: gRPC用例生成模块

import sys
import os
import json
import tempfile
import subprocess
from ruamel import yaml
from loguru import logger
from google.protobuf.descriptor_pb2 import FileDescriptorSet
from google.protobuf.descriptor import FieldDescriptor


class GrpcForYaml:
    """
    将 protobuf (.proto) 文件转为 YAML 格式用例
    """

    def __init__(self, case_dir, proto_path):
        """
        :param case_dir: 用例需要保存的目录
        :param proto_path: 需要读取的 .proto 文件路径
        """
        self.case_dir = case_dir
        self.proto_path = proto_path
        self.messages = {}  # 存储消息定义
        self.services = []  # 存储服务定义

    def _compile_proto(self):
        """
        使用 protoc 编译 proto 文件并生成描述符集
        """
        if not os.path.exists(self.proto_path):
            raise FileNotFoundError(f"Proto file not found: {self.proto_path}")

        proto_dir = os.path.dirname(os.path.abspath(self.proto_path))
        proto_file = os.path.basename(self.proto_path)

        with tempfile.NamedTemporaryFile(suffix='.desc', delete=False) as tmp_desc:
            desc_path = tmp_desc.name

        # 构建 protoc 命令
        # 注意：这里假设 grpc_tools 已安装
        # 使用绝对路径来避免相对路径问题
        abs_proto_path = os.path.abspath(self.proto_path)
        cmd = [
            sys.executable, "-m", "grpc_tools.protoc",
            f"-I{proto_dir}",
            f"--descriptor_set_out={desc_path}",
            "--include_imports",
            abs_proto_path
        ]

        try:
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # 读取描述符集
            with open(desc_path, 'rb') as f:
                descriptor_set = FileDescriptorSet()
                descriptor_set.ParseFromString(f.read())
            
            return descriptor_set
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to compile proto file: {e.stderr.decode()}")
            raise
        finally:
            if os.path.exists(desc_path):
                os.remove(desc_path)

    def _parse_descriptor(self, descriptor_set):
        """
        解析描述符集，提取消息和服务信息
        """
        for file_desc in descriptor_set.file:
            # 提取消息定义
            for msg_type in file_desc.message_type:
                self._parse_message_type(msg_type, package=file_desc.package)
            
            # 提取服务定义
            for service in file_desc.service:
                self.services.append({
                    'name': service.name,
                    'package': file_desc.package,
                    'methods': service.method
                })

    def _parse_message_type(self, msg_type, package):
        """
        递归解析消息类型
        """
        full_name = f"{package}.{msg_type.name}" if package else msg_type.name
        fields = {}
        for field in msg_type.field:
            fields[field.name] = {
                'type': field.type,
                'label': field.label,
                'type_name': field.type_name
            }
        self.messages[full_name] = fields
        
        # 处理嵌套消息
        for nested_type in msg_type.nested_type:
            self._parse_message_type(nested_type, full_name)

    def _generate_payload(self, message_type_name):
        """
        根据消息类型生成默认 payload
        """
        # 移除开头的 .
        if message_type_name.startswith('.'):
            message_type_name = message_type_name[1:]
            
        if message_type_name not in self.messages:
            return {}
            
        payload = {}
        for field_name, field_info in self.messages[message_type_name].items():
            # 这里简单处理基本类型，复杂类型递归生成
            if field_info['type'] == FieldDescriptor.TYPE_MESSAGE:
                payload[field_name] = self._generate_payload(field_info['type_name'])
            elif field_info['type'] in [FieldDescriptor.TYPE_STRING, FieldDescriptor.TYPE_BYTES]:
                payload[field_name] = "string_value"
            elif field_info['type'] in [FieldDescriptor.TYPE_INT32, FieldDescriptor.TYPE_INT64, 
                                      FieldDescriptor.TYPE_UINT32, FieldDescriptor.TYPE_UINT64]:
                payload[field_name] = 0
            elif field_info['type'] in [FieldDescriptor.TYPE_FLOAT, FieldDescriptor.TYPE_DOUBLE]:
                payload[field_name] = 0.0
            elif field_info['type'] == FieldDescriptor.TYPE_BOOL:
                payload[field_name] = False
            elif field_info['type'] == FieldDescriptor.TYPE_ENUM:
                payload[field_name] = 0 # Enum default
            else:
                payload[field_name] = None
                
            # 处理 repeated 字段
            if field_info['label'] == FieldDescriptor.LABEL_REPEATED:
                payload[field_name] = [payload[field_name]]
                
        return payload

    def yaml_file_dump(self):
        """
        生成 YAML 用例文件
        """
        descriptor_set = self._compile_proto()
        self._parse_descriptor(descriptor_set)

        for service in self.services:
            service_name = service['name']
            package_name = service['package']
            
            case_list = []
            for method in service['methods']:
                method_name = method.name
                input_type = method.input_type
                
                # 生成默认请求体
                payload = self._generate_payload(input_type)
                
                case_info = {
                    "id": f"{method_name}_01",
                    "title": f"测试 {method_name}",
                    "run": True,
                    "severity": "normal",
                    "url": f"grpc://{package_name}.{service_name}/{method_name}", # 模拟 GRPC URL
                    "method": "GRPC",
                    "headers": {
                        "Content-Type": "application/grpc"
                    },
                    "request_type": "grpc",
                    "payload": payload,
                    "assert_response": {
                        "status_code": 0 # GRPC OK status
                    }
                }
                case_list.append(case_info)
            
            # 构建 YAML 内容
            yaml_data = {
                "case_common": {
                    "allure_epic": f"{package_name} Epic",
                    "allure_feature": service_name,
                    "allure_story": "GRPC Interface Tests",
                    "case_markers": ["grpc", service_name.lower()]
                },
                "case_info": case_list
            }
            
            # 保存文件
            file_name = f"test_{service_name}.yaml"
            file_path = os.path.join(self.case_dir, file_name)
            
            yaml_dumper = yaml.YAML()
            yaml_dumper.allow_unicode = True
            yaml_dumper.default_flow_style = False
            
            with open(file_path, "w", encoding="utf-8") as f:
                yaml_dumper.dump(yaml_data, f)
            
            logger.info(f"Generated GRPC test case: {file_path}")

if __name__ == "__main__":
    # 测试代码
    pass
