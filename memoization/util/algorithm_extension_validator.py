import sys
import traceback

from memoization.constant.flag import CachingAlgorithmFlag
from memoization.config.algorithm_mapping import get_cache_toolkit
from memoization.model import CacheInfo
from memoization import cached

_problematic = False
_non_internal_algorithms_found = False


def validate():
    """
    Use this function to validate your extended caching algorithms.
    """
    global _non_internal_algorithms_found
    internal_algorithms = ['FIFO', 'LRU', 'LFU']
    has_cache_info = True

    for name, member in CachingAlgorithmFlag.__members__.items():
        if name not in internal_algorithms:

            @cached(max_size=5, ttl=0.5, algorithm=member, thread_safe=True)
            def tested_function(x):
                return x

            def undecorated_tested_function(x):
                return x

            _non_internal_algorithms_found = True
            print('Found extended algorithm <{}>'.format(name))
            try:
                cache_toolkit = get_cache_toolkit(member)
            except KeyError:
                _error('Cannot find mapping configuration for algorithm <{}>\n'.format(name))
                return
            if not hasattr(cache_toolkit, 'get_caching_wrapper'):
                _error('Cannot find get_caching_wrapper function in module <{}>\n'
                                 .format(cache_toolkit.__name__))
                return
            if not callable(cache_toolkit.get_caching_wrapper):
                _error('Expected {}.get_caching_wrapper to be callable\n'
                                 .format(cache_toolkit.__name__))
                return
            wrapper = cache_toolkit.get_caching_wrapper(
                user_function=undecorated_tested_function, max_size=5, ttl=0.5, algorithm=member,
                thread_safe=True, order_independent=False, custom_key_maker=None)

            if not hasattr(wrapper, 'cache_info'):
                has_cache_info = False
                _error('Cannot find cache_info function in the cache wrapper of <{}>\n'
                                 .format(cache_toolkit.__name__))
            elif not callable(wrapper.cache_info):
                has_cache_info = False
                _error('Expected cache_info of wrapper of <{}> to be callable\n'
                                 .format(cache_toolkit.__name__))

            for function_name in (
                    'cache_clear', 'cache_is_empty', 'cache_is_full', 'cache_contains_argument',
                    'cache_contains_result', 'cache_for_each', 'cache_arguments', 'cache_results', 'cache_items',
                    'cache_remove_if',
            ):
                _expect_has_attribute_and_callable(wrapper, function_name, cache_toolkit.__name__)

            for x in range(0, 5):
                tested_function(x)

            if has_cache_info:
                info = tested_function.cache_info()
                if not isinstance(info, CacheInfo):
                    _error('The return value of cache_info is not an instance of CacheInfo')
                else:
                    if not isinstance(info.hits, int):
                        _error('Expected cache_info().hits to be an integer')
                    if not isinstance(info.misses, int):
                        _error('Expected cache_info().misses to be an integer')
                    if not isinstance(info.current_size, int):
                        _error('Expected cache_info().current_size to be an integer')
                    if info.max_size is not None and not isinstance(info.max_size, int):
                        _error('Expected cache_info().max_size to be an integer')
                    if info.algorithm != member:
                        _error('Expected cache_info().algorithm = <{}> to be <{}>'
                                         .format(info.algorithm, member))
                    if info.ttl is not None and not isinstance(info.ttl, int) and not isinstance(info.ttl, float):
                        _error('Expected cache_info().ttl to be an integer or a float')
                    if not isinstance(info.thread_safe, bool):
                        _error('Expected cache_info().thread_safe to be a bool')


def _expect_has_attribute_and_callable(wrapper, attribute_name, parent_object_name):
    if not hasattr(wrapper, attribute_name):
        _error('Cannot find {} function in the cache wrapper of <{}>\n'.format(attribute_name, parent_object_name))
    elif not callable(getattr(wrapper, attribute_name)):
        _error('Expected {} of wrapper of <{}> to be callable\n'.format(attribute_name, parent_object_name))


def _error(message):
    global _problematic
    _problematic = True
    sys.stderr.write('[ERROR] ' + message + '\n')


if __name__ == '__main__':
    try:
        validate()
        if _non_internal_algorithms_found is False:
            sys.stderr.write('No extended algorithms found. Please read the extension guidance.\n')
        else:
            if _problematic is False:
                print('\n[Validation OK]')
                print('Congratulations! Your extended algorithm passed the validation. Thanks for your efforts.')
                print('Please understand that this validator only ensure that the typings of your extension are correct. '
                      'You are still required to write test cases for your algorithms.')
            else:
                _error('\nError(s) occurred during validation. It\'s likely that your extended algorithm '
                       'does not function properly. Please read the extension guidance.\n'
                       'If you consider it a bug of the validator itself, you are welcome to fix it in '
                       'your pull request or to create an issue for further help. Thanks!\n')
    except:
        _error('\nUnexpected error(s) occurred during validation. It\'s likely that your extended algorithm '
               'does not function properly. Please read the extension guidance.\n'
               'If you consider it a bug of the validator itself, you are welcome to fix it in '
               'your pull request or to create an issue for further help. Thanks!\n')
        traceback.print_exc()

