import unittest
from unittest.mock import mock_open, patch

from nostr.commands.config import Config


class TestConfig(unittest.TestCase):
    @patch('nostr.commands.config.Path')
    def test_locate_with_existing_file_in_cwd(self, mock_path):
        # GIVEN
        expected_path = mock_path('/cwd/path/to/config.hcl')
        # Mock the cwd method to return a known path
        mock_path.cwd.return_value.joinpath.return_value = expected_path
        mock_path.cwd.return_value.joinpath.return_value.exists.return_value = True

        mock_path.home.return_value.joinpath.return_value.exists.return_value = False

        # WHEN
        actual_path = Config.locate()
        # THEN
        self.assertEqual(expected_path, actual_path)
        mock_path.cwd.return_value.joinpath.assert_called_once_with('config.hcl')

    @patch('nostr.commands.config.Path')
    def test_locate_with_existing_file_in_home_directory(self, mock_path):
        # GIVEN
        expected_path = mock_path('/home/path/to/config.hcl')
        # Mock the home method to return a known path
        mock_path.home.return_value.joinpath.return_value = expected_path
        mock_path.home.return_value.joinpath.return_value.exists.return_value = True

        mock_path.cwd.return_value.joinpath.return_value.exists.return_value = False
        # WHEN
        actual_path = Config.locate()
        # THEN
        self.assertEqual(expected_path, actual_path)
        mock_path.home.return_value.joinpath.assert_called_once_with(
            '.nostr', 'config.hcl'
        )

    @patch('nostr.commands.config.Path')
    def test_locate_file_not_found(self, mock_path):
        # GIVEN
        mock_path.cwd.return_value.joinpath.return_value.exists.return_value = False
        mock_path.home.return_value.joinpath.return_value.exists.return_value = False
        # WHEN
        actual = Config.locate()
        # THEN
        self.assertEqual(None, actual)

    @patch('nostr.commands.config.Config.locate', return_value="test.hcl")
    @patch('builtins.open', new_callable=mock_open, read_data='key = "value"')
    def test_load_valid_file(self, mock_file, mock_locate):
        config = Config.load()
        mock_file.assert_called_once_with("test.hcl")
        self.assertEqual(config, {'key': 'value'})
        mock_locate.assert_called_once_with()

    @patch('nostr.commands.config.Config.locate')
    @patch('builtins.open', new_callable=mock_open, read_data='key = "value"')
    def test_load_valid_file_with_param(self, mock_file, mock_locate):
        config = Config.load("test.hcl")
        mock_file.assert_called_once_with("test.hcl")
        self.assertEqual(config, {'key': 'value'})
        mock_locate.assert_not_called()

    @patch('nostr.commands.config.Config.locate', return_value=None)
    @patch('builtins.open', side_effect=FileNotFoundError)
    def test_load_file_not_found(self, mock_file, mock_locate):
        config = Config.load()
        self.assertEqual(config, {})
        mock_locate.assert_called_once_with()

    def test_dump_with_content(self):
        content = {"key": "value"}
        result = Config.dump(content)
        expected_result = "{\n  \"key\": \"value\"\n}"
        self.assertEqual(result, expected_result)

    def test_dump_without_content(self):
        result = Config.dump()
        self.assertIsNone(result)
