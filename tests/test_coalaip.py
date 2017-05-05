#!/usr/bin/env python

from pytest import mark, raises


def test_coalaip_expects_plugin():
    from coalaip.coalaip import CoalaIp
    with raises(TypeError):
        CoalaIp()


def test_coalaip_expcects_subclassed_plugin():
    from coalaip.coalaip import CoalaIp

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
def test_register_manifestation(mock_plugin, mock_coalaip, manifestation_data,
                                alice_user, data_format, use_data_format_enum,
                                mock_work_create_id,
                                mock_manifestation_create_id,
                                mock_copyright_create_id):
    from tests.utils import create_entity_id_setter

    # Remove the 'manifestationOfWork' key to create a new Work
    del manifestation_data['manifestationOfWork']

    # Set the persisted ids of the entities
    mock_plugin.save.side_effect = create_entity_id_setter(
        mock_work_create_id,
        mock_manifestation_create_id,
        mock_copyright_create_id,
        type_key='type' if data_format == 'json' else '@type',
    )

    # Set up the data format
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
        copyright_holder=alice_user,
        **register_manifestation_kwargs
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
        work_entity, mock_manifestation_create_id, mock_copyright_create_id):
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
        copyright_holder=alice_user,
        existing_work=ignored_work_entity,
    )
    assert work is None
    assert manifestation_copyright.data['rightsOf'] == manifestation.persist_id
    assert manifestation.data['manifestationOfWork'] == provided_work_id


def test_register_work(mock_plugin, mock_coalaip, manifestation_data,
                       alice_user, work_data):
    from tests.utils import (
        assert_key_values_present_in_dict,
    )
    work = mock_coalaip.register_work(
        work_data=work_data,
        copyright_holder=alice_user
    )

    work_persisted_data = work.to_jsonld()

    if work_data:
        assert_key_values_present_in_dict(work_persisted_data, **work_data)
        assert_key_values_present_in_dict(work.data, **work_data)

    # Check we called plugin.save() with the correct data
    mock_plugin.save.assert_any_call(work_persisted_data, user=alice_user)


