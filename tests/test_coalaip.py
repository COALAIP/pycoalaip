#!/usr/bin/env python

from pytest import mark, raises


def test_coalaip_expects_plugin():
    from coalaip.coalaip import CoalaIp

    with raises(TypeError):
        CoalaIp()

    class NonSubclassPlugin():
        pass

    plugin = NonSubclassPlugin()
    with raises(TypeError):
        CoalaIp(plugin)


def test_generate_user(mock_plugin, mock_coalaip, alice_user):
    mock_plugin.generate_user.return_value = alice_user
    generate_user_args = ['arg1']
    generate_user_kwargs = {'arg2': 'arg2'}

    generated_user = mock_coalaip.generate_user(*generate_user_args,
                                                **generate_user_kwargs)
    assert alice_user == generated_user
    mock_plugin.generate_user.assert_called_with(*generate_user_args,
                                                 **generate_user_kwargs)


@mark.parametrize('use_data_format_enum', [True, False])
@mark.parametrize('data_format', [None, 'json', 'jsonld', mark.skip('ipld')])
def test_register_manifestation(mock_plugin, mock_coalaip,
                                manifestation_data_factory, alice_user,
                                data_format, use_data_format_enum,
                                mock_work_create_id,
                                mock_manifestation_create_id,
                                mock_copyright_create_id):
    from tests.utils import create_entity_id_setter

    # Create the default manifestation model, but remove the
    # 'manifestationOfWork' key to create a new Work
    manifestation_data = manifestation_data_factory()
    del manifestation_data['manifestationOfWork']

    # Set the persisted ids of the entities
    mock_plugin.save.side_effect = create_entity_id_setter(
        mock_work_create_id,
        mock_manifestation_create_id,
        mock_copyright_create_id,
        type_key='type' if data_format == 'json' else '@type',
    )

    register_manifestation_kwargs = {}
    if data_format:
        if use_data_format_enum:
            from tests.utils import get_data_format_enum_member
            data_format_arg = get_data_format_enum_member(data_format)
        else:
            data_format_arg = data_format
        register_manifestation_kwargs['data_format'] = data_format_arg

    # Create the entities and test they contain the right links
    manifestation_copyright, manifestation, work = mock_coalaip.register_manifestation(
        manifestation_data,
        user=alice_user,
        **register_manifestation_kwargs,
    )
    assert manifestation_copyright.data['rightsOf'] == manifestation.persist_id
    assert manifestation.data['manifestationOfWork'] == work.persist_id

    # Test the entities were persisted with the set persisted ids
    assert manifestation_copyright.persist_id == mock_copyright_create_id
    assert manifestation.persist_id == mock_manifestation_create_id
    assert work.persist_id == mock_work_create_id

    # Test the correct data format was persisted
    if data_format == 'json':
        manifestation_persisted_data = manifestation.to_json()
        copyright_persisted_data = manifestation_copyright.to_json()
        work_persisted_data = work.to_json()
    elif data_format == 'ipld':
        raise NotImplementedError('IPLD is not implemented yet')
    else:
        manifestation_persisted_data = manifestation.to_jsonld()
        copyright_persisted_data = manifestation_copyright.to_jsonld()
        work_persisted_data = work.to_jsonld()

    # By checking we called plugin.save() in the right order
    mock_save_call_list = mock_plugin.save.call_args_list
    assert len(mock_save_call_list) == 3
    assert mock_save_call_list[0] == (
        (work_persisted_data,),
        {'user': alice_user},
    )
    assert mock_save_call_list[1] == (
        (manifestation_persisted_data,),
        {'user': alice_user},
    )
    assert mock_save_call_list[2] == (
        (copyright_persisted_data,),
        {'user': alice_user},
    )


def test_register_manifestation_with_work_id_in_data(
        mock_plugin, mock_coalaip, manifestation_data_factory, alice_user,
        work_entity, manifestation_entity, persisted_jsonld_registration,
        mock_manifestation_create_id, mock_copyright_create_id):
    from tests.utils import create_entity_id_setter
    ignored_work_entity = work_entity
    provided_work_id = 'provided_work_id'

    # Create the default manifestation model, but change the
    # 'manifestationOfWork' key to differentiate it from work_entity
    manifestation_data = manifestation_data_factory(data={
        'manifestationOfWork': provided_work_id
    })

    # Set the persisted ids of the entities
    mock_plugin.save.side_effect = create_entity_id_setter(
        None,  # No Work should be created
        mock_manifestation_create_id,
        mock_copyright_create_id,
    )

    manifestation_copyright, manifestation, work = mock_coalaip.register_manifestation(
        manifestation_data,
        user=alice_user,
        existing_work=ignored_work_entity,
    )
    assert work is None
    assert manifestation_copyright.data['rightsOf'] == manifestation.persist_id
    assert manifestation.data['manifestationOfWork'] == provided_work_id


