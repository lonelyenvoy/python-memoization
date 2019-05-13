import sys

__all__ = ['cached', 'CachingAlgorithmFlag', 'FIFO', 'LRU', 'LFU']

if (3, 4) <= sys.version_info < (3, 9):  # 3.4, 3.5, 3.6, 3.7, 3.8
    from . import memoization as _memoization
elif (2, 6) <= sys.version_info < (2, 8):  # 2.6, 2.7
    from . import memoization_py2 as _memoization

try:
    _memoization
except NameError:
    sys.stderr.write('python-memoization does not support your python version.\n')
    sys.stderr.write('Go to https://github.com/lonelyenvoy/python-memoization for usage and more details.\n')
else:
    cached = _memoization.cached
    CachingAlgorithmFlag = _memoization.CachingAlgorithmFlag
    FIFO = _memoization.FIFO
    LRU = _memoization.LRU
    LFU = _memoization.LFU
