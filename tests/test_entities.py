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


@mark.parametrize('entity_cls_name,entity_data_name', [
    (e_cls, DATA_NAME_FOR_ENTITY_CLS[e_cls]) for e_cls in ALL_ENTITY_CLS
])
def test_entity_from_data_consistent(mock_plugin, entity_cls_name,
                                     entity_data_name, request):
    from tests.utils import assert_key_values_present_in_dict
    entity_cls = get_entity_cls(entity_cls_name)
    entity_data = request.getfixturevalue(entity_data_name)

    entity = entity_cls.from_data(data=entity_data, plugin=mock_plugin)

    assert_key_values_present_in_dict(entity.to_json(), **entity_data)
    assert_key_values_present_in_dict(entity.to_jsonld(), **entity_data)


@mark.parametrize('entity_cls_name', ['Work', 'Copyright', 'RightsAssignment'])
@mark.parametrize('use_data_format_enum', [True, False])
@mark.parametrize('data_format', ['json', 'jsonld', mark.skip('ipld')])
def test_entity_with_static_type_ignores_diff_type(mock_plugin, data_format,
                                                   use_data_format_enum,
                                                   entity_cls_name,
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

    # Test entity ignores specified @type
    assert entity.model.ld_type != mock_entity_type
    assert entity.to_jsonld()['@type'] != mock_entity_type


@mark.parametrize('entity_cls_name', ['Manifestation', 'Right'])
@mark.parametrize('use_data_format_enum', [True, False])
@mark.parametrize('data_format', ['json', 'jsonld', mark.skip('ipld')])
def test_entity_with_static_type_keeps_diff_type(mock_plugin, data_format,
                                                 use_data_format_enum,
                                                 entity_cls_name,
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

    # Test entity ignores specified @type
    assert entity.model.ld_type == mock_entity_type
    assert entity.to_jsonld()['@type'] == mock_entity_type


def test_entity_init_from_data_other_context(mock_plugin, work_data,
                                             work_jsonld, mock_entity_type):
    from coalaip.entities import Work
    work_data['@context'] = 'other_context'
    work_jsonld['@context'] = 'other_context'
    work = Work.from_data(work_data, plugin=mock_plugin)

    # Test work keeps @context
    assert work.to_jsonld() == work_jsonld


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
def test_entity_raises_on_creation_error(mock_plugin, alice_user, entity_name,
                                         request):
    from coalaip.exceptions import EntityCreationError
    mock_creation_error = 'mock_creation_error'
    mock_plugin.save.side_effect = EntityCreationError(mock_creation_error)

    entity = request.getfixturevalue(entity_name)
    with raises(EntityCreationError) as excinfo:
        entity.create(alice_user)
    assert mock_creation_error == excinfo.value.error


@mark.parametrize('entity_name', CREATABLE_ENTITIES)
def test_entity_raises_on_creation_if_already_created(
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
def test_entity_raises_on_status_if_not_found(mock_plugin, alice_user,
                                              entity_name,
                                              mock_entity_create_id, request):
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

    is_manifestation_data = copy(work_data)
    is_manifestation_data['isManifestation'] = True
    with raises(ModelDataError):
        Work.from_data(is_manifestation_data, plugin=mock_plugin)

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


def test_manifestation_init_raises_without_manifestation_of_work(
        mock_plugin, manifestation_data):
    from coalaip.entities import Manifestation
    from coalaip.exceptions import ModelDataError
    del manifestation_data['manifestationOfWork']
    with raises(ModelDataError):
        Manifestation.from_data(manifestation_data, plugin=mock_plugin)


def test_manifestation_init_raises_without_str_manifestation_of_work(
        mock_plugin, manifestation_data):
    from coalaip.entities import Manifestation
    from coalaip.exceptions import ModelDataError
    manifestation_data['manifestationOfWork'] = {}
    with raises(ModelDataError):
        Manifestation.from_data(manifestation_data, plugin=mock_plugin)


def test_manifestation_init_raises_with_false_is_manifestation(
        mock_plugin, manifestation_data):
    from coalaip.entities import Manifestation
    from coalaip.exceptions import ModelDataError
    manifestation_data['isManifestation'] = False
    with raises(ModelDataError):
        Manifestation.from_data(manifestation_data, plugin=mock_plugin)


def test_right_init_raises_without_str_allowed_by(mock_plugin, right_data):
    from coalaip.entities import Right
    from coalaip.exceptions import ModelDataError

    del right_data['allowedBy']
    with raises(ModelDataError):
        Right.from_data(right_data, plugin=mock_plugin)

    right_data['allowedBy'] = {}
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
    assert copyright_data['allowedBy']
    with raises(ModelDataError):
        Copyright.from_data(copyright_data, plugin=mock_plugin)


def test_right_init_raises_with_both_rights_of_allowed_by(
        mock_plugin, right_data_factory, mock_manifestation_create_id):
    from coalaip.entities import Right
    from coalaip.exceptions import ModelDataError

    right_data = right_data_factory(
        data={'rightsOf': mock_manifestation_create_id})
    with raises(ModelDataError):
        Right.from_data(right_data, plugin=mock_plugin)


@mark.parametrize('right_entity_name,mock_create_id_name', [
    ('right_entity', 'mock_right_create_id'),
    ('copyright_entity', 'mock_copyright_create_id'),
])
@mark.parametrize('use_data_format_enum', [True, False])
@mark.parametrize('data_format,rights_assignment_data_name', [
    ('', 'rights_assignment_jsonld'),
    ('json', 'rights_assignment_json'),
    ('jsonld', 'rights_assignment_jsonld'),
    mark.skip(('ipld', 'rights_assignment_ipld')),
])
def test_right_transferrable(mock_plugin, alice_user, bob_user,
                             rights_assignment_data, right_entity_name,
                             mock_create_id_name, data_format,
                             rights_assignment_data_name,
                             use_data_format_enum,
                             mock_rights_assignment_create_id, request):
    right_entity = request.getfixturevalue(right_entity_name)
    mock_create_id = request.getfixturevalue(mock_create_id_name)

    # Save the Copyright
    mock_plugin.save.return_value = mock_create_id
    right_entity.create(user=alice_user)

    # Set up the arguments
    mock_plugin.transfer.return_value = mock_rights_assignment_create_id
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
    transfer_tx_id = right_entity.transfer(rights_assignment_data,
                                           **transfer_kwargs)
    assert transfer_tx_id == mock_rights_assignment_create_id

    rights_assignment_data = request.getfixturevalue(
        rights_assignment_data_name)
    mock_plugin.transfer.assert_called_with(mock_create_id,
                                            rights_assignment_data,
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
    from coalaip.exceptions import EntityError
    with raises(EntityError):
        rights_assignment_entity.create(user=alice_user)


@mark.skip('Rights Assignments require transfer() to be implemented')
def test_rights_assignment_get_status(rights_assignment_entity):
    pass
