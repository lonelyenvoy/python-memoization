from threading import RLock

from memoization.model import DummyWithable, CacheInfo


def get_caching_wrapper(user_function, max_size, ttl, algorithm, thread_safe):
    """
    Get a caching wrapper for statistics only, without any actual caching
    """

    misses = 0                                          # number of misses of the cache
    lock = RLock() if thread_safe else DummyWithable()  # ensure thread-safe

    def wrapper(*args, **kwargs):
        """
        The actual wrapper
        """
        nonlocal misses
        with lock:
            misses += 1
        return user_function(*args, **kwargs)

    def cache_clear():
        """
        Clear the cache and statistics information
        """
        nonlocal misses
        with lock:
            misses = 0

    def cache_info():
        """
        Show statistics information
        :return: a CacheInfo object describing the cache
        """
        with lock:
            return CacheInfo(0, misses, 0, max_size, algorithm, ttl, thread_safe)

    # expose operations and members of wrapper
    wrapper.cache_clear = cache_clear
    wrapper.cache_info = cache_info
    wrapper._cache = None

    return wrapper

