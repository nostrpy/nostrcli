import shutil
import unittest
from pathlib import Path
from unittest.mock import Mock, mock_open, patch

from nostr.commands.config import Config


class TestConfig(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.filename = 'config.hcl'

        cls.home_directory = Path.home().joinpath('.nostr')
        cls.home_directory.mkdir(exist_ok=True)

    @classmethod
    def tearDownClass(cls):
        if Path.cwd().joinpath(cls.filename).exists():
            Path.cwd().joinpath(cls.filename).unlink()
        if cls.home_directory.exists():
            shutil.rmtree(cls.home_directory, ignore_errors=True)

    def test_existing_file_in_cwd(self):
        # GIVEN
        Path.cwd().joinpath(self.filename).touch()
        expected_path = Path.cwd().joinpath(self.filename)
        # WHEN
        actual_path = Config.locate()
        # THEN
        self.assertEqual(expected_path, actual_path)

    def test_existing_file_in_home_directory(self):
        # GIVEN
        Path.cwd().joinpath(self.filename).unlink(missing_ok=True)
        self.home_directory.joinpath(self.filename).touch()
        expected_path = self.home_directory.joinpath(self.filename)
        # WHEN
        actual_path = Config.locate()
        # THEN
        self.assertEqual(expected_path, actual_path)

    def test_file_not_found(self):
        # GIVEN
        Path.cwd().joinpath(self.filename).unlink(missing_ok=True)
        shutil.rmtree(self.home_directory, ignore_errors=True)
        # WHEN
        actual = Config.locate()
        # THEN
        self.assertEqual(None, actual)

    @patch('builtins.open', new_callable=mock_open, read_data='key = "value"')
    def test_load_valid_file(self, mock_file):
        # Mock the locate method to return a valid file path
        Config.locate = Mock()
        Config.locate.return_value = "test.hcl"
        config = Config.load()
        mock_file.assert_called_once_with("test.hcl")
        self.assertEqual(config, {'key': 'value'})

    @patch('builtins.open', new_callable=mock_open, read_data='key = "value"')
    def test_load_valid_file_with_param(self, mock_file):
        # Mock the locate method to return a valid file path
        config = Config.load("test.hcl")
        mock_file.assert_called_once_with("test.hcl")
        self.assertEqual(config, {'key': 'value'})

    @patch('builtins.open', side_effect=FileNotFoundError)
    def test_load_file_not_found(self, mock_file):
        # Mock the locate method to return None
        Config.locate = Mock()
        Config.locate.return_value = None
        config = Config.load()
        self.assertEqual(config, {})

    def test_dump_with_content(self):
        content = {"key": "value"}
        result = Config.dump(content)
        expected_result = "{\n  \"key\": \"value\"\n}"
        self.assertEqual(result, expected_result)

    def test_dump_without_content(self):
        result = Config.dump()
        self.assertIsNone(result)
