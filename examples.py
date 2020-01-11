from memoization import cached, CachingAlgorithmFlag
import timeit


def factorial(n):
    assert n >= 0
    if n == 0 or n == 1:
        return 1
    return n * factorial(n - 1)


# Example usage
@cached(max_size=64, algorithm=CachingAlgorithmFlag.FIFO, thread_safe=False)
def quick_factorial(n):
    assert n >= 0
    if n == 0 or n == 1:
        return 1
    return n * quick_factorial(n - 1)


def test1():
    for i in range(1, 500):
        factorial(i)


def test2():
    for i in range(1, 500):
        quick_factorial(i)


depth = 500
test_times = 100

time1 = timeit.timeit(test1, number=test_times) / test_times
time2 = timeit.timeit(test2, number=test_times) / test_times

print('factorial(' + str(depth) + ') without memoization took ' + str(time1 * 1000) + ' ms')
print('factorial(' + str(depth) + ') with    memoization took ' + str(time2 * 1000) + ' ms')
