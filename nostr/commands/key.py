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
    click.echo(f"Private key: {private_key.bech32()}")
    click.echo(f"Public key: {public_key.bech32()}")


@cli.command()
@click.option("-i", "--identifier", required=True, type=str)
def convert(identifier: str):
    """Converts npub key to hex."""
    if "npub" in identifier:
        public_key = PublicKey.from_npub(identifier)
    else:
        public_key = PublicKey.from_hex(identifier)
    click.echo(f"npub: {public_key.bech32()}")
    click.echo(f"hex: {public_key.hex()}")
