"""Utilities for data formats supported by pycoalaip."""

from collections import namedtuple, Mapping
from copy import copy
from enum import Enum, unique
from types import MappingProxyType


@unique
class DataFormat(Enum):
    """Enum of supported data formats."""
    json = 'json'
    jsonld = 'jsonld'
    ipld = 'ipld'


def _copy_context_into_mutable(context):
    """Copy a properly formatted context into a mutable data structure.
    """
    def make_mutable(val):
        if isinstance(val, Mapping):
            return dict(val)
        else:
            return val

    if not isinstance(context, (str, Mapping)):
        try:
            return [make_mutable(val) for val in context]
        except TypeError:
            pass
    return make_mutable(context)


def _make_context_immutable(context):
    """Best effort attempt at turning a properly formatted context
    (either a string, dict, or array of strings and dicts) into an
    immutable data structure.

    If we get an array, make it immutable by creating a tuple; if we get
    a dict, copy it into a MappingProxyType. Otherwise, return as-is.
    """
    def make_immutable(val):
        if isinstance(val, Mapping):
            return MappingProxyType(val)
        else:
            return val

    if not isinstance(context, (str, Mapping)):
        try:
            return tuple([make_immutable(val) for val in context])
        except TypeError:
            pass
    return make_immutable(context)


def _data_format_resolver(data_format, resolver_dict):
    """Resolve a value from :attr:`resolver_dict` based on the
    :attr:`data_format`.

    Args:
        data_format (:class:`~.DataFormat` or str): The data format;
            must be a member of :class:`~.DataFormat` or a string
            equivalent.
        resolver_dict (dict): the resolving dict. Can hold any value
            for any of the valid :attr:`data_format` strings

    Returns:
        The value of the key in :attr:`resolver_dict` that matches
        :attr:`data_format`
    """
    try:
        data_format = DataFormat(data_format)
    except ValueError:
        supported_formats = ', '.join(
            ["'{}'".format(f.value) for f in DataFormat])
        raise ValueError(("'data_format' must be one of {formats}. Given "
                          "'{value}'.").format(formats=supported_formats,
                                               value=data_format))
    return (resolver_dict.get(data_format) or
            resolver_dict.get(data_format.value))


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
        return DataFormat.jsonld
    else:
        return DataFormat.json
