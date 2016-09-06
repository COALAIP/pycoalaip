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


@mark.parametrize('data_format', [(''), ('json'), ('jsonld')])
@mark.parametrize('work_data', [None, {'name': 'mock_work_name'}])
def test_register_manifestation(mock_plugin, mock_coalaip,
                                manifestation_data_factory, alice_user,
                                data_format, work_data, mock_work_create_id,
                                mock_manifestation_create_id,
                                mock_copyright_create_id):
    from tests.utils import (
        assert_key_values_present_in_dict,
        create_entity_id_setter
    )

    # Create the default manifestation model, but remove the
    # 'manifestationOfWork' key since it'll be created through registration
    manifestation_model = manifestation_data_factory()
    del manifestation_model['manifestationOfWork']

    # Set the persisted ids of the entities
    mock_plugin.save.side_effect = create_entity_id_setter(
        mock_work_create_id,
        mock_manifestation_create_id,
        mock_copyright_create_id,
        type_key='type' if data_format == 'json' else '@type',
    )

    register_manifestation_kwargs = {}
    if data_format:
        register_manifestation_kwargs['data_format'] = data_format

    # Test the entities were persisted
    manifestation_copyright, manifestation, work = mock_coalaip.register_manifestation(
        manifestation_model,
        user=alice_user,
        work_data=work_data,
        **register_manifestation_kwargs,
    )
    assert manifestation_copyright.persist_id == mock_copyright_create_id
    assert manifestation.persist_id == mock_manifestation_create_id
    assert work.persist_id == mock_work_create_id

    assert manifestation_copyright.data['rightsOf'] == manifestation.persist_id
    assert manifestation.data['manifestationOfWork'] == work.persist_id

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

    # If given custom Work information, make sure that is reflected in the
    # entities
    if work_data:
        assert_key_values_present_in_dict(work_persisted_data, **work_data)

    # Check we called plugin.save() in the right order
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


def test_register_manifestation_with_existing_work(mock_plugin, mock_coalaip,
                                                   manifestation_data_factory,
                                                   alice_user, work_model,
                                                   manifestation_model,
                                                   persisted_jsonld_registration,
                                                   mock_manifestation_create_id,
                                                   mock_copyright_create_id):
    from coalaip.exceptions import EntityNotYetPersistedError
    from tests.utils import create_entity_id_setter

    new_manifestation_create_id = mock_manifestation_create_id + '2'
    new_copyright_create_id = mock_copyright_create_id + '2'

    # Create the default manifestation model, but remove the
    # 'manifestationOfWork' key since it'll be created through registration
    manifestation_model = manifestation_data_factory()
    del manifestation_model['manifestationOfWork']

    # Set the persisted ids of the entities
    mock_plugin.save.side_effect = create_entity_id_setter(
        None,  # No work is created
        new_manifestation_create_id,
        new_copyright_create_id,
    )

    # Throws if given Work is not a Work
    with raises(TypeError):
        mock_coalaip.register_manifestation(
            manifestation_model,
            user=alice_user,
            existing_work=manifestation_model,
        )

    # Throws if given Work has not been persisted yet
    with raises(EntityNotYetPersistedError):
        mock_coalaip.register_manifestation(
            manifestation_model,
            user=alice_user,
            existing_work=work_model,
            work_data={'ignored': 'ignored'}
        )

    # Test the new manifestation is created with the given existing_work (and
    # ignores any given work_data)
    mock_plugin.reset_mock()  # Reset call counts on the mock from before
    new_manifestation_copyright, new_manifestation, old_work = mock_coalaip.register_manifestation(
        manifestation_model,
        user=alice_user,
        existing_work=persisted_jsonld_registration.work
    )
    assert new_manifestation_copyright.persist_id == new_copyright_create_id
    assert new_manifestation.persist_id == new_manifestation_create_id

    assert new_manifestation_copyright.data['rightsOf'] == new_manifestation.persist_id
    assert new_manifestation.data['manifestationOfWork'] == old_work.persist_id
    assert old_work == persisted_jsonld_registration.work

    assert new_manifestation.data.get('ignored') is None
    assert old_work.data.get('ignored') is None

    # Check we called plugin.save() in the right order
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


def test_register_manifestation_raises_on_creation_error(mock_plugin,
                                                         mock_coalaip,
                                                         manifestation_data_factory,
                                                         alice_user):
    from coalaip.exceptions import EntityCreationError

    mock_creation_error = 'mock_creation_error'
    mock_plugin.save.side_effect = EntityCreationError(mock_creation_error)

    # Create the default manifestation model, but remove the
    # 'manifestationOfWork' key since it'll be created through registration
    manifestation_model = manifestation_data_factory()
    del manifestation_model['manifestationOfWork']

    with raises(EntityCreationError):
        manifestation_copyright, manifestation, work = mock_coalaip.register_manifestation(
            manifestation_model,
            user=alice_user,
        )
