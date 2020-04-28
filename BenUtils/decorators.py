"""Various decorators."""

from functools import wraps
from logging import getLogger

def retry(logMsg: str = None, retries: int = 5):
    """Try func for n retries."""

    def middle(func):
        @wraps(func)  # maintain docstring of the wrapped function
        def inner(*args, **kwargs):
            # convert to function to allow exc_info to be the default
            if not logMsg:
                logMsgCallable = exc_info

            else:
                logMsgCallable = lambda : logMsg

            log = getLogger()

            # try repeatedly
            for try_ in range(0, retries):
                try:
                    return func(*args, **kwargs)

                except:
                    log.error(logMsgCallable())

            # if retries exhausted
            return log.error(f"Failed to execute {func}")
        return inner
    return middle