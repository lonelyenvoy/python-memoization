from collections import namedtuple


__all__ = ['DummyWithable', 'HashedList', 'CacheInfo']


class DummyWithable(object):
    """
    This class is used to create instances that can bypass "with" statements

    e.g.
    lock = DummyWithable()
    with lock:
        manipulate_data()
    """

    __slots__ = ()

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class HashedList(list):
    """
    This class guarantees that hash() will be called no more than once per element.
    """

    __slots__ = ('hash_value', )

    def __init__(self, tup, hash_value):
        super().__init__(tup)
        self.hash_value = hash_value

    def __hash__(self):
        return self.hash_value


# Named type CacheInfo
CacheInfo = namedtuple('CacheInfo', ['hits', 'misses', 'current_size', 'max_size', 'algorithm',
                                     'ttl', 'thread_safe', 'order_independent', 'use_custom_key'])
