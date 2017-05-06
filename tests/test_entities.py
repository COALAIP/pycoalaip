#!/usr/bin/env python

from pytest import mark, raises


ALL_ENTITIES = [
    'work_entity',
    'manifestation_entity',
    'right_entity',
    'copyright_entity',
    'rights_assignment_entity',
]

CREATABLE_ENTITIES = [e for e in ALL_ENTITIES
                      if e != 'rights_assignment_entity']

CLS_FOR_ENTITY = {
    'work_entity': 'Work',
    'manifestation_entity': 'Manifestation',
    'right_entity': 'Right',
    'copyright_entity': 'Copyright',
    'rights_assignment_entity': 'RightsAssignment',
}

ALL_ENTITY_CLS = [
    'Work',
    'Manifestation',
    'Right',
    'Copyright',
    'RightsAssignment',
]

DATA_NAME_FOR_ENTITY_CLS = {
    'Work': 'work_data',
    'Manifestation': 'manifestation_data',
    'Copyright': 'copyright_data',
    'Right': 'right_data',
    'RightsAssignment': 'rights_assignment_data',
}

JSON_NAME_FOR_ENTITY_CLS = {
    'Work': 'work_json',
    'Manifestation': 'manifestation_json',
    'Copyright': 'copyright_json',
    'Right': 'right_json',
    'RightsAssignment': 'rights_assignment_json',
}

JSONLD_NAME_FOR_ENTITY_CLS = {
    'Work': 'work_jsonld',
    'Manifestation': 'manifestation_jsonld',
    'Copyright': 'copyright_jsonld',
    'Right': 'right_jsonld',
    'RightsAssignment': 'rights_assignment_jsonld',
}


def get_entity_cls(entity_cls_name):
    import importlib
    entities = importlib.import_module('coalaip.entities')
    entity_cls = getattr(entities, entity_cls_name)
    return entity_cls


@mark.parametrize('entity_cls_name', ALL_ENTITY_CLS)
def test_entity_init(mock_plugin, base_model, entity_cls_name):
    entity_cls = get_entity_cls(entity_cls_name)
    entity = entity_cls(base_model, plugin=mock_plugin)
    assert entity.model == base_model
    assert entity.data == base_model.data
    assert entity.plugin == mock_plugin
    assert entity.persist_id is None


@mark.parametrize('entity_cls_name', ALL_ENTITY_CLS)
@mark.parametrize('bad_model', [1, ('name', 'id'), {'name': 'name'}])
def test_entity_init_raises_on_non_model(mock_plugin, bad_model,
                                         entity_cls_name):
    entity_cls = get_entity_cls(entity_cls_name)
    with raises(TypeError):
        entity_cls(model=bad_model, plugin=mock_plugin)


@mark.parametrize('entity_cls_name', ALL_ENTITY_CLS)
def test_entity_init_raises_on_no_plugin(base_model, entity_cls_name):
    entity_cls = get_entity_cls(entity_cls_name)
    with raises(TypeError):
        entity_cls(model=base_model, plugin=None)


@mark.parametrize('entity_cls_name', ALL_ENTITY_CLS)
def test_entity_init_raises_on_non_subclassed_plugin(base_model,
                                                     entity_cls_name):
    entity_cls = get_entity_cls(entity_cls_name)

    class NonSubclassPlugin():
        pass

    # Instantiation should raise if plugin not subclassed from AbstractPlugin
    with raises(TypeError):
        entity_cls(model=base_model, plugin=NonSubclassPlugin())


