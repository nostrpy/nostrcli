import json
import unittest
from pathlib import Path
from unittest.mock import ANY

import hcl2
from click.testing import CliRunner

from nostr.commands.message import cli


class TestCLIMessageWithConfig(unittest.TestCase):
    def setUp(self):
        self.config_file = Path.cwd().joinpath('test', 'fixtures', 'config.hcl')
        with open(self.config_file) as file:
            self.config = hcl2.load(file)

    def test_publish(self):
        # GIVEN
        message = "Hello nostr world!!"
        runner = CliRunner()

        # WHEN
        result = runner.invoke(
            cli,
            ['-c', self.config_file, 'publish', '-m', message],
            catch_exceptions=False,
        )

        # THEN
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(json.loads(result.output), {"Message": message})

    def test_send(self):
        # GIVEN
        message = "Hello nostr world!!"
        runner = CliRunner()

        # WHEN
        result = runner.invoke(
            cli,
            ['-c', self.config_file, 'send', '-m', message, '-i', 'Ray'],
        )

        # THEN
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(json.loads(result.output), {"Message": message})

    def test_receive(self):
        # GIVEN
        runner = CliRunner()

        # WHEN
        result = runner.invoke(
            cli,
            [
                '-c',
                self.config_file,
                'receive',
                '-i',
                'jon',
            ],
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
