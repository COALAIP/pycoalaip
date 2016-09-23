#!/usr/bin/env python

from pytest import mark, raises


def test_entity_init(mock_plugin, base_model, mock_entity_class):
    entity = mock_entity_class(base_model, plugin=mock_plugin)
    assert entity.model == base_model
    assert entity.plugin == mock_plugin
    assert entity.persist_id is None


def test_entity_raises_on_bad_init(mock_plugin, base_model, mock_entity_class):
    # Test that instantiation raises if plugin not subclassed from
    # AbstractPlugin
    with raises(TypeError):
        mock_entity_class(model=base_model, plugin=None)

    class NonSubclassPlugin():
        pass

    with raises(TypeError):
        mock_entity_class(model=base_model, plugin=NonSubclassPlugin())

    # Test that instantiation raises if model is not a model
    with raises(TypeError):
        mock_entity_class(model=1, plugin=mock_plugin)

    with raises(TypeError):
        mock_entity_class(model=('name', 'id'), plugin=mock_plugin)


def test_entity_create_raises_on_bad_format(mock_entity, alice_user):
    with raises(ValueError):
        mock_entity.create(alice_user, 'bad_format')


def test_entity_raises_on_creation_error(mock_plugin, mock_entity, alice_user):
    from coalaip.exceptions import EntityCreationError

    mock_creation_error = 'mock_creation_error'
    mock_plugin.save.side_effect = EntityCreationError(mock_creation_error)
    with raises(EntityCreationError) as excinfo:
        mock_entity.create(alice_user)

    assert mock_creation_error == excinfo.value.error


def test_entity_raises_on_creation_if_already_created(
        mock_plugin, mock_entity, alice_user, mock_entity_create_id):
    from coalaip.exceptions import EntityPreviouslyCreatedError

    # Save the entity
    mock_plugin.save.return_value = mock_entity_create_id
    mock_entity.create(alice_user)

    # Test create raises on already persisted entity
    with raises(EntityPreviouslyCreatedError) as excinfo:
        mock_entity.create(alice_user)
    assert mock_entity_create_id == excinfo.value.existing_id


def test_entity_have_none_status_if_not_persisted(mock_plugin, mock_entity):
    status = mock_entity.status
    assert status is None
    mock_plugin.get_status.assert_not_called()


def test_entity_data_format_consistent(mock_plugin, mock_entity_class):
    from tests.utils import assert_key_values_present_in_dict
    entity_data = {'test_data': 'test_data', 'extra_data': 'extra_data'}
    entity = mock_entity_class.from_data(data=entity_data, plugin=mock_plugin)

    assert_key_values_present_in_dict(entity.to_json(), **entity_data)
    assert_key_values_present_in_dict(entity.to_jsonld(), **entity_data)


def test_entity_get_status(mock_plugin, mock_entity, alice_user,
                           mock_entity_create_id, mock_entity_status):
    # Save the entity
    mock_plugin.save.return_value = mock_entity_create_id
    mock_entity.create(alice_user)

    # Test status returned
    mock_plugin.get_status.return_value = mock_entity_status
    status = mock_entity.status
    assert mock_plugin.get_status.call_count == 1
    assert status == mock_entity_status


def test_entity_raises_on_status_if_not_found(mock_plugin, mock_entity,
                                              alice_user,
                                              mock_entity_create_id):
    from coalaip.exceptions import EntityNotFoundError

    # Save the entity
    mock_plugin.save.return_value = mock_entity_create_id
    mock_entity.create(alice_user)

    mock_plugin.get_status.side_effect = EntityNotFoundError()
    with raises(EntityNotFoundError):
        mock_entity.status


@mark.parametrize('use_data_format_enum', [True, False])
@mark.parametrize('data_format,data_name', [
    (None, 'work_data'),
    ('json', 'work_json'),
    ('jsonld', 'work_jsonld'),
    mark.skip(('ipld', 'work_ipld')),
])
def test_work_init_from_data(mock_plugin, data_format, data_name,
                             use_data_format_enum, work_json, work_jsonld,
                             request):
    from coalaip.entities import Work
    data = request.getfixturevalue(data_name)

    kwargs = {}
    if data_format:
        if use_data_format_enum:
            from tests.utils import get_data_format_enum_member
            data_format = get_data_format_enum_member(data_format)
        kwargs['data_format'] = data_format

    work = Work.from_data(data, plugin=mock_plugin, **kwargs)
    assert work.persist_id is None
    assert work.to_json() == work_json
    assert work.to_jsonld() == work_jsonld


