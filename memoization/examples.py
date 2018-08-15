from memoization import cached
import timeit


def factorial(n):
    assert n >= 0
    if n == 0 or n == 1:
        return 1
    return n * factorial(n - 1)


@cached()
def quick_factorial(n):
    assert n >= 0
    if n == 0 or n == 1:
        return 1
    return n * quick_factorial(n - 1)


def test1():
    for i in range(1, 100):
        factorial(i)


def test2():
    for i in range(1, 100):
        quick_factorial(i)


test_times = 1000
time1 = timeit.timeit(test1, number=test_times) / test_times
time2 = timeit.timeit(test2, number=test_times) / test_times

print('factorial(100) without memoization took ' + str(time1 * 1000) + ' ms')
print('factorial(100) with    memoization took ' + str(time2 * 1000) + ' ms')
