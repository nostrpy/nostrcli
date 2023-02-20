import json

import click
from click_aliases import ClickAliasedGroup

from nostr.key import PrivateKey, PublicKey


@click.group(cls=ClickAliasedGroup)
def cli():
    """Command related to key(s)."""


@cli.command(aliases=['gen', 'new'])
def create():
    """Creates a private and public key."""
    private_key = PrivateKey()
    public_key = private_key.public_key

    click.echo(
        json.dumps(
            {"Private key": private_key.bech32(), "Public key": public_key.bech32()},
            indent=2,
        )
    )


@cli.command()
@click.option("-i", "--identifier", required=True, type=str)
def convert(identifier: str):
    """Converts npub key to hex."""
    if "npub" in identifier:
        public_key = PublicKey.from_npub(identifier)
    else:
        public_key = PublicKey.from_hex(identifier)

    click.echo(
        json.dumps({"npub": public_key.bech32(), "hex": public_key.hex()}, indent=2)
    )