def test_work_init_from_data_ignores_diff_type(mock_plugin, work_data,
                                               work_jsonld,
                                               mock_creation_type):
    from coalaip.entities import Work
    work_data['@type'] = mock_creation_type
    work = Work.from_data(work_data, plugin=mock_plugin)

    # Test work ignores specified @type
    assert work.to_jsonld() == work_jsonld
    assert work.to_jsonld()['@type'] != mock_creation_type


def test_work_init_from_data_other_context(mock_plugin, work_data,
                                           work_jsonld, mock_creation_type):
    from coalaip.entities import Work
    work_data['@context'] = 'other_context'
    work_jsonld['@context'] = 'other_context'
    work = Work.from_data(work_data, plugin=mock_plugin)

    # Test work keeps @context
    assert work.to_jsonld() == work_jsonld


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


@mark.parametrize('use_data_format_enum', [True, False])
@mark.parametrize('data_format,model_data_name', [
    (None, 'work_jsonld'),
    ('json', 'work_json'),
    ('jsonld', 'work_jsonld'),
    mark.skip(('ipld', 'work_ipld')),
])
def test_work_create(mock_plugin, work_entity, alice_user, data_format,
                     use_data_format_enum, model_data_name,
                     mock_work_create_id, request):
    mock_plugin.save.return_value = mock_work_create_id

    if data_format:
        if use_data_format_enum:
            from tests.utils import get_data_format_enum_member
            data_format = get_data_format_enum_member(data_format)
        persist_id = work_entity.create(alice_user, data_format)
    else:
        persist_id = work_entity.create(alice_user)
    assert mock_plugin.save.call_count == 1
    assert persist_id == mock_work_create_id
    assert persist_id == work_entity.persist_id

    model_data = request.getfixturevalue(model_data_name)
    mock_plugin.save.assert_called_with(model_data, user=alice_user)


def test_work_non_transferrable(work_entity):
    with raises(AttributeError):
        work_entity.transfer()


@mark.parametrize('use_data_format_enum', [True, False])
@mark.parametrize('data_format,data_factory_name', [
    (None, 'manifestation_data_factory'),
    ('json', 'manifestation_json_factory'),
    ('jsonld', 'manifestation_jsonld_factory'),
    mark.skip(('ipld', 'manifestation_ipld_factory')),
])
def test_manifestation_init(mock_plugin, data_format, data_factory_name,
                            use_data_format_enum, manifestation_json_factory,
                            manifestation_jsonld_factory, request):
    from coalaip.entities import Manifestation
    data_factory = request.getfixturevalue(data_factory_name)

    kwargs = {}
    if data_format:
        if use_data_format_enum:
            from tests.utils import get_data_format_enum_member
            data_format = get_data_format_enum_member(data_format)
        kwargs['data_format'] = data_format

    data = data_factory()
    manifestation_json = manifestation_json_factory()
    manifestation_jsonld = manifestation_jsonld_factory()

    manifestation = Manifestation.from_data(data, plugin=mock_plugin, **kwargs)
    assert manifestation.persist_id is None
    assert manifestation.to_json() == manifestation_json
    assert manifestation.to_jsonld() == manifestation_jsonld


@mark.parametrize('use_data_format_enum', [True, False])
@mark.parametrize('data_format,type_key', [
    ('json', 'type'),
    ('jsonld', '@type'),
    mark.skip(('ipld', 'type')),
])
def test_manifestation_init_other_type(mock_plugin, manifestation_data_factory,
                                       data_format, type_key,
                                       use_data_format_enum,
                                       manifestation_json_factory,
                                       manifestation_jsonld_factory,
                                       mock_creation_type):
    from coalaip.entities import Manifestation

    if use_data_format_enum:
        from tests.utils import get_data_format_enum_member
        data_format = get_data_format_enum_member(data_format)

    manifestation_data = manifestation_data_factory(data={
        type_key: mock_creation_type
    })
    manifestation_json = manifestation_json_factory(data={
        'type': mock_creation_type
    })
    manifestation_jsonld = manifestation_jsonld_factory(data={
        '@type': mock_creation_type
    })

    manifestation = Manifestation.from_data(manifestation_data,
                                            plugin=mock_plugin,
                                            data_format=data_format)
    assert manifestation.to_json() == manifestation_json
    assert manifestation.to_jsonld() == manifestation_jsonld


def test_manifestation_init_raises_if_no_name(mock_plugin,
                                              manifestation_data_factory):
    from coalaip.entities import Manifestation
    from coalaip.exceptions import ModelDataError

    manifestation_data = manifestation_data_factory()
    del manifestation_data['name']

    with raises(ModelDataError):
        Manifestation.from_data(manifestation_data, plugin=mock_plugin)


