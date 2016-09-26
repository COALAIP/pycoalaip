import attr


class PostInitImmutable:
    def __setattr__(self, name, value):
        """Mimic attr.s(frozen=True) behaviour but allow for attributes
        to be initialized after class instantiation.

        Useful when you would like a class to be immutable after a
        certain action, such as a save to a database.

        Any attributes created with ``attr.ib(init=False)`` or are
        initially set to ``None`` in ``__init__()`` are allowed to have
        their values be set once after initialization. Any other
        attributes with initial values set are immediately frozen upon
        initialization.

        **Note**: Obviously, this doesn't stop anyone from setting the
        uninitialized attributes before you've set it yourself.
        Hopefully, you've got responsibile users.

        Raises:
            :class:`attr.exceptions.FronzenInstanceError`: if a frozen
                attribute is set
        """
        current_value = getattr(self, name, None)
        if current_value is None or isinstance(current_value, attr.Attribute):
            super().__setattr__(name, value)
        else:
            raise attr.exceptions.FrozenInstanceError()


# See http://stackoverflow.com/a/26853961/1375656
def extend_dict(x, *y):
    """Similar to Object.assign() / _.extend() in Javascript, using
    'dict.update()'

    Args:
        x (dict): the base dict to merge into with 'update()'
        *y (dict, iter): any number of dictionary or iterable key/value
            pairs to be sequentially merged into 'x'. Skipped if None.
    """
    z = x.copy()
    for d in [d for d in y if d is not None]:
        z.update(d)
    return z