@mark.parametrize('work_data', [None, {'name': 'mock_work_name'}])
def test_register_manifestation_with_work_data(
        mock_plugin, mock_coalaip, manifestation_data_factory, alice_user,
        work_data, mock_work_create_id, mock_manifestation_create_id,
        mock_copyright_create_id):
    from tests.utils import (
        assert_key_values_present_in_dict,
        create_entity_id_setter
    )

    # Create the default manifestation model, but remove the
    # 'manifestationOfWork' key to create a new Work
    manifestation_data = manifestation_data_factory()
    del manifestation_data['manifestationOfWork']

    # Set the persisted ids of the entities
    mock_plugin.save.side_effect = create_entity_id_setter(
        mock_work_create_id,
        mock_manifestation_create_id,
        mock_copyright_create_id,
    )

    # Create the entities
    manifestation_copyright, manifestation, work = mock_coalaip.register_manifestation(
        manifestation_data,
        user=alice_user,
        work_data=work_data,
    )
    assert manifestation_copyright.data['rightsOf'] == manifestation.persist_id
    assert manifestation.data['manifestationOfWork'] == work.persist_id

    work_persisted_data = work.to_jsonld()

    # If given custom Work information, make sure that it's reflected in the
    # created Work
    if work_data:
        assert_key_values_present_in_dict(work_persisted_data, **work_data)
        assert_key_values_present_in_dict(work.data, **work_data)

    # Check we called plugin.save() with the correct data
    mock_plugin.save.assert_any_call(work_persisted_data, user=alice_user)


def test_register_manifestation_with_existing_work(
        mock_plugin, mock_coalaip, manifestation_data_factory, alice_user,
        work_entity, manifestation_entity, persisted_jsonld_registration,
        mock_manifestation_create_id, mock_copyright_create_id):
    from coalaip.exceptions import EntityNotYetPersistedError
    from tests.utils import create_entity_id_setter

    new_manifestation_create_id = mock_manifestation_create_id + '2'
    new_copyright_create_id = mock_copyright_create_id + '2'

    # Create the default manifestation model, but remove the
    # 'manifestationOfWork' key to use the existing_work
    manifestation_data = manifestation_data_factory()
    del manifestation_data['manifestationOfWork']

    # Set the persisted ids of the entities
    mock_plugin.save.side_effect = create_entity_id_setter(
        None,  # No work is created
        new_manifestation_create_id,
        new_copyright_create_id,
    )

    # Throws if given existing_work is not a Work
    with raises(TypeError):
        mock_coalaip.register_manifestation(
            manifestation_data,
            user=alice_user,
            existing_work={},
        )

    # Throws if given existing_work has not been persisted yet
    with raises(EntityNotYetPersistedError):
        mock_coalaip.register_manifestation(
            manifestation_data,
            user=alice_user,
            existing_work=work_entity,
        )

    # Test the new Manifestation is created with the given existing_work (and
    # ignores any given work_data)
    mock_plugin.reset_mock()  # Reset call counts on the mock from before
    new_manifestation_copyright, new_manifestation, old_work = mock_coalaip.register_manifestation(
        manifestation_data,
        user=alice_user,
        existing_work=persisted_jsonld_registration.work,
        work_data={'ignored': 'ignored'},
    )
    assert new_manifestation_copyright.persist_id == new_copyright_create_id
    assert new_manifestation.persist_id == new_manifestation_create_id

    assert new_manifestation_copyright.data['rightsOf'] == new_manifestation.persist_id
    assert new_manifestation.data['manifestationOfWork'] == old_work.persist_id
    assert old_work == persisted_jsonld_registration.work

    assert new_manifestation.data.get('ignored') is None
    assert old_work.data.get('ignored') is None

    # Check we called plugin.save() twice (only saving the Manifestation and
    # Copyright) and in the right order
    mock_save_call_list = mock_plugin.save.call_args_list
    assert len(mock_save_call_list) == 2
    assert mock_save_call_list[0] == (
        (new_manifestation.to_jsonld(),),
        {'user': alice_user},
    )
    assert mock_save_call_list[1] == (
        (new_manifestation_copyright.to_jsonld(),),
        {'user': alice_user},
    )


def test_register_manifestation_raises_on_creation_error(
        mock_plugin, mock_coalaip, manifestation_data_factory, alice_user):
    from coalaip.exceptions import EntityCreationError

    mock_creation_error = 'mock_creation_error'
    mock_plugin.save.side_effect = EntityCreationError(mock_creation_error)

    manifestation_data = manifestation_data_factory()
    with raises(EntityCreationError):
        mock_coalaip.register_manifestation(manifestation_data,
                                            user=alice_user)


