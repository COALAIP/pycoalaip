from pytest import mark, raises


@mark.parametrize('use_data_format_enum', [True, False])
@mark.parametrize('data_format,format_resolved', [
    ('json', 'json_resolved'),
    ('jsonld', 'jsonld_resolved'),
    ('ipld', 'ipld_resolved')
])
def test_data_format_resolver(data_format, format_resolved):
    from coalaip.data_formats import _data_format_resolver
    resolver = {}
    resolver[data_format] = format_resolved

    resolved = _data_format_resolver(data_format, resolver)
    assert resolved == format_resolved


def test_data_format_resolver_raises_on_bad_format():
    from coalaip.data_formats import _data_format_resolver
    with raises(ValueError):
        _data_format_resolver('bad_format', {})


@mark.parametrize('data_format', ['json', 'jsonld', 'ipld'])
def test_extract_ld_data_calls_extract_format(mocker, data_format):
    from coalaip.data_formats import _extract_ld_data
    mock_extract_from_format = mocker.patch(
        'coalaip.data_formats._extract_ld_data_from_{}'.format(data_format))
    data = {'data': 'data'}
    kwargs = {'type_key': 'type', 'context_key': 'context', 'id_key': 'id'}

    _extract_ld_data(data, data_format=data_format, **kwargs)
    mock_extract_from_format.assert_called_once_with(data, **kwargs)


def test_extract_ld_data_finds_type_from_data(mocker):
    from coalaip.data_formats import _extract_ld_data
    mock_get_format = mocker.patch('coalaip.data_formats._get_format_from_data')
    mock_extract_from_json = mocker.patch('coalaip.data_formats._extract_ld_data_from_json')

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
    utils = importlib.import_module('coalaip.data_formats')
    extract_fn = getattr(utils, '_extract_ld_data_from_{}'.format(data_format))

    mock_extract_from_keys = mocker.patch('coalaip.data_formats._extract_ld_data_from_keys')
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
    utils = importlib.import_module('coalaip.data_formats')
    extract_fn = getattr(utils, '_extract_ld_data_from_{}'.format(data_format))

    mock_extract_from_keys = mocker.patch('coalaip.data_formats._extract_ld_data_from_keys')
    data = {'data': 'data'}

    extract_fn(data, **custom_keys)
    mock_extract_from_keys.assert_called_once_with(data, **custom_keys)


def test_extract_ld_data_from_keys(work_data, work_jsonld):
    from coalaip.data_formats import _extract_ld_data_from_keys
    result = _extract_ld_data_from_keys(work_jsonld, type_key='@type',
                                        context_key='@context', id_key='@id')
    assert result.data == work_data
    assert result.ld_type == work_jsonld['@type']
    assert result.ld_context == work_jsonld['@context']
    assert result.ld_id == work_jsonld['@id']


def test_extract_ld_data_from_keys_ignores_missing_keys(work_data):
    from coalaip.data_formats import _extract_ld_data_from_keys
    result = _extract_ld_data_from_keys(work_data, type_key='@type',
                                        context_key='@context', id_key='@id')
    assert result.data == work_data
    assert result.ld_type is None
    assert result.ld_context is None
    assert result.ld_id is None


@mark.parametrize('data,expected_format', [
    ({'@type': 'type'}, 'jsonld'),
    ({'@context': 'context'}, 'jsonld'),
    ({'@id': 'id'}, 'jsonld'),
    ({'type': 'type'}, 'json'),
    ({'data': 'data'}, 'json'),
])
def test_get_format_from_data(data, expected_format):
    from coalaip.data_formats import _get_format_from_data

    result_format = _get_format_from_data(data)
    assert result_format.value == expected_format