@mark.parametrize('entity_cls_name', ALL_ENTITY_CLS)
@mark.parametrize('use_data_format_enum', [True, False])
@mark.parametrize('data_format', [None, 'json', 'jsonld', mark.skip('ipld')])
def test_entity_init_from_data(mock_plugin, data_format, use_data_format_enum,
                               entity_cls_name, request):
    entity_cls = get_entity_cls(entity_cls_name)
    data = request.getfixturevalue(DATA_NAME_FOR_ENTITY_CLS[entity_cls_name])
    json = request.getfixturevalue(JSON_NAME_FOR_ENTITY_CLS[entity_cls_name])
    jsonld = request.getfixturevalue(JSONLD_NAME_FOR_ENTITY_CLS[entity_cls_name])

    kwargs = {}
    if data_format is None:
        kwargs['data'] = data
    else:
        if data_format == 'json':
            kwargs['data'] = json
        elif data_format == 'jsonld':
            kwargs['data'] = jsonld

        if use_data_format_enum:
            from tests.utils import get_data_format_enum_member
            data_format = get_data_format_enum_member(data_format)
        kwargs['data_format'] = data_format

    entity = entity_cls.from_data(plugin=mock_plugin, **kwargs)
    assert entity.persist_id is None
    assert entity.to_json() == json
    assert entity.to_jsonld() == jsonld


@mark.parametrize('entity_cls_name', ALL_ENTITY_CLS)
def test_entity_from_data_consistent(mock_plugin, entity_cls_name, request):
    from tests.utils import assert_key_values_present_in_dict
    entity_cls = get_entity_cls(entity_cls_name)
    entity_data = request.getfixturevalue(DATA_NAME_FOR_ENTITY_CLS[entity_cls_name])

    entity = entity_cls.from_data(data=entity_data, plugin=mock_plugin)

    assert_key_values_present_in_dict(entity.to_json(), **entity_data)
    assert_key_values_present_in_dict(entity.to_jsonld(), **entity_data)


@mark.parametrize('entity_cls_name', ALL_ENTITY_CLS)
def test_entity_from_jsonld_data_keeps_ld_id(mock_plugin, entity_cls_name,
                                             mock_entity_create_id, request):
    from tests.utils import assert_key_values_present_in_dict
    entity_cls = get_entity_cls(entity_cls_name)
    jsonld = request.getfixturevalue(JSONLD_NAME_FOR_ENTITY_CLS[entity_cls_name])

    jsonld['@id'] = mock_entity_create_id
    entity = entity_cls.from_data(data=jsonld, data_format='jsonld',
                                  plugin=mock_plugin)

    assert_key_values_present_in_dict(entity.to_jsonld(), **jsonld)


@mark.parametrize('entity_cls_name', ALL_ENTITY_CLS)
def test_entity_data_and_to_format_are_copies(mock_plugin, entity_cls_name,
                                              request):
    entity_cls = get_entity_cls(entity_cls_name)
    entity_data = request.getfixturevalue(DATA_NAME_FOR_ENTITY_CLS[entity_cls_name])

    entity = entity_cls.from_data(data=entity_data, plugin=mock_plugin)
    data = entity.data
    json = entity.to_json()
    jsonld = entity.to_jsonld()

    # Change the copied data
    data['new_data'] = 'new_data'
    json['new_data'] = 'new_data'
    jsonld['new_data'] = 'new_data'

    # Check that the entity's own data hasn't changed
    assert entity.data != data
    assert 'new_data' not in entity.data
    assert entity.to_json() != json
    assert 'new_data' not in entity.to_json()
    assert entity.to_jsonld() != jsonld
    assert 'new_data' not in entity.to_jsonld()


@mark.parametrize('entity_cls_name', ['Work', 'Copyright', 'RightsAssignment'])
@mark.parametrize('use_data_format_enum', [True, False])
@mark.parametrize('data_format', ['json', 'jsonld', mark.skip('ipld')])
def test_strict_type_entity_raises_on_diff_type_from_data(
        mock_plugin, data_format, use_data_format_enum, entity_cls_name,
        mock_entity_type, request):
    from coalaip.exceptions import ModelError
    entity_cls = get_entity_cls(entity_cls_name)

    kwargs = {}
    if data_format:
        if data_format == 'json':
            data = request.getfixturevalue(JSON_NAME_FOR_ENTITY_CLS[entity_cls_name])
            data['type'] = mock_entity_type
        elif data_format == 'jsonld':
            data = request.getfixturevalue(JSONLD_NAME_FOR_ENTITY_CLS[entity_cls_name])
            data['@type'] = mock_entity_type

        if use_data_format_enum:
            from tests.utils import get_data_format_enum_member
            data_format = get_data_format_enum_member(data_format)
        kwargs['data_format'] = data_format
    kwargs['data'] = data

    with raises(ModelError):
        entity_cls.from_data(plugin=mock_plugin, **kwargs)