@mark.parametrize('use_data_format_enum', [True, False])
@mark.parametrize('data_format', [None, 'json', 'jsonld', mark.skip('ipld')])
def test_derive_right(mock_plugin, mock_coalaip, right_data_factory,
                      alice_user, data_format, use_data_format_enum,
                      mock_copyright_create_id, mock_right_create_id):
    mock_plugin.save.return_value = mock_right_create_id

    # Create the default right model with 'allowedBy' already set
    right_data = right_data_factory()

    derive_right_kwargs = {}
    if data_format:
        if use_data_format_enum:
            from tests.utils import get_data_format_enum_member
            data_format_arg = get_data_format_enum_member(data_format)
        else:
            data_format_arg = data_format
        derive_right_kwargs['data_format'] = data_format_arg

    # Create the Right and test it was persisted
    right = mock_coalaip.derive_right(right_data, current_holder=alice_user,
                                      **derive_right_kwargs)
    assert right.persist_id == mock_right_create_id

    # Test the correct data format was persisted
    if data_format == 'json':
        right_persisted_data = right.to_json()
    elif data_format == 'ipld':
        raise NotImplementedError('IPLD is not implemented yet')
    else:
        right_persisted_data = right.to_jsonld()

    # Check we called plugin.save() with the right format
    mock_plugin.save.assert_called_once_with(right_persisted_data,
                                             user=alice_user)


def test_derive_right_with_allowed_by_in_data(mock_plugin, mock_coalaip,
                                              right_data_factory, alice_user,
                                              copyright_entity,
                                              mock_right_create_id):
    ignored_copyright_entity = copyright_entity
    provided_copyright_id = 'provided_copyright_id'
    mock_plugin.save.return_value = mock_right_create_id

    # Create the default right model, but change the 'allowedBy' key to
    # differentiate it from copyright_entity
    right_data = right_data_factory(data={
        'allowedBy': provided_copyright_id
    })

    # Create the Right and test it was persisted with the correct Copyright
    right = mock_coalaip.derive_right(right_data, current_holder=alice_user,
                                      source_right=ignored_copyright_entity)
    assert right.data['allowedBy'] == provided_copyright_id


def test_derive_right_with_existing_source_right(mock_plugin, mock_coalaip,
                                                 right_data_factory,
                                                 alice_user, copyright_entity,
                                                 persisted_jsonld_registration,
                                                 mock_right_create_id):
    from coalaip.exceptions import EntityNotYetPersistedError
    persisted_copyright = persisted_jsonld_registration.copyright
    mock_plugin.save.return_value = mock_right_create_id

    # Create the default right model, but remove the 'allowedBy' key to use
    # the source_right
    right_data = right_data_factory()
    del right_data['allowedBy']

    # Throws if given source_right is not a Right
    with raises(TypeError):
        mock_coalaip.derive_right(right_data, current_holder=alice_user,
                                  source_right={})

    # Throws if given source_right has not been persisted yet
    with raises(EntityNotYetPersistedError):
        mock_coalaip.derive_right(right_data, current_holder=alice_user,
                                  source_right=copyright_entity)

    # Test the new Right is created with the given source_right
    mock_plugin.reset_mock()  # Reset call counts on the mock from before
    right = mock_coalaip.derive_right(right_data, current_holder=alice_user,
                                      source_right=persisted_copyright)
    assert right.data['allowedBy'] == persisted_copyright.persist_id

    # Check we called plugin.save() with the correct Copyright
    mock_plugin.save.assert_called_once_with(right.to_jsonld(),
                                             user=alice_user)


def test_derive_right_with_custom_entity_cls(mock_plugin, mock_coalaip,
                                             right_data_factory, alice_user,
                                             mock_right_create_id):
    from coalaip.entities import Right
    from coalaip.models import _model_factory
    mock_plugin.save.return_value = mock_right_create_id

    custom_right_type = 'CustomRight'

    class CustomRight(Right):
        @classmethod
        def generate_model(cls, *args, **kwargs):
            return _model_factory(ld_type=custom_right_type, *args, **kwargs)

    # Create the default right model with 'allowedBy' already set
    right_data = right_data_factory()

    # Test the new Right is created with the given source_right
    custom_right = mock_coalaip.derive_right(
        right_data,
        current_holder=alice_user,
        right_entity_cls=CustomRight
    )
    assert isinstance(custom_right, CustomRight)
    assert custom_right.to_json()['type'] == custom_right_type
    assert custom_right.persist_id == mock_right_create_id
    assert custom_right.data['allowedBy'] == right_data['allowedBy']


def test_derive_right_raises_on_no_allowed_by_or_source_right(
        mock_plugin, mock_coalaip, right_data_factory, alice_user):

    right_data = right_data_factory()
    del right_data['allowedBy']
    with raises(ValueError):
        mock_coalaip.derive_right(right_data, current_holder=alice_user)


def test_derive_right_raises_on_creation_error(mock_plugin, mock_coalaip,
                                               right_data_factory, alice_user):
    from coalaip.exceptions import EntityCreationError

    mock_creation_error = 'mock_creation_error'
    mock_plugin.save.side_effect = EntityCreationError(mock_creation_error)

    right_data = right_data_factory()
    with raises(EntityCreationError):
        mock_coalaip.derive_right(right_data, current_holder=alice_user)
