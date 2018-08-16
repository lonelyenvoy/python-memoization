def include_undecorated_function(key='original'):
    """
    Decorator to include original function in a decorated one

    e.g.
    @include_undecorated_function()
    def shout(f):
        def _():
            string = f()
            return string.upper()
        return _


    @shout
    def hello():
        return 'hello world'

    print hello()               # HELLO WORLD
    print hello.original()      # hello world

    :param key: The key to access the original function
    :return: decorator
    """
    def this_decorator(decorator):
        def wrapper(func):
            decorated = decorator(func)
            setattr(decorated, key, func)
            return decorated
        return wrapper
    return this_decorator
