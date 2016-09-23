import attr

from collections import namedtuple
from copy import copy


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

        \*\*Note\*\*: Obviously, this doesn't stop anyone from setting
        the uninitialized attributes before you've set it yourself.
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


def _data_format_resolver(data_format, resolver_dict):
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


ExtractedLinkedDataResult = namedtuple('ExtractedLinkedDataResult', [
    'data',
    'ld_type',
    'ld_context',
    'ld_id'
])


def _extract_ld_data(data, data_format=None, **kwargs):
    """Extract the given :attr:`data` into a
    :class:`~.ExtractedLinkedDataResult` with the resulting data
    stripped of any Linked Data specifics. Any missing Linked Data
    properties are returned as ``None`` in the resulting
    :class:`~.ExtractLinkedDataResult`.

    Does not modify the given :attr:`data`.
    """
    if not data_format:
        data_format = _get_format_from_data(data)

    extract_ld_data_fn = _data_format_resolver(data_format, {
        'jsonld': _extract_ld_data_from_jsonld,
        'json': _extract_ld_data_from_json,
        'ipld': _extract_ld_data_from_ipld,
    })
    return extract_ld_data_fn(data, **kwargs)


def _extract_ld_data_from_jsonld(data, type_key='@type',
                                 context_key='@context', id_key='@id',
                                 **kwargs):
    return _extract_ld_data_from_keys(data, type_key=type_key,
                                      context_key=context_key, id_key=id_key,
                                      **kwargs)


def _extract_ld_data_from_json(data, type_key='type', **kwargs):
    return _extract_ld_data_from_keys(data, type_key=type_key, **kwargs)


def _extract_ld_data_from_ipld(data, type_key='type', **kwargs):
    raise NotImplementedError(('Extracting data from IPLD has not been '
                               'implemented yet'))


def _extract_ld_data_from_keys(orig_data, type_key=None, context_key=None,
                               id_key=None):
    data = copy(orig_data)
    extracted_kwargs = {
        'ld_type': None,
        'ld_context': None,
        'ld_id': None
    }

    if type_key and type_key in data:
        extracted_kwargs['ld_type'] = data[type_key]
        del data[type_key]
    if context_key and context_key in data:
        extracted_kwargs['ld_context'] = data[context_key]
        del data[context_key]
    if id_key and id_key in data:
        extracted_kwargs['ld_id'] = data[id_key]
        del data[id_key]

    return ExtractedLinkedDataResult(data, **extracted_kwargs)


def _get_format_from_data(data):
    # TODO: add IPLD
    if bool(data.get('@type') or data.get('@context') or data.get('@id')):
        return 'jsonld'
    else:
        return 'json'
