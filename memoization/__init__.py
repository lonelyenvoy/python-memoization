import sys

__all__ = ['cached', 'suppress_warnings', 'CachingAlgorithmFlag', 'FIFO', 'LRU', 'LFU']

if (3, 4) <= sys.version_info < (4, 0):  # for Python >=3.4 <4
    from . import memoization as _memoization

try:
    _memoization
except NameError:
    sys.stderr.write('python-memoization does not support your python version.\n')
    sys.stderr.write('Go to https://github.com/lonelyenvoy/python-memoization for usage and more details.\n')
    raise ImportError('Unsupported python version')
else:
    cached = _memoization.cached
    suppress_warnings = _memoization.suppress_warnings
    CachingAlgorithmFlag = _memoization.CachingAlgorithmFlag
    FIFO = _memoization.CachingAlgorithmFlag.FIFO
    LRU = _memoization.CachingAlgorithmFlag.LRU
    LFU = _memoization.CachingAlgorithmFlag.LFU
