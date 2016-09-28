#!/usr/bin/env python

from pytest import fixture, mark, raises


@fixture
def model_data():
    return {'data': 'data'}


@fixture
def model_type():
    return 'ld_type'


def test_model_init(model_data, model_type):
    from coalaip.models import Model
    ld_context = 'ld_context'

    def validator(instance, attribute, value):
        if not value.get('data'):
            raise ValueError()

    model = Model(data=model_data, ld_type=model_type, ld_context=ld_context,
                  validator=validator)
    assert model.data == model_data
    assert model.ld_type == model_type
    assert model.ld_context == ld_context
    assert model.validator == validator


def test_model_init_defaults(context_urls_all, model_data, model_type):
    from coalaip.models import Model
    model = Model(data=model_data, ld_type=model_type)
    assert model.data == model_data
    assert model.ld_type == model_type
    assert set(model.ld_context) == set(context_urls_all)
    assert callable(model.validator)


def test_model_immutable(model_data, model_type):
    from attr import validators
    from attr.exceptions import FrozenInstanceError
    from coalaip.models import Model
    model = Model(data=model_data, ld_type=model_type)
    with raises(FrozenInstanceError):
        model.data = {'other': 'other'}
    with raises(FrozenInstanceError):
        model.ld_type = 'other_type'
    with raises(FrozenInstanceError):
        model.ld_context = 'other_context'
    with raises(FrozenInstanceError):
        model.validator = validators.instance_of(str)


def test_lazy_model_init(model_type):
    from attr import validators
    from coalaip.models import LazyLoadableModel
    ld_context = 'ld_context'
    validator = validators.instance_of(dict)

    model = LazyLoadableModel(ld_type=model_type, ld_context=ld_context,
                              validator=validator)
    assert model.loaded_model is None
    assert model.ld_type == model_type
    assert model.ld_context == ld_context
    assert model.validator == validator


def test_lazy_model_init_defaults(context_urls_all, model_type):
    from coalaip.models import LazyLoadableModel
    model = LazyLoadableModel(ld_type=model_type)
    assert model.loaded_model is None
    assert model.ld_type == model_type
    assert set(model.ld_context) == set(context_urls_all)
    assert callable(model.validator)


def test_lazy_model_init_with_data(mock_plugin, model_data, model_type,
                                   mock_entity_create_id):
    from coalaip.models import Model, LazyLoadableModel
    model = LazyLoadableModel(data=model_data, ld_type=model_type)
    assert model.data == model_data
    assert isinstance(model.loaded_model, Model)
    assert model.loaded_model.data == model_data
    assert model.loaded_model.ld_type == model.ld_type
    assert model.loaded_model.ld_context == model.ld_context
    assert model.loaded_model.validator == model.validator

    # If initialized with data, load() becomes a noop
    model.load(mock_entity_create_id, plugin=mock_plugin)
    mock_plugin.load.assert_not_called()


def test_lazy_model_raises_on_data_access_before_load(model_type):
    from coalaip.models import LazyLoadableModel
    from coalaip.exceptions import ModelNotYetLoadedError
    model = LazyLoadableModel(ld_type=model_type)
    with raises(ModelNotYetLoadedError):
        model.data


def test_lazy_model_immutable(model_data, model_type):
    from attr import validators
    from attr.exceptions import FrozenInstanceError
    from coalaip.models import Model, LazyLoadableModel
    model = LazyLoadableModel(data=model_data, ld_type=model_type)
    with raises(FrozenInstanceError):
        model.loaded_model = Model(data={'other': 'other'}, ld_type='other_type')
    with raises(FrozenInstanceError):
        model.ld_type = 'other_type'
    with raises(FrozenInstanceError):
        model.ld_context = 'other_context'
    with raises(FrozenInstanceError):
        model.validator = validators.instance_of(str)


