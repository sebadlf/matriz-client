"""
Time-based caching decorator that caches function results based on parameters and time.
Only calls the function if parameters are new or specified seconds have passed.
"""

import time
import functools
from typing import Any, Callable, Dict, Tuple, TypeVar, cast
from typing_extensions import ParamSpec

# Type variables for preserving function signatures
P = ParamSpec("P")  # For parameters
R = TypeVar("R")  # For return type
F = TypeVar("F", bound=Callable[..., Any])


def time_cached(seconds: float, *, debug: bool = False) -> Callable[[F], F]:
    """
    Decorator that caches function results based on parameters and time.
    Only calls the function if parameters are new or specified seconds have passed.

    Args:
        seconds: Number of seconds to cache results for each parameter combination
        debug: If True, prints cache hit/miss information. Defaults to False.

    Returns:
        A decorator that preserves the original function's type signature

    Example:
        @time_cached(seconds=5.0)
        def expensive_function(param1: int, param2: str) -> str:
            # Expensive computation here
            return f"Result for {param1} and {param2}"

        @time_cached(seconds=5.0, debug=True)
        def debug_function(x: int) -> int:
            # This will print cache information
            return x * 2
    """

    def decorator(func: F) -> F:
        # Dictionary to store cached results and timestamps
        # Key: hash of arguments, Value: (result, timestamp)
        cache: Dict[int, Tuple[Any, float]] = {}

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Create a hashable key from arguments
            # Convert kwargs to sorted tuple for consistent hashing
            key_args = args
            key_kwargs = tuple(sorted(kwargs.items())) if kwargs else ()
            cache_key = hash((key_args, key_kwargs))

            current_time = time.time()

            # Check if we have a cached result
            if cache_key in cache:
                cached_result, cached_time = cache[cache_key]

                # If the cached result is still fresh (within the time limit)
                if current_time - cached_time < seconds:
                    if debug:
                        print(
                            f"Cache hit for {func.__name__} with args={args}, kwargs={kwargs}"
                        )
                    return cached_result
                else:
                    if debug:
                        print(
                            f"Cache expired for {func.__name__} with args={args}, kwargs={kwargs}"
                        )
            else:
                if debug:
                    print(
                        f"New parameter combination for {func.__name__} with args={args}, kwargs={kwargs}"
                    )

            # Call the function and cache the result
            result = func(*args, **kwargs)
            cache[cache_key] = (result, current_time)

            return result

        # Add method to clear cache if needed
        wrapper.clear_cache = lambda: cache.clear()  # type: ignore
        wrapper.cache_info = lambda: {  # type: ignore
            "cache_size": len(cache),
            "cached_calls": list(cache.keys()),
        }

        return cast(F, wrapper)

    return decorator


# Export the decorator
__all__ = ["time_cached"]