def test_manifestation_init_raises_without_str_manifestation_of(
        mock_plugin, manifestation_data_factory):
    from coalaip.entities import Manifestation
    from coalaip.exceptions import ModelDataError

    manifestation_data = manifestation_data_factory()

    del manifestation_data['manifestationOfWork']
    with raises(ModelDataError):
        Manifestation.from_data(manifestation_data, plugin=mock_plugin)

    manifestation_data['manifestationOfWork'] = {}
    with raises(ModelDataError):
        Manifestation.from_data(manifestation_data, plugin=mock_plugin)


@mark.parametrize('use_data_format_enum', [True, False])
@mark.parametrize('data_format,model_data_factory_name', [
    (None, 'manifestation_jsonld_factory'),
    ('json', 'manifestation_json_factory'),
    ('jsonld', 'manifestation_jsonld_factory'),
    mark.skip(('ipld', 'manifestation_ipld_factory')),
])
def test_manifestation_create(mock_plugin, manifestation_entity, alice_user,
                              data_format, model_data_factory_name,
                              use_data_format_enum,
                              mock_manifestation_create_id, request):
    mock_plugin.save.return_value = mock_manifestation_create_id

    if data_format:
        if use_data_format_enum:
            from tests.utils import get_data_format_enum_member
            data_format = get_data_format_enum_member(data_format)
        persist_id = manifestation_entity.create(alice_user, data_format)
    else:
        persist_id = manifestation_entity.create(alice_user)
    assert mock_plugin.save.call_count == 1
    assert persist_id == mock_manifestation_create_id
    assert persist_id == manifestation_entity.persist_id

    model_data_factory = request.getfixturevalue(model_data_factory_name)
    model_data = model_data_factory()

    mock_plugin.save.assert_called_with(model_data, user=alice_user)


def test_manifestation_non_transferrable(manifestation_entity):
    with raises(AttributeError):
        manifestation_entity.transfer()


@mark.parametrize('use_data_format_enum', [True, False])
@mark.parametrize('data_format', [None, 'json', 'jsonld', mark.skip('ipld')])
@mark.parametrize('right_cls,data_factory_name,json_factory_name, jsonld_factory_name', [
    ('Right', 'right_data_factory', 'right_json_factory', 'right_jsonld_factory'),
    ('Copyright', 'copyright_data_factory', 'copyright_json_factory', 'copyright_jsonld_factory'),
])
def test_right_init(mock_plugin, data_format, right_cls, data_factory_name,
                    json_factory_name, jsonld_factory_name,
                    use_data_format_enum, request):
    import importlib
    entities = importlib.import_module('coalaip.entities')
    right_cls = getattr(entities, right_cls)
    data_factory = request.getfixturevalue(data_factory_name)
    json_factory = request.getfixturevalue(json_factory_name)
    jsonld_factory = request.getfixturevalue(jsonld_factory_name)

    right_data = data_factory()
    right_json = json_factory()
    right_jsonld = jsonld_factory()

    kwargs = {}
    if data_format is None:
        kwargs['data'] = right_data
    else:
        if data_format == 'json':
            kwargs['data'] = right_json
        elif data_format == 'jsonld':
            kwargs['data'] = right_jsonld

        if use_data_format_enum:
            from tests.utils import get_data_format_enum_member
            data_format = get_data_format_enum_member(data_format)
        kwargs['data_format'] = data_format

    right = right_cls.from_data(plugin=mock_plugin, **kwargs)
    assert right.persist_id is None
    assert right.to_json() == right_json
    assert right.to_jsonld() == right_jsonld


def test_right_init_raises_without_str_allowed_by(mock_plugin,
                                                  right_data_factory):
    from coalaip.entities import Right
    from coalaip.exceptions import ModelDataError

    right_data = right_data_factory()

    del right_data['allowedBy']
    with raises(ModelDataError):
        Right.from_data(right_data, plugin=mock_plugin)

    right_data['allowedBy'] = {}
    with raises(ModelDataError):
        Right.from_data(right_data, plugin=mock_plugin)


def test_copyright_init_raises_without_str_rights_of(mock_plugin,
                                                     copyright_data_factory):
    from coalaip.entities import Copyright
    from coalaip.exceptions import ModelDataError

    copyright_data = copyright_data_factory()

    del copyright_data['rightsOf']
    with raises(ModelDataError):
        Copyright.from_data(copyright_data, plugin=mock_plugin)

    copyright_data['rightsOf'] = {}
    with raises(ModelDataError):
        Copyright.from_data(copyright_data, plugin=mock_plugin)


