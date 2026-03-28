# -*- coding: utf-8 -*-
# @Author  : 会飞的🐟
# @File    : dingding_bot.py
# @Desc: 钉钉机器人模块
import hmac
import time
import base64
import hashlib
import urllib.parse
import urllib.request
from loguru import logger
from requests import request



class DingTalkBot:
    """
    钉钉机器人
    """

    def __init__(self, webhook_url, secret=None):
        """
        :param secret: 安全设置的加签秘钥
        :param webhook_url: 机器人没有加签的WebHook_url
        """
        # 适配钉钉机器人的加签模式和关键字模式/白名单IP模式
        if secret:
            timestamp = str(round(time.time() * 1000))
            sign = self.get_sign(secret, timestamp)
            self.webhook_url = webhook_url + f'&timestamp={timestamp}&sign={sign}'  # 最终url，url+时间戳+签名
        else:
            self.webhook_url = webhook_url

        self.headers = {
            "Content-Type": "application/json",
            "Charset": "UTF-8"
        }

    def get_sign(self, secret, timestamp):
        """
        根据时间戳 + "sign" 生成密钥
        把timestamp+"\n"+密钥当做签名字符串，使用HmacSHA256算法计算签名，然后进行Base64 encode，最后再把签名参数再进行urlEncode，得到最终的签名（需要使用UTF-8字符集）。
        :return:
        """
        string_to_sign = f'{timestamp}\n{secret}'.encode('utf-8')
        hmac_code = hmac.new(
            secret.encode('utf-8'),
            string_to_sign,
            digestmod=hashlib.sha256).digest()

        sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
        return sign

    def send_message(self, payload):
        """
        发送钉钉消息
        :payload: 请求json数据
        """
        logger.debug("\n======================================================\n" \
                     "-------------Start：发送钉钉消息--------------------\n"
                     f"Webhook_Url: {self.webhook_url}\n" \
                     f"内容: {payload}\n" \
                     "=====================================================")
        response = request(
            url=self.webhook_url,
            json=payload,
            headers=self.headers,
            method="POST"
        )
        if response.json().get("errcode") == 0:
            logger.debug("\n======================================================\n" \
                         "-------------End：发送钉钉消息--------------------\n"
                         f"通过钉钉机器人发送{payload.get('msgtype', '')}消息成功：{response.json()}\n" \
                         "=====================================================")
            print(f"通过钉钉机器人发送{payload.get('msgtype', '')}消息成功：{response.json()}")
            return True
        else:
            logger.error(f"通过钉钉机器人发送{payload.get('msgtype', '')}消息失败：{response.text}")
            print(f"通过钉钉机器人发送{payload.get('msgtype', '')}消息失败：{response.text}")
            return False

    def send_text(self, content, mobiles=None, is_at_all=False):
        """
        发送文本消息
        :param content: 发送的内容
        :param mobiles: 被艾特的用户的手机号码，格式是列表，注意需要在content里面添加@人的手机号码
        :param is_at_all: 是否艾特所有人，布尔类型，true为艾特所有人，false为不艾特
        """
        at_mobiles = ""
        if mobiles:
            if isinstance(mobiles, list):
                at_mobiles = mobiles
                is_at_all = False
                for mobile in mobiles:
                    content += f"@{mobile}"
            else:
                raise TypeError("mobiles类型错误 不是list类型.")

        payload = {
            "msgtype": "text",
            "text": {
                "content": content
            },
            "at": {
                "atMobiles": at_mobiles,
                "isAtAll": is_at_all
            }
        }
        return self.send_message(payload)

    def send_link(self, title, text, message_url, pic_url=None):
        """
        发送链接消息
        :param title: 消息标题
        :param text: 消息内容，如果太长只会部分展示
        :param message_url: 点击消息跳转的url地址
        :param pic_url: 图片url
        """
        payload = {
            "msgtype": "link",
            "link": {
                "title": title,
                "text": text,
                "picUrl": pic_url,
                "messageUrl": message_url
            }
        }
        return self.send_message(payload)

    def send_markdown(self, title, text, mobiles=None, is_at_all=False):
        """
        发送markdown消息
        目前仅支持md语法的子集，如标题，引用，文字加粗，文字斜体，链接，图片，无序列表，有序列表
        :param title: 消息标题，首屏回话透出的展示内容
        :param text: 消息内容，markdown格式
        :param mobiles: 被艾特的用户的手机号码，格式是列表，注意需要在text里面添加@人的手机号码
        :param is_at_all: 是否艾特所有人，布尔类型，true为艾特所有人，false为不艾特
        """
        at_mobiles = ""
        if mobiles:
            if isinstance(mobiles, list):
                at_mobiles = mobiles
                is_at_all = False
                for mobile in mobiles:
                    text += f"@{mobile}"
            else:
                raise TypeError("mobiles类型错误 不是list类型.")
        payload = {
            "msgtype": "markdown",
            "markdown": {
                "title": title,
                "text": text
            },
            "at": {
                "atMobiles": at_mobiles,
                "isAtAll": is_at_all
            }
        }

        return self.send_message(payload)

    def send_action_card_single(self, title, text, single_title, single_url, btn_orientation=0):
        """
        发送消息卡片(整体跳转ActionCard类型)
        :param title: 消息标题
        :param text: 消息内容，md格式消息
        :param single_title: 单个按钮的标题
        :param single_url: 点击singleTitle按钮后触发的URL
        :param btn_orientation: 0-按钮竖直排列，1-按钮横向排列
        """
        payload = {
            "msgtype": "actionCard",
            "actionCard": {
                "title": title,
                "text": text,
                "singleTitle": single_title,
                "singleURL": single_url,
                "btnOrientation": btn_orientation,
            }

        }
        return self.send_message(payload)

    def send_action_card_split(self, title, text, btns, btn_orientation=0):
        """
        发送消息卡片(独立跳转ActionCard类型)
        :param title: 消息标题
        :param text: 消息内容，md格式消息
        :param btns: 列表嵌套字典类型，"btns": [{"title": "内容不错", "actionURL": "https://www.dingtalk.com/"}, ......]
        :param btn_orientation: 0-按钮竖直排列，1-按钮横向排列
        """
        payload = {
            "msgtype": "actionCard",
            "actionCard": {
                "title": title,
                "text": text,
                "btns": [],
                "btnOrientation": btn_orientation,
            }

        }
        for btn in btns:
            payload["actionCard"]["btns"].append({
                "title": btn.get("title"),
                "actionURL": btn.get("action_url")
            })

        return self.send_message(payload)

    def send_feed_card(self, links_msg):
        """
        发送多组消息卡片(FeedCard类型)
        :param links_msg: 列表嵌套字典类型，每一个字段包括如下参数：title(单条信息文本), messageURL(点击单条信息后的跳转链接), picURL(单条信息后面图片的url)
        """
        payload = {
            "msgtype": "feedCard",
            "feedCard": {
                "links": []
            }
        }
        for link in links_msg:
            payload["feedCard"]["links"].append(
                {
                    "title": link.get("title"),
                    "messageURL": link.get("messageURL"),
                    "picURL": link.get("picURL")
                }
            )

        return self.send_message(payload)
