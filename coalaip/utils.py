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
