#!/usr/bin/env python

from pytest import mark, raises


def test_entities_raise_on_bad_plugin():
    from coalaip.models import CoalaIpEntity

    with raises(TypeError):
        CoalaIpEntity(data={}, plugin=None)

    # Test that plugins also need to be subclassed from AbstractPlugin
    class NonSubclassPlugin():
        pass

    plugin = NonSubclassPlugin()
    with raises(TypeError):
        CoalaIpEntity(data={}, entity_type='type', plugin=plugin)


def test_entities_raise_on_creation_error(mock_plugin, base_entity_model,
                                          alice_user):
    from coalaip.exceptions import EntityCreationError

    mock_creation_error = 'mock_creation_error'
    mock_plugin.save.side_effect = EntityCreationError(mock_creation_error)
    with raises(EntityCreationError) as excinfo:
        base_entity_model.create(alice_user)

    assert mock_creation_error == excinfo.value.error


def test_entities_raise_on_creation_if_already_created(
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


def test_entities_have_none_status_if_not_persisted(mock_plugin,
                                                    base_entity_model):
    status = base_entity_model.get_status()
    assert mock_plugin.get_status.call_count == 0
    assert status is None


def test_entities_get_status(mock_plugin, base_entity_model, alice_user,
                             mock_base_entity_create_id, mock_model_status):
    # Save the entity
    mock_plugin.save.return_value = mock_base_entity_create_id
    base_entity_model.create(alice_user)

    # Test status returned
    mock_plugin.get_status.return_value = mock_model_status
    status = base_entity_model.get_status()
    assert mock_plugin.get_status.call_count == 1
    assert status == mock_model_status


def test_entities_raise_on_status_if_not_found(mock_plugin, base_entity_model,
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


def test_work_create_raises_on_bad_format(work_model, alice_user):
    with raises(ValueError):
        work_model.create(alice_user, 'bad_format')


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


def test_manifestation_init_raise_without_manifestation_of(
        mock_plugin, manifestation_data_factory):
    from coalaip.models import Manifestation
    from coalaip.exceptions import EntityDataError

    manifestation_data = manifestation_data_factory()
    del manifestation_data['manifestationOfWork']

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


def test_copyright_init(mock_plugin, copyright_data_factory,
                        copyright_json_factory, copyright_jsonld_factory):
    from coalaip.models import Copyright

    copyright_data = copyright_data_factory()
    copyright_json = copyright_json_factory()
    copyright_jsonld = copyright_jsonld_factory()

    copyright = Copyright(copyright_data, plugin=mock_plugin)
    assert copyright.persist_id is None
    assert copyright.to_json() == copyright_json
    assert copyright.to_jsonld() == copyright_jsonld


def test_copyright_init_raise_without_rights_of(mock_plugin,
                                                copyright_data_factory):
    from coalaip.models import Copyright
    from coalaip.exceptions import EntityDataError

    copyright_data = copyright_data_factory(rightsOf='')
    del copyright_data['rightsOf']

    with raises(EntityDataError):
        Copyright(copyright_data, plugin=mock_plugin)


@mark.parametrize('data_format,model_factory_name', [
    ('', 'copyright_jsonld_factory'),
    ('json', 'copyright_json_factory'),
    ('jsonld', 'copyright_jsonld_factory'),
])
def test_copyright_create(mock_plugin, copyright_model, alice_user,
                          data_format, model_factory_name,
                          mock_copyright_create_id, request):
    mock_plugin.save.return_value = mock_copyright_create_id

    if data_format:
        persist_id = copyright_model.create(alice_user, data_format)
    else:
        persist_id = copyright_model.create(alice_user)
    assert mock_plugin.save.call_count == 1
    assert persist_id == mock_copyright_create_id
    assert persist_id == copyright_model.persist_id

    model_factory = request.getfixturevalue(model_factory_name)
    model_data = model_factory()

    mock_plugin.save.assert_called_with(model_data, user=alice_user)


@mark.parametrize('data_format,rights_assignment_data_name', [
    ('', 'rights_assignment_jsonld'),
    ('json', 'rights_assignment_json'),
    ('jsonld', 'rights_assignment_jsonld'),
])
def test_copyright_transferrable(mock_plugin, copyright_model,
                                 rights_assignment_data, alice_user, bob_user,
                                 data_format, rights_assignment_data_name,
                                 mock_copyright_create_id,
                                 mock_rights_assignment_create_id, request):
    from coalaip.exceptions import EntityNotYetPersistedError

    with raises(EntityNotYetPersistedError):
        copyright_model.transfer(rights_assignment_data, from_user=alice_user,
                                 to_user=bob_user)

    # Save the Copyright
    mock_plugin.save.return_value = mock_copyright_create_id
    copyright_model.create(user=alice_user)

    # Test the transfer
    mock_plugin.transfer.return_value = mock_rights_assignment_create_id
    transfer_kwargs = {
        'from_user': alice_user,
        'to_user': bob_user
    }
    if data_format:
        transfer_kwargs['rights_assignment_format'] = data_format

    transfer_tx_id = copyright_model.transfer(rights_assignment_data,
                                              **transfer_kwargs)
    assert transfer_tx_id == mock_rights_assignment_create_id

    rights_assignment_model_data = request.getfixturevalue(
        rights_assignment_data_name)
    mock_plugin.transfer.assert_called_with(mock_copyright_create_id,
                                            rights_assignment_model_data,
                                            from_user=alice_user,
                                            to_user=bob_user)


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
