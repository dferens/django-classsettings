import functools


def defaultargs(func):
    """
    Calls parameterized decorator automatically if no args were
    supplied.
    
    With : @mydecorator
    Without: @mydecorator()
    """
    @functools.wraps(func)
    def decorated(*args, **kwargs):
        if len(args) == 1 and callable(args[0]):
            return func()(args[0])
        else:
            return func(*args, **kwargs)
    return decorated
