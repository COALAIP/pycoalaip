#!/usr/bin/env python

from pytest import mark, raises


def test_entity_raise_on_bad_instantiation(mock_plugin):
    from coalaip.models import CoalaIpEntity
    from coalaip.exceptions import EntityDataError

    # Test that instantiation raises if plugin not subclassed from
    # AbstractPlugin
    with raises(TypeError):
        CoalaIpEntity(data={}, plugin=None)

    class NonSubclassPlugin():
        pass

    plugin = NonSubclassPlugin()
    with raises(TypeError):
        CoalaIpEntity(data={}, entity_type='type', plugin=plugin)

    # Test that instantiation raises if data not a dict
    with raises(EntityDataError):
        CoalaIpEntity(data=1, entity_type='type', plugin=mock_plugin)

    with raises(EntityDataError):
        CoalaIpEntity(data=('name', 'id'), entity_type='type',
                      plugin=mock_plugin)

    # Test that instantiation raises if entity_type not given as string
    with raises(EntityDataError):
        CoalaIpEntity(data={}, entity_type=None, plugin=mock_plugin)

    with raises(EntityDataError):
        CoalaIpEntity(data={}, entity_type={'type': 'type'},
                      plugin=mock_plugin)


def test_entity_create_raises_on_bad_format(base_entity_model, alice_user):
    with raises(ValueError):
        base_entity_model.create(alice_user, 'bad_format')


def test_entity_raise_on_creation_error(mock_plugin, base_entity_model,
                                        alice_user):
    from coalaip.exceptions import EntityCreationError

    mock_creation_error = 'mock_creation_error'
    mock_plugin.save.side_effect = EntityCreationError(mock_creation_error)
    with raises(EntityCreationError) as excinfo:
        base_entity_model.create(alice_user)

    assert mock_creation_error == excinfo.value.error


def test_entity_raise_on_creation_if_already_created(
        mock_plugin, base_entity_model, alice_user,
        mock_base_entity_create_id):
    from coalaip.exceptions import EntityPreviouslyCreatedError

    # Save the entity
    mock_plugin.save.return_value = mock_base_entity_create_id
    base_entity_model.create(alice_user)

    # Test create raises on already persisted entity
    mock_plugin.save.side_effect = EntityPreviouslyCreatedError(
        mock_base_entity_create_id)
    with raises(EntityPreviouslyCreatedError) as excinfo:
        base_entity_model.create(alice_user)

    assert mock_base_entity_create_id == excinfo.value.existing_id


def test_entity_plugin_type(mock_plugin, base_entity_model):
    plugin_type = base_entity_model.plugin_type
    assert plugin_type == mock_plugin.type


def test_entity_have_none_status_if_not_persisted(mock_plugin,
                                                  base_entity_model):
    status = base_entity_model.get_status()
    assert status is None
    mock_plugin.get_status.assert_not_called()


def test_entity_data_format_consistent(mock_plugin):
    from coalaip.models import CoalaIpEntity
    from tests.utils import assert_key_values_present_in_dict
    entity_data = {'test_data': 'test_data', 'extra_data': 'extra_data'}
    entity_model = CoalaIpEntity(data=entity_data, entity_type='type',
                                 plugin=mock_plugin)

    assert_key_values_present_in_dict(entity_model.to_json(), **entity_data)
    assert_key_values_present_in_dict(entity_model.to_jsonld(), **entity_data)


def test_entity_get_status(mock_plugin, base_entity_model, alice_user,
                           mock_base_entity_create_id, mock_model_status):
    # Save the entity
    mock_plugin.save.return_value = mock_base_entity_create_id
    base_entity_model.create(alice_user)

    # Test status returned
    mock_plugin.get_status.return_value = mock_model_status
    status = base_entity_model.get_status()
    assert mock_plugin.get_status.call_count == 1
    assert status == mock_model_status


def test_entity_raise_on_status_if_not_found(mock_plugin, base_entity_model,
                                             alice_user,
                                             mock_base_entity_create_id):
    from coalaip.exceptions import EntityNotFoundError

    # Save the entity
    mock_plugin.save.return_value = mock_base_entity_create_id
    base_entity_model.create(alice_user)

    mock_plugin.get_status.side_effect = EntityNotFoundError()
    with raises(EntityNotFoundError):
        base_entity_model.get_status()