@mark.parametrize('entity_cls_name', ['Manifestation', 'Right'])
@mark.parametrize('use_data_format_enum', [True, False])
@mark.parametrize('data_format', ['json', 'jsonld', mark.skip('ipld')])
def test_non_strict_type_entity_keeps_diff_type_from_data(
        mock_plugin, data_format, use_data_format_enum, entity_cls_name,
        mock_entity_type, request):
    entity_cls = get_entity_cls(entity_cls_name)

    kwargs = {}
    if data_format:
        if data_format == 'json':
            data = request.getfixturevalue(JSON_NAME_FOR_ENTITY_CLS[entity_cls_name])
            data['type'] = mock_entity_type
        elif data_format == 'jsonld':
            data = request.getfixturevalue(JSONLD_NAME_FOR_ENTITY_CLS[entity_cls_name])
            data['@type'] = mock_entity_type

        if use_data_format_enum:
            from tests.utils import get_data_format_enum_member
            data_format = get_data_format_enum_member(data_format)
        kwargs['data_format'] = data_format
    kwargs['data'] = data

    entity = entity_cls.from_data(plugin=mock_plugin, **kwargs)

    # Test entity uses specified @type
    assert entity.model.ld_type == mock_entity_type
    assert entity.to_jsonld()['@type'] == mock_entity_type


@mark.parametrize('entity_cls_name', ALL_ENTITY_CLS)
@mark.parametrize('use_data_format_enum', [True, False])
def test_entity_keeps_context_from_ld_data(mock_plugin, use_data_format_enum,
                                           entity_cls_name,
                                           mock_entity_context, request):
    entity_cls = get_entity_cls(entity_cls_name)

    data = request.getfixturevalue(JSONLD_NAME_FOR_ENTITY_CLS[entity_cls_name])
    data['@context'] = mock_entity_context

    data_format = 'jsonld'
    if use_data_format_enum:
        from tests.utils import get_data_format_enum_member
        data_format = get_data_format_enum_member(data_format)

    entity = entity_cls.from_data(data, data_format=data_format,
                                  plugin=mock_plugin)

    # Test entity keeps @context if the data's in JSON-LD
    assert entity.model.ld_context == mock_entity_context
    assert entity.to_jsonld()['@context'] == mock_entity_context


@mark.parametrize('entity_cls_name', ALL_ENTITY_CLS)
@mark.parametrize('use_data_format_enum', [True, False])
@mark.parametrize('data_format', ['json', mark.skip('ipld')])
def test_entity_ignores_context_from_non_ld_data(
        mock_plugin, data_format, use_data_format_enum, entity_cls_name,
        mock_entity_context, request):
    entity_cls = get_entity_cls(entity_cls_name)

    data = request.getfixturevalue(JSONLD_NAME_FOR_ENTITY_CLS[entity_cls_name])
    data['@context'] = mock_entity_context

    kwargs = {}
    if data_format:
        if data_format == 'json':
            data = request.getfixturevalue(JSON_NAME_FOR_ENTITY_CLS[entity_cls_name])
            data['context'] = mock_entity_context

        if use_data_format_enum:
            from tests.utils import get_data_format_enum_member
            data_format = get_data_format_enum_member(data_format)
        kwargs['data_format'] = data_format
    kwargs['data'] = data

    entity = entity_cls.from_data(plugin=mock_plugin, **kwargs)

    # Test entity ignores @context since the data wasn't in JSON-LD
    assert entity.model.ld_context != mock_entity_context
    assert entity.to_jsonld()['@context'] != mock_entity_context


