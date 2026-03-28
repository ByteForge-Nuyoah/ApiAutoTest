# -*- coding: utf-8 -*-
# @Author  : 会飞的🐟
# @File    : send_result_handle.py
# @Desc: 发送测试结果通知模块

from loguru import logger
from core.models import NotificationType
from core.data_utils.data_handle import data_handle
from utils.notify_utils.wechat_bot import WechatBot
from utils.notify_utils.dingding_bot import DingTalkBot
from utils.notify_utils.yagmail_bot import YagEmailServe
from core.report_utils.get_results_handle import get_test_results_from_from_allure_report
from config.settings import SEND_RESULT_TYPE, email, ding_talk, wechat, email_subject, email_content, ding_talk_title, \
    ding_talk_content, wechat_content


def send_email(user, pwd, host, subject, content, to, attachments):
    """
    发送邮件
    """
    try:
        yag = YagEmailServe(user=user, password=pwd, host=host)
        info = {
            "subject": subject,
            "contents": content,
            "to": to,
            "attachments": attachments

        }
        yag.send_email(info)
    except Exception as e:
        logger.error(f"发送邮件通知异常， 错误信息：{e}")


def send_dingding(webhook_url, secret, title, content):
    """
    发送钉钉消息
    """
    try:
        bot_dingding = DingTalkBot(webhook_url=webhook_url, secret=secret)
        res = bot_dingding.send_markdown(title=title, text=content, is_at_all=True)
        if res:
            logger.debug(f"发送钉钉通知成功~")
        else:
            logger.error(f"发送钉钉通知失败~")
    except Exception as e:
        logger.error(f"发送钉钉通知异常， 错误信息：{e}")


def send_wechat(webhook_url, content, attachment=None):
    """
    发送企业微信消息
    """
    try:
        bot_wechat = WechatBot(webhook_url=webhook_url)
        msg = bot_wechat.send_markdown(content=content)
        if msg:
            if attachment:
                file = bot_wechat.send_file(bot_wechat.upload_file(attachment))
                if file:
                    logger.debug(f"发送企业微信通知(包括文本以及附件)成功~")
                else:
                    logger.error(f"发送企业微信通知(附件)失败~")
        else:
            logger.error(f"发送企业微信（文本）失败~")
    except Exception as e:
        logger.error(f"发送企业微信通知异常， 错误信息：{e}")


def send_result(report_info: dict, report_path: str, attachment_path: str = None):
    """
    根据用户配置，采取指定方式，发送测试结果
    :param report_info: 报告相关信息，包括tester, department, env
    :param report_path: 报告路径
    :param attachment_path: 发送的附件， pytest-html就是报告本身作为附件发送， allure是压缩包发送
    """
    # 默认不发送任何通知
    if SEND_RESULT_TYPE == NotificationType.DEFAULT.value:
        logger.trace(f"SEND_RESULT_TYPE={SEND_RESULT_TYPE}， 配置了不发送任何邮件")
        return

    results = get_test_results_from_from_allure_report(report_path)
    for k, v in report_info.items():
        results[k] = v

    # 建立发送消息的内容、函数以及参数的映射关系
    notification_mappings = {
        NotificationType.EMAIL.value: {
            'sender': send_email,
            'sender_args': {
                'user': email.get("user"),
                'pwd': email.get("password"),
                'host': email.get("host"),
                'subject': email_subject,
                'content': email_content,
                'to': email.get("to"),
                'attachments': attachment_path,
            }
        },
        NotificationType.DING_TALK.value: {
            'sender': send_dingding,
            'sender_args': {
                'webhook_url': ding_talk["webhook_url"],
                'secret': ding_talk["secret"],
                'title': ding_talk_title,
                'content': ding_talk_content,
            }
        },
        NotificationType.WECHAT.value: {
            'sender': send_wechat,
            'sender_args': {
                'webhook_url': wechat["webhook_url"],
                'content': wechat_content,
                'attachment': attachment_path,
            }
        }
    }
    # 单一渠道发送消息
    if SEND_RESULT_TYPE in notification_mappings:
        notification = notification_mappings[SEND_RESULT_TYPE]
        # 获取消息内容并替换
        notification['sender_args']['content'] = data_handle(obj=notification['sender_args']['content'],
                                                             source=results)
        # 获取消息发送函数
        sender = notification['sender']
        # 获取对应消息发送函数的参数
        sender_args = notification['sender_args']
        # 调用消息发送函数
        sender(**sender_args)
    # 全渠道发送消息
    else:
        # 遍历所有消息发送方式
        for notification in notification_mappings.values():
            # 获取消息内容并替换
            notification['sender_args']['content'] = data_handle(obj=notification['sender_args']['content'],
                                                                 source=results)
            # 获取消息发送函数
            sender = notification['sender']
            # 获取对应消息发送函数的参数
            sender_args = notification['sender_args']
            # 调用消息发送函数
            sender(**sender_args)