def test_work_init(mock_plugin, work_data, work_json,
                   work_jsonld):
    from coalaip.models import Work
    work = Work(work_data, plugin=mock_plugin)
    assert work.persist_id is None
    assert work.to_json() == work_json
    assert work.to_jsonld() == work_jsonld


def test_work_init_raises_if_no_name(mock_plugin, work_data):
    from coalaip.models import Work
    from coalaip.exceptions import EntityDataError

    del work_data['name']
    with raises(EntityDataError):
        Work(work_data, plugin=mock_plugin)


def test_work_init_raises_if_manifestation(mock_plugin, work_data):
    from copy import copy
    from coalaip.models import Work
    from coalaip.exceptions import EntityDataError

    is_manifestation_data = copy(work_data)
    is_manifestation_data['isManifestation'] = True
    with raises(EntityDataError):
        Work(is_manifestation_data, plugin=mock_plugin)

    manifestation_of_data = copy(work_data)
    manifestation_of_data['manifestationOfWork'] = {}
    with raises(EntityDataError):
        Work(manifestation_of_data, plugin=mock_plugin)


@mark.parametrize('data_format,model_data_name', [
    ('', 'work_jsonld'),
    ('json', 'work_json'),
    ('jsonld', 'work_jsonld'),
])
def test_work_create(mock_plugin, work_model, alice_user, data_format,
                     model_data_name, mock_work_create_id, request):
    mock_plugin.save.return_value = mock_work_create_id

    if data_format:
        persist_id = work_model.create(alice_user, data_format)
    else:
        persist_id = work_model.create(alice_user)
    assert mock_plugin.save.call_count == 1
    assert persist_id == mock_work_create_id
    assert persist_id == work_model.persist_id

    model_data = request.getfixturevalue(model_data_name)
    mock_plugin.save.assert_called_with(model_data, user=alice_user)


def test_work_non_transferrable(work_model):
    with raises(AttributeError):
        work_model.transfer()


def test_manifestation_init(mock_plugin, manifestation_data_factory,
                            manifestation_json_factory,
                            manifestation_jsonld_factory):
    from coalaip.models import Manifestation

    manifestation_data = manifestation_data_factory()
    manifestation_json = manifestation_json_factory()
    manifestation_jsonld = manifestation_jsonld_factory()

    manifestation = Manifestation(manifestation_data, plugin=mock_plugin)
    assert manifestation.persist_id is None
    assert manifestation.to_json() == manifestation_json
    assert manifestation.to_jsonld() == manifestation_jsonld


@mark.parametrize('type_key', ['type', '@type'])
def test_manifestation_init_with_type(mock_plugin, manifestation_data_factory,
                                      manifestation_json_factory,
                                      manifestation_jsonld_factory, type_key,
                                      mock_manifestation_type):
    from coalaip.models import Manifestation

    manifestation_data = manifestation_data_factory(data={
        type_key: mock_manifestation_type
    })
    manifestation_json = manifestation_json_factory(data={
        'type': mock_manifestation_type
    })
    manifestation_jsonld = manifestation_jsonld_factory(data={
        '@type': mock_manifestation_type
    })

    manifestation = Manifestation(manifestation_data, plugin=mock_plugin)
    assert manifestation.persist_id is None
    assert manifestation.to_json() == manifestation_json
    assert manifestation.to_jsonld() == manifestation_jsonld


def test_manifestation_init_raises_if_no_name(mock_plugin,
                                              manifestation_data_factory):
    from coalaip.models import Manifestation
    from coalaip.exceptions import EntityDataError

    manifestation_data = manifestation_data_factory()
    del manifestation_data['name']

    with raises(EntityDataError):
        Manifestation(manifestation_data, plugin=mock_plugin)