@mark.parametrize('entity_cls_name', ALL_ENTITY_CLS)
def test_entity_init_from_persist_id(mock_plugin, entity_cls_name,
                                     mock_entity_create_id, request):
    from coalaip.models import LazyLoadableModel
    from coalaip.exceptions import ModelNotYetLoadedError
    entity_cls = get_entity_cls(entity_cls_name)
    entity_data = request.getfixturevalue(DATA_NAME_FOR_ENTITY_CLS[entity_cls_name])
    entity_from_data = entity_cls.from_data(entity_data, plugin=mock_plugin)

    entity_from_persist_id = entity_cls.from_persist_id(mock_entity_create_id,
                                                        plugin=mock_plugin)
    assert entity_from_persist_id.persist_id == mock_entity_create_id
    assert isinstance(entity_from_persist_id.model, LazyLoadableModel)
    assert entity_from_persist_id.model.ld_type == entity_from_data.model.ld_type
    assert entity_from_persist_id.model.ld_context == entity_from_data.model.ld_context
    assert entity_from_persist_id.model.ld_type == entity_from_data.model.ld_type

    with raises(ModelNotYetLoadedError):
        entity_from_persist_id.model.data


@mark.parametrize('entity_cls_name', ALL_ENTITY_CLS)
def test_entity_init_from_persist_id_force_load(mocker, mock_plugin,
                                                entity_cls_name,
                                                mock_entity_create_id):
    from coalaip.models import LazyLoadableModel
    mocker.patch.object(LazyLoadableModel, 'load')

    entity_cls = get_entity_cls(entity_cls_name)
    entity_from_persist_id = entity_cls.from_persist_id(mock_entity_create_id,
                                                        force_load=True,
                                                        plugin=mock_plugin)
    lazy_model = entity_from_persist_id.model
    lazy_model.load.assert_called_once_with(mock_entity_create_id,
                                            plugin=mock_plugin)


@mark.parametrize('entity_cls_name', ALL_ENTITY_CLS)
def test_entity_init_from_persist_id_can_load(mocker, mock_plugin,
                                              entity_cls_name,
                                              mock_entity_create_id):
    from coalaip.models import LazyLoadableModel
    mocker.patch.object(LazyLoadableModel, 'load')

    entity_cls = get_entity_cls(entity_cls_name)
    entity_from_persist_id = entity_cls.from_persist_id(mock_entity_create_id,
                                                        plugin=mock_plugin)
    lazy_model = entity_from_persist_id.model
    entity_from_persist_id.load()
    lazy_model.load.assert_called_once_with(mock_entity_create_id,
                                            plugin=mock_plugin)


@mark.parametrize('entity_cls_name', ALL_ENTITY_CLS)
def test_entity_init_from_persist_id_loads_on_data_access(
        mocker, mock_plugin, entity_cls_name, mock_entity_create_id,
        mock_entity_type, request):
    from coalaip.models import Model, LazyLoadableModel
    mocker.patch.object(LazyLoadableModel, 'load')

    entity_cls = get_entity_cls(entity_cls_name)
    entity_data = request.getfixturevalue(DATA_NAME_FOR_ENTITY_CLS[entity_cls_name])
    entity_from_persist_id = entity_cls.from_persist_id(mock_entity_create_id,
                                                        plugin=mock_plugin)

    lazy_model = entity_from_persist_id.model

    def set_model(*args, **kwargs):
        lazy_model.loaded_model = Model(entity_data, mock_entity_type)
    lazy_model.load.side_effect = set_model

    entity_from_persist_id.data
    lazy_model.load.assert_called_once_with(mock_entity_create_id,
                                            plugin=mock_plugin)
    assert entity_from_persist_id.data == entity_data
    assert entity_from_persist_id.model.data == entity_data


