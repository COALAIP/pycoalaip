from pytest import fixture

from tests.utils import extend_dict


@fixture
def alice_user():
    return {'name': 'alice'}


@fixture
def bob_user():
    return {'name': 'bob'}


@fixture
def context_urls_all():
    from coalaip.context_urls import COALAIP, SCHEMA
    return [COALAIP, SCHEMA]


@fixture
def mock_plugin():
    from tests.utils import create_mock_plugin
    return create_mock_plugin()


@fixture
def mock_plugin_for_deriving_rights(mock_plugin, right_data,
                                    mock_right_create_id):
    # Same `mock_plugin` instance used for `mock_coalaip` but with some auto
    # mocks that are useful for testing CoalaIp.derive_right()
    mock_plugin.get_history.return_value = []
    mock_plugin.is_same_user.return_value = True
    mock_plugin.load.return_value = right_data
    mock_plugin.save.return_value = mock_right_create_id
    return mock_plugin


@fixture
def mock_coalaip(mock_plugin):
    from coalaip import CoalaIp
    return CoalaIp(mock_plugin)


@fixture
def mock_entity_status():
    return 'valid'


@fixture
def mock_entity_create_id():
    return 'mock_entity_create_id'


@fixture
def base_model():
    from coalaip.models import Model
    model = Model(data={}, ld_type='type')
    return model


@fixture
def mock_entity_type():
    return 'mock_entity_type'


@fixture
def mock_entity_context():
    return 'mock_entity_context'


@fixture
def mock_creation_error():
    from coalaip.exceptions import EntityCreationError
    exception = EntityCreationError('mock_creation_error',
                                    error=Exception())
    return exception


@fixture
def mock_load_data_error():
    from coalaip.exceptions import ModelDataError
    exception = ModelDataError('mock_load_data_error')
    return exception


@fixture
def mock_not_found_error():
    from coalaip.exceptions import EntityNotFoundError
    exception = EntityNotFoundError('mock_not_found_error')
    return exception


@fixture
def mock_transfer_error():
    from coalaip.exceptions import EntityTransferError
    exception = EntityTransferError('mock_transfer_error',
                                    error=Exception())
    return exception


@fixture
def work_data():
    return {
        'name': 'Title',
    }


@fixture
def work_jsonld(context_urls_all, work_data):
    ld_data = {
        '@context': context_urls_all,
        '@type': 'AbstractWork',
        '@id': '',
    }
    return extend_dict(ld_data, work_data)


@fixture
def work_json(work_data):
    json_data = {
        'type': 'AbstractWork',
    }
    return extend_dict(json_data, work_data)


@fixture
def work_model(work_data):
    from coalaip.models import work_model_factory
    return work_model_factory(data=work_data)


@fixture
def work_entity(mock_plugin, work_data):
    from coalaip.entities import Work
    return Work.from_data(work_data, plugin=mock_plugin)


@fixture
def mock_work_create_id():
    return 'mock_work_create_id'


@fixture
def manifestation_data_factory(mock_work_create_id):
    def factory(*, manifestationOfWork=mock_work_create_id, data=None):
        manifestation_data = {
            'name': 'Title',
            'creator': 'https://ipdb.foundation/api/transactions/12346789',
            'manifestationOfWork': manifestationOfWork
        }
        return extend_dict(manifestation_data, data)

    return factory


@fixture
def manifestation_data(manifestation_data_factory):
    return manifestation_data_factory()


@fixture
def manifestation_jsonld_factory(context_urls_all, manifestation_data_factory):
    def factory(**kwargs):
        ld_data = {
            '@context': context_urls_all,
            '@type': 'CreativeWork',
            '@id': '',
        }
        return extend_dict(
            ld_data,
            manifestation_data_factory(**kwargs))

    return factory


@fixture
def manifestation_jsonld(manifestation_jsonld_factory):
    return manifestation_jsonld_factory()


@fixture
def manifestation_json_factory(manifestation_data_factory):
    def factory(**kwargs):
        json_data = {
            'type': 'CreativeWork',
        }
        return extend_dict(
            json_data,
            manifestation_data_factory(**kwargs))

    return factory


@fixture
def manifestation_json(manifestation_json_factory):
    return manifestation_json_factory()


@fixture
def manifestation_model(manifestation_data):
    from coalaip.models import manifestation_model_factory
    return manifestation_model_factory(data=manifestation_data)


@fixture
def manifestation_entity(mock_plugin, manifestation_data):
    from coalaip.entities import Manifestation
    return Manifestation.from_data(manifestation_data, plugin=mock_plugin)


@fixture
def mock_manifestation_create_id():
    return 'mock_manifestation_create_id'


@fixture
def copyright_data_factory(mock_manifestation_create_id):
    def factory(*, rightsOf=mock_manifestation_create_id, data=None):
        copyright_data = {
            'rightsOf': rightsOf
        }
        return extend_dict(copyright_data, data)
    return factory


@fixture
def copyright_data(copyright_data_factory):
    return copyright_data_factory()


@fixture
def copyright_jsonld_factory(context_urls_all, copyright_data_factory):
    def factory(**kwargs):
        ld_data = {
            '@context': context_urls_all,
            '@type': 'Copyright',
            '@id': '',
        }
        return extend_dict(ld_data, copyright_data_factory(**kwargs))
    return factory