def test_manifestation_init_raises_without_str_manifestation_of(
        mock_plugin, manifestation_data_factory):
    from coalaip.models import Manifestation
    from coalaip.exceptions import EntityDataError

    manifestation_data = manifestation_data_factory()

    del manifestation_data['manifestationOfWork']
    with raises(EntityDataError):
        Manifestation(manifestation_data, plugin=mock_plugin)

    manifestation_data['manifestationOfWork'] = {}
    with raises(EntityDataError):
        Manifestation(manifestation_data, plugin=mock_plugin)


@mark.parametrize('data_format,model_factory_name', [
    ('', 'manifestation_jsonld_factory'),
    ('json', 'manifestation_json_factory'),
    ('jsonld', 'manifestation_jsonld_factory'),
])
def test_manifestation_create(mock_plugin, manifestation_model, alice_user,
                              data_format, model_factory_name,
                              mock_manifestation_create_id, request):
    mock_plugin.save.return_value = mock_manifestation_create_id

    if data_format:
        persist_id = manifestation_model.create(alice_user, data_format)
    else:
        persist_id = manifestation_model.create(alice_user)
    assert mock_plugin.save.call_count == 1
    assert persist_id == mock_manifestation_create_id
    assert persist_id == manifestation_model.persist_id

    model_factory = request.getfixturevalue(model_factory_name)
    model_data = model_factory()

    mock_plugin.save.assert_called_with(model_data, user=alice_user)


def test_manifestation_non_transferrable(manifestation_model):
    with raises(AttributeError):
        manifestation_model.transfer()


@mark.parametrize('right_type,data_factory_name,json_factory_name, jsonld_factory_name', [
    ('right', 'right_data_factory', 'right_json_factory', 'right_jsonld_factory'),
    ('copyright', 'copyright_data_factory', 'copyright_json_factory', 'copyright_jsonld_factory'),
])
def test_right_init(mock_plugin, right_type, data_factory_name,
                    json_factory_name, jsonld_factory_name, request):
    from coalaip.models import Copyright, Right
    data_factory = request.getfixturevalue(data_factory_name)
    json_factory = request.getfixturevalue(json_factory_name)
    jsonld_factory = request.getfixturevalue(jsonld_factory_name)

    right_data = data_factory()
    right_json = json_factory()
    right_jsonld = jsonld_factory()

    if right_type == 'right':
        right = Right(right_data, plugin=mock_plugin)
    elif right_type == 'copyright':
        right = Copyright(right_data, plugin=mock_plugin)

    assert right.persist_id is None
    assert right.to_json() == right_json
    assert right.to_jsonld() == right_jsonld


@mark.parametrize('right_type,right_model_name,mock_create_id_name', [
    ('right', 'right_model', 'mock_right_create_id'),
    ('copyright', 'copyright_model', 'mock_copyright_create_id'),
])
@mark.parametrize('data_format,model_factory_name_template', [
    ('', '{right_type}_jsonld_factory'),
    ('json', '{right_type}_json_factory'),
    ('jsonld', '{right_type}_jsonld_factory'),
])
def test_copyright_create(mock_plugin, alice_user, right_type,
                          right_model_name, mock_create_id_name,
                          data_format, model_factory_name_template, request):
    model_factory_name = model_factory_name_template.format(right_type=right_type)

    model_factory = request.getfixturevalue(model_factory_name)
    right_model = request.getfixturevalue(right_model_name)
    mock_create_id = request.getfixturevalue(mock_create_id_name)

    mock_plugin.save.return_value = mock_create_id

    if data_format:
        persist_id = right_model.create(alice_user, data_format)
    else:
        persist_id = right_model.create(alice_user)
    assert mock_plugin.save.call_count == 1
    assert persist_id == mock_create_id
    assert persist_id == right_model.persist_id

    model_data = model_factory()
    mock_plugin.save.assert_called_with(model_data, user=alice_user)


