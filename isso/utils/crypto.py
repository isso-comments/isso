# -*- encoding: utf-8 -*-
#
# Copyright (c) Django Software Foundation and individual contributors.
# All rights reserved.

import hmac
import struct
import base64
import hashlib
import binascii
import operator

from functools import reduce


def _bin_to_long(x):
    """
    Convert a binary string into a long integer

    This is a clever optimization for fast xor vector math
    """
    return int(binascii.hexlify(x), 16)


def _long_to_bin(x, hex_format_string):
    """
    Convert a long integer into a binary string.
    hex_format_string is like "%020x" for padding 10 characters.
    """
    return binascii.unhexlify((hex_format_string % x).encode('ascii'))


def _fast_hmac(key, msg, digest):
    """
    A trimmed down version of Python's HMAC implementation.

    This function operates on bytes.
    """
    dig1, dig2 = digest(), digest()
    if len(key) > dig1.block_size:
        key = digest(key).digest()
    key += b'\x00' * (dig1.block_size - len(key))
    dig1.update(key.translate(hmac.trans_36))
    dig1.update(msg)
    dig2.update(key.translate(hmac.trans_5C))
    dig2.update(dig1.digest())
    return dig2


def _pbkdf2(password, salt, iterations, dklen=0, digest=None):
    """
    Implements PBKDF2 as defined in RFC 2898, section 5.2

    HMAC+SHA256 is used as the default pseudo random function.

    Right now 10,000 iterations is the recommended default which takes
    100ms on a 2.2Ghz Core 2 Duo. This is probably the bare minimum
    for security given 1000 iterations was recommended in 2001. This
    code is very well optimized for CPython and is only four times
    slower than openssl's implementation.
    """

    assert iterations > 0
    if not digest:
        digest = hashlib.sha1
    password = b'' + password
    salt = b'' + salt
    hlen = digest().digest_size
    if not dklen:
        dklen = hlen
    if dklen > (2 ** 32 - 1) * hlen:
        raise OverflowError('dklen too big')
    l = -(-dklen // hlen)
    r = dklen - (l - 1) * hlen

    hex_format_string = "%%0%ix" % (hlen * 2)

    def F(i):
        def U():
            u = salt + struct.pack(b'>I', i)
            for j in range(int(iterations)):
                u = _fast_hmac(password, u, digest).digest()
                yield _bin_to_long(u)
        return _long_to_bin(reduce(operator.xor, U()), hex_format_string)

    T = [F(x) for x in range(1, l + 1)]
    return b''.join(T[:-1]) + T[-1][:r]

pbkdf2 = lambda text, salt, iterations, dklen: base64.b16encode(
    _pbkdf2(text.encode('utf-8'), salt, iterations, dklen)).lower()