@mark.parametrize('entity_name', CREATABLE_ENTITIES)
@mark.parametrize('use_data_format_enum', [True, False])
@mark.parametrize('data_format', [None, 'json', 'jsonld', mark.skip('ipld')])
def test_entity_create(mock_plugin, alice_user, data_format,
                       use_data_format_enum, entity_name,
                       mock_entity_create_id, request):
    entity = request.getfixturevalue(entity_name)
    entity_cls_name = CLS_FOR_ENTITY[entity_name]

    mock_plugin.save.return_value = mock_entity_create_id

    if data_format:
        if use_data_format_enum:
            from tests.utils import get_data_format_enum_member
            data_format_arg = get_data_format_enum_member(data_format)
        else:
            data_format_arg = data_format
        persist_id = entity.create(alice_user, data_format_arg)
    else:
        persist_id = entity.create(alice_user)
    assert mock_plugin.save.call_count == 1
    assert persist_id == mock_entity_create_id
    assert persist_id == entity.persist_id

    if not data_format or data_format == 'jsonld':
        data = request.getfixturevalue(JSONLD_NAME_FOR_ENTITY_CLS[entity_cls_name])
    elif data_format == 'json':
        data = request.getfixturevalue(JSON_NAME_FOR_ENTITY_CLS[entity_cls_name])
    mock_plugin.save.assert_called_with(data, user=alice_user)


@mark.parametrize('entity_name', CREATABLE_ENTITIES)
def test_entity_create_raises_on_bad_format(alice_user, entity_name, request):
    entity = request.getfixturevalue(entity_name)
    with raises(ValueError):
        entity.create(alice_user, 'bad_format')


@mark.parametrize('entity_name', CREATABLE_ENTITIES)
def test_entity_create_raises_on_creation_error(mock_plugin, alice_user,
                                                entity_name,
                                                mock_creation_error,
                                                request):
    from coalaip.exceptions import EntityCreationError
    mock_plugin.save.side_effect = mock_creation_error

    entity = request.getfixturevalue(entity_name)
    with raises(EntityCreationError) as excinfo:
        entity.create(alice_user)
    assert mock_creation_error == excinfo.value


@mark.parametrize('entity_name', CREATABLE_ENTITIES)
def test_entity_create_raises_on_creation_if_already_created(
        mock_plugin, alice_user, entity_name, mock_entity_create_id, request):
    from coalaip.exceptions import EntityPreviouslyCreatedError
    entity = request.getfixturevalue(entity_name)

    # Save the entity
    mock_plugin.save.return_value = mock_entity_create_id
    entity.create(alice_user)

    # Test create raises on already persisted entity
    with raises(EntityPreviouslyCreatedError) as excinfo:
        entity.create(alice_user)
    assert mock_entity_create_id == excinfo.value.existing_id


@mark.parametrize('entity_cls_name', ALL_ENTITY_CLS)
def test_entity_load_raises_if_not_persisted(mock_plugin, entity_cls_name):
    from coalaip.models import LazyLoadableModel
    from coalaip.exceptions import EntityNotYetPersistedError
    entity_cls = get_entity_cls(entity_cls_name)
    model = entity_cls.generate_model(model_cls=LazyLoadableModel)
    entity = entity_cls(model, mock_plugin)

    with raises(EntityNotYetPersistedError):
        entity.load()


@mark.parametrize('entity_cls_name', ALL_ENTITY_CLS)
def test_entity_load_raises_on_load_error(mock_plugin, entity_cls_name,
                                          mock_not_found_error,
                                          mock_entity_create_id):
    from coalaip.models import LazyLoadableModel
    from coalaip.exceptions import EntityNotFoundError
    entity_cls = get_entity_cls(entity_cls_name)
    model = entity_cls.generate_model(model_cls=LazyLoadableModel)
    entity = entity_cls(model, mock_plugin)
    entity.persist_id = mock_entity_create_id

    mock_plugin.load.side_effect = mock_not_found_error
    with raises(EntityNotFoundError):
        entity.load()


@mark.parametrize('entity_name', ALL_ENTITIES)
def test_entity_has_no_current_owner_if_not_persisted(mock_plugin, entity_name,
                                                      request):
    entity = request.getfixturevalue(entity_name)
    current_owner = entity.current_owner
    assert current_owner is None
    mock_plugin.get_history.assert_not_called()