@mark.parametrize('right_type,right_model_name,mock_create_id_name', [
    ('right', 'right_model', 'mock_right_create_id'),
    ('copyright', 'copyright_model', 'mock_copyright_create_id'),
])
@mark.parametrize('data_format,rights_assignment_data_name', [
    ('', 'rights_assignment_jsonld'),
    ('json', 'rights_assignment_json'),
    ('jsonld', 'rights_assignment_jsonld'),
])
def test_copyright_transferrable(mock_plugin, alice_user, bob_user,
                                 rights_assignment_data, right_type,
                                 right_model_name, mock_create_id_name,
                                 data_format, rights_assignment_data_name,
                                 mock_rights_assignment_create_id, request):
    from coalaip.exceptions import EntityNotYetPersistedError
    right_model = request.getfixturevalue(right_model_name)
    mock_create_id = request.getfixturevalue(mock_create_id_name)

    with raises(EntityNotYetPersistedError):
        right_model.transfer(rights_assignment_data, from_user=alice_user,
                             to_user=bob_user)

    # Save the Copyright
    mock_plugin.save.return_value = mock_create_id
    right_model.create(user=alice_user)

    # Test the transfer
    mock_plugin.transfer.return_value = mock_rights_assignment_create_id
    transfer_kwargs = {
        'from_user': alice_user,
        'to_user': bob_user
    }
    if data_format:
        transfer_kwargs['rights_assignment_format'] = data_format

    transfer_tx_id = right_model.transfer(rights_assignment_data,
                                          **transfer_kwargs)
    assert transfer_tx_id == mock_rights_assignment_create_id

    rights_assignment_model_data = request.getfixturevalue(
        rights_assignment_data_name)
    mock_plugin.transfer.assert_called_with(mock_create_id,
                                            rights_assignment_model_data,
                                            from_user=alice_user,
                                            to_user=bob_user)


def test_right_init_raises_without_str_allowed_by(mock_plugin,
                                                  right_data_factory):
    from coalaip.models import Right
    from coalaip.exceptions import EntityDataError

    right_data = right_data_factory()

    del right_data['allowedBy']
    with raises(EntityDataError):
        Right(right_data, plugin=mock_plugin)

    right_data['allowedBy'] = {}
    with raises(EntityDataError):
        Right(right_data, plugin=mock_plugin)


def test_copyright_init_raises_without_str_rights_of(mock_plugin,
                                                     copyright_data_factory):
    from coalaip.models import Copyright
    from coalaip.exceptions import EntityDataError

    copyright_data = copyright_data_factory()

    del copyright_data['rightsOf']
    with raises(EntityDataError):
        Copyright(copyright_data, plugin=mock_plugin)

    copyright_data['rightsOf'] = {}
    with raises(EntityDataError):
        Copyright(copyright_data, plugin=mock_plugin)


def test_copyright_init_raises_if_derived(mock_plugin, copyright_data_factory,
                                          mock_copyright_create_id):
    from coalaip.models import Copyright
    from coalaip.exceptions import EntityDataError

    copyright_data = copyright_data_factory()
    copyright_data['allowedBy'] = mock_copyright_create_id

    with raises(EntityDataError):
        Copyright(copyright_data, plugin=mock_plugin)


def test_right_init_raises_with_both_rights_of_allowed_by(
        mock_plugin, right_data_factory, mock_manifestation_create_id):
    from coalaip.models import Right
    from coalaip.exceptions import EntityDataError

    right_data = right_data_factory(
        data={'rightsOf': mock_manifestation_create_id}
    )

    with raises(EntityDataError):
        Right(right_data, plugin=mock_plugin)


def test_rights_assignment_init(mock_plugin, rights_assignment_data,
                                rights_assignment_json,
                                rights_assignment_jsonld):
    from coalaip.models import RightsAssignment

    rights_assignment = RightsAssignment(rights_assignment_data,
                                         plugin=mock_plugin)
    assert rights_assignment.persist_id is None
    assert rights_assignment.to_json() == rights_assignment_json
    assert rights_assignment.to_jsonld() == rights_assignment_jsonld


def test_rights_assignment_cannot_create(rights_assignment_model, alice_user):
    from coalaip.exceptions import EntityError
    with raises(EntityError):
        rights_assignment_model.create(user=alice_user)


@mark.skip('Rights Assignments require transfer() to be implemented')
def test_rights_assignment_get_status(rights_assignment_model):
    pass


def test_rights_assignment_non_transferrable(rights_assignment_model):
    with raises(AttributeError):
        rights_assignment_model.transfer()
