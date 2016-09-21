def data_format_resolver(data_format, resolver_dict):
    """Resolve a value from :attr:`resolver_dict` based on the
    :attr:`data_format`.

    Args:
        data_format (str): the data format; must be one of:
            - 'jsonld' (default)
            - 'json'
            - 'ipld'
        resolver_dict (dict): the resolving dict. Can hold any value
            for any of the valid :attr:`data_format` strings

    Returns:
        the value of the key in :attr:`resolver_dict` that matches
        :attr:`data_format`
    """
    if data_format not in ['jsonld', 'json', 'ipld']:
        raise ValueError(("'data_format' must be one of 'json', 'jsonld', "
                          "or 'ipld'. Given '{}'.").format(data_format))
    return resolver_dict[data_format]


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
