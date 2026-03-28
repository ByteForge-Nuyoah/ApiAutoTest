# -*- coding: utf-8 -*-
# @Author  : 会飞的🐟
# @File    : aes_encrypt_decrypt.py
# @Desc: AES加密解密模块

"""
@FileName：aes_encrypt_decrypt.py
@Description：
@Author：Floraachy
@Time：2024/11/22 14:48
"""

"""
AES 加密最常用的模式就是 ECB模式 和 CBC 模式，当然还有很多其它模式，他们都属于AES加密。ECB模式和CBC 模式俩者区别就是 ECB 不需要 iv偏移量，而CBC需要。
AES加密使用参数:
1) 秘钥: 加密的时候用秘钥，解密的时候需要同样的秘钥才能解出来; 数据类型为bytes
2) 明文: 需要加密的参数; 数据类型为bytes
3) 模式: aes 加密常用的有 ECB 和 CBC 模式（我只用了这两个模式，还有其他模式）;数据类型为aes类内部的枚举量
4) iv 偏移量: 这个参数在 ECB 模式下不需要，在 CBC 模式下需要；数据类型为bytes

1. 在Python中进行AES加密解密时，所传入的密文、明文、秘钥、iv偏移量、都需要是bytes（字节型）数据。python 在构建aes对象时也只能接受bytes类型数据。
2.当秘钥，iv偏移量，待加密的明文，字节长度不够16字节或者16字节倍数的时候需要进行补全。
3. CBC模式需要重新生成AES对象，为了防止这类错误，我写代码无论是什么模式都重新生成AES对象。

【编码模式】
由于python中的 AES 加密解密，只能接受字节型(bytes)数据。而我们常见的 待加密的明文可能是中文，或者待解密的密文经过base64编码的，这种都需要先进行编码或者解码，然后才能用AES进行加密或解密。
因此，在python使用AES进行加密或者解密时，都需要先转换成bytes型数据。
对于中文明文，我们可以使用encode()函数进行编码，将字符串转换成bytes类型数据。解密后，同样是需要decode()函数进行解码的，将字节型数据转换回中文字符（字符串类型）。

【填充模式】
前面我使用秘钥，还有明文，包括IV向量，都是固定16字节，也就是数据块对齐了。而填充模式就是为了解决数据块不对齐的问题，使用什么字符进行填充就对应着不同的填充模式
AES补全模式常见有以下几种：
1）ZeroPadding： 用b’\x00’进行填充，这里的0可不是字符串0，而是字节型数据的b’\x00’
2）PKCS7Padding： 当需要N个数据才能对齐时，填充字节型数据为N、并且填充N个
3）PKCS5Padding：与PKCS7Padding相同，在AES加密解密填充方面我没感到什么区别
4）no padding：当为16字节数据时候，可以不进行填充，而不够16字节数据时同ZeroPadding一样


"""
import base64
from Crypto.Cipher import AES


class Encrypt:
    """
    使用AES-CBC对称加密算法对密码进行加密，填充模式为PKCS7Padding
    """
    def __init__(self, key, iv):
        self.key = key.encode('utf-8')
        self.iv = iv.encode('utf-8')

    # @staticmethod
    def pkcs7padding(self, text):
        """明文使用PKCS7填充 """
        bs = 16
        length = len(text)
        bytes_length = len(text.encode('utf-8'))
        padding_size = length if (bytes_length == length) else bytes_length
        padding = bs - padding_size % bs
        padding_text = chr(padding) * padding
        self.coding = chr(padding)
        return text + padding_text

    def aes_encrypt(self, content):
        """ AES加密 """
        cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
        # 处理明文
        content_padding = self.pkcs7padding(content)
        # 加密
        encrypt_bytes = cipher.encrypt(content_padding.encode('utf-8'))
        # 重新编码
        result = str(base64.b64encode(encrypt_bytes), encoding='utf-8')
        return result

    def aes_decrypt(self, content):
        """AES解密 """
        cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
        content = base64.b64decode(content)
        text = cipher.decrypt(content).decode('utf-8')
        return text.rstrip(self.coding)