@mark.parametrize('entity_name', ALL_ENTITIES)
def test_entity_current_owner(mock_plugin, alice_user, bob_user, entity_name,
                              mock_entity_create_id, request):
    entity = request.getfixturevalue(entity_name)
    mock_history = [{
        'user': alice_user,
        'event_id': mock_entity_create_id,
    }, {
        'user': bob_user,
        'event_id': mock_entity_create_id,
    }]

    entity.persist_id = mock_entity_create_id

    # Test current owner returned
    mock_plugin.get_history.return_value = mock_history
    current_owner = entity.current_owner
    assert mock_plugin.get_history.call_count == 1
    assert current_owner == bob_user


@mark.parametrize('entity_name', ALL_ENTITIES)
def test_entity_current_owner_raises_if_not_found(mock_plugin, alice_user,
                                                  entity_name,
                                                  mock_entity_create_id,
                                                  request):
    from coalaip.exceptions import EntityNotFoundError
    entity = request.getfixturevalue(entity_name)

    entity.persist_id = mock_entity_create_id

    mock_plugin.get_history.side_effect = EntityNotFoundError()
    with raises(EntityNotFoundError):
        entity.current_owner


@mark.parametrize('entity_name', ALL_ENTITIES)
def test_entity_has_no_history_if_not_persisted(mock_plugin, entity_name,
                                                request):
    entity = request.getfixturevalue(entity_name)
    history = entity.history
    assert history == []
    mock_plugin.get_history.assert_not_called()


@mark.parametrize('entity_name', ALL_ENTITIES)
def test_entity_history(mock_plugin, alice_user, bob_user, entity_name,
                        mock_entity_create_id, request):
    entity = request.getfixturevalue(entity_name)
    mock_history = [{
        'user': alice_user,
        'event_id': mock_entity_create_id,
    }, {
        'user': bob_user,
        'event_id': mock_entity_create_id,
    }]

    entity.persist_id = mock_entity_create_id

    # Test history is returned with the same events
    mock_plugin.get_history.return_value = mock_history
    returned_history = entity.history
    assert mock_plugin.get_history.call_count == 1

    for returned_event, original_event in zip(returned_history, mock_history):
        assert returned_event == original_event


@mark.parametrize('entity_name', ALL_ENTITIES)
def test_entity_history_raises_if_not_found(mock_plugin, alice_user,
                                            entity_name, mock_entity_create_id,
                                            request):
    from coalaip.exceptions import EntityNotFoundError
    entity = request.getfixturevalue(entity_name)

    entity.persist_id = mock_entity_create_id

    mock_plugin.get_history.side_effect = EntityNotFoundError()
    with raises(EntityNotFoundError):
        entity.history


@mark.parametrize('entity_name', ALL_ENTITIES)
def test_entity_have_none_status_if_not_persisted(mock_plugin, entity_name,
                                                  request):
    entity = request.getfixturevalue(entity_name)
    status = entity.status
    assert status is None
    mock_plugin.get_status.assert_not_called()


@mark.parametrize('entity_name', ALL_ENTITIES)
def test_entity_get_status(mock_plugin, alice_user, entity_name,
                           mock_entity_create_id, mock_entity_status, request):
    entity = request.getfixturevalue(entity_name)

    entity.persist_id = mock_entity_create_id

    # Test status returned
    mock_plugin.get_status.return_value = mock_entity_status
    status = entity.status
    assert mock_plugin.get_status.call_count == 1
    assert status == mock_entity_status


@mark.parametrize('entity_name', ALL_ENTITIES)
def test_entity_status_raises_if_not_found(mock_plugin, alice_user,
                                           entity_name, mock_entity_create_id,
                                           request):
    from coalaip.exceptions import EntityNotFoundError
    entity = request.getfixturevalue(entity_name)

    entity.persist_id = mock_entity_create_id

    mock_plugin.get_status.side_effect = EntityNotFoundError()
    with raises(EntityNotFoundError):
        entity.status


