import memoization
from memoization import cached
import unittest
import time


class TestedFunctions:
    """
    Functions to be tested
    """
    def __init__(self):
        self.number = 0

    @cached()
    def add(self, a, b):
        return a + b

    @cached()
    def subtract(self, a, b):
        return a - b

    @cached(ttl=0.01)
    def multiply(self, a, b):
        return a * b

    @cached()
    def function_with_side_effects(self, a):
        self.number += 1
        return a


class TestMemoization(unittest.TestCase):
    """
    Test python-memoization
    """

    def setUp(self):
        self.f = TestedFunctions()

    def tearDown(self):
        memoization.clear()

    @staticmethod
    def _wrapped_func_id(func):
        """
        Get the id of the function wrapped by decorator
        :param func: The inspecting function
        :return: id of the function wrapped by the decorator of func
        """
        return id(memoization._retrieve_undecorated_function(func))
    
    def _make_cache_key(self, *args, **kwargs):
        """
        Convert arguments to cache key

        e.g.
        _make_cache_key(1, 2) == '(<__main__.TestedFunctions instance at 0x100000000>, 1, 2)'
        _make_cache_key(1, 2, a=3) == '(<__main__.TestedFunctions instance at 0x100000000>, 1, 2, {a: 3})'

        :param args: function args
        :param kwargs: function kwargs
        :return: cache key
        """
        result = [self.f]
        for arg in args:
            result.append(arg)
        if len(kwargs) != 0:
            result.append(kwargs)
        return str(tuple(result))

    @staticmethod
    def _make_cache_value(result, access_count):
        """
        Convert result and access_count to cache value
        :param result: cache result
        :param access_count: cache access count
        :return: cache value
        """
        return {'result': result, 'access_count': access_count}

    def test_cache(self):
        """
        Test memoization.cached
        """

        # test add
        self.assertEqual(self.f.add(1, 2), 3)
        self.assertEqual(memoization._cache.get(self._wrapped_func_id(self.f.add)),
                         {self._make_cache_key(1, 2): self._make_cache_value(3, 0)})
        self.assertEqual(self.f.add(1, 2), 3)
        self.assertEqual(memoization._cache.get(self._wrapped_func_id(self.f.add)),
                         {self._make_cache_key(1, 2): self._make_cache_value(3, 1)})

        # test function_with_side_effects
        self.assertEqual(self.f.function_with_side_effects(1), 1)
        self.assertEqual(self.f.number, 1)
        self.assertEqual(self.f.function_with_side_effects(1), 1)  # the real function should not be executed
        self.assertEqual(self.f.number, 1)

    def _make_cache(self):
        """
        Cache preparation used in tests
        """
        for _ in range(6):
            self.f.add(1, 2)
            self.f.subtract(10, 5)
        for _ in range(5):
            self.f.add(3, 4)
            self.f.subtract(20, 10)
        self.f.add(5, 6)
        self.f.subtract(30, 20)

    def test_make_cache(self):
        """
        Test self._make_cache
        """
        self._make_cache()
        self.assertEqual(memoization._cache.get(self._wrapped_func_id(self.f.add)),
                         {self._make_cache_key(1, 2): self._make_cache_value(3, 5),
                          self._make_cache_key(3, 4): self._make_cache_value(7, 4),
                          self._make_cache_key(5, 6): self._make_cache_value(11, 0)})
        self.assertEqual(memoization._cache.get(self._wrapped_func_id(self.f.subtract)),
                         {self._make_cache_key(10, 5): self._make_cache_value(5, 5),
                          self._make_cache_key(20, 10): self._make_cache_value(10, 4),
                          self._make_cache_key(30, 20): self._make_cache_value(10, 0)})

    def test_clean_with_safe_access_count_and_func_restriction(self):
        """
        Test memoization.clean with safe_access_count and func restriction
        """
        self._make_cache()
        memoization.clean(safe_access_count=5, func=self.f.add)
        self.assertEqual(memoization._cache.get(self._wrapped_func_id(self.f.add)),
                         {self._make_cache_key(1, 2): self._make_cache_value(3, 5)})
        self.assertEqual(memoization._cache.get(self._wrapped_func_id(self.f.subtract)),
                         {self._make_cache_key(10, 5): self._make_cache_value(5, 5),
                          self._make_cache_key(20, 10): self._make_cache_value(10, 4),
                          self._make_cache_key(30, 20): self._make_cache_value(10, 0)})

    def test_clean_with_safe_access_count_restriction(self):
        """
        Test memoization.clean with safe_access_count restriction
        """
        self._make_cache()
        memoization.clean(safe_access_count=5)
        self.assertEqual(memoization._cache.get(self._wrapped_func_id(self.f.add)),
                         {self._make_cache_key(1, 2): self._make_cache_value(3, 5)})
        self.assertEqual(memoization._cache.get(self._wrapped_func_id(self.f.subtract)),
                         {self._make_cache_key(10, 5): self._make_cache_value(5, 5)})

    def test_clean_with_func_restriction(self):
        """
        Test memoization.clean with func restriction
        """
        self._make_cache()
        memoization.clean(func=self.f.add)
        self.assertEqual(memoization._cache.get(self._wrapped_func_id(self.f.add)),
                         {self._make_cache_key(1, 2): self._make_cache_value(3, 5),
                          self._make_cache_key(3, 4): self._make_cache_value(7, 4)})
        self.assertEqual(memoization._cache.get(self._wrapped_func_id(self.f.subtract)),
                         {self._make_cache_key(10, 5): self._make_cache_value(5, 5),
                          self._make_cache_key(20, 10): self._make_cache_value(10, 4),
                          self._make_cache_key(30, 20): self._make_cache_value(10, 0)})

    def test_clean_without_restriction(self):
        """
        Test memoization.clean with default arguments
        """
        self._make_cache()
        memoization.clean()
        self.assertEqual(memoization._cache.get(self._wrapped_func_id(self.f.add)),
                         {self._make_cache_key(1, 2): self._make_cache_value(3, 5),
                          self._make_cache_key(3, 4): self._make_cache_value(7, 4)})
        self.assertEqual(memoization._cache.get(self._wrapped_func_id(self.f.subtract)),
                         {self._make_cache_key(10, 5): self._make_cache_value(5, 5),
                          self._make_cache_key(20, 10): self._make_cache_value(10, 4)})

    def test_clear_with_func_restriction(self):
        """
        Test memoization.clear with func restriction
        """
        self._make_cache()
        memoization.clear(func=self.f.add)
        self.assertEqual(memoization._cache.get(self._wrapped_func_id(self.f.add)), {})
        self.assertEqual(memoization._cache.get(self._wrapped_func_id(self.f.subtract)),
                         {self._make_cache_key(10, 5): self._make_cache_value(5, 5),
                          self._make_cache_key(20, 10): self._make_cache_value(10, 4),
                          self._make_cache_key(30, 20): self._make_cache_value(10, 0)})

    def test_clear_without_restriction(self):
        """
        Test memoization.clear without any restriction
        """
        self._make_cache()
        memoization.clear()
        self.assertEqual(memoization._cache.get(self._wrapped_func_id(self.f.add)), {})
        self.assertEqual(memoization._cache.get(self._wrapped_func_id(self.f.subtract)), {})

    def test_size_with_func_restriction(self):
        """
        Test memoization.size with func restriction
        """
        self._make_cache()
        self.assertEqual(memoization.size(self.f.add), 3)
        self.assertEqual(memoization.size(self.f.subtract), 3)
        memoization.clear()
        self.assertEqual(memoization.size(self.f.add), 0)
        self.assertEqual(memoization.size(self.f.subtract), 0)

    def test_size_without_restriction(self):
        """
        Test memoization.size with default arguments
        """
        self._make_cache()
        self.assertEqual(memoization.size(), 6)
        memoization.clear()
        self.assertEqual(memoization.size(), 0)

    def test_ttl(self):
        """
        Test memoization.cached with ttl
        """
        for _ in range(3):
            self.f.multiply(2, 3)
        cache_unit = memoization._cache.get(self._wrapped_func_id(self.f.multiply))[self._make_cache_key(2, 3)]
        self.assertEqual(cache_unit['result'], 6)
        self.assertEqual(cache_unit['access_count'], 2)
        time.sleep(0.02)
        self.f.multiply(2, 3)
        cache_unit = memoization._cache.get(self._wrapped_func_id(self.f.multiply))[self._make_cache_key(2, 3)]
        self.assertEqual(cache_unit['access_count'], 0)


if __name__ == '__main__':
    unittest.main()
