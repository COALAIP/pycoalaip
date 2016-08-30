from unittest.mock import Mock


def create_mock_plugin():
    mock_plugin = Mock(
        name="mock_ledger_plugin",
        spec_set=['generate_user', 'get_status', 'save', 'transfer', 'type'])
    mock_plugin.type = 'mock'
    return mock_plugin
