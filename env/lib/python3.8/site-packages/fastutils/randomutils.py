# -*- coding: utf-8 -*-

import hashlib
import time
import uuid
import os
import threading
import getpass
import socket

from .numericutils import NUMERIC_TYPES

DEFAULT_BASE = (2 ** 30 - 123) * 0.91 # always NOT change this
DEFAULT_A = (2 ** 29 - 456) * 0.93 # always NOT change this
DEFAULT_B = (2 ** 28 - 789) * 0.95 # always NOT change this

class Random(object):
    """Pseudo-random number generator.

    ## randomness testing

    import os
    import random
    from fastutils import randomutils

    def test1(length):
        data = set()
        while True:
            bs = os.urandom(length)
            if bs in data:
                return "os.urandom({})={}".format(length, len(data))
            data.add(bs)

    def test2(length):
        data = set()
        while True:
            bs = random.randbytes(length)
            if bs in data:
                return "random.randbytes({})={}".format(length, len(data))
            data.add(bs)

    def test3(length):
        data = set()
        rnd = randomutils.Random()
        while True:
            bs = rnd.get_bytes(length)
            if bs in data:
                return "randomutils.Random({})={}".format(length, len(data))
            data.add(bs)

    print(test1(1))
    print(test1(2))
    print(test1(3))
    print(test1(4))
    print(test1(5))
    print(test1(6))

    print(test2(1))
    print(test2(2))
    print(test2(3))
    print(test2(4))
    print(test2(5))
    print(test2(6))

    print(test3(1))
    print(test3(2))
    print(test3(3))
    print(test3(4))
    print(test3(5))
    print(test3(6))

    ## randomness testing result

    os.urandom(1)=13
    os.urandom(2)=583
    os.urandom(3)=3245
    os.urandom(4)=51189
    os.urandom(5)=1280810
    os.urandom(6)=33771127               # good, always about 35,000,000
    random.randbytes(1)=2
    random.randbytes(2)=347
    random.randbytes(3)=1274
    random.randbytes(4)=66322
    random.randbytes(5)=1060238
    random.randbytes(6)=38210136         # good, always about 38,000,000
    randomutils.Random(1)=6
    randomutils.Random(2)=80
    randomutils.Random(3)=53
    randomutils.Random(4)=98189
    randomutils.Random(5)=1097420
    randomutils.Random(6)=10117127       # not so good, about 5,000,000 ~ 10,000,000

    """
    def __init__(self, seed=None, a=DEFAULT_A, b=DEFAULT_B, base=DEFAULT_BASE):
        self.seed = self.get_seed(seed)
        self.a = a
        self.b = b
        self.base = base

    @classmethod
    def get_seed(cls, seed):
        if seed is None:
            return time.time()
        if isinstance(seed, str):
            seed = seed.encode("utf-8")
        if isinstance(seed, bytes):
            seed = int.from_bytes(hashlib.sha512(seed).digest(), "big")
        if isinstance(seed, NUMERIC_TYPES):
            return seed
        else:
            raise RuntimeError("Random seed type must be in (str, bytes, int, float), but {} got.".format(type(seed)))

    def random(self):
        """return a float number in [0, 1).
        """
        r = (self.a * self.seed + self.b) % self.base
        p = r / self.base
        self.seed = r
        return p

    def randint(self, a, b = None):
        """If a<b, then return int number in [a, b). If a>b, then return int number in [b, a).
        """
        if b is None:
            return int(self.random() * a)
        else:
            if a > b:
                a, b = b, a
            return int(self.random() * (b - a) + a)

    def get_bytes(self, length = 1):
        return bytes(bytearray([self.randint(256) for _ in range(length)]))

    def choice(self, seq):
        index = self.randint(len(seq))
        return seq[index]

    def choices(self, population, k=1):
        result = []
        for _ in range(k):
            result.append(self.choice(population))
        return result

    def shuffle(self, thelist, x=2):
        length = len(thelist)
        if not isinstance(thelist, list):
            thelist = list(thelist)
        for _ in range(int(length * x)):
            p = self.randint(length)
            q = self.randint(length)
            if p == q:
                q += self.randint(length)
                q %= length
            thelist[p], thelist[q] = thelist[q], thelist[p]
        return thelist


class UuidGenerator(object):
    """UUID generator, using machine based counter, so that it will NOT generate conflict UUIDs.
    """
    def __init__(self, namespace=None):
        self.namespace = str(namespace or "default")
        self.seed1 = str(uuid.uuid1())
        self.seed4 = str(uuid.uuid4())
        self.hostname = str(socket.gethostname())
        self.node = str(uuid.getnode())
        self.user = str(getpass.getuser())
        self.pid = str(os.getpid())
        self.tid = str(threading.get_ident())
        self.counter = 0
        self.counter_lock = threading.Lock()
        self.domain_template = ".".join(["{ts1}", "{ts2}", "{counter}", self.tid, self.pid, self.user, self.node, self.hostname, self.seed4, self.seed1, self.namespace])
        self.ts0 = time.perf_counter()

    def next(self, n=1):
        if n < 1:
            return []
        with self.counter_lock:
            counter_start = self.counter
            self.counter += n
            counter_end = self.counter
        uuids = []
        for counter in range(counter_start, counter_end):
            ts1 = int(time.time() * 1000000)
            ts2 = int(time.perf_counter() * 1000000000)
            domain = self.domain_template.format(ts1=ts1, ts2=ts2, counter=counter)
            new_uuid = uuid.uuid3(uuid.NAMESPACE_DNS, domain)
            uuids.append(new_uuid)
        if n == 1:
            return uuids[0]
        else:
            return uuids

uuidgen = UuidGenerator()

def uuid1():
    return uuidgen.next()

uuid3 = uuid4 = uuid5 = uuid1
