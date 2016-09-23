from pytest import fixture, mark, raises


@fixture
def base_dict():
    return {'foo': 'foo', 'bar': {'baz': 'baz'}}


@fixture
def override_foo_dict():
    return {'foo': 'overridden_foo'}


@fixture
def override_bar_dict():
    return {'bar': 'overriden_bar'}


@fixture
def override_all_dict():
    return {'foo': 'overriden_both', 'bar': 'overriden_both'}


@fixture
def override_all_tuple_iter():
    return [('foo', 'tuple_overriden_foo'), ('bar', 'tuple_overriden_bar')]


def test_post_init_immutable():
    from attr.exceptions import FrozenInstanceError
    from coalaip.utils import PostInitImmutable

    class Immutable(PostInitImmutable):
        def __init__(self, attr1):
            self.attr1 = attr1
            self.attr2 = None

    immutable = Immutable('attr1')
    with raises(FrozenInstanceError):
        immutable.attr1 = 'other_attr'

    # Note that attr2 can be set only once
    immutable.attr2 = 'attr2'
    with raises(FrozenInstanceError):
        immutable.attr2 = 'other_attr'


def test_extend_dict_single_arg(base_dict):
    from coalaip.utils import extend_dict
    copy = extend_dict(base_dict)

    # Returns a copy of the original if no other arguments given
    assert copy == base_dict

    copy['foo'] = 'changed_dict'
    assert copy != base_dict


def test_extend_dict_single_override(base_dict, override_foo_dict):
    from coalaip.utils import extend_dict
    overriden_dict = extend_dict(base_dict, override_foo_dict)

    # Returns a copy of the original with the 'foo' key overriden
    assert overriden_dict != base_dict
    assert overriden_dict != override_foo_dict
    assert overriden_dict['bar'] == base_dict['bar']
    assert overriden_dict['foo'] == override_foo_dict['foo']


def test_extend_dict_multiple_override(base_dict, override_foo_dict,
                                       override_bar_dict):
    from coalaip.utils import extend_dict
    overriden_dict = extend_dict(base_dict, override_foo_dict,
                                 override_bar_dict)

    # Returns a copy of the original with the 'foo' and 'bar' keys overriden
    assert overriden_dict != base_dict
    assert overriden_dict != override_foo_dict
    assert overriden_dict != override_bar_dict
    assert overriden_dict['foo'] == override_foo_dict['foo']
    assert overriden_dict['bar'] == override_bar_dict['bar']


def test_extend_dict_last_override_kept(base_dict, override_foo_dict,
                                        override_bar_dict, override_all_dict):
    from coalaip.utils import extend_dict
    overriden_dict = extend_dict(base_dict, override_foo_dict,
                                 override_bar_dict, override_all_dict)

    # Returns a copy with the last key override being kept
    assert overriden_dict != base_dict
    assert overriden_dict != override_foo_dict
    assert overriden_dict != override_bar_dict
    assert overriden_dict == override_all_dict


def test_extend_dict_tuple_override(base_dict, override_all_tuple_iter):
    from coalaip.utils import extend_dict
    overriden_dict = extend_dict(base_dict, override_all_tuple_iter)

    # Returns a copy that has overriden all keys from the tuple iter
    assert overriden_dict == dict(override_all_tuple_iter)


def test_extend_dict_skips_none(base_dict, override_foo_dict,
                                override_bar_dict):

    from coalaip.utils import extend_dict
    overriden_dict = extend_dict(base_dict, override_foo_dict)
    overriden_with_none_dict = extend_dict(base_dict, None, override_foo_dict,
                                           None)

    # Results in the same dict as if the `None`s weren't given
    assert overriden_dict == overriden_with_none_dict


@mark.parametrize('data_format,format_resolved', [
    ('json', 'json_resolved'),
    ('jsonld', 'jsonld_resolved'),
    ('ipld', 'ipld_resolved')
])
def test_data_format_resolver(data_format, format_resolved):
    from coalaip.utils import _data_format_resolver
    resolver = {}
    resolver[data_format] = format_resolved

    resolved = _data_format_resolver(data_format, resolver)
    assert resolved == format_resolved


