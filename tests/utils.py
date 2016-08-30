from unittest.mock import Mock
from coalaip.plugin import AbstractPlugin


def create_mock_plugin():
    mock_plugin = Mock(
        name="mock_ledger_plugin",
        spec_set=AbstractPlugin)
    mock_plugin.type = 'mock'
    return mock_plugin
