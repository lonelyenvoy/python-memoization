import unittest
from memoization import cached, CachingAlgorithmFlag, _memoization
from itertools import chain
from threading import Thread
import random
from threading import Lock
import weakref
import gc
import time


make_key = _memoization._make_key   # bind make_key function
exec_times = {}                     # executed time of each tested function
lock = Lock()                       # for multi-threading tests
random.seed(100)                    # set seed to ensure that test results are reproducible

for i in range(1, 12):
    exec_times['f' + str(i)] = 0  # init to zero


################################################################################
# Tested functions
################################################################################

@cached
def f1(x):
    exec_times['f1'] += 1
    return x


@cached()
def f2(x):
    exec_times['f2'] += 1
    return x


@cached(max_size=5, algorithm=CachingAlgorithmFlag.FIFO, thread_safe=False)
def f3(x):
    exec_times['f3'] += 1
    return x


@cached(max_size=5, algorithm=CachingAlgorithmFlag.LRU, thread_safe=False)
def f4(x):
    exec_times['f4'] += 1
    return x


@cached(max_size=5, algorithm=CachingAlgorithmFlag.LFU, thread_safe=False)
def f5(x):
    exec_times['f5'] += 1
    return x


@cached(max_size=5, algorithm=CachingAlgorithmFlag.FIFO, thread_safe=True)
def f6(x):
    with lock:
        exec_times['f6'] += 1
    return x


@cached(max_size=5, algorithm=CachingAlgorithmFlag.LRU, thread_safe=True)
def f7(x):
    with lock:
        exec_times['f7'] += 1
    return x


@cached(max_size=5, algorithm=CachingAlgorithmFlag.LFU, thread_safe=True)
def f8(x):
    with lock:
        exec_times['f8'] += 1
    return x


@cached(max_size=5, algorithm=CachingAlgorithmFlag.FIFO, thread_safe=False, ttl=0.5)
def f9(x):
    exec_times['f9'] += 1
    return x


@cached(max_size=5, algorithm=CachingAlgorithmFlag.LRU, thread_safe=False, ttl=0.5)
def f10(x):
    exec_times['f10'] += 1
    return x


@cached(max_size=5, algorithm=CachingAlgorithmFlag.LFU, thread_safe=False, ttl=0.5)
def f11(x):
    exec_times['f11'] += 1
    return x


################################################################################
# Test entry point
################################################################################