def test_data_format_resolver_raises_on_bad_format():
    from coalaip.utils import _data_format_resolver
    with raises(ValueError):
        _data_format_resolver('bad_format', {})


@mark.parametrize('data_format', ['json', 'jsonld', 'ipld'])
def test_extract_ld_data_calls_extract_format(mocker, data_format):
    from coalaip.utils import _extract_ld_data
    mock_extract_from_format = mocker.patch(
        'coalaip.utils._extract_ld_data_from_{}'.format(data_format))
    data = {'data': 'data'}
    kwargs = {'type_key': 'type', 'context_key': 'context', 'id_key': 'id'}

    _extract_ld_data(data, data_format=data_format, **kwargs)
    mock_extract_from_format.assert_called_once_with(data, **kwargs)


def test_extract_ld_data_finds_type_from_data(mocker):
    from coalaip.utils import _extract_ld_data
    mock_get_format = mocker.patch('coalaip.utils._get_format_from_data')
    mock_extract_from_json = mocker.patch('coalaip.utils._extract_ld_data_from_json')

    mock_get_format.return_value = 'json'
    data = {'data': 'data'}

    _extract_ld_data(data)
    mock_get_format.assert_called_once_with(data)
    mock_extract_from_json.assert_called_once_with(data)


@mark.parametrize('data_format,default_keys', [
    ('json', {'type_key': 'type'}),
    ('jsonld', {'type_key': '@type', 'context_key': '@context', 'id_key': '@id'}),
    mark.skip(('ipld', {'type_key': 'type'})),
])
def test_extract_from_format_calls_extract_from_keys(mocker, data_format,
                                                     default_keys):
    import importlib
    utils = importlib.import_module('coalaip.utils')
    extract_fn = getattr(utils, '_extract_ld_data_from_{}'.format(data_format))

    mock_extract_from_keys = mocker.patch('coalaip.utils._extract_ld_data_from_keys')
    data = {'data': 'data'}

    extract_fn(data)
    mock_extract_from_keys.assert_called_once_with(data, **default_keys)


@mark.parametrize('data_format,custom_keys', [
    ('json', {'type_key': 'custom_type'}),
    ('jsonld', {'type_key': 'custom_type', 'context_key': 'custom_context', 'id_key': 'custom_id'}),
    mark.skip(('ipld', {'type_key': 'custom_type'})),
])
def test_extract_from_format_calls_with_non_default_keys(mocker, data_format,
                                                         custom_keys):
    import importlib
    utils = importlib.import_module('coalaip.utils')
    extract_fn = getattr(utils, '_extract_ld_data_from_{}'.format(data_format))

    mock_extract_from_keys = mocker.patch('coalaip.utils._extract_ld_data_from_keys')
    data = {'data': 'data'}

    extract_fn(data, **custom_keys)
    mock_extract_from_keys.assert_called_once_with(data, **custom_keys)


def test_extract_ld_data_from_keys(work_data, work_jsonld):
    from coalaip.utils import _extract_ld_data_from_keys
    result = _extract_ld_data_from_keys(work_jsonld, type_key='@type',
                                        context_key='@context', id_key='@id')
    assert result.data == work_data
    assert result.ld_type == work_jsonld['@type']
    assert result.ld_context == work_jsonld['@context']
    assert result.ld_id == work_jsonld['@id']


def test_extract_ld_data_from_keys_ignores_missing_keys(work_data):
    from coalaip.utils import _extract_ld_data_from_keys
    result = _extract_ld_data_from_keys(work_data, type_key='@type',
                                        context_key='@context', id_key='@id')
    assert result.data == work_data
    assert result.ld_type is None
    assert result.ld_context is None
    assert result.ld_id is None