def test_lazy_model_load(mock_plugin, model_data, model_type,
                         mock_entity_create_id):
    from attr.exceptions import FrozenInstanceError
    from coalaip.models import Model, LazyLoadableModel
    mock_plugin.load.return_value = model_data

    model = LazyLoadableModel(ld_type=model_type)
    model.load(mock_entity_create_id, plugin=mock_plugin)
    mock_plugin.load.assert_called_with(mock_entity_create_id)
    assert model.data == model_data
    assert isinstance(model.loaded_model, Model)
    assert model.loaded_model.data == model_data
    assert model.loaded_model.ld_type == model.ld_type
    assert model.loaded_model.ld_context == model.ld_context
    assert model.loaded_model.validator == model.validator

    with raises(FrozenInstanceError):
        model.loaded_model = Model(data={'other': 'other'}, ld_type='other_type')

    # If initialized with data, load() becomes a noop
    mock_plugin.reset_mock()
    model.load(mock_entity_create_id, plugin=mock_plugin)
    mock_plugin.load.assert_not_called()


@mark.parametrize('bad_type_data', [
    {'@type': 'other_type'},
    {'type': 'other_type'},
])
def test_lazy_model_load_raises_on_type_validation(mock_plugin, model_type,
                                                   bad_type_data,
                                                   mock_entity_create_id):
    from coalaip.models import LazyLoadableModel
    from coalaip.exceptions import ModelDataError
    mock_plugin.load.return_value = bad_type_data
    assert model_type != (bad_type_data.get('@type') or
                          bad_type_data.get('type'))

    model = LazyLoadableModel(ld_type=model_type)
    with raises(ModelDataError):
        model.load(mock_entity_create_id, plugin=mock_plugin)


def test_lazy_model_load_raises_on_context_validation(mock_plugin,
                                                      context_urls_all,
                                                      model_type,
                                                      mock_entity_create_id):
    from coalaip.models import LazyLoadableModel
    from coalaip.exceptions import ModelDataError
    bad_context_data = {'@context': 'other_context'}
    mock_plugin.load.return_value = bad_context_data
    assert context_urls_all != bad_context_data.get('@context')

    model = LazyLoadableModel(ld_type=model_type, ld_context=context_urls_all)
    with raises(ModelDataError):
        model.load(mock_entity_create_id, plugin=mock_plugin)


def test_lazy_model_load_raises_on_model_validation(mock_plugin, work_jsonld,
                                                    right_jsonld_factory,
                                                    model_type,
                                                    mock_entity_create_id):
    from coalaip.models import LazyLoadableModel
    from coalaip.model_validators import is_creation_model
    from coalaip.exceptions import ModelDataError
    mock_plugin.load.return_value = right_jsonld_factory()

    model = LazyLoadableModel(ld_type=model_type, validator=is_creation_model)
    with raises(ModelDataError):
        model.load(mock_entity_create_id, plugin=mock_plugin)


@mark.parametrize('model_factory_name,data_name,jsonld_name', [
    ('work_model_factory', 'work_data', 'work_jsonld'),
    ('manifestation_model_factory', 'manifestation_data', 'manifestation_jsonld'),
    ('copyright_model_factory', 'copyright_data', 'copyright_jsonld'),
    ('right_model_factory', 'right_data', 'right_jsonld'),
    ('rights_assignment_model_factory', 'rights_assignment_data', 'rights_assignment_jsonld'),
])
@mark.parametrize('model_cls_name', ['Model', 'LazyLoadableModel'])
def test_model_factories(model_factory_name, data_name, jsonld_name,
                         model_cls_name, request):
    import importlib
    from collections import Mapping
    from tests.utils import assert_key_values_present_in_dict

    models = importlib.import_module('coalaip.models')
    model_factory = getattr(models, model_factory_name)
    model_cls = getattr(models, model_cls_name)

    data = request.getfixturevalue(data_name)
    jsonld = request.getfixturevalue(jsonld_name)

    model = model_factory(data=data, model_cls=model_cls)
    assert_key_values_present_in_dict(model.data, **data)
    assert model.ld_type == jsonld['@type']
    if isinstance(model.ld_context, str):
        assert model.ld_context == jsonld['@context']
    elif isinstance(model.ld_context, Mapping):
        assert dict(model.ld_context) == dict(jsonld['@context'])
    else:
        assert set(model.ld_context) == set(jsonld['@context'])
