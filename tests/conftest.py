from pytest import fixture

from coalaip.context_urls import COALAIP
from coalaip.models import DEFAULT_LD_CONTEXT
from coalaip.utils import extend_dict

from tests.utils import create_mock_plugin


@fixture
def alice_user():
    return {'name': 'alice'}


@fixture
def bob_user():
    return {'name': 'bob'}


@fixture
def mock_plugin():
    return create_mock_plugin()


@fixture
def mock_bound_coalaip(mock_plugin):
    from coalaip import CoalaIp
    return CoalaIp(mock_plugin)


@fixture
def mock_model_status():
    return 'valid'


@fixture
def work_data():
    return {
        'name': 'Title',
    }


@fixture
def work_jsonld(work_data):
    ld_data = {
        '@context': DEFAULT_LD_CONTEXT,
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


# FIXME: the factories should default their required IDs to the mock ones
@fixture
def manifestation_data_factory():
    def factory(*, manifestationOfWork, data=None):
        manifestation_data = {
            'name': 'Title',
            'creator': 'https://ipdb.foundation/api/transactions/12346789',
            'manifestationOfWork': manifestationOfWork
        }
        return extend_dict(manifestation_data, data)

    return factory


@fixture
def manifestation_jsonld_factory(manifestation_data_factory):
    def factory(**kwargs):
        ld_data = {
            '@context': DEFAULT_LD_CONTEXT,
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
def manifestation_model(mock_plugin, manifestation_data_factory,
                        mock_work_create_id):
    from coalaip.models import Manifestation
    manifestation_data = manifestation_data_factory(
        manifestationOfWork=mock_work_create_id)
    return Manifestation(manifestation_data, plugin=mock_plugin)


@fixture
def mock_manifestation_create_id():
    return 'mock_manifestation_create_id'


@fixture
def copyright_data_factory():
    def factory(*, rightsOf, data=None):
        copyright_data = {
            'rightsOf': rightsOf
        }
        return extend_dict(copyright_data, data)
    return factory


@fixture
def copyright_jsonld_factory(copyright_data_factory):
    def factory(**kwargs):
        ld_data = {
            '@context': COALAIP,
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
def copyright_model(mock_plugin, copyright_data_factory,
                    mock_manifestation_create_id):
    from coalaip.models import Copyright
    copyright_data = copyright_data_factory(
        rightsOf=mock_manifestation_create_id)
    return Copyright(copyright_data, plugin=mock_plugin)


@fixture
def transfer_contract_url():
    return 'https://ipdb.s3.amazonaws.com/1234567890.pdf'


@fixture
def rights_assignment_jsonld(transfer_contract_url):
    return {
        '@context': DEFAULT_LD_CONTEXT,
        '@type': 'RightsTransferAction',
        'transferContract': transfer_contract_url
    }


@fixture
def rights_assignment_json(transfer_contract_url):
    return {
        'type': 'RightsTransferAction',
        'transferContract': transfer_contract_url
    }


@fixture
def rights_assignment_model(mock_plugin, rights_assignment_json):
    from coalaip.models import RightsAssignment
    return RightsAssignment(rights_assignment_json, plugin=mock_plugin)


@fixture
def persisted_registration(mock_bound_coalaip, manifestation_data_factory,
                           alice_user):
    # Create the default manifestation model, but remove the
    # 'manifestationOfWork' key since it'll be created through registration
    manifestation_model = manifestation_data_factory(
        manifestationOfWork='none'
    )
    del manifestation_model['manifestationOfWork']

    return mock_bound_coalaip.register_manifestation(
        manifestation_model,
        user=alice_user
    )
