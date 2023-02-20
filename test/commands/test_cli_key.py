import json
import unittest
from unittest.mock import ANY

from click.testing import CliRunner

from nostr.commands.key import convert, create


class TestCLIKey(unittest.TestCase):
    def test_create(self):
        # GIVEN
        runner = CliRunner()

        # WHEN
        result = runner.invoke(create, [])

        # THEN
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(
            json.loads(result.output), {"Private key": ANY, "Public key": ANY}
        )

    def test_convert_npub(self):
        # GIVEN
        npub = "npub1mg2nzunrsk9df94zr3uudhzltnu6lzq2muax09xmhu5gxxrvnkqsvpjg3p"
        runner = CliRunner()

        # WHEN
        result = runner.invoke(
            convert,
            [
                '-i',
                npub,
            ],
        )

        # THEN
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(json.loads(result.output), {"npub": npub, "hex": ANY})

    def test_convert_hex(self):
        # GIVEN
        hex = "1a60c40a7a897cb2eaffb666f477b895fafa3411defa0bee6ecdb3ecedc5b472"
        runner = CliRunner()

        # WHEN
        result = runner.invoke(
            convert,
            [
                '-i',
                hex,
            ],
        )

        # THEN
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(json.loads(result.output), {"npub": ANY, "hex": hex})