@fixture
def copyright_jsonld(copyright_jsonld_factory):
    return copyright_jsonld_factory()


@fixture
def copyright_json_factory(copyright_data_factory):
    def factory(**kwargs):
        json_data = {
            'type': 'Copyright',
        }
        return extend_dict(json_data, copyright_data_factory(**kwargs))
    return factory


@fixture
def copyright_json(copyright_json_factory):
    return copyright_json_factory()


@fixture
def copyright_model(copyright_data):
    from coalaip.models import copyright_model_factory
    return copyright_model_factory(data=copyright_data)


@fixture
def copyright_entity(mock_plugin, copyright_data):
    from coalaip.entities import Copyright
    return Copyright.from_data(copyright_data, plugin=mock_plugin)


@fixture
def mock_copyright_create_id():
    return 'mock_copyright_create_id'


@fixture
def right_data_factory(mock_license_url, mock_copyright_create_id):
    def factory(*, source=mock_copyright_create_id, data=None):
        right_data = {
            'source': source,
            'license': mock_license_url
        }
        return extend_dict(right_data, data)
    return factory


@fixture
def right_data(right_data_factory):
    return right_data_factory()


@fixture
def right_jsonld_factory(context_urls_all, right_data_factory):
    def factory(**kwargs):
        ld_data = {
            '@context': context_urls_all,
            '@type': 'Right',
            '@id': '',
        }
        return extend_dict(ld_data, right_data_factory(**kwargs))
    return factory


@fixture
def right_jsonld(right_jsonld_factory):
    return right_jsonld_factory()


@fixture
def right_json_factory(right_data_factory):
    def factory(**kwargs):
        json_data = {
            'type': 'Right',
        }
        return extend_dict(json_data, right_data_factory(**kwargs))
    return factory


@fixture
def right_json(right_json_factory):
    return right_json_factory()


@fixture
def right_model(right_data):
    from coalaip.models import right_model_factory
    return right_model_factory(data=right_data)


@fixture
def right_entity(mock_plugin, right_data):
    from coalaip.entities import Right
    return Right.from_data(right_data, plugin=mock_plugin)


@fixture
def mock_right_create_id():
    return 'mock_right_create_id'


@fixture
def mock_license_url():
    return 'https://ipdb.s3.amazonaws.com/mock_license.pdf'


@fixture
def mock_transfer_contract_url():
    return 'https://ipdb.s3.amazonaws.com/mock_transfer_contract.pdf'


@fixture
def rights_assignment_data(mock_transfer_contract_url):
    return {
        'transferContract': mock_transfer_contract_url
    }


@fixture
def rights_assignment_jsonld(context_urls_all, rights_assignment_data):
    ld_data = {
        '@context': context_urls_all,
        '@type': 'RightsTransferAction',
        '@id': '',
    }
    return extend_dict(ld_data, rights_assignment_data)


@fixture
def rights_assignment_json(rights_assignment_data):
    json_data = {
        'type': 'RightsTransferAction',
    }
    return extend_dict(json_data, rights_assignment_data)


@fixture
def rights_assignment_model(rights_assignment_data):
    from coalaip.models import rights_assignment_model_factory
    return rights_assignment_model_factory(data=rights_assignment_data)


@fixture
def rights_assignment_entity(mock_plugin, rights_assignment_data):
    from coalaip.entities import RightsAssignment
    return RightsAssignment.from_data(rights_assignment_data,
                                      plugin=mock_plugin)


@fixture
def mock_rights_assignment_transfer_id():
    return 'mock_rights_assignment_transfer_id'


@fixture
def persisted_jsonld_registration(mock_plugin, mock_coalaip,
                                  manifestation_data, alice_user,
                                  mock_work_create_id,
                                  mock_manifestation_create_id,
                                  mock_copyright_create_id):
    from tests.utils import create_entity_id_setter

    # Remove the 'manifestationOfWork' key to also register a new Work
    del manifestation_data['manifestationOfWork']

    # Set the persisted ids of the entities
    mock_plugin.save.side_effect = create_entity_id_setter(
        mock_work_create_id,
        mock_manifestation_create_id,
        mock_copyright_create_id)

    register_result = mock_coalaip.register_manifestation(
        manifestation_data,
        copyright_holder=alice_user,
    )

    # Reset mock for later users
    mock_plugin.save.reset_mock()
    mock_plugin.save.side_effect = None
    return register_result


@fixture
def persisted_jsonld_derived_right(mock_plugin_for_deriving_rights,
                                   mock_coalaip, alice_user,
                                   persisted_jsonld_registration, right_data,
                                   mock_right_create_id):
    copyright_ = persisted_jsonld_registration.copyright
    # Remove the 'source' key to use the persisted copyright
    del right_data['source']

    mock_plugin_for_deriving_rights.save.return_value = 'asdf'
    right = mock_coalaip.derive_right(right_data, current_holder=alice_user,
                                      source_right=copyright_)

    # Reset mock for later users
    mock_plugin_for_deriving_rights.save.reset_mock()
    mock_plugin_for_deriving_rights.save.return_value = None
    return right
