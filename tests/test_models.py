#!/usr/bin/env python

from pytest import mark, raises


def test_work_init(mock_plugin, work_data, work_json,
                   work_jsonld):
    from coalaip.models import Work
    work = Work(work_data, plugin=mock_plugin)
    assert work.persist_id is None
    assert work.to_json() == work_json
    assert work.to_jsonld() == work_jsonld


# TODO: Add ipld
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


def test_work_get_status(mock_plugin, work_model, mock_model_status):
    mock_plugin.get_status.return_value = mock_model_status

    status = work_model.get_status()
    assert mock_plugin.get_status.call_count == 1
    assert status == mock_model_status


def test_work_non_transferrable(work_model):
    with raises(AttributeError):
        work_model.transfer()


def test_manifestation_init(mock_plugin, mock_work_create_id,
                            manifestation_data_factory,
                            manifestation_json_factory,
                            manifestation_jsonld_factory):
    from coalaip.models import Manifestation

    manifestation_data = manifestation_data_factory(
        manifestationOfWork=mock_work_create_id)
    manifestation_json = manifestation_json_factory(
        manifestationOfWork=mock_work_create_id)
    manifestation_jsonld = manifestation_jsonld_factory(
        manifestationOfWork=mock_work_create_id)

    manifestation = Manifestation(manifestation_data, plugin=mock_plugin)
    assert manifestation.persist_id is None
    assert manifestation.to_json() == manifestation_json
    assert manifestation.to_jsonld() == manifestation_jsonld


def test_manifestation_init_raise_without_manifestation_of(
        mock_plugin, manifestation_data_factory):
    from coalaip.models import Manifestation
    from coalaip.exceptions import EntityDataError

    manifestation_data = manifestation_data_factory(
        manifestationOfWork='')
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
                              mock_work_create_id,
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
    model_data = model_factory(manifestationOfWork=mock_work_create_id)

    mock_plugin.save.assert_called_with(model_data, user=alice_user)


def test_manifestation_get_status(mock_plugin, manifestation_model,
                                  mock_model_status):
    mock_plugin.get_status.return_value = mock_model_status

    status = manifestation_model.get_status()
    assert mock_plugin.get_status.call_count == 1
    assert status == mock_model_status


def test_manifestation_non_transferrable(manifestation_model):
    with raises(AttributeError):
        manifestation_model.transfer()


def test_copyright_init(mock_plugin, copyright_data_factory):
    from coalaip.models import Copyright


def test_copyright_init_raise_without_rights_of():
    pass


def test_copyright_create(copyright_model, mock_manifestation_create_id,
                          copyright_data_factory):
    pass


def test_copyright_get_status(copyright_model):
    pass


def test_copyright_transferrable():
    pass


def test_rights_assignment_init(mock_plugin):
    from coalaip.models import RightsAssignment


def test_rights_assignment_init_raise_without_plugin():
    pass


def test_rights_assignment_cannot_create(rights_assignment_model):
    pass


@mark.skip('Rights Assignments require transfer() to be implemented')
def test_rights_assignment_get_status(rights_assignment_model):
    pass


def test_rights_assignment_non_transferrable():
    pass
