# -*- coding: utf-8 -*-
# @Author  : 会飞的🐟
# @File    : mock_config.py
# @Desc: workspace 项目 Mock 配置

import time
from utils.tools.mock_service import MockRule, MockResponse


def get_workspace_mock_rules():
    """
    获取 workspace 项目的 Mock 规则
    :return: Mock 规则列表
    """
    rules = []
    
    # 登录接口 Mock 规则
    login_rule = MockRule(
        name="workspace_login",
        url_pattern=r"/api/crm/v4/user/login",
        method="POST",
        response_builder=build_login_response,
        delay=0.1,
        priority=10
    )
    rules.append(login_rule)
    
    return rules


def build_login_response(url: str, method: str, **kwargs) -> MockResponse:
    """
    构建登录接口 Mock 响应
    :param url: 请求 URL
    :param method: 请求方法
    :param kwargs: 其他参数（包含 payload, headers 等）
    :return: Mock 响应对象
    """
    # 获取请求体
    payload = kwargs.get("payload", {})
    username = payload.get("username", "admin")
    
    # 模拟真实响应数据
    response_data = {
        "code": 200,
        "message": "success",
        "data": {
            "token": f"mock_token_{username}_{int(time.time())}",
            "user": {
                "id": 1,
                "username": username,
                "openid": "o3oc760tfUizHMk03BlecWSKkBW0",
                "nickname": "管理员",
                "avatar": "https://example.com/avatar.png",
                "phone": "13800138000",
                "email": f"{username}@example.com",
                "status": 1,
                "createTime": "2024-01-01 00:00:00",
                "updateTime": time.strftime("%Y-%m-%d %H:%M:%S")
            },
            "permissions": [
                "user:read",
                "user:write",
                "crm:read",
                "crm:write"
            ],
            "roles": [
                "admin",
                "user"
            ]
        },
        "timestamp": int(time.time() * 1000)
    }
    
    return MockResponse(
        status_code=200,
        headers={
            "Content-Type": "application/json;charset=utf-8",
            "X-Request-Id": f"mock-{int(time.time() * 1000)}"
        },
        body=response_data,
        elapsed=0.15
    )
