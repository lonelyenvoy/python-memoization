import sys

__all__ = ['cached', 'CachingAlgorithmFlag', 'FIFO', 'LRU', 'LFU']

if (3, 4) <= sys.version_info <= (3, 10):  # for Python 3.4, 3.5, 3.6, 3.7, 3.8, 3.9
    from . import memoization as _memoization

try:
    _memoization
except NameError:
    sys.stderr.write('python-memoization does not support your python version.\n')
    sys.stderr.write('Go to https://github.com/lonelyenvoy/python-memoization for usage and more details.\n')
    raise ImportError('Unsupported python version')
else:
    cached = _memoization.cached
    CachingAlgorithmFlag = _memoization.CachingAlgorithmFlag
    FIFO = _memoization.CachingAlgorithmFlag.FIFO
    LRU = _memoization.CachingAlgorithmFlag.LRU
    LFU = _memoization.CachingAlgorithmFlag.LFU
