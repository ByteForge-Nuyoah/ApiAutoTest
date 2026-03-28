# -*- coding: utf-8 -*-
# @Author  : 会飞的🐟
# @File    : mock_templates.py
# @Desc: Mock 数据模板模块

import random
import string
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from faker import Faker


fake = Faker('zh_CN')


class MockTemplates:
    """
    Mock 数据模板类
    提供常用的 Mock 数据生成方法
    """
    
    @staticmethod
    def user(user_id: int = None) -> Dict[str, Any]:
        """
        生成用户数据
        :param user_id: 用户ID（可选）
        :return: 用户数据字典
        """
        return {
            "id": user_id or random.randint(1, 10000),
            "username": fake.user_name(),
            "name": fake.name(),
            "email": fake.email(),
            "phone": fake.phone_number(),
            "avatar": fake.image_url(),
            "status": random.choice(["active", "inactive", "pending"]),
            "created_at": fake.date_time_this_year().isoformat(),
            "updated_at": fake.date_time_this_year().isoformat()
        }
    
    @staticmethod
    def users(count: int = 10) -> List[Dict[str, Any]]:
        """
        生成用户列表
        :param count: 数量
        :return: 用户列表
        """
        return [MockTemplates.user(i + 1) for i in range(count)]
    
    @staticmethod
    def product(product_id: int = None) -> Dict[str, Any]:
        """
        生成商品数据
        :param product_id: 商品ID（可选）
        :return: 商品数据字典
        """
        return {
            "id": product_id or random.randint(1, 10000),
            "name": fake.word() + "商品",
            "description": fake.text(max_nb_chars=200),
            "price": round(random.uniform(10, 10000), 2),
            "original_price": round(random.uniform(10, 10000), 2),
            "stock": random.randint(0, 1000),
            "category": random.choice(["电子产品", "服装", "食品", "家居", "图书"]),
            "brand": fake.company(),
            "images": [fake.image_url() for _ in range(3)],
            "rating": round(random.uniform(1, 5), 1),
            "sales": random.randint(0, 10000),
            "status": random.choice(["on_sale", "off_sale", "sold_out"]),
            "created_at": fake.date_time_this_year().isoformat()
        }
    
    @staticmethod
    def products(count: int = 10) -> List[Dict[str, Any]]:
        """
        生成商品列表
        :param count: 数量
        :return: 商品列表
        """
        return [MockTemplates.product(i + 1) for i in range(count)]
    
    @staticmethod
    def order(order_id: str = None) -> Dict[str, Any]:
        """
        生成订单数据
        :param order_id: 订单ID（可选）
        :return: 订单数据字典
        """
        items_count = random.randint(1, 5)
        items = []
        total_amount = 0
        
        for i in range(items_count):
            price = round(random.uniform(10, 1000), 2)
            quantity = random.randint(1, 3)
            items.append({
                "product_id": random.randint(1, 1000),
                "product_name": fake.word() + "商品",
                "price": price,
                "quantity": quantity,
                "subtotal": round(price * quantity, 2)
            })
            total_amount += price * quantity
        
        return {
            "order_id": order_id or f"ORD{datetime.now().strftime('%Y%m%d')}{random.randint(100000, 999999)}",
            "user_id": random.randint(1, 10000),
            "items": items,
            "total_amount": round(total_amount, 2),
            "status": random.choice(["pending", "paid", "shipped", "delivered", "cancelled"]),
            "payment_method": random.choice(["alipay", "wechat", "credit_card", "cash"]),
            "shipping_address": {
                "receiver": fake.name(),
                "phone": fake.phone_number(),
                "province": fake.province(),
                "city": fake.city(),
                "district": fake.district(),
                "address": fake.street_address()
            },
            "created_at": fake.date_time_this_year().isoformat(),
            "updated_at": fake.date_time_this_year().isoformat()
        }
    
    @staticmethod
    def orders(count: int = 10) -> List[Dict[str, Any]]:
        """
        生成订单列表
        :param count: 数量
        :return: 订单列表
        """
        return [MockTemplates.order() for _ in range(count)]
    
    @staticmethod
    def article(article_id: int = None) -> Dict[str, Any]:
        """
        生成文章数据
        :param article_id: 文章ID（可选）
        :return: 文章数据字典
        """
        return {
            "id": article_id or random.randint(1, 10000),
            "title": fake.sentence(nb_words=10),
            "content": fake.text(max_nb_chars=2000),
            "summary": fake.text(max_nb_chars=200),
            "author": fake.name(),
            "category": random.choice(["技术", "生活", "娱乐", "新闻", "教育"]),
            "tags": [fake.word() for _ in range(random.randint(1, 5))],
            "views": random.randint(0, 100000),
            "likes": random.randint(0, 10000),
            "comments_count": random.randint(0, 1000),
            "is_published": random.choice([True, False]),
            "created_at": fake.date_time_this_year().isoformat(),
            "updated_at": fake.date_time_this_year().isoformat()
        }
    
    @staticmethod
    def articles(count: int = 10) -> List[Dict[str, Any]]:
        """
        生成文章列表
        :param count: 数量
        :return: 文章列表
        """
        return [MockTemplates.article(i + 1) for i in range(count)]
    
    @staticmethod
    def comment(comment_id: int = None) -> Dict[str, Any]:
        """
        生成评论数据
        :param comment_id: 评论ID（可选）
        :return: 评论数据字典
        """
        return {
            "id": comment_id or random.randint(1, 10000),
            "user_id": random.randint(1, 10000),
            "user_name": fake.name(),
            "user_avatar": fake.image_url(),
            "content": fake.text(max_nb_chars=500),
            "likes": random.randint(0, 1000),
            "replies_count": random.randint(0, 50),
            "is_deleted": False,
            "created_at": fake.date_time_this_year().isoformat()
        }
    
    @staticmethod
    def comments(count: int = 10) -> List[Dict[str, Any]]:
        """
        生成评论列表
        :param count: 数量
        :return: 评论列表
        """
        return [MockTemplates.comment(i + 1) for i in range(count)]
    
    @staticmethod
    def token(expire_hours: int = 24) -> Dict[str, Any]:
        """
        生成 Token 数据
        :param expire_hours: 过期时间（小时）
        :return: Token 数据字典
        """
        now = datetime.now()
        expire = now + timedelta(hours=expire_hours)
        
        return {
            "access_token": str(uuid.uuid4()).replace('-', ''),
            "refresh_token": str(uuid.uuid4()).replace('-', ''),
            "token_type": "Bearer",
            "expires_in": expire_hours * 3600,
            "expires_at": expire.isoformat(),
            "created_at": now.isoformat()
        }
    
    @staticmethod
    def pagination(
        items: List[Any],
        page: int = 1,
        page_size: int = 10,
        total: int = None
    ) -> Dict[str, Any]:
        """
        生成分页数据
        :param items: 数据项列表
        :param page: 当前页码
        :param page_size: 每页数量
        :param total: 总数量（可选）
        :return: 分页数据字典
        """
        total = total or len(items)
        total_pages = (total + page_size - 1) // page_size
        
        return {
            "items": items,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1
            }
        }
    
    @staticmethod
    def success(data: Any = None, message: str = "操作成功") -> Dict[str, Any]:
        """
        生成成功响应
        :param data: 数据
        :param message: 消息
        :return: 成功响应字典
        """
        return {
            "code": 0,
            "message": message,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
    
    @staticmethod
    def error(
        code: int = 500,
        message: str = "操作失败",
        errors: List[str] = None
    ) -> Dict[str, Any]:
        """
        生成错误响应
        :param code: 错误码
        :param message: 消息
        :param errors: 错误列表
        :return: 错误响应字典
        """
        return {
            "code": code,
            "message": message,
            "errors": errors or [],
            "timestamp": datetime.now().isoformat()
        }
    
    @staticmethod
    def login_success(user_type: str = "normal") -> Dict[str, Any]:
        """
        生成登录成功响应
        :param user_type: 用户类型
        :return: 登录成功响应字典
        """
        user = MockTemplates.user()
        user["type"] = user_type
        user["roles"] = ["user"] if user_type == "normal" else ["user", "admin"]
        
        return MockTemplates.success({
            "user": user,
            "token": MockTemplates.token()
        }, "登录成功")
    
    @staticmethod
    def api_response(
        data: Any = None,
        code: int = 0,
        message: str = "success"
    ) -> Dict[str, Any]:
        """
        生成标准 API 响应
        :param data: 数据
        :param code: 状态码
        :param message: 消息
        :return: API 响应字典
        """
        return {
            "code": code,
            "message": message,
            "data": data,
            "trace_id": str(uuid.uuid4()),
            "timestamp": int(datetime.now().timestamp())
        }


class MockDataFactory:
    """
    Mock 数据工厂
    支持动态生成 Mock 数据
    """
    
    _templates: Dict[str, Callable] = {
        "user": MockTemplates.user,
        "users": MockTemplates.users,
        "product": MockTemplates.product,
        "products": MockTemplates.products,
        "order": MockTemplates.order,
        "orders": MockTemplates.orders,
        "article": MockTemplates.article,
        "articles": MockTemplates.articles,
        "comment": MockTemplates.comment,
        "comments": MockTemplates.comments,
        "token": MockTemplates.token,
        "success": MockTemplates.success,
        "error": MockTemplates.error,
        "login_success": MockTemplates.login_success,
        "api_response": MockTemplates.api_response
    }
    
    @classmethod
    def register(cls, name: str, template: Callable) -> None:
        """
        注册模板
        :param name: 模板名称
        :param template: 模板函数
        """
        cls._templates[name] = template
    
    @classmethod
    def create(cls, name: str, **kwargs) -> Any:
        """
        创建 Mock 数据
        :param name: 模板名称
        :param kwargs: 模板参数
        :return: Mock 数据
        """
        if name not in cls._templates:
            raise ValueError(f"未找到模板: {name}")
        
        return cls._templates[name](**kwargs)
    
    @classmethod
    def list_templates(cls) -> List[str]:
        """
        列出所有模板
        :return: 模板名称列表
        """
        return list(cls._templates.keys())


def create_mock_data(template: str, **kwargs) -> Any:
    """
    快捷创建 Mock 数据
    :param template: 模板名称
    :param kwargs: 模板参数
    :return: Mock 数据
    """
    return MockDataFactory.create(template, **kwargs)
