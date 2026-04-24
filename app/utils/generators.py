from functools import wraps


def gen_list_doc(func):
    """Generate a simple hint about the return data structure for all list endpoint services"""

    # original_doc = func.__doc__ or ""
    func.__doc__ = "Returns the data as list and the total count"

    @wraps(func)
    async def wrapper(self, *args, **kwargs):

        return await func(self, *args, **kwargs)

    return wrapper