def test_copyright_init_raises_if_derived(mock_plugin, copyright_data_factory,
                                          mock_copyright_create_id):
    from coalaip.entities import Copyright
    from coalaip.exceptions import ModelDataError

    copyright_data = copyright_data_factory()
    copyright_data['allowedBy'] = mock_copyright_create_id
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


@mark.parametrize('use_data_format_enum', [True, False])
@mark.parametrize('right_type,right_entity_name,mock_create_id_name', [
    ('right', 'right_entity', 'mock_right_create_id'),
    ('copyright', 'copyright_entity', 'mock_copyright_create_id'),
])
@mark.parametrize('data_format,model_data_factory_name_template', [
    ('', '{right_type}_jsonld_factory'),
    ('json', '{right_type}_json_factory'),
    ('jsonld', '{right_type}_jsonld_factory'),
    mark.skip(('ipld', '{right_type}_ipld_factory')),
])
def test_copyright_create(mock_plugin, alice_user, right_type,
                          right_entity_name, mock_create_id_name,
                          data_format, model_data_factory_name_template,
                          use_data_format_enum, request):
    model_data_factory_name = model_data_factory_name_template.format(right_type=right_type)

    model_data_factory = request.getfixturevalue(model_data_factory_name)
    right_entity = request.getfixturevalue(right_entity_name)
    mock_create_id = request.getfixturevalue(mock_create_id_name)

    mock_plugin.save.return_value = mock_create_id

    if data_format:
        if use_data_format_enum:
            from tests.utils import get_data_format_enum_member
            data_format = get_data_format_enum_member(data_format)
        persist_id = right_entity.create(alice_user, data_format)
    else:
        persist_id = right_entity.create(alice_user)
    assert mock_plugin.save.call_count == 1
    assert persist_id == mock_create_id
    assert persist_id == right_entity.persist_id

    model_data = model_data_factory()
    mock_plugin.save.assert_called_with(model_data, user=alice_user)


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
def test_copyright_transferrable(mock_plugin, alice_user, bob_user,
                                 rights_assignment_data, right_entity_name,
                                 mock_create_id_name, data_format,
                                 rights_assignment_data_name,
                                 use_data_format_enum,
                                 mock_rights_assignment_create_id, request):
    from coalaip.exceptions import EntityNotYetPersistedError
    right_entity = request.getfixturevalue(right_entity_name)
    mock_create_id = request.getfixturevalue(mock_create_id_name)

    with raises(EntityNotYetPersistedError):
        right_entity.transfer(rights_assignment_data, from_user=alice_user,
                              to_user=bob_user)

    # Save the Copyright
    mock_plugin.save.return_value = mock_create_id
    right_entity.create(user=alice_user)

    # Test the transfer
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

    transfer_tx_id = right_entity.transfer(rights_assignment_data,
                                           **transfer_kwargs)
    assert transfer_tx_id == mock_rights_assignment_create_id

    rights_assignment_data = request.getfixturevalue(
        rights_assignment_data_name)
    mock_plugin.transfer.assert_called_with(mock_create_id,
                                            rights_assignment_data,
                                            from_user=alice_user,
                                            to_user=bob_user)


@mark.parametrize('use_data_format_enum', [True, False])
@mark.parametrize('data_format,data_name', [
    (None, 'rights_assignment_data'),
    ('json', 'rights_assignment_json'),
    ('jsonld', 'rights_assignment_jsonld'),
    mark.skip(('jsonld', 'rights_assignment_ipld')),
])
def test_rights_assignment_init(mock_plugin, data_format, data_name,
                                use_data_format_enum, rights_assignment_json,
                                rights_assignment_jsonld, request):
    from coalaip.entities import RightsAssignment
    data = request.getfixturevalue(data_name)

    kwargs = {}
    if data_format:
        if use_data_format_enum:
            from tests.utils import get_data_format_enum_member
            data_format = get_data_format_enum_member(data_format)
        kwargs['data_format'] = data_format

    rights_assignment = RightsAssignment.from_data(data, plugin=mock_plugin,
                                                   **kwargs)
    assert rights_assignment.persist_id is None
    assert rights_assignment.to_json() == rights_assignment_json
    assert rights_assignment.to_jsonld() == rights_assignment_jsonld


def test_rights_assignment_cannot_create(rights_assignment_entity, alice_user):
    from coalaip.exceptions import EntityError
    with raises(EntityError):
        rights_assignment_entity.create(user=alice_user)


@mark.skip('Rights Assignments require transfer() to be implemented')
def test_rights_assignment_get_status(rights_assignment_entity):
    pass


def test_rights_assignment_non_transferrable(rights_assignment_entity):
    with raises(AttributeError):
        rights_assignment_entity.transfer()
