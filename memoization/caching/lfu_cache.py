from threading import RLock

from memoization.model import DummyWithable, CacheInfo
import memoization.caching.general.keys_order_dependent as keys_toolkit_order_dependent
import memoization.caching.general.keys_order_independent as keys_toolkit_order_independent
import memoization.caching.general.values_with_ttl as values_toolkit_with_ttl
import memoization.caching.general.values_without_ttl as values_toolkit_without_ttl


def get_caching_wrapper(user_function, max_size, ttl, algorithm, thread_safe, order_independent, custom_key_maker):
    """Get a caching wrapper for LFU cache"""

    cache = {}                                                  # the cache to store function results
    key_argument_map = {}                                       # mapping from cache keys to user function arguments
    sentinel = object()                                         # sentinel object for the default value of map.get
    hits = misses = 0                                           # hits and misses of the cache
    lock = RLock() if thread_safe else DummyWithable()          # ensure thread-safe
    if ttl is not None:                                         # set up values toolkit according to ttl
        values_toolkit = values_toolkit_with_ttl
    else:
        values_toolkit = values_toolkit_without_ttl
    if custom_key_maker is not None:                            # use custom make_key function
        make_key = custom_key_maker
    else:
        if order_independent:                                   # set up keys toolkit according to order_independent
            make_key = keys_toolkit_order_independent.make_key
        else:
            make_key = keys_toolkit_order_dependent.make_key
    lfu_freq_list_root = _FreqNode.root()                       # LFU frequency list root

    def wrapper(*args, **kwargs):
        """The actual wrapper"""
        nonlocal hits, misses
        key = make_key(args, kwargs)
        cache_expired = False
        with lock:
            result = _access_lfu_cache(cache, key, sentinel)
            if result is not sentinel:
                if values_toolkit.is_cache_value_valid(result):
                    hits += 1
                    return values_toolkit.retrieve_result_from_cache_value(result)
                else:
                    cache_expired = True
            misses += 1
        result = user_function(*args, **kwargs)
        with lock:
            if key in cache:
                if cache_expired:
                    # update cache with new ttl
                    cache[key].value = values_toolkit.make_cache_value(result, ttl)
                else:
                    # result added to the cache while the lock was released
                    # no need to add again
                    pass
            else:
                user_function_arguments = (args, kwargs)
                cache_value = values_toolkit.make_cache_value(result, ttl)
                _insert_into_lfu_cache(cache, key_argument_map, user_function_arguments, key, cache_value,
                                       lfu_freq_list_root, max_size)
        return result

    def cache_clear():
        """Clear the cache and its statistics information"""
        nonlocal hits, misses, lfu_freq_list_root
        with lock:
            cache.clear()
            key_argument_map.clear()
            hits = misses = 0
            lfu_freq_list_root.prev = lfu_freq_list_root.next = lfu_freq_list_root

    def cache_info():
        """
        Show statistics information

        :return: a CacheInfo object describing the cache
        """
        with lock:
            return CacheInfo(hits, misses, cache.__len__(), max_size, algorithm,
                             ttl, thread_safe, order_independent, custom_key_maker is not None)

    def cache_is_empty():
        """Return True if the cache contains no elements"""
        return cache.__len__() == 0

    def cache_is_full():
        """Return True if the cache is full"""
        return cache.__len__() >= max_size

    def cache_contains_argument(function_arguments, alive_only=True):
        """
        Return True if the cache contains a cached item with the specified function call arguments

        :param function_arguments:  Can be a list, a tuple or a dict.
                                    - Full arguments: use a list to represent both positional arguments and keyword
                                      arguments. The list contains two elements, a tuple (positional arguments) and
                                      a dict (keyword arguments). For example,
                                        f(1, 2, 3, a=4, b=5, c=6)
                                      can be represented by:
                                        [(1, 2, 3), {'a': 4, 'b': 5, 'c': 6}]
                                    - Positional arguments only: when the arguments does not include keyword arguments,
                                      a tuple can be used to represent positional arguments. For example,
                                        f(1, 2, 3)
                                      can be represented by:
                                        (1, 2, 3)
                                    - Keyword arguments only: when the arguments does not include positional arguments,
                                      a dict can be used to represent keyword arguments. For example,
                                        f(a=4, b=5, c=6)
                                      can be represented by:
                                        {'a': 4, 'b': 5, 'c': 6}

        :param alive_only:          Whether to check alive cache item only (default to True).

        :return:                    True if the desired cached item is present, False otherwise.
        """
        if isinstance(function_arguments, tuple):
            positional_argument_tuple = function_arguments
            keyword_argument_dict = {}
        elif isinstance(function_arguments, dict):
            positional_argument_tuple = ()
            keyword_argument_dict = function_arguments
        elif isinstance(function_arguments, list) and len(function_arguments) == 2:
            positional_argument_tuple, keyword_argument_dict = function_arguments
            if not isinstance(positional_argument_tuple, tuple) or not isinstance(keyword_argument_dict, dict):
                raise TypeError('Expected function_arguments to be a list containing a positional argument tuple '
                                'and a keyword argument dict')
        else:
            raise TypeError('Expected function_arguments to be a tuple, a dict, or a list with 2 elements')
        key = make_key(positional_argument_tuple, keyword_argument_dict)
        with lock:
            cache_node = cache.get(key, sentinel)
            if cache_node is not sentinel:
                return values_toolkit.is_cache_value_valid(cache_node.value) if alive_only else True
            return False

    def cache_contains_result(return_value, alive_only=True):
        """
        Return True if the cache contains a cache item with the specified user function return value. O(n) time
        complexity.

        :param return_value:        A return value coming from the user function.

        :param alive_only:          Whether to check alive cache item only (default to True).

        :return:                    True if the desired cached item is present, False otherwise.
        """
        with lock:
            freq_node = lfu_freq_list_root.prev
            while freq_node != lfu_freq_list_root:
                cache_head = freq_node.cache_head
                cache_node = cache_head.next
                while cache_node != cache_head:
                    is_alive = values_toolkit.is_cache_value_valid(cache_node.value)
                    cache_result = values_toolkit.retrieve_result_from_cache_value(cache_node.value)
                    if cache_result == return_value:
                        return is_alive if alive_only else True
                    cache_node = cache_node.next
                freq_node = freq_node.prev
            return False

    def cache_for_each(consumer):
        """
        Perform the given action for each cache element in an order determined by the algorithm until all
        elements have been processed or the action throws an error

        :param consumer:            an action function to process the cache elements. Must have 3 arguments:
                                      def consumer(user_function_arguments, user_function_result, is_alive): ...
                                    user_function_arguments is a tuple holding arguments in the form of (args, kwargs).
                                      args is a tuple holding positional arguments.
                                      kwargs is a dict holding keyword arguments.
                                      for example, for a function: foo(a, b, c, d), calling it by: foo(1, 2, c=3, d=4)
                                      user_function_arguments == ((1, 2), {'c': 3, 'd': 4})
                                    user_function_result is a return value coming from the user function.
                                    cache_result is a return value coming from the user function.
                                    is_alive is a boolean value indicating whether the cache is still alive
                                    (if a TTL is given).
        """
        with lock:
            freq_node = lfu_freq_list_root.prev
            while freq_node != lfu_freq_list_root:
                cache_head = freq_node.cache_head
                cache_node = cache_head.next
                while cache_node != cache_head:
                    is_alive = values_toolkit.is_cache_value_valid(cache_node.value)
                    user_function_result = values_toolkit.retrieve_result_from_cache_value(cache_node.value)
                    user_function_arguments = key_argument_map[cache_node.key]
                    consumer(user_function_arguments, user_function_result, is_alive)
                    cache_node = cache_node.next
                freq_node = freq_node.prev

    def cache_arguments():
        """
        Get user function arguments of all alive cache elements

        see also: cache_items()

        Example:
            @cached
            def f(a, b, c, d):
                ...
            f(1, 2, c=3, d=4)
            for argument in f.cache_arguments():
                print(argument)  # ((1, 2), {'c': 3, 'd': 4})

        :return: an iterable which iterates through a list of a tuple containing a tuple (positional arguments) and
                 a dict (keyword arguments)
        """
        with lock:
            freq_node = lfu_freq_list_root.prev
            while freq_node != lfu_freq_list_root:
                cache_head = freq_node.cache_head
                cache_node = cache_head.next
                while cache_node != cache_head:
                    if values_toolkit.is_cache_value_valid(cache_node.value):
                        yield key_argument_map[cache_node.key]
                    cache_node = cache_node.next
                freq_node = freq_node.prev

    def cache_results():
        """
        Get user function return values of all alive cache elements

        see also: cache_items()

        Example:
            @cached
            def f(a):
                return a
            f('hello')
            for result in f.cache_results():
                print(result)  # 'hello'

        :return: an iterable which iterates through a list of user function result (of any type)
        """
        with lock:
            freq_node = lfu_freq_list_root.prev
            while freq_node != lfu_freq_list_root:
                cache_head = freq_node.cache_head
                cache_node = cache_head.next
                while cache_node != cache_head:
                    if values_toolkit.is_cache_value_valid(cache_node.value):
                        yield values_toolkit.retrieve_result_from_cache_value(cache_node.value)
                    cache_node = cache_node.next
                freq_node = freq_node.prev

    def cache_items():
        """
        Get cache items, i.e. entries of all alive cache elements, in the form of (argument, result).

        argument: a tuple containing a tuple (positional arguments) and a dict (keyword arguments).
        result: a user function return value of any type.

        see also: cache_arguments(), cache_results().

        Example:
            @cached
            def f(a, b, c, d):
                return 'the answer is ' + str(a)
            f(1, 2, c=3, d=4)
            for argument, result in f.cache_items():
                print(argument)  # ((1, 2), {'c': 3, 'd': 4})
                print(result)    # 'the answer is 1'

        :return: an iterable which iterates through a list of (argument, result) entries
        """
        with lock:
            freq_node = lfu_freq_list_root.prev
            while freq_node != lfu_freq_list_root:
                cache_head = freq_node.cache_head
                cache_node = cache_head.next
                while cache_node != cache_head:
                    if values_toolkit.is_cache_value_valid(cache_node.value):
                        yield (key_argument_map[cache_node.key],
                               values_toolkit.retrieve_result_from_cache_value(cache_node.value))
                    cache_node = cache_node.next
                freq_node = freq_node.prev

    def cache_remove_if(predicate):
        """
        Remove all cache elements that satisfy the given predicate

        :param predicate:           a predicate function to judge whether the cache elements should be removed. Must
                                    have 3 arguments, and returns True or False:
                                      def consumer(user_function_arguments, user_function_result, is_alive): ...
                                    user_function_arguments is a tuple holding arguments in the form of (args, kwargs).
                                      args is a tuple holding positional arguments.
                                      kwargs is a dict holding keyword arguments.
                                      for example, for a function: foo(a, b, c, d), calling it by: foo(1, 2, c=3, d=4)
                                      user_function_arguments == ((1, 2), {'c': 3, 'd': 4})
                                    user_function_result is a return value coming from the user function.
                                    cache_result is a return value coming from the user function.
                                    is_alive is a boolean value indicating whether the cache is still alive
                                    (if a TTL is given).

        :return:                    True if at least one element is removed, False otherwise.
        """
        removed = False
        with lock:
            freq_node = lfu_freq_list_root.prev
            while freq_node != lfu_freq_list_root:
                cache_head = freq_node.cache_head
                cache_node = cache_head.next
                removed_under_this_freq_node = False
                while cache_node != cache_head:
                    is_alive = values_toolkit.is_cache_value_valid(cache_node.value)
                    user_function_result = values_toolkit.retrieve_result_from_cache_value(cache_node.value)
                    user_function_arguments = key_argument_map[cache_node.key]
                    if predicate(user_function_arguments, user_function_result, is_alive):
                        removed = removed_under_this_freq_node = True
                        next_cache_node = cache_node.next
                        del cache[cache_node.key]  # delete from cache
                        del key_argument_map[cache_node.key]
                        cache_node.destroy()  # modify references, drop this cache node
                        cache_node = next_cache_node
                    else:
                        cache_node = cache_node.next
                # check whether only one cache node is left
                if removed_under_this_freq_node and freq_node.cache_head.next == freq_node.cache_head:
                    # Getting here means that we just deleted the only data node in the cache list
                    # Note: there is still an empty sentinel node
                    # We then need to destroy the sentinel node and its parent frequency node too
                    prev_freq_node = freq_node.prev
                    freq_node.cache_head.destroy()
                    freq_node.destroy()
                    freq_node = prev_freq_node
                else:
                    freq_node = freq_node.prev
        return removed

    # expose operations to wrapper
    wrapper.cache_clear = cache_clear
    wrapper.cache_info = cache_info
    wrapper.cache_is_empty = cache_is_empty
    wrapper.cache_is_full = cache_is_full
    wrapper.cache_contains_argument = cache_contains_argument
    wrapper.cache_contains_result = cache_contains_result
    wrapper.cache_for_each = cache_for_each
    wrapper.cache_arguments = cache_arguments
    wrapper.cache_results = cache_results
    wrapper.cache_items = cache_items
    wrapper.cache_remove_if = cache_remove_if
    wrapper._cache = cache
    wrapper._lfu_root = lfu_freq_list_root
    wrapper._root_name = '_lfu_root'

    return wrapper