@mark.parametrize('work_data', [None, {'name': 'mock_work_name'}])
def test_register_manifestation_with_work_data(
        mock_plugin, mock_coalaip, manifestation_data, alice_user, work_data,
        mock_work_create_id, mock_manifestation_create_id,
        mock_copyright_create_id):
    from tests.utils import (
        assert_key_values_present_in_dict,
        create_entity_id_setter
    )

    # Remove the 'manifestationOfWork' key to create a new Work
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
        copyright_holder=alice_user,
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
        mock_plugin, mock_coalaip, manifestation_data, alice_user,
        persisted_jsonld_registration, mock_manifestation_create_id,
        mock_copyright_create_id):
    from tests.utils import create_entity_id_setter

    new_manifestation_create_id = mock_manifestation_create_id + '2'
    new_copyright_create_id = mock_copyright_create_id + '2'

    # Remove the 'manifestationOfWork' key to use the existing_work
    del manifestation_data['manifestationOfWork']

    # Set the persisted ids of the entities
    mock_plugin.save.side_effect = create_entity_id_setter(
        None,  # No work is created
        new_manifestation_create_id,
        new_copyright_create_id,
    )

    # Test the new Manifestation is created with the given existing_work (and
    # ignores any given work_data)
    mock_plugin.reset_mock()  # Reset call counts on the mock from before
    new_manifestation_copyright, new_manifestation, old_work = mock_coalaip.register_manifestation(
        manifestation_data,
        copyright_holder=alice_user,
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


def test_register_manifestation_with_existing_work_raises_on_non_work(
        mock_coalaip, alice_user, manifestation_data):
    # Remove the 'manifestationOfWork' key to use the existing_work
    del manifestation_data['manifestationOfWork']

    with raises(TypeError):
        mock_coalaip.register_manifestation(
            manifestation_data,
            copyright_holder=alice_user,
            existing_work={},
        )


def test_register_manifestation_with_existing_work_raises_on_not_persisted_work(
        mock_coalaip, alice_user, manifestation_data, work_entity):
    from coalaip.exceptions import EntityNotYetPersistedError
    # Remove the 'manifestationOfWork' key to use the existing_work
    del manifestation_data['manifestationOfWork']

    with raises(EntityNotYetPersistedError):
        mock_coalaip.register_manifestation(
            manifestation_data,
            copyright_holder=alice_user,
            existing_work=work_entity,
        )


def test_register_manifestation_with_existing_work_raises_on_incompatible_plugin(
        mock_coalaip, mock_plugin, alice_user, manifestation_data, work_data,
        mock_work_create_id):
    from coalaip.entities import Work
    from coalaip.exceptions import IncompatiblePluginError
    from tests.utils import create_mock_plugin
    diff_plugin = create_mock_plugin()
    existing_work_from_diff_plugin = Work.from_data(work_data,
                                                    plugin=diff_plugin)

    # Save the existing_work
    mock_plugin.save.return_value = mock_work_create_id
    existing_work_from_diff_plugin.create(user=alice_user)

    # Remove the 'manifestationOfWork' key to use the existing_work
    del manifestation_data['manifestationOfWork']

    with raises(IncompatiblePluginError):
        mock_coalaip.register_manifestation(
            manifestation_data,
            copyright_holder=alice_user,
            existing_work=existing_work_from_diff_plugin,
        )


def test_register_manifestation_raises_on_creation_error(
        mock_plugin, mock_coalaip, manifestation_data, alice_user):
    from coalaip.exceptions import EntityCreationError
    mock_creation_error = 'mock_creation_error'
    mock_plugin.save.side_effect = EntityCreationError(mock_creation_error)

    with raises(EntityCreationError):
        mock_coalaip.register_manifestation(manifestation_data,
                                            copyright_holder=alice_user)


@mark.parametrize('use_data_format_enum', [True, False])
@mark.parametrize('data_format', [None, 'json', 'jsonld', mark.skip('ipld')])
def test_derive_right(mock_plugin_for_deriving_rights, mock_coalaip,
                      right_data, alice_user, data_format,
                      use_data_format_enum, mock_right_create_id):
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
    mock_plugin_for_deriving_rights.save.assert_called_once_with(
        right_persisted_data, user=alice_user)


def test_derive_right_with_source_in_data(mock_plugin_for_deriving_rights,
                                          mock_coalaip, right_data_factory,
                                          alice_user, copyright_entity):
    ignored_copyright_entity = copyright_entity
    provided_copyright_id = 'provided_copyright_id'

    # Create the default right model, but change the 'source' key to
    # differentiate it from copyright_entity
    right_data = right_data_factory(data={
        'source': provided_copyright_id
    })

    # Create the Right and test it was persisted with the correct Copyright
    right = mock_coalaip.derive_right(right_data, current_holder=alice_user,
                                      source_right=ignored_copyright_entity)
    assert right.data['source'] == provided_copyright_id


def test_derive_right_with_existing_source_right(
        mock_plugin_for_deriving_rights, mock_coalaip, right_data, alice_user,
        persisted_jsonld_registration):
    persisted_copyright = persisted_jsonld_registration.copyright

    # Remove the 'source' key to use the source_right
    del right_data['source']

    # Test the new Right is created with the given source_right
    right = mock_coalaip.derive_right(right_data, current_holder=alice_user,
                                      source_right=persisted_copyright)
    assert right.data['source'] == persisted_copyright.persist_id

    # Check we called plugin.save() with the correct Copyright
    mock_plugin_for_deriving_rights.save.assert_called_once_with(
        right.to_jsonld(), user=alice_user)


def test_derive_right_with_custom_entity_cls(mock_plugin_for_deriving_rights,
                                             mock_coalaip, right_data,
                                             alice_user, mock_right_create_id):
    from coalaip.entities import Right
    from coalaip.models import _model_factory
    mock_plugin_for_deriving_rights.save.return_value = mock_right_create_id

    custom_right_type = 'CustomRight'

    class CustomRight(Right):
        @classmethod
        def generate_model(cls, *args, **kwargs):
            return _model_factory(ld_type=custom_right_type, *args, **kwargs)

    # Test the new Right is created with the given source_right
    custom_right = mock_coalaip.derive_right(
        right_data,
        current_holder=alice_user,
        right_entity_cls=CustomRight
    )
    assert isinstance(custom_right, CustomRight)
    assert custom_right.to_json()['type'] == custom_right_type
    assert custom_right.persist_id == mock_right_create_id
    assert custom_right.data['source'] == right_data['source']


def test_derive_right_with_existing_source_right_raises_on_non_right(
        mock_plugin_for_deriving_rights, mock_coalaip, alice_user, right_data):
    # Remove the 'source' key to use the source_right
    del right_data['source']
    with raises(TypeError):
        mock_coalaip.derive_right(right_data, current_holder=alice_user,
                                  source_right={})


def test_derive_right_with_existing_source_right_raises_on_not_persisted_right(
        mock_plugin_for_deriving_rights, mock_coalaip, alice_user, right_data,
        copyright_entity):
    from coalaip.exceptions import EntityNotYetPersistedError

    # Remove the 'source' key to use the source_right
    del right_data['source']
    with raises(EntityNotYetPersistedError):
        mock_coalaip.derive_right(right_data, current_holder=alice_user,
                                  source_right=copyright_entity)


def test_derive_right_with_existing_source_right_raises_on_incompatible_plugin(
        mock_plugin_for_deriving_rights, mock_coalaip, alice_user,
        copyright_data, right_data, mock_copyright_create_id):
    from coalaip.entities import Copyright
    from coalaip.exceptions import IncompatiblePluginError
    from tests.utils import create_mock_plugin
    diff_plugin = create_mock_plugin()
    source_right_from_diff_plugin = Copyright.from_data(copyright_data,
                                                        plugin=diff_plugin)

    # Save the source_right
    mock_plugin_for_deriving_rights.save.return_value = mock_copyright_create_id
    source_right_from_diff_plugin.create(user=alice_user)

    # Remove the 'source' key to use the existing_work
    del right_data['source']

    with raises(IncompatiblePluginError):
        mock_coalaip.derive_right(right_data, current_holder=alice_user,
                                  source_right=source_right_from_diff_plugin)


def test_derive_right_raises_on_no_source_or_source_right(
        mock_plugin_for_deriving_rights, mock_coalaip, right_data, alice_user):
    del right_data['source']
    with raises(ValueError):
        mock_coalaip.derive_right(right_data, current_holder=alice_user)


def test_derive_right_raises_on_wrong_entity_given_for_source(
        mock_plugin_for_deriving_rights, mock_coalaip, mock_load_data_error,
        right_data, alice_user):
    from coalaip.exceptions import ModelDataError
    mock_plugin_for_deriving_rights.load.side_effect = mock_load_data_error
    with raises(ModelDataError):
        mock_coalaip.derive_right(right_data, current_holder=alice_user)


def test_derive_right_raises_on_wrong_rights_holder(
        mock_plugin_for_deriving_rights, mock_coalaip, right_data, alice_user):
    from coalaip.exceptions import ModelDataError
    mock_plugin_for_deriving_rights.is_same_user.return_value = False
    with raises(ModelDataError):
        mock_coalaip.derive_right(right_data, current_holder=alice_user)


def test_derive_right_raises_on_creation_error(mock_plugin_for_deriving_rights,
                                               mock_coalaip, right_data,
                                               alice_user):
    from coalaip.exceptions import EntityCreationError

    mock_creation_error = 'mock_creation_error'
    mock_plugin_for_deriving_rights.save.side_effect = EntityCreationError(
        mock_creation_error)

    with raises(EntityCreationError):
        mock_coalaip.derive_right(right_data, current_holder=alice_user)


@mark.parametrize('use_data_format_enum', [True, False])
@mark.parametrize('data_format', [None, 'json', 'jsonld', mark.skip('ipld')])
def test_transfer_right(mock_plugin, mock_coalaip, alice_user, bob_user,
                        data_format, use_data_format_enum,
                        rights_assignment_data, persisted_jsonld_derived_right,
                        mock_rights_assignment_transfer_id):
    mock_plugin.transfer.return_value = mock_rights_assignment_transfer_id

    transfer_right_kwargs = {}
    if data_format:
        if use_data_format_enum:
            from tests.utils import get_data_format_enum_member
            data_format_arg = get_data_format_enum_member(data_format)
        else:
            data_format_arg = data_format
        transfer_right_kwargs['rights_assignment_format'] = data_format_arg

    # Transfer the Right and test the resulting RightsAssignment is correct
    rights_assignment = mock_coalaip.transfer_right(
        persisted_jsonld_derived_right, rights_assignment_data,
        current_holder=alice_user, to=bob_user, **transfer_right_kwargs)
    assert rights_assignment.persist_id == mock_rights_assignment_transfer_id
    assert rights_assignment.data == rights_assignment_data

    # Test the correct data format was used in the transfer
    if data_format == 'json':
        rights_assignment_persisted_data = rights_assignment.to_json()
    elif data_format == 'ipld':
        raise NotImplementedError('IPLD is not implemented yet')
    else:
        rights_assignment_persisted_data = rights_assignment.to_jsonld()

    # Check we called plugin.transfer() with the right format
    mock_plugin.transfer.assert_called_once_with(
            persisted_jsonld_derived_right.persist_id,
            rights_assignment_persisted_data,
            from_user=alice_user,
            to_user=bob_user)


def test_transfer_right_without_rights_assignment_data(
        mock_plugin, mock_coalaip, alice_user, bob_user,
        persisted_jsonld_derived_right, mock_rights_assignment_transfer_id):
    mock_plugin.transfer.return_value = mock_rights_assignment_transfer_id

    # Transfer the Right and test the resulting RightsAssignment is correct
    rights_assignment = mock_coalaip.transfer_right(
        persisted_jsonld_derived_right,
        current_holder=alice_user,
        to=bob_user,
        rights_assignment_format='json')
    assert rights_assignment.persist_id == mock_rights_assignment_transfer_id
    assert rights_assignment.data == {}

    # Check we called plugin.transfer() with the right format
    mock_plugin.transfer.assert_called_once_with(
            persisted_jsonld_derived_right.persist_id,
            {'type': 'RightsTransferAction'},
            from_user=alice_user,
            to_user=bob_user)


def test_transfer_right_raises_on_non_right(mock_coalaip, alice_user, bob_user,
                                            persisted_jsonld_registration):
    with raises(TypeError):
        mock_coalaip.transfer_right(persisted_jsonld_registration.work,
                                    current_holder=alice_user, to=bob_user)


def test_transfer_right_raises_on_not_persisted_right(mock_coalaip, alice_user,
                                                      bob_user, right_entity):
    from coalaip.exceptions import EntityNotYetPersistedError
    with raises(EntityNotYetPersistedError):
        mock_coalaip.transfer_right(right_entity, current_holder=alice_user,
                                    to=bob_user)


def test_transfer_right_raises_on_incompatible_plugin(
        mock_coalaip, mock_plugin, alice_user, bob_user, right_data,
        mock_right_create_id):
    from coalaip.entities import Right
    from coalaip.exceptions import IncompatiblePluginError
    from tests.utils import create_mock_plugin
    diff_plugin = create_mock_plugin()
    right_from_diff_plugin = Right.from_data(right_data, plugin=diff_plugin)

    # Save the right
    mock_plugin.save.return_value = mock_right_create_id
    right_from_diff_plugin.create(user=alice_user)

    with raises(IncompatiblePluginError):
        mock_coalaip.transfer_right(right_from_diff_plugin,
                                    current_holder=alice_user, to=bob_user)


def test_transfer_right_raises_on_transfer_error(
        mock_plugin, mock_coalaip, alice_user, bob_user,
        persisted_jsonld_derived_right, mock_transfer_error):
    from coalaip.exceptions import EntityTransferError

    mock_plugin.transfer.side_effect = mock_transfer_error

    with raises(EntityTransferError):
        mock_coalaip.transfer_right(persisted_jsonld_derived_right,
                                    current_holder=alice_user, to=bob_user)
