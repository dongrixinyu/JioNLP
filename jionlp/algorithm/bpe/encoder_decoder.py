# -*- coding=utf-8 -*-
# library: jionlp
# author: dongrixinyu
# license: Apache License 2.0
# email: dongrixinyu.89@163.com
# github: https://github.com/dongrixinyu/JioNLP
# description: Preprocessing & Parsing tool for Chinese NLP
# website: http://www.jionlp.com


# 参考 https://github.com/huggingface/tokenizers/issues/1162
# Byte-level BPE 算法

def _bytes_to_unicode():
    """
    所有 uft-8 的 unicode 都由 byte 构成，所有的 byte 总共 256 个，但由于其中一些属于控制字符，
    无具体打印符号，因此需要将这些符号后移 256 位，从而映射到可打印符号。
    所有这些符号均为 unicode 字符。

    Returns list of utf-8 byte and a corresponding list of unicode strings.
    The reversible bpe codes work on unicode strings.
    This means you need a large # of unicode characters in your vocab if you want to avoid UNKs.
    When you're at something like a 10B token dataset you end up needing around 5K for decent coverage.
    This is a signficant percentage of your normal, say, 32K bpe vocab.
    To avoid that, we want lookup tables between utf-8 bytes and unicode strings.
    And avoids mapping to whitespace/control characters the bpe code barfs on.
    """
    bs = list(range(ord("!"), ord("~") + 1)) \
         + list(range(ord("¡"), ord("¬") + 1)) \
         + list(range(ord("®"), ord("ÿ") + 1))  # 可打印符号

    cs = bs[:]
    n = 0
    for b in range(2 ** 8):
        if b not in bs:
            bs.append(b)
            cs.append(2 ** 8 + n)
            n += 1
    cs = [chr(n) for n in cs]

    return dict(zip(bs, cs))


def byte_encoder():
    # byte-level BPE 所依赖的编码器
    return _bytes_to_unicode()


def byte_decoder():
    # byte-level BPE 所依赖的解码器
    return {v: k for k, v in _bytes_to_unicode().items()}


class ByteLevelBPE(object):
    """
    主要用于编码字符串为 Byte-level string. 但并非完整版的 BPE 算法的实现。 TODO: BPE 实现过程
    Byte-level BPE 算法优势：
        - 克服了 character-level 中大量存在的低频词造成的 UNK token。
        - 适应多种语言，不局限于 英文，中文，同时可以处理日文、俄文、泰语、等各种语言。

    TODO：该方法应当按 C 语言编写，以提速。

    Examples:
        >>> import jionlp as jio
        >>> res = jio.bpe.byte_level_bpe.encode('メトロ')
        >>> res = jio.bpe.byte_level_bpe.decode(['ãĥ¡', 'ãĥĪ', 'ãĥŃ'])  # 这一步由 BPE 算法检索 vocab.json 得到

    """
    def __init__(self):
        self.byte_encoder = None

    def _prepare(self):
        self.byte_decoder = byte_decoder()
        self.byte_encoder = byte_encoder()

    def encode(self, text):
        if self.byte_encoder is None:
            self._prepare()

        encoded_list = []
        for char in text:
            encoded_char = ''.join([self.byte_encoder[b] for b in char.encode('utf-8')])
            encoded_list.append(encoded_char)

        return ''.join(encoded_list)

    def _decode(self, chars_list):
        if self.byte_encoder is None:
            self._prepare()

        decoded_list = []
        for chars in chars_list:
            decoded_char = bytearray(
                [self.byte_decoder[b] for b in chars]).decode('utf-8')
            decoded_list.append(decoded_char)

        return ''.join(decoded_list)

    def decode(self, chars):
        if self.byte_encoder is None:
            self._prepare()

        decoded_list = []
        idx = 0
        while idx < len(chars):
            exception_flag = True
            for i in range(1, 5):  # unicode char 被编码在 4 字节以内（含）
                tmp_chars = chars[idx: idx + i]
                try:
                    decoded_char = bytearray(
                        [self.byte_decoder[b] for b in tmp_chars]).decode('utf-8')
                    decoded_list.append(decoded_char)
                    exception_flag = False
                    break
                except:
                    pass

            if exception_flag:  # 没有匹配到，存在异常，则加入 UNK token �
                decoded_list.append('�')
                idx += 1
            else:
                idx += i

        return ''.join(decoded_list)
