from pytest import fixture

from coalaip.utils import extend_dict


@fixture
def alice_user():
    return {'name': 'alice'}


@fixture
def bob_user():
    return {'name': 'bob'}


@fixture
def context_urls_coalaip():
    from coalaip.context_urls import COALAIP
    return COALAIP


@fixture
def context_urls_all():
    from coalaip.context_urls import COALAIP, SCHEMA
    return [COALAIP, SCHEMA]


@fixture
def mock_plugin():
    from tests.utils import create_mock_plugin
    return create_mock_plugin()


@fixture
def mock_coalaip(mock_plugin):
    from coalaip import CoalaIp
    return CoalaIp(mock_plugin)


@fixture
def mock_model_status():
    return 'valid'


@fixture
def base_entity_model(mock_plugin):
    from coalaip.models import CoalaIpEntity

    class BaseEntityModel(CoalaIpEntity):
        @classmethod
        def from_dict(*args, **kwargs):
            return super().from_dict(*args, **kwargs)

    return BaseEntityModel(data={}, ld_type='type', plugin=mock_plugin)


@fixture
def mock_base_entity_create_id():
    return 'mock_entity_create_id'


@fixture
def work_data():
    return {
        'name': 'Title',
    }


@fixture
def work_jsonld(context_urls_all, work_data):
    ld_data = {
        '@context': context_urls_all,
        '@type': 'CreativeWork',
        '@id': '',
    }
    return extend_dict(ld_data, work_data)


@fixture
def work_json(work_data):
    json_data = {
        'type': 'CreativeWork',
    }
    return extend_dict(json_data, work_data)


@fixture
def work_model(mock_plugin, work_data):
    from coalaip.models import Work
    return Work(work_data, plugin=mock_plugin)


@fixture
def mock_work_create_id():
    return 'mock_create_id'


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
def manifestation_jsonld_factory(context_urls_all, manifestation_data_factory):
    def factory(**kwargs):
        ld_data = {
            '@context': context_urls_all,
            '@type': 'CreativeWork',
            '@id': '',
            'isManifestation': True,
        }
        return extend_dict(
            ld_data,
            manifestation_data_factory(**kwargs))

    return factory


@fixture
def manifestation_json_factory(manifestation_data_factory):
    def factory(**kwargs):
        json_data = {
            'type': 'CreativeWork',
            'isManifestation': True,
        }
        return extend_dict(
            json_data,
            manifestation_data_factory(**kwargs))

    return factory


@fixture
def manifestation_model(mock_plugin, manifestation_data_factory):
    from coalaip.models import Manifestation
    manifestation_data = manifestation_data_factory()
    return Manifestation(manifestation_data, plugin=mock_plugin)


@fixture
def mock_manifestation_create_id():
    return 'mock_manifestation_create_id'


@fixture
def mock_manifestation_type():
    return 'mock_manifestation_type'


@fixture
def copyright_data_factory(mock_manifestation_create_id):
    def factory(*, rightsOf=mock_manifestation_create_id, data=None):
        copyright_data = {
            'rightsOf': rightsOf
        }
        return extend_dict(copyright_data, data)
    return factory


@fixture
def copyright_jsonld_factory(context_urls_coalaip, copyright_data_factory):
    def factory(**kwargs):
        ld_data = {
            '@context': context_urls_coalaip,
            '@type': 'Copyright',
            '@id': '',
        }
        return extend_dict(ld_data, copyright_data_factory(**kwargs))
    return factory


@fixture
def copyright_json_factory(copyright_data_factory):
    def factory(**kwargs):
        json_data = {
            'type': 'Copyright',
        }
        return extend_dict(json_data, copyright_data_factory(**kwargs))
    return factory


@fixture
def copyright_model(mock_plugin, copyright_data_factory):
    from coalaip.models import Copyright
    copyright_data = copyright_data_factory()
    return Copyright(copyright_data, plugin=mock_plugin)


@fixture
def mock_copyright_create_id():
    return 'mock_copyright_create_id'


@fixture
def right_data_factory(mock_copyright_create_id):
    def factory(*, allowedBy=mock_copyright_create_id, data=None):
        right_data = {
            'allowedBy': allowedBy
        }
        return extend_dict(right_data, data)
    return factory


@fixture
def right_jsonld_factory(context_urls_coalaip, right_data_factory):
    def factory(**kwargs):
        ld_data = {
            '@context': context_urls_coalaip,
            '@type': 'Right',
            '@id': '',
        }
        return extend_dict(ld_data, right_data_factory(**kwargs))
    return factory


@fixture
def right_json_factory(right_data_factory):
    def factory(**kwargs):
        json_data = {
            'type': 'Right',
        }
        return extend_dict(json_data, right_data_factory(**kwargs))
    return factory


@fixture
def right_model(mock_plugin, right_data_factory):
    from coalaip.models import Right
    right_data = right_data_factory()
    return Right(right_data, plugin=mock_plugin)


@fixture
def mock_right_create_id():
    return 'mock_right_create_id'


@fixture
def transfer_contract_url():
    return 'https://ipdb.s3.amazonaws.com/1234567890.pdf'


@fixture
def rights_assignment_data(transfer_contract_url):
    return {
        'transferContract': transfer_contract_url
    }


@fixture
def rights_assignment_jsonld(context_urls_coalaip, rights_assignment_data):
    ld_data = {
        '@context': context_urls_coalaip,
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
def rights_assignment_model(mock_plugin, rights_assignment_json):
    from coalaip.models import RightsAssignment
    return RightsAssignment(rights_assignment_json, plugin=mock_plugin)


@fixture
def mock_rights_assignment_create_id():
    return 'mock_rights_assignment_create_id'


@fixture
def persisted_jsonld_registration(mock_plugin, mock_coalaip,
                                  manifestation_data_factory, alice_user,
                                  mock_work_create_id,
                                  mock_manifestation_create_id,
                                  mock_copyright_create_id):
    from tests.utils import create_entity_id_setter

    # Create the default manifestation model, but remove the
    # 'manifestationOfWork' key since it'll be created through registration
    manifestation_model = manifestation_data_factory()
    del manifestation_model['manifestationOfWork']

    # Set the persisted ids of the entities
    mock_plugin.save.side_effect = create_entity_id_setter(
        mock_work_create_id,
        mock_manifestation_create_id,
        mock_copyright_create_id)

    return mock_coalaip.register_manifestation(
        manifestation_model,
        user=alice_user,
    )