class TestMemoization(unittest.TestCase):
    def test_memoization_with_default_arguments(self):
        for _ in range(5):
            f1(10)
            f2(10)
        f1(20)
        f2(20)

        self.assertEqual(exec_times['f1'], 2)
        self.assertEqual(exec_times['f2'], 2)

        for info in f1.cache_info(), f2.cache_info():
            self.assertIsNone(info.max_size)
            self.assertEqual(info.algorithm, CachingAlgorithmFlag.LRU)
            self.assertIsNone(info.ttl)
            self.assertTrue(info.thread_safe)

            self.assertEqual(info.hits, 4)
            self.assertEqual(info.misses, 2)
            self.assertEqual(info.current_size, 2)
        for f in f1, f2:
            keys = make_key((10,), None), make_key((20,), None)
            for key in keys:
                self.assertIn(key, f._cache)

    def test_memoization_with_FIFO(self):
        self.assertTrue(hasattr(f3, '_fifo_root'))
        self._fifo_test(f3)
        f3.cache_clear()
        self._check_empty_cache_after_clearing(f3)

    def test_memoization_with_LRU(self):
        self.assertTrue(hasattr(f4, '_lru_root'))
        self._lru_test(f4)
        f4.cache_clear()
        self._check_empty_cache_after_clearing(f4)

    def test_memoization_with_LFU(self):
        self.assertTrue(hasattr(f5, '_lfu_root'))
        self._lfu_test(f5)
        self._check_lfu_cache_clearing(f5)

    def test_memoization_with_FIFO_multithread(self):
        self.assertTrue(hasattr(f6, '_fifo_root'))
        self._general_multithreading_test(f6, CachingAlgorithmFlag.FIFO)
        self._fifo_test(f6)
        f6.cache_clear()
        self._check_empty_cache_after_clearing(f6)

    def test_memoization_with_LRU_multithread(self):
        self.assertTrue(hasattr(f7, '_lru_root'))
        self._general_multithreading_test(f7, CachingAlgorithmFlag.LRU)
        self._lru_test(f7)
        f7.cache_clear()
        self._check_empty_cache_after_clearing(f7)

    def test_memoization_with_LFU_multithread(self):
        self.assertTrue(hasattr(f8, '_lfu_root'))
        self._general_multithreading_test(f8, CachingAlgorithmFlag.LFU)
        self._lfu_test(f8)
        self._check_lfu_cache_clearing(f8)

    def test_memoization_with_FIFO_TTL(self):
        self.assertTrue(hasattr(f9, '_fifo_root'))
        self._general_ttl_test(f9)
        f9.cache_clear()
        self._check_empty_cache_after_clearing(f9)

    def test_memoization_with_LRU_TTL(self):
        self.assertTrue(hasattr(f10, '_lru_root'))
        self._general_ttl_test(f10)
        f10.cache_clear()
        self._check_empty_cache_after_clearing(f10)

    def test_memoization_with_LFU_TTL(self):
        self.assertTrue(hasattr(f11, '_lfu_root'))
        self._general_ttl_test(f11)
        self._check_lfu_cache_clearing(f11)

    def test_memoization_for_unhashable_arguments_with_FIFO(self):
        self._general_unhashable_arguments_test(f3)
        f3.cache_clear()
        self._check_empty_cache_after_clearing(f3)

    def test_memoization_for_unhashable_arguments_with_LRU(self):
        self._general_unhashable_arguments_test(f4)
        f4.cache_clear()
        self._check_empty_cache_after_clearing(f4)

    def test_memoization_for_unhashable_arguments_with_LFU(self):
        self._general_unhashable_arguments_test(f5)
        self._check_lfu_cache_clearing(f5)


    def _general_test(self, tested_function, algorithm, hits, misses, in_cache, not_in_cache):
        # clear
        exec_times[tested_function.__name__] = 0
        tested_function.cache_clear()

        for i in range(20):
            tested_function(i)
        tested_function(99)

        self.assertEqual(exec_times[tested_function.__name__], 21)
        info = tested_function.cache_info()
        self.assertEqual(info.max_size, 5)
        self.assertEqual(info.algorithm, algorithm)
        self.assertIsNone(info.ttl)
        self.assertIsNotNone(info.thread_safe)

        self.assertEqual(info.hits, 0)
        self.assertEqual(info.misses, 21)
        self.assertEqual(info.current_size, 5)

        keys = [make_key((x,), None) for x in (99, 19, 18, 17, 16)]
        for key in keys:
            self.assertIn(key, tested_function._cache)

        # 10 consecutive calls here
        tested_function(16)
        tested_function(17)
        tested_function(18)
        tested_function(16)
        tested_function(17)
        tested_function(18)

        tested_function(19)
        tested_function(15)
        tested_function(100)
        tested_function(16)

        info = tested_function.cache_info()
        self.assertEqual(info.hits, hits)
        self.assertEqual(info.misses, misses)
        self.assertEqual(info.current_size, 5)

        keys = [make_key((x,), None) for x in in_cache]
        for key in keys:
            self.assertIn(key, tested_function._cache)
        keys = [make_key((x,), None) for x in chain(not_in_cache, range(0, 15))]
        for key in keys:
            self.assertNotIn(key, tested_function._cache)

    def _general_multithreading_test(self, tested_function, algorithm):
        number_of_keys = 30000
        number_of_threads = 4

        # clear
        exec_times[tested_function.__name__] = 0
        tested_function.cache_clear()

        info = tested_function.cache_info()
        self.assertEqual(info.max_size, 5)
        self.assertEqual(info.algorithm, algorithm)
        self.assertIsNone(info.ttl)
        self.assertTrue(info.thread_safe)
        self.assertEqual(info.current_size, 0)

        # Test must-hit
        def run_must_hit():
            keys = list(range(5)) * int(number_of_keys / 5)
            random.shuffle(keys)
            for i in keys:
                tested_function(i)

        threads = [Thread(target=run_must_hit) for _ in range(number_of_threads)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        self.assertGreaterEqual(exec_times[tested_function.__name__], 5)
        info = tested_function.cache_info()
        self.assertLessEqual(info.hits, number_of_keys * number_of_threads - 5)
        self.assertGreaterEqual(info.misses, 5)
        self.assertEqual(info.current_size, 5)

        for key in [make_key((x,), None) for x in range(5)]:
            self.assertIn(key, tested_function._cache)

        # Test can-miss
        def run_can_miss():
            keys = list(range(20)) * int(number_of_keys / 20)
            random.shuffle(keys)
            for i in keys:
                tested_function(i)

        threads = [Thread(target=run_can_miss) for _ in range(number_of_threads)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        executed_times = exec_times[tested_function.__name__]
        self.assertLessEqual(executed_times, number_of_keys * number_of_threads)
        self.assertGreaterEqual(executed_times, 20)
        info = tested_function.cache_info()
        self.assertGreaterEqual(info.hits, 0)
        self.assertLessEqual(info.misses, number_of_keys * number_of_threads)
        self.assertEqual(info.current_size, 5)

    def _fifo_test(self, tested_function):
        self._general_test(tested_function=tested_function, algorithm=CachingAlgorithmFlag.FIFO, hits=7, misses=24,
                           in_cache=(16, 100, 15, 99, 19), not_in_cache=(18, 17))
        self.assertEqual(exec_times[tested_function.__name__], 24)

    def _lru_test(self, tested_function):
        self._general_test(tested_function=tested_function, algorithm=CachingAlgorithmFlag.LRU, hits=7, misses=24,
                           in_cache=(16, 100, 15, 19, 18), not_in_cache=(99, 17))
        self.assertEqual(exec_times[tested_function.__name__], 24)

    def _lfu_test(self, tested_function):
        self._general_test(tested_function=tested_function, algorithm=CachingAlgorithmFlag.LFU, hits=8, misses=23,
                           in_cache=(18, 17, 16, 19, 100), not_in_cache=(99, 15))
        self.assertEqual(exec_times[tested_function.__name__], 23)

    def _check_empty_cache_after_clearing(self, tested_function):
        info = tested_function.cache_info()
        self.assertEqual(info.hits, 0)
        self.assertEqual(info.misses, 0)
        self.assertEqual(info.current_size, 0)
        self.assertEqual(info.max_size, 5)

        cache = tested_function._cache
        self.assertEqual(len(cache), 0)

    def _check_lfu_cache_clearing(self, tested_function):
        root_next = weakref.ref(tested_function._lfu_root.next)
        first_cache_head = weakref.ref(tested_function._lfu_root.next.cache_head)
        self.assertIsNotNone(root_next())
        self.assertIsNotNone(first_cache_head())

        tested_function.cache_clear()
        self._check_empty_cache_after_clearing(tested_function)

        gc.collect()
        self.assertIsNone(root_next())
        self.assertIsNone(first_cache_head())

    def _general_ttl_test(self, tested_function):
        # clear
        exec_times[tested_function.__name__] = 0
        tested_function.cache_clear()

        arg = 1
        key = make_key((arg,), None)
        tested_function(arg)
        time.sleep(0.25)  # wait for a short time

        info = tested_function.cache_info()
        self.assertEqual(info.hits, 0)
        self.assertEqual(info.misses, 1)
        self.assertEqual(info.current_size, 1)
        self.assertIn(key, tested_function._cache)

        tested_function(arg)  # this WILL NOT call the tested function

        info = tested_function.cache_info()
        self.assertEqual(info.hits, 1)
        self.assertEqual(info.misses, 1)
        self.assertEqual(info.current_size, 1)
        self.assertIn(key, tested_function._cache)
        self.assertEqual(exec_times[tested_function.__name__], 1)

        time.sleep(0.35)  # wait until the cache expires

        info = tested_function.cache_info()
        self.assertEqual(info.current_size, 1)

        tested_function(arg)  # this WILL call the tested function

        info = tested_function.cache_info()
        self.assertEqual(info.hits, 1)
        self.assertEqual(info.misses, 2)
        self.assertEqual(info.current_size, 1)
        self.assertIn(key, tested_function._cache)
        self.assertEqual(exec_times[tested_function.__name__], 2)

    def _general_unhashable_arguments_test(self, tested_function):
        args = ([1, 2, 3], {'this': 'is unhashable'}, ['yet', ['another', ['complex', {'type, ': 'isn\'t it?'}]]])
        for arg in args:
            # clear
            exec_times[tested_function.__name__] = 0
            tested_function.cache_clear()

            key = make_key((arg,), None)
            tested_function(arg)
            self.assertIn(key, tested_function._cache)

            if isinstance(arg, list):
                arg.append(0)
            elif isinstance(arg, dict):
                arg['foo'] = 'bar'
            else:
                raise TypeError
            key = make_key((arg,), None)
            tested_function(arg)
            self.assertIn(key, tested_function._cache)

            if isinstance(arg, list):
                arg.pop()
            elif isinstance(arg, dict):
                del arg['foo']
            else:
                raise TypeError
            key = make_key((arg,), None)
            tested_function(arg)
            self.assertIn(key, tested_function._cache)

            self.assertEqual(exec_times[tested_function.__name__], 2)
            info = tested_function.cache_info()
            self.assertEqual(info.hits, 1)
            self.assertEqual(info.misses, 2)
            self.assertEqual(info.current_size, 2)


if __name__ == '__main__':
    unittest.main()
