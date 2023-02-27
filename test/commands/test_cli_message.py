import json
import unittest
from unittest import mock
from unittest.mock import ANY, MagicMock, patch

from click.testing import CliRunner

from nostr.commands.message import cli
from nostr.event import Event
from nostr.message_pool import EventMessage


class TestCLIMessage(unittest.TestCase):
    @patch('nostr.commands.message.RelayManager', autospec=True)
    def test_publish(self, mock_relay_manager):
        # GIVEN
        nsec = "nsec1lrjqzalcev9ard0274pu8ynwx0xzzexh56sfn0c97rumh8f2tfcqd3lf8h"
        message = "Hello nostr world!"
        runner = CliRunner()

        mock_manager = MagicMock()
        mock_relay_manager.return_value = mock_manager
        mock_manager.__enter__.return_value = mock_manager
        mock_manager.add_relay.return_value = None

        # WHEN
        result = runner.invoke(
            cli,
            ['publish', '-s', nsec, '-m', message, '--sleep', 0],
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
        nsec = "nsec1jqaxtwk4tymddju9dmn58tdxgwgl5ck23gg847fla9cyuslxklrq86fcjd"
        npub = "npub1mg2nzunrsk9df94zr3uudhzltnu6lzq2muax09xmhu5gxxrvnkqsvpjg3p"
        message = "Hello nostr world!"
        runner = CliRunner()

        mock_manager = MagicMock()
        mock_relay_manager.return_value = mock_manager
        mock_manager.__enter__.return_value = mock_manager
        mock_manager.add_relay.return_value = None

        # WHEN
        result = runner.invoke(
            cli,
            ['send', '-s', nsec, '-m', message, '-p', npub, '--sleep', 0],
        )

        # THEN
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(json.loads(result.output), {"Message": message})
        mock_manager.add_relay.assert_has_calls([mock.call(ANY), mock.call(ANY)])
        mock_manager.publish_event.assert_called()

    @patch('nostr.commands.message.RelayManager', autospec=True)
    def test_receive(self, mock_relay_manager):
        # GIVEN
        npub = "npub1mg2nzunrsk9df94zr3uudhzltnu6lzq2muax09xmhu5gxxrvnkqsvpjg3p"
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
            ['receive', '-p', npub, '-s', 0],
        )

        # THEN
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(
            json.loads(result.output),
            {"Public key(s)": [npub], "Events": ANY, "Notices": ANY},
        )
        mock_manager.add_relay.assert_has_calls([mock.call(ANY), mock.call(ANY)])
        mock_manager.publish_message.assert_called()
        mock_manager.message_pool.has_events.assert_called()
        mock_manager.message_pool.get_event.assert_called()
        mock_manager.message_pool.has_notices.assert_called()
        mock_manager.message_pool.get_notice.assert_not_called()
