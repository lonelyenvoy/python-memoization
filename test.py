# import memoization
#
#
# @memoization.cached()
# def f(a):
#     return a + 1
#
#
# result = f(2)
# f(3)
# f(4)
# f(5)
# f(2)
# # memoization.clear(f)
# print result
# print memoization.size()

import memoization
from memoization import cached
import unittest


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

    def test_cache(self):
        """
        Test memoization.cached
        """

        # test add
        self.assertEqual(self.f.add(1, 2), 3)
        self.assertEqual(memoization._cache.get(id(self.f.add)), {(1, 2): 3})
        self.assertEqual(memoization._access_count.get(id(self.f.add)), {(1, 2): 0})
        self.assertEqual(self.f.add(1, 2), 3)
        self.assertEqual(memoization._access_count.get(id(self.f.add)), {(1, 2): 1})

        # test function_with_side_effects
        self.assertEqual(self.f.function_with_side_effects(1), 1)
        self.assertEqual(self.f.number, 2)
        self.assertEqual(self.f.function_with_side_effects(1), 1)  # the real function should not be executed
        self.assertEqual(self.f.number, 2)

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
        self.assertEqual(memoization._cache.get(id(self.f.add)),             {(1, 2): 3, (3, 4): 7, (5, 6): 11})
        self.assertEqual(memoization._cache.get(id(self.f.subtract)),        {(10, 5): 5, (20, 10): 10, (30, 20): 10})
        self.assertEqual(memoization._access_count.get(id(self.f.add)),      {(1, 2): 5, (3, 4): 4, (5, 6): 0})
        self.assertEqual(memoization._access_count.get(id(self.f.subtract)), {(10, 5): 5, (20, 10): 4, (30, 20): 0})

    def test_clean_with_safe_access_count_and_func_restriction(self):
        """
        Test memoization.clean with safe_access_count and func restriction
        """
        self._make_cache()
        memoization.clean(safe_access_count=5, func=self.f.add)
        self.assertEqual(memoization._cache, {id(self.f.add): {(1, 2): 3},
                                              id(self.f.subtract): {(10, 5): 5, (20, 10): 10, (30, 20): 10}})
        self.assertEqual(memoization._access_count, {id(self.f.add): {(1, 2): 5},
                                                     id(self.f.subtract): {(10, 5): 5, (20, 10): 4, (30, 20): 0}})

    def test_clean_with_safe_access_count_restriction(self):
        """
        Test memoization.clean with safe_access_count restriction
        """
        self._make_cache()
        memoization.clean(safe_access_count=5)
        self.assertEqual(memoization._cache, {id(self.f.add): {(1, 2): 3},
                                              id(self.f.subtract): {(10, 5): 5}})
        self.assertEqual(memoization._access_count, {id(self.f.add): {(1, 2): 5},
                                                     id(self.f.subtract): {(10, 5): 5}})

    def test_clean_with_func_restriction(self):
        """
        Test memoization.clean with func restriction
        """
        self._make_cache()
        memoization.clean(func=self.f.add)
        self.assertEqual(memoization._cache, {id(self.f.add): {(1, 2): 3, (3, 4): 7},
                                              id(self.f.subtract): {(10, 5): 5, (20, 10): 10, (30, 20): 10}})
        self.assertEqual(memoization._access_count, {id(self.f.add): {(1, 2): 5, (3, 4): 4},
                                                     id(self.f.subtract): {(10, 5): 5, (20, 10): 4, (30, 20): 0}})

    def test_clean_without_restriction(self):
        """
        Test memoization.clean with default arguments
        """
        self._make_cache()
        memoization.clean()
        self.assertEqual(memoization._cache, {id(self.f.add): {(1, 2): 3, (3, 4): 7},
                                              id(self.f.subtract): {(10, 5): 5, (20, 10): 10}})
        self.assertEqual(memoization._access_count, {id(self.f.add): {(1, 2): 5, (3, 4): 4},
                                                     id(self.f.subtract): {(10, 5): 5, (20, 10): 4}})

    def test_clear_with_func_restriction(self):
        """
        Test memoization.clear with func restriction
        """
        self._make_cache()
        memoization.clear(func=self.f.add)
        self.assertEqual(memoization._cache, {id(self.f.subtract): {(10, 5): 5, (20, 10): 10, (30, 20): 10}})
        self.assertEqual(memoization._access_count, {id(self.f.subtract): {(10, 5): 5, (20, 10): 4, (30, 20): 0}})

    def test_clear_without_restriction(self):
        """
        Test memoization.clear without any restriction
        """
        self._make_cache()
        memoization.clear()
        self.assertEqual(memoization._cache, {})
        self.assertEqual(memoization._access_count, {})

    def test_size(self):
        """
        Test memoization.size
        TODO implement this function
        """
        raise NotImplementedError


if __name__ == '__main__':
    unittest.main()
