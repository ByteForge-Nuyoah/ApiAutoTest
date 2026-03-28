# -*- coding: utf-8 -*-
# @Author  : 会飞的🐟
# @File    : fake_data.py
# @Desc: 测试数据生成模块
import re
import random
import string
from faker import Faker
from datetime import datetime, date, timedelta

class FakerData:
    """
    测试数据生成类
    """

    def __init__(self):
        self.fk_zh = Faker(locale='zh_CN')
        self.faker = Faker()

    @classmethod
    def generate_random_int(cls, *args) -> int:
        """
        :return: 随机数
        """
        # 检查是否传入了参数
        if not args:
            # 没有传参，就从5000内随机取一个整数返回
            return random.randint(0, 5000)

        # 排序参数并获取最小值和最大值
        min_val = min(args)
        max_val = max(args)

        # 生成并返回随机整数
        return random.randint(min_val, max_val)

    def generate_catch_phrase(self):
        """
        :return: 生成妙句(口号) （输出结果都是英文）
        """
        return self.faker.catch_phrase()

    def generate_phone(self, lan="en") -> int:
        """
        :return: 随机生成手机号码
        """
        if lan == "zh":
            phone = self.fk_zh.phone_number()
        else:
            phone = self.faker.phone_number()
        return phone

    def generate_id_number(self, lan="en") -> int:
        """

        :return: 随机生成身份证号码
        """
        if lan == "zh":
            id_number = self.fk_zh.ssn()
        else:
            id_number = self.faker.ssn()
        return id_number

    def generate_female_name(self, lan="en") -> str:
        """

        :return: 女生姓名
        """
        if lan == "zh":
            female_name = self.fk_zh.name_female()
        else:
            female_name = self.faker.name_female()
        return female_name

    def generate_male_name(self, lan="en") -> str:
        """

        :return: 男生姓名
        """
        if lan == "zh":
            male_name = self.fk_zh.name_male()
        else:
            male_name = self.faker.name_male()
        return male_name

    def generate_name(self, lan="en") -> str:
        """
        生成人名
        :return: 人名
        """
        if lan == "zh":
            name = self.fk_zh.name()
        else:
            name = self.faker.name()
        return name

    def generate_company_name(self, lan: str = "en", fix: str = None) -> str:
        """
        生成公司名
        :param lan: 语言类型，可选：en, zh； zh表示中文，en表示英文，默认是en
        :param fix: 前后缀，可选pre， suf； pre表示公司前缀，suf标识公司后缀
        :return: 公司名
        """
        if lan == "zh":
            if fix == "pre":
                name = self.fk_zh.company_prefix()
            elif fix == "suf":
                name = self.fk_zh.company_suffix()
            else:
                name = self.fk_zh.company()
        else:
            if fix == "pre":
                name = self.faker.company_prefix()
            elif fix == "suf":
                name = self.faker.company_suffix()
            else:
                name = self.faker.company()

        return name

    def generate_paragraph(self, lan: str = "en", nb: int = 3) -> str:
        """
        生成段落
        :param lan: 语言类型，可选：en, zh； zh表示中文，en表示英文，默认是en
        :param nb: 段落个数，默认是3个
        """
        if lan == "zh":
            text = self.fk_zh.paragraph(nb_sentences=nb, variable_nb_sentences=True, ext_word_list=None)
        else:
            text = self.faker.paragraph(nb_sentences=nb, variable_nb_sentences=True, ext_word_list=None)

        return text

    def generate_words(self, lan: str = "en", nb: int = 1) -> str:

        """
        生成词语
        :param lan: 语言类型，可选：en, zh； zh表示中文，en表示英文，默认是en
        :param nb: 词语个数，默认是1个
        """
        if lan == "zh":
            if nb == 1 or nb < 1:
                text = self.fk_zh.word(ext_word_list=None)
            else:
                res = self.fk_zh.words(nb=nb, ext_word_list=None)
                text = "-".join(res)

        else:
            if nb == 1 or nb < 1:
                text = self.faker.word(ext_word_list=None)
            else:
                res = self.faker.words(nb=nb, ext_word_list=None)
                text = "-".join(res)

        return text

    def generate_email(self, lan="en") -> str:
        """

        :return: 生成邮箱
        """
        if lan == "zh":
            email = self.fk_zh.email()
        else:
            email = self.faker.email()
        return email

    def generate_identifier(self, lan="en", char_len=8):
        """
        :return:生成随机标识，满足要求：长度为2~100（这里长度通过传参控制，默认为8）， 只能包含数字，字母，下划线(_)，中划线(-)，英文句号(.)，必须以数字和字母开头，不能以下划线/中划线/英文句号开头和结尾
        """
        if lan == "zh":
            fk = self.fk_zh
        else:
            fk = self.faker
        while True:
            identifier = ''.join(random.choices(string.ascii_letters + string.digits + '_.-', k=char_len))  # 生成指定长度的随机标识

            if (
                    re.match(r'^[a-zA-Z0-9][a-zA-Z0-9_.-]{0,98}[a-zA-Z0-9]$', identifier) and
                    not (identifier.startswith('_') or identifier.startswith('-') or identifier.startswith('.')) and
                    not (identifier.endswith('_') or identifier.startswith('-') or identifier.endswith('.'))
            ):
                return identifier

    def generate_city(self, lan="en", full: bool = True) -> str:
        """
        :return: 随机生成城市名
        """
        if lan == "zh":
            faker = self.fk_zh
        else:
            faker = self.faker

        if full:
            city = faker.city()
        else:
            city = faker.city_name()

        return city

    def generate_province(self, lan="en") -> str:
        """
        :return: 随机生成城市名
        """
        if lan == "zh":
            faker = self.fk_zh
        else:
            faker = self.faker

        return faker.province()

    def generate_address(self, lan="en") -> str:
        """

        :return: 生成地址
        """
        if lan == "zh":
            address = self.fk_zh.address()
        else:
            address = self.faker.address()
        return address

    @classmethod
    def generate_time(cls, fmt='%Y-%m-%d %H:%M:%S', days=0) -> str:
        """
        根据传入的天数，返回当前时间加上或减去这些天数后的日期和时间，或者仅返回当前时间。
        :return:
        """
        # 获取当前时间
        current_time = datetime.now()
        # 计算增加或减少天数后的时间
        if days != 0:
            future_time = current_time + timedelta(days=days)
        else:
            future_time = current_time
        # 格式化时间
        return future_time.strftime(fmt)

    @classmethod
    def generate_today_date(cls, fmt='%Y-%m-%d'):
        """获取今日0点整时间"""
        today = datetime.now().date()
        if fmt == '%Y-%m-%d %H:%M:%S':
            return today.strftime(fmt) + " 00:00:00"
        return today.strftime(fmt)

    @classmethod
    def generate_time_after_week(cls, fmt='%Y-%m-%d'):
        """获取一周后12点整的时间"""
        if fmt == '%Y-%m-%d %H:%M:%S':
            return (date.today() + timedelta(days=+6)).strftime(fmt) + " 00:00:00"
        return (date.today() + timedelta(days=+6)).strftime(fmt)

    @classmethod
    def remove_special_characters(cls, target: str):
        """
        移除字符串中的特殊字符。
        在Python中用replace()函数操作指定字符
        常用字符unicode的编码范围：
        数字：\u0030-\u0039
        汉字：\u4e00-\u9fa5
        大写字母：\u0041-\u005a
        小写字母：\u0061-\u007a
        英文字母：\u0041-\u007a
        """
        pattern = r'([^\u4e00-\u9fa5])'
        result = re.sub(pattern, '', target)
        return result

    def generate_iso_8601_time(cls, days=0) -> str:
        """
        根据传入的天数，返回当前时间加上或减去这些天数后的日期和时间，格式为ISO 8601。
        :param days: 增加或减少的天数
        :return: ISO 8601格式的时间字符串
        """
        # 获取当前UTC时间
        current_time = datetime.now()
        # 计算增加或减少天数后的时间
        future_time = current_time + timedelta(days=days)
        # 格式化时间为ISO 8601格式
        iso_format_time = future_time.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        return iso_format_time

if __name__ == '__main__':
    faker = FakerData()
    res = faker.generate_iso_8601_time()
    print(res)