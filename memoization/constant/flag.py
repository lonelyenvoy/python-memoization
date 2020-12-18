try:
    import enum  # only works on Python 3.5+
    enum.IntFlag  # only works on Python 3.6+
except (ImportError, AttributeError):
    # backport for Python 3.4 and 3.5
    from memoization.backport import enum  # type: ignore


class CachingAlgorithmFlag(enum.IntFlag):
    """
    Use this class to specify which caching algorithm you would like to use
    """
    FIFO = 1    # First In First Out
    LRU = 2     # Least Recently Used
    LFU = 4     # Least Frequently Used