@mark.parametrize('entity_name', [
    'work_entity',
    'manifestation_entity',
    'rights_assignment_entity',
])
def test_non_transferrable_entity_actually_non_transferrable(entity_name,
                                                             request):
    entity = request.getfixturevalue(entity_name)
    with raises(AttributeError):
        entity.transfer()


def test_work_init_from_data_raises_if_no_name(mock_plugin, work_data):
    from coalaip.entities import Work
    from coalaip.exceptions import ModelDataError

    del work_data['name']
    with raises(ModelDataError):
        Work.from_data(work_data, plugin=mock_plugin)


def test_work_init_from_data_raises_if_manifestation(mock_plugin, work_data):
    from copy import copy
    from coalaip.entities import Work
    from coalaip.exceptions import ModelDataError

    manifestation_of_data = copy(work_data)
    manifestation_of_data['manifestationOfWork'] = {}
    with raises(ModelDataError):
        Work.from_data(manifestation_of_data, plugin=mock_plugin)


def test_manifestation_init_raises_if_no_name(mock_plugin, manifestation_data):
    from coalaip.entities import Manifestation
    from coalaip.exceptions import ModelDataError
    del manifestation_data['name']
    with raises(ModelDataError):
        Manifestation.from_data(manifestation_data, plugin=mock_plugin)


@mark.skip(reason="We decided to go with Manifestation's that do not need works to be registered.")
def test_manifestation_init_raises_without_manifestation_of_work(
        mock_plugin, manifestation_data):
    from coalaip.entities import Manifestation
    from coalaip.exceptions import ModelDataError
    del manifestation_data['manifestationOfWork']
    with raises(ModelDataError):
        Manifestation.from_data(manifestation_data, plugin=mock_plugin)


@mark.skip(reason="We decided to go with Manifestation's that do not need works to be registered.")
def test_manifestation_init_raises_without_str_manifestation_of_work(
        mock_plugin, manifestation_data):
    from coalaip.entities import Manifestation
    from coalaip.exceptions import ModelDataError
    manifestation_data['manifestationOfWork'] = {}
    with raises(ModelDataError):
        Manifestation.from_data(manifestation_data, plugin=mock_plugin)


def test_right_init_raises_without_str_source(mock_plugin, right_data):
    from coalaip.entities import Right
    from coalaip.exceptions import ModelDataError

    del right_data['source']
    with raises(ModelDataError):
        Right.from_data(right_data, plugin=mock_plugin)

    right_data['source'] = {}
    with raises(ModelDataError):
        Right.from_data(right_data, plugin=mock_plugin)


def test_right_init_raises_without_str_license(mock_plugin, right_data):
    from coalaip.entities import Right
    from coalaip.exceptions import ModelDataError

    del right_data['license']
    with raises(ModelDataError):
        Right.from_data(right_data, plugin=mock_plugin)

    right_data['license'] = {}
    with raises(ModelDataError):
        Right.from_data(right_data, plugin=mock_plugin)


def test_copyright_init_raises_without_str_rights_of(mock_plugin,
                                                     copyright_data):
    from coalaip.entities import Copyright
    from coalaip.exceptions import ModelDataError

    del copyright_data['rightsOf']
    with raises(ModelDataError):
        Copyright.from_data(copyright_data, plugin=mock_plugin)

    copyright_data['rightsOf'] = {}
    with raises(ModelDataError):
        Copyright.from_data(copyright_data, plugin=mock_plugin)


def test_copyright_init_raises_if_derived(mock_plugin, right_data,
                                          mock_copyright_create_id):
    from coalaip.entities import Copyright
    from coalaip.exceptions import ModelDataError

    copyright_data = right_data
    assert copyright_data['source']
    with raises(ModelDataError):
        Copyright.from_data(copyright_data, plugin=mock_plugin)


