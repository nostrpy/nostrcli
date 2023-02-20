import json
import unittest
from unittest.mock import ANY

from click.testing import CliRunner

from nostr.commands.message import publish, receive, send


class TestCLIMessage(unittest.TestCase):
    def test_publish(self):
        # GIVEN
        nsec = "nsec1lrjqzalcev9ard0274pu8ynwx0xzzexh56sfn0c97rumh8f2tfcqd3lf8h"
        message = "Hello nostr world!"
        runner = CliRunner()

        # WHEN
        result = runner.invoke(publish, ['-s', nsec, '-m', message])

        # THEN
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(json.loads(result.output), {"Message": message})

    def test_send(self):
        # GIVEN
        nsec = "nsec1jqaxtwk4tymddju9dmn58tdxgwgl5ck23gg847fla9cyuslxklrq86fcjd"
        npub = "npub1mg2nzunrsk9df94zr3uudhzltnu6lzq2muax09xmhu5gxxrvnkqsvpjg3p"
        message = "Hello nostr world!"
        runner = CliRunner()

        # WHEN
        result = runner.invoke(
            send,
            ['-s', nsec, '-m', message, '-p', npub],
        )

        # THEN
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(json.loads(result.output), {"Message": message})

    def test_receive(self):
        # GIVEN
        npub = "npub1mg2nzunrsk9df94zr3uudhzltnu6lzq2muax09xmhu5gxxrvnkqsvpjg3p"
        runner = CliRunner()

        # WHEN
        result = runner.invoke(
            receive,
            [
                '-p',
                npub,
            ],
        )

        # THEN
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(
            json.loads(result.output),
            {"Public key": npub, "Events": ANY, "Notices": ANY},
        )
