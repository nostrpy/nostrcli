import json
import unittest
from pathlib import Path
from unittest import mock
from unittest.mock import ANY, MagicMock, patch

import hcl2
from click.testing import CliRunner

from nostr.commands.message import cli
from nostr.event import Event
from nostr.message_pool import EventMessage


class TestCLIMessageWithConfig(unittest.TestCase):
    def setUp(self):
        self.config_file = Path.cwd().joinpath('test', 'fixtures', 'config.hcl')
        with open(self.config_file) as file:
            self.config = hcl2.load(file)

    @patch('nostr.commands.message.RelayManager', autospec=True)
    def test_publish(self, mock_relay_manager):
        # GIVEN
        message = "Hello nostr world!!"
        runner = CliRunner()

        mock_manager = MagicMock()
        mock_relay_manager.return_value = mock_manager
        mock_manager.__enter__.return_value = mock_manager
        mock_manager.add_relay.return_value = None

        # WHEN
        result = runner.invoke(
            cli,
            ['-c', self.config_file, 'publish', '-m', message, '--sleep', 0],
            catch_exceptions=False,
        )

        # THEN
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(json.loads(result.output), {"Message": message})
        mock_manager.add_relay.assert_has_calls([mock.call(ANY), mock.call(ANY)])
        mock_manager.publish_message.assert_called()

    @patch('nostr.commands.message.RelayManager', autospec=True)
    def test_send(self, mock_relay_manager):
        # GIVEN
        message = "Hello nostr world!!"
        runner = CliRunner()

        mock_manager = MagicMock()
        mock_relay_manager.return_value = mock_manager
        mock_manager.__enter__.return_value = mock_manager
        mock_manager.add_relay.return_value = None

        # WHEN
        result = runner.invoke(
            cli,
            ['-c', self.config_file, 'send', '-m', message, '-i', 'Ray', '--sleep', 0],
        )

        # THEN
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(json.loads(result.output), {"Message": message})
        mock_manager.add_relay.assert_has_calls([mock.call(ANY), mock.call(ANY)])
        mock_manager.publish_event.assert_called()

    @patch('nostr.commands.message.RelayManager', autospec=True)
    def test_receive(self, mock_relay_manager):
        # GIVEN
        runner = CliRunner()

        mock_manager = MagicMock()
        mock_relay_manager.return_value = mock_manager
        mock_manager.__enter__.return_value = mock_manager
        mock_manager.add_relay.return_value = None

        mock_manager.message_pool.has_events.side_effect = [True, False]
        mock_manager.message_pool.get_event.return_value = EventMessage(
            Event(content="any"), subscription_id=123, url="wss://any.relay"
        )

        mock_manager.message_pool.has_notices.return_value = False

        # WHEN
        result = runner.invoke(
            cli,
            ['-c', self.config_file, 'receive', '-i', 'jon', '-s', 0],
        )

        # THEN
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(
            json.loads(result.output),
            {
                "Public key(s)": [self.config['nostr'][0]['listen'][0]['jon']['npub']],
                "Events": ANY,
                "Notices": ANY,
            },
        )
        mock_manager.add_relay.assert_has_calls([mock.call(ANY), mock.call(ANY)])
        mock_manager.publish_message.assert_called()
        mock_manager.message_pool.has_events.assert_called()
        mock_manager.message_pool.get_event.assert_called()
        mock_manager.message_pool.has_notices.assert_called()
        mock_manager.message_pool.get_notice.assert_not_called()
