from memoization import cached
import timeit


def factorial(n):
    if n <= 0:
        return 0
    if n == 1:
        return 1
    return n * factorial(n - 1)


@cached()
def quick_factorial(n):
    if n <= 0:
        return 0
    if n == 1:
        return 1
    return n * quick_factorial(n - 1)


def test1():
    factorial(100)


def test2():
    quick_factorial(100)


test_times = 100000
time1 = timeit.timeit(test1, number=test_times) / test_times
time2 = timeit.timeit(test2, number=test_times) / test_times

print('factorial(100) without memoization took ' + str(time1 * 1000) + ' ms')
print('factorial(100) with    memoization took ' + str(time2 * 1000) + ' ms')