@mark.parametrize('entity_cls_name', ['Right', 'Copyright'])
def test_right_init_raises_if_both_copyright_and_right(
        mock_plugin, entity_cls_name, copyright_data, right_data):
    from coalaip.exceptions import ModelDataError
    from tests.utils import extend_dict
    entity_cls = get_entity_cls(entity_cls_name)

    data = extend_dict(right_data, copyright_data)
    with raises(ModelDataError):
        entity_cls.from_data(data, plugin=mock_plugin)


@mark.parametrize('right_entity_name,mock_create_id_name', [
    ('right_entity', 'mock_right_create_id'),
    ('copyright_entity', 'mock_copyright_create_id'),
])
@mark.parametrize('use_data_format_enum', [True, False])
@mark.parametrize('data_format,rights_assignment_saved_data_name', [
    ('', 'rights_assignment_jsonld'),
    ('json', 'rights_assignment_json'),
    ('jsonld', 'rights_assignment_jsonld'),
    mark.skip(('ipld', 'rights_assignment_ipld')),
])
def test_right_transferrable(mock_plugin, alice_user, bob_user,
                             rights_assignment_data, right_entity_name,
                             mock_create_id_name, data_format,
                             rights_assignment_saved_data_name,
                             use_data_format_enum,
                             mock_rights_assignment_transfer_id, request):
    right_entity = request.getfixturevalue(right_entity_name)
    mock_create_id = request.getfixturevalue(mock_create_id_name)

    # Save the Copyright
    mock_plugin.save.return_value = mock_create_id
    right_entity.create(user=alice_user)

    # Set up the arguments
    mock_plugin.transfer.return_value = mock_rights_assignment_transfer_id
    transfer_kwargs = {
        'from_user': alice_user,
        'to_user': bob_user
    }
    if data_format:
        if use_data_format_enum:
            from tests.utils import get_data_format_enum_member
            data_format = get_data_format_enum_member(data_format)
        transfer_kwargs['rights_assignment_format'] = data_format

    # Test the transfer
    rights_assignment = right_entity.transfer(rights_assignment_data,
                                              **transfer_kwargs)
    assert rights_assignment.persist_id == mock_rights_assignment_transfer_id
    assert rights_assignment.data == rights_assignment_data

    rights_assignment_saved_data = request.getfixturevalue(
        rights_assignment_saved_data_name)
    mock_plugin.transfer.assert_called_with(mock_create_id,
                                            rights_assignment_saved_data,
                                            from_user=alice_user,
                                            to_user=bob_user)


@mark.parametrize('right_entity_name', ['right_entity', 'copyright_entity'])
def test_right_transfer_raises_if_not_persisted(alice_user, bob_user,
                                                rights_assignment_data,
                                                right_entity_name, request):
    from coalaip.exceptions import EntityNotYetPersistedError
    right_entity = request.getfixturevalue(right_entity_name)

    with raises(EntityNotYetPersistedError):
        right_entity.transfer(rights_assignment_data, from_user=alice_user,
                              to_user=bob_user)


def test_rights_assignment_cannot_create(rights_assignment_entity, alice_user):
    from coalaip.exceptions import PersistenceError
    with raises(PersistenceError):
        rights_assignment_entity.create(user=alice_user)


@mark.parametrize('right_entity_name,right_create_id_name', [
    ('right_entity', 'mock_right_create_id'),
    ('copyright_entity', 'mock_copyright_create_id'),
])
def test_right_transfer_raises_on_transfer_error(mock_plugin, alice_user,
                                                 bob_user, right_entity_name,
                                                 right_create_id_name,
                                                 rights_assignment_data,
                                                 mock_transfer_error,
                                                 request):
    from coalaip.exceptions import EntityTransferError
    mock_plugin.transfer.side_effect = mock_transfer_error

    # Save the right
    mock_create_id = request.getfixturevalue(right_create_id_name)
    right_entity = request.getfixturevalue(right_entity_name)
    mock_plugin.save.return_value = mock_create_id
    right_entity.create(user=alice_user)

    with raises(EntityTransferError) as excinfo:
        right_entity.transfer(rights_assignment_data, from_user=alice_user,
                              to_user=bob_user)
    assert mock_transfer_error == excinfo.value
