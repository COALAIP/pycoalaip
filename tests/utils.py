def create_mock_plugin():
    from unittest.mock import Mock
    from coalaip.plugin import AbstractPlugin
    mock_plugin = Mock(
        name="mock_ledger_plugin",
        spec_set=AbstractPlugin)
    mock_plugin.type = 'mock'
    return mock_plugin


def create_entity_id_setter(work_id, manifestation_id, copyright_id,
                            type_key='@type'):
    def set_entity_id(entity_data, *args, **kwargs):
        if entity_data[type_key] == 'AbstractWork':
            return work_id
        elif entity_data[type_key] == 'Copyright':
            return copyright_id
        elif entity_data.get('manifestationOfWork', False):
            return manifestation_id
    return set_entity_id


def get_data_format_enum_member(data_format):
    from coalaip.data_formats import DataFormat
    return DataFormat(data_format)


def assert_key_values_present_in_dict(check_dict, **kwargs):
    from functools import reduce
    assert reduce(lambda present, k: present and check_dict.get(k) == kwargs[k],
                  kwargs, True)