################################################################################################################################
# LFU Cache
# Least Frequently Used Cache
#
# O(1) implementation - please refer to the following documents for more details:
# http://dhruvbird.com/lfu.pdf
# https://medium.com/@epicshane/a-python-implementation-of-lfu-least-frequently-used-cache-with-o-1-time-complexity-e16b34a3c49b
################################################################################################################################


class _CacheNode(object):
    """
    Cache Node for LFU Cache
    """

    __slots__ = 'prev', 'next', 'parent', 'key', 'value', '__weakref__'

    def __init__(self, prev=None, next=None, parent=None, key=None, value=None):
        self.prev = prev
        self.next = next
        self.parent = parent
        self.key = key
        self.value = value

    @classmethod
    def root(cls, parent=None, key=None, value=None):
        """
        Generate an empty root node
        """
        node = cls(None, None, parent, key, value)
        node.prev = node.next = node
        return node

    def destroy(self):
        """
        Destroy the current cache node
        """
        self.prev.next = self.next
        self.next.prev = self.prev
        if self.parent.cache_head == self:
            self.parent.cache_head = None
        self.prev = self.next = self.parent = self.key = self.value = None


class _FreqNode(object):
    """
    Frequency Node for LFU Cache
    """

    __slots__ = 'prev', 'next', 'frequency', 'cache_head', '__weakref__'

    def __init__(self, prev=None, next=None, frequency=None, cache_head=None):
        self.prev = prev
        self.next = next
        self.frequency = frequency
        self.cache_head = cache_head

    @classmethod
    def root(cls, frequency=None, cache_head=None):
        """
        Generate an empty root node
        """
        node = cls(None, None, frequency, cache_head)
        node.prev = node.next = node
        return node

    def destroy(self):
        """
        Destroy the current frequency node
        """
        self.prev.next = self.next
        self.next.prev = self.prev
        self.prev = self.next = self.cache_head = None


