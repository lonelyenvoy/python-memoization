import time


def make_cache_value(result, ttl):
    return result, time.time() + ttl


def is_cache_value_valid(value):
    return time.time() < value[1]


def retrieve_result_from_cache_value(value):
    return value[0]
