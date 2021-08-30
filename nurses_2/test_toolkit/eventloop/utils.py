from asyncio import get_event_loop

import contextvars

__all__ = "run_in_executor_with_context",

def run_in_executor_with_context(func, *args, loop=None):
    """
    Run a function in an executor, but make sure it uses the same contextvars.
    This is required so that the function will see the right application.

    See also: https://bugs.python.org/issue34014
    """
    loop = loop or get_event_loop()
    ctx: contextvars.Context = contextvars.copy_context()

    return loop.run_in_executor(None, ctx.run, func, *args)