def _insert_into_lfu_cache(cache, key_argument_map, user_function_arguments, key, value, root, max_size):
    first_freq_node = root.next
    if cache.__len__() >= max_size:
        # The cache is full

        if first_freq_node.frequency != 1:
            # The first element in frequency list has its frequency other than 1 (> 1)
            # We need to drop the last element in the cache list of the first frequency node
            # and then insert a new frequency node, attaching an empty cache node together with
            # another cache node with data to the frequency node

            # Find the target
            cache_head = first_freq_node.cache_head
            last_node = cache_head.prev

            # Modify references
            last_node.prev.next = cache_head
            cache_head.prev = last_node.prev

            # Drop the last node; hold the old data to prevent arbitrary GC
            old_key = last_node.key
            old_value = last_node.value
            last_node.destroy()

            if first_freq_node.cache_head.next == first_freq_node.cache_head:
                # Getting here means that we just deleted the only data node in the cache list
                # under the first frequency list
                # Note: there is still an empty sentinel node
                # We then need to destroy the sentinel node and its parent frequency node too
                first_freq_node.cache_head.destroy()
                first_freq_node.destroy()
                first_freq_node = root.next  # update

            # Delete from cache
            del cache[old_key]
            del key_argument_map[old_key]

            # Prepare a new frequency node, a cache root node and a cache data node
            empty_cache_root = _CacheNode.root()
            freq_node = _FreqNode(root, first_freq_node, 1, empty_cache_root)
            cache_node = _CacheNode(empty_cache_root, empty_cache_root, freq_node, key, value)
            empty_cache_root.parent = freq_node

            # Modify references
            root.next.prev = root.next = freq_node
            empty_cache_root.prev = empty_cache_root.next = cache_node

        else:
            # We can find the last element in the cache list under the first frequency list
            # Moving it to the head and replace the stored data with a new key and a new value
            # This is more efficient

            # Find the target
            cache_head = first_freq_node.cache_head
            manipulated_node = cache_head.prev

            # Modify references
            manipulated_node.prev.next = cache_head
            cache_head.prev = manipulated_node.prev
            manipulated_node.next = cache_head.next
            manipulated_node.prev = cache_head
            cache_head.next.prev = cache_head.next = manipulated_node

            # Replace the data; hold the old data to prevent arbitrary GC
            old_key = manipulated_node.key
            old_value = manipulated_node.value
            manipulated_node.key = key
            manipulated_node.value = value

            # use another name so it can be accessed later
            cache_node = manipulated_node

            # Delete from cache
            del cache[old_key]
            del key_argument_map[old_key]
    else:
        # The cache is not full

        if first_freq_node.frequency != 1:
            # The first element in frequency list has its frequency other than 1 (> 1)
            # Creating a new node in frequency list with 1 as its frequency required
            # We also need to create a new cache list and attach it to this new node

            # Create a cache root and a frequency node
            cache_root = _CacheNode.root()
            freq_node = _FreqNode(root, first_freq_node, 1, cache_root)
            cache_root.parent = freq_node

            # Create another cache node to store data
            cache_node = _CacheNode(cache_root, cache_root, freq_node, key, value)

            # Modify references
            cache_root.prev = cache_root.next = cache_node
            first_freq_node.prev = root.next = freq_node  # note: DO NOT swap "=", because first_freq_node == root.next

        else:
            # We create a new cache node in the cache list
            # under the frequency node with frequency 1

            # Create a cache node and store data in it
            cache_head = first_freq_node.cache_head
            cache_node = _CacheNode(cache_head, cache_head.next, first_freq_node, key, value)

            # Modify references
            cache_node.prev.next = cache_node.next.prev = cache_node

    # Finally, insert the data into the cache
    cache[key] = cache_node
    key_argument_map[key] = user_function_arguments


