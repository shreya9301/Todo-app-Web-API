import typing

def get_cached_value(holder_object : typing.Any, cache_key : str, getter : typing.Callable, *args, **kwargs) -> typing.Any:
    """Get cached value from an holder_object and set the cache value at the first request.
    """
    if not hasattr(holder_object, cache_key):
        setattr(holder_object, cache_key, getter(*args, **kwargs))
    return getattr(holder_object, cache_key)
