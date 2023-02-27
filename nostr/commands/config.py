import json
from dataclasses import dataclass
from pathlib import Path

import hcl2


@dataclass
class Config:
    filename: str = "config.hcl"

    @classmethod
    def locate(cls) -> Path:
        """
        Locate config path

        # Search paths:
        # 1. ${CURRENT_PATH}/config.hcl
        # 2. ${HOME}/.nostr/config.hcl
        """
        paths = [
            Path.cwd().joinpath(cls.filename),
            Path.home().joinpath('.nostr', cls.filename),
        ]

        for path in paths:
            if path.exists():
                return path

        return None

    @classmethod
    def load(cls, filename: str = None) -> dict:
        """
        Load the config file
        """
        filename = filename or cls.locate()
        if filename:
            with open(filename) as file:
                return hcl2.load(file)
        return {}

    @staticmethod
    def dump(content: dict = None) -> str:
        """
        Dump the config content
        """
        if content:
            return json.dumps(content, indent=2)