def _access_lfu_cache(cache, key, sentinel):
    if key in cache:
        cache_node = cache[key]
    else:
        # Key does not exist
        # Access failed
        return sentinel
    freq_node = cache_node.parent
    target_frequency = freq_node.frequency + 1
    if freq_node.next.frequency != target_frequency:
        # The next node on the frequency list has a frequency value different from
        # (the frequency of the current node) + 1, which means we need to construct
        # a new frequency node and an empty cache root node
        # Then we move the current node to the newly created cache list

        # Create a cache root and a frequency root
        cache_root = _CacheNode.root()
        new_freq_node = _FreqNode(freq_node, freq_node.next, target_frequency, cache_root)
        cache_root.parent = new_freq_node

        # Modify references
        cache_node.prev.next = cache_node.next
        cache_node.next.prev = cache_node.prev
        cache_node.prev = cache_node.next = cache_root
        cache_root.prev = cache_root.next = cache_node
        new_freq_node.next.prev = new_freq_node.prev.next = new_freq_node
        cache_node.parent = cache_root.parent

    else:
        # We can move the cache node to the cache list of the next node on the frequency list

        # Find the head element of the next cache list
        next_cache_head = freq_node.next.cache_head

        # Modify references
        cache_node.prev.next = cache_node.next
        cache_node.next.prev = cache_node.prev
        cache_node.next = next_cache_head.next
        cache_node.prev = next_cache_head
        next_cache_head.next.prev = next_cache_head.next = cache_node
        cache_node.parent = freq_node.next

    # check the status of the current frequency node
    if freq_node.cache_head.next == freq_node.cache_head:
        # Getting here means that we just moved away the only data node in the cache list
        # Note: there is still an empty sentinel node
        # We then need to destroy the sentinel node and its parent frequency node too
        freq_node.cache_head.destroy()
        freq_node.destroy()

    return cache_node.value
