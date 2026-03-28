#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author  : 会飞的🐟
# @File    : generate_mock.py
# @Desc: Mock 配置生成命令行工具

import os
import sys
import argparse
from loguru import logger

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from utils.tools.mock_generator import OpenApiMockGenerator, generate_mock_from_yaml


def generate_from_openapi(openapi_path: str, project_name: str, output_dir: str):
    """
    从 OpenAPI 文档生成 Mock 配置
    :param openapi_path: OpenAPI 文档路径
    :param project_name: 项目名称
    :param output_dir: 输出目录
    """
    if not os.path.exists(openapi_path):
        logger.error(f"OpenAPI 文件不存在: {openapi_path}")
        return
    
    generator = OpenApiMockGenerator(output_dir)
    mock_rules = generator.generate_from_openapi(openapi_path, project_name)
    
    if mock_rules:
        config_file = generator.generate_mock_config_file(mock_rules, project_name)
        logger.success(f"成功生成 {len(mock_rules)} 个 Mock 规则")
        logger.info(f"配置文件: {config_file}")
    else:
        logger.warning("未找到可用的接口定义")


def generate_from_yaml_dir(yaml_dir: str, project_name: str, output_dir: str):
    """
    从 YAML 用例目录生成 Mock 配置
    :param yaml_dir: YAML 用例目录
    :param project_name: 项目名称
    :param output_dir: 输出目录
    """
    if not os.path.exists(yaml_dir):
        logger.error(f"YAML 目录不存在: {yaml_dir}")
        return
    
    generator = OpenApiMockGenerator(output_dir)
    all_mock_rules = {}
    
    # 遍历目录中的 YAML 文件
    for root, dirs, files in os.walk(yaml_dir):
        for file in files:
            if file.endswith((".yaml", ".yml")) and file.startswith("test_"):
                yaml_path = os.path.join(root, file)
                logger.info(f"处理文件: {yaml_path}")
                
                try:
                    mock_rules = generate_mock_from_yaml(yaml_path, project_name)
                    all_mock_rules.update(mock_rules)
                except Exception as e:
                    logger.error(f"处理文件失败 {yaml_path}: {e}")
    
    if all_mock_rules:
        config_file = generator.generate_mock_config_file(all_mock_rules, project_name)
        logger.success(f"成功生成 {len(all_mock_rules)} 个 Mock 规则")
        logger.info(f"配置文件: {config_file}")
    else:
        logger.warning("未找到可用的用例定义")


def generate_from_yaml_file(yaml_path: str, project_name: str, output_dir: str):
    """
    从单个 YAML 用例文件生成 Mock 配置
    :param yaml_path: YAML 用例文件路径
    :param project_name: 项目名称
    :param output_dir: 输出目录
    """
    if not os.path.exists(yaml_path):
        logger.error(f"YAML 文件不存在: {yaml_path}")
        return
    
    generator = OpenApiMockGenerator(output_dir)
    mock_rules = generate_mock_from_yaml(yaml_path, project_name)
    
    if mock_rules:
        config_file = generator.generate_mock_config_file(mock_rules, project_name)
        logger.success(f"成功生成 {len(mock_rules)} 个 Mock 规则")
        logger.info(f"配置文件: {config_file}")
    else:
        logger.warning("未找到可用的用例定义")


def main():
    parser = argparse.ArgumentParser(
        description="Mock 配置生成工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 从 OpenAPI 文档生成 Mock 配置
  python generate_mock.py openapi --file api.json --project myproject
  
  # 从 YAML 用例目录生成 Mock 配置
  python generate_mock.py yaml --dir ./interfaces/projects/workspace --project workspace
  
  # 从单个 YAML 文件生成 Mock 配置
  python generate_mock.py yaml --file test_login.yaml --project workspace
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="生成方式")
    
    # OpenAPI 方式
    openapi_parser = subparsers.add_parser("openapi", help="从 OpenAPI 文档生成")
    openapi_parser.add_argument("--file", "-f", required=True, help="OpenAPI 文档路径 (JSON)")
    openapi_parser.add_argument("--project", "-p", required=True, help="项目名称")
    openapi_parser.add_argument("--output", "-o", default=None, help="输出目录")
    
    # YAML 方式
    yaml_parser = subparsers.add_parser("yaml", help="从 YAML 用例生成")
    yaml_parser.add_argument("--file", "-f", help="YAML 用例文件路径")
    yaml_parser.add_argument("--dir", "-d", help="YAML 用例目录")
    yaml_parser.add_argument("--project", "-p", required=True, help="项目名称")
    yaml_parser.add_argument("--output", "-o", default=None, help="输出目录")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # 确定输出目录
    output_dir = args.output
    if output_dir is None:
        # 默认输出到项目目录
        from config.settings import PROJECT_DIR
        output_dir = os.path.join(PROJECT_DIR, args.project)
    
    if args.command == "openapi":
        generate_from_openapi(args.file, args.project, output_dir)
    
    elif args.command == "yaml":
        if args.file:
            generate_from_yaml_file(args.file, args.project, output_dir)
        elif args.dir:
            generate_from_yaml_dir(args.dir, args.project, output_dir)
        else:
            logger.error("请指定 --file 或 --dir 参数")
            yaml_parser.print_help()


if __name__ == "__main__":
    main()
